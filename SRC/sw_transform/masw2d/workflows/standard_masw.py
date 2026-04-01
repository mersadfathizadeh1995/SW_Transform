"""Standard MASW workflow: Fixed array with multiple source offsets.

This is the primary workflow for Phase 1 of MASW 2D implementation.
It processes multiple shots from a fixed array, extracting sub-arrays
and generating dispersion curves at multiple midpoint positions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from .base import BaseWorkflow
from ..config.loader import load_config
from ..geometry.shot_classifier import classify_all_shots, ShotType, filter_exterior_shots
from ..geometry.subarray import get_all_subarrays_from_config, flatten_subarrays
from ..extraction.subarray_extractor import extract_all_subarrays_from_shot
from ..processing.batch_processor import process_batch, DispersionResult
from ..output.organizer import (
    organize_results, export_single_result, write_summary_from_metadata,
    write_combined_csv_per_midpoint, write_combined_npz_per_midpoint
)


def _load_npz_metadata(data) -> dict:
    """Reconstruct metadata dict from NPZ file, handling mixed types safely."""
    meta = {}
    for k in data.files:
        if k.startswith('meta_'):
            key = k.replace('meta_', '', 1)
            val = data[k]
            if val.ndim == 0:
                try:
                    meta[key] = float(val)
                except (ValueError, TypeError):
                    meta[key] = str(val)
            else:
                meta[key] = val
    return meta


class StandardMASWWorkflow(BaseWorkflow):
    """Workflow for standard MASW with fixed array and multiple shots.
    
    This workflow:
    1. Loads configuration (from file or dict)
    2. Classifies all shots (exterior, edge, interior)
    3. Filters to exterior shots only (Phase 1)
    4. Defines sub-arrays based on configuration
    5. For each shot:
       a. Loads shot data
       b. Extracts all valid sub-arrays
       c. Processes each sub-array for dispersion curve
    6. Organizes and exports results
    
    Parameters
    ----------
    config : dict or str
        Survey configuration dictionary or path to JSON config file
    
    Examples
    --------
    >>> workflow = StandardMASWWorkflow("survey_config.json")
    >>> results = workflow.run(output_dir="./output")
    >>> print(f"Processed {results['n_results']} dispersion curves")
    """
    
    def __init__(self, config):
        """Initialize workflow with configuration.
        
        Parameters
        ----------
        config : dict or str or Path
            Configuration dictionary or path to config file
        """
        if isinstance(config, (str, Path)):
            config = load_config(config)
        super().__init__(config)
        
        # Lazy-loaded properties
        self._classified_shots = None
        self._subarray_defs = None
    
    @property
    def classified_shots(self):
        """Get classified shots (cached)."""
        if self._classified_shots is None:
            self._classified_shots = classify_all_shots(
                self.config["shots"],
                self.config["array"]
            )
        return self._classified_shots
    
    @property
    def exterior_shots(self):
        """Get exterior shots only."""
        return filter_exterior_shots(self.classified_shots)
    
    @property
    def subarray_defs(self):
        """Get all sub-array definitions (cached)."""
        if self._subarray_defs is None:
            sa_dict = get_all_subarrays_from_config(self.config)
            self._subarray_defs = flatten_subarrays(sa_dict)
        return self._subarray_defs
    
    def get_info(self) -> Dict[str, Any]:
        """Get workflow information without running.
        
        Returns
        -------
        dict
            Information about the workflow configuration
        """
        n_shots = len(self.config.get("shots", []))
        n_exterior = len(self.exterior_shots)
        n_subarrays = len(self.subarray_defs)
        
        # Unique midpoints
        midpoints = sorted(set(sa.midpoint for sa in self.subarray_defs))
        
        # Expected number of results (exterior shots × sub-arrays)
        expected_results = n_exterior * n_subarrays
        
        return {
            "survey_name": self.survey_name,
            "workflow": self.name,
            "array": self.config.get("array", {}),
            "n_total_shots": n_shots,
            "n_exterior_shots": n_exterior,
            "n_subarray_configs": len(self.config.get("subarray_configs", [])),
            "n_subarrays_per_shot": n_subarrays,
            "n_unique_midpoints": len(midpoints),
            "midpoints": midpoints,
            "expected_results": expected_results,
            "processing_method": self.config.get("processing", {}).get("method", "ps")
        }
    
    def run(
        self,
        output_dir: Optional[str] = None,
        parallel: bool = False,
        max_workers: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute the workflow.
        
        Results are written to disk incrementally (CSV/NPZ) as produced,
        keeping memory usage bounded. Images are deferred to after all
        processing completes to avoid matplotlib overhead during transforms.
        
        Parameters
        ----------
        output_dir : str, optional
            Output directory (overrides config if provided)
        parallel : bool
            If True, process sub-arrays in parallel
        max_workers : int, optional
            Number of parallel workers (default: auto)
        
        Returns
        -------
        dict
            Summary including status, counts, file paths, etc.
        """
        from sw_transform.processing.seg2 import load_seg2_ar
        
        # Determine output directory
        output_dir = output_dir or self.config.get("output", {}).get("directory", "./output_2d/")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Get exterior shots
        shots = self.exterior_shots
        if not shots:
            return {
                "status": "error",
                "error": "No exterior shots found in configuration",
                "n_results": 0
            }
        
        # Get sub-array definitions
        subarrays = self.subarray_defs
        
        # Get processing parameters
        proc_params = self.config.get("processing", {})
        method = proc_params.get("method", "ps")
        
        # Prepare export settings
        output_config = self.config.get("output", {})
        export_formats = output_config.get("export_formats", ["csv"])
        organize_by = output_config.get("organize_by", "midpoint")
        include_images = (
            output_config.get("include_images", False) or
            any(fmt in export_formats for fmt in ("image", "png", "jpg", "jpeg"))
        )
        image_params = {
            "max_frequency": output_config.get("max_frequency", None),
            "cmap": output_config.get("cmap", "jet"),
            "dpi": output_config.get("image_dpi", 150),
            "auto_velocity_limit": output_config.get("auto_velocity_limit", True),
            "auto_frequency_limit": output_config.get("auto_frequency_limit", True)
        }
        if "max_velocity" in output_config and not output_config.get("auto_velocity_limit", True):
            image_params["max_velocity"] = output_config["max_velocity"]
        
        # When images are deferred, NPZ must be saved during processing
        # so the image renderer can read data back without keeping it in RAM.
        # Also needed for combined NPZ per midpoint.
        export_fmts_for_processing = list(export_formats)
        needs_npz = (
            include_images or
            output_config.get("export_combined_npz_per_midpoint", True) or
            output_config.get("export_individual_npz", True)
        )
        if needs_npz and "npz" not in export_fmts_for_processing:
            export_fmts_for_processing.append("npz")
        
        # Lightweight metadata list (replaces all_results accumulation)
        all_results_meta: List[Dict[str, Any]] = []
        all_exported_files: List[str] = []
        total_shots = len(shots)
        
        self._report_progress(0, total_shots, "Starting processing...")
        
        if parallel:
            # Parallel processing: collect all extracted sub-arrays first
            all_extracted = []
            for shot_idx, shot in enumerate(shots):
                self._report_progress(
                    shot_idx, total_shots,
                    f"Extracting shot {shot_idx + 1}/{total_shots}: {Path(shot.file).name}"
                )
                try:
                    time, data, _, file_dx, dt, _ = load_seg2_ar(shot.file)
                    dx = self.config["array"]["dx"]
                    if file_dx > 0:
                        dx = file_dx
                    
                    extracted = extract_all_subarrays_from_shot(
                        data, time, dt, dx,
                        shot, subarrays,
                        reverse_if_needed=True
                    )
                    all_extracted.extend(extracted)
                except Exception as e:
                    import warnings
                    warnings.warn(f"Failed to extract from {shot.file}: {e}")
                    continue
            
            if all_extracted:
                self._report_progress(total_shots, total_shots, 
                    f"Processing {len(all_extracted)} sub-arrays in parallel...")
                
                from sw_transform.masw2d.processing.batch_processor import process_batch_parallel
                results = process_batch_parallel(
                    all_extracted,
                    method=method,
                    processing_params=proc_params,
                    max_workers=max_workers,
                    progress_callback=self._progress_callback
                )
                
                # Write CSV/NPZ immediately (no images yet), then release
                for result in results:
                    meta = export_single_result(
                        result, output_dir,
                        organize_by=organize_by,
                        export_formats=export_fmts_for_processing,
                        include_images=False,
                        image_params=image_params
                    )
                    all_results_meta.append(meta)
                    all_exported_files.extend(meta['files'])
                del results  # Free memory
        else:
            # Sequential processing with incremental disk writes
            for shot_idx, shot in enumerate(shots):
                self._report_progress(
                    shot_idx, total_shots,
                    f"Processing shot {shot_idx + 1}/{total_shots}: {Path(shot.file).name}"
                )
                
                try:
                    time, data, _, file_dx, dt, _ = load_seg2_ar(shot.file)
                    dx = self.config["array"]["dx"]
                    if file_dx > 0:
                        dx = file_dx
                    
                    extracted = extract_all_subarrays_from_shot(
                        data, time, dt, dx,
                        shot, subarrays,
                        reverse_if_needed=True
                    )
                    
                    if not extracted:
                        continue
                    
                    results = process_batch(
                        extracted,
                        method=method,
                        processing_params=proc_params
                    )
                    
                    # Write CSV/NPZ immediately (no images yet), then release
                    for result in results:
                        meta = export_single_result(
                            result, output_dir,
                            organize_by=organize_by,
                            export_formats=export_fmts_for_processing,
                            include_images=False,
                            image_params=image_params
                        )
                        all_results_meta.append(meta)
                        all_exported_files.extend(meta['files'])
                    del results  # Free memory
                    
                except Exception as e:
                    import warnings
                    warnings.warn(f"Failed to process {shot.file}: {e}")
                    continue
        
        self._report_progress(total_shots, total_shots, "Writing summary...")
        
        if not all_results_meta:
            return {
                "status": "error",
                "error": "No dispersion curves were extracted",
                "n_results": 0
            }
        
        # Write combined CSV per midpoint (for DC Cut compatibility)
        if output_config.get("export_combined_csv_per_midpoint", True):
            combined_csv_files = write_combined_csv_per_midpoint(
                all_results_meta, output_dir, organize_by
            )
            all_exported_files.extend(combined_csv_files)
        
        # Write combined NPZ per midpoint (for refinement workflow)
        if output_config.get("export_combined_npz_per_midpoint", True):
            combined_npz_files = write_combined_npz_per_midpoint(
                all_results_meta, output_dir, organize_by
            )
            all_exported_files.extend(combined_npz_files)
        
        # Write summary files (optional, controlled by config)
        generate_summary = output_config.get("generate_summary", True)
        summary_result = {}
        
        if generate_summary:
            export_midpoint_summary = output_config.get("export_midpoint_summary", True)
            export_all_picks = output_config.get("export_all_picks", True)
            export_combined_npz = output_config.get("export_combined_npz", False)
            
            summary_result = write_summary_from_metadata(
                all_results_meta, output_dir,
                write_midpoint_summary=export_midpoint_summary,
                write_all_picks=export_all_picks,
                write_combined_npz=export_combined_npz,
            )
            all_exported_files.extend(summary_result['files'])
        
        # Deferred image export: render PNGs from saved NPZ files (after processing)
        if include_images:
            npz_files = [m['npz_path'] for m in all_results_meta if m.get('npz_path')]
            if npz_files:
                self._report_progress(total_shots, total_shots, "Rendering images...")
                from ..output.export import export_dispersion_image
                from ..processing.batch_processor import DispersionResult as DR
                for i, npz_path in enumerate(npz_files):
                    try:
                        with np.load(npz_path, allow_pickle=True) as data:
                            result = DR(
                                frequencies=data['frequencies'],
                                velocities=data['velocities'],
                                power=data['power'],
                                picked_velocities=data['picked_velocities'],
                                wavelengths=data['wavelengths'],
                                midpoint=float(data['midpoint']),
                                subarray_config=str(data['subarray_config']),
                                shot_file=str(data.get('shot_file', '')),
                                source_offset=float(data['source_offset']),
                                source_position=float(data.get('source_position', 0.0)),
                                direction=str(data['direction']),
                                method=str(data['method']),
                                metadata=_load_npz_metadata(data)
                            )
                        png_path = npz_path.replace('.npz', '.png')
                        img_p = image_params.copy()
                        img_p.setdefault('auto_velocity_limit', True)
                        img_p.setdefault('auto_frequency_limit', True)
                        export_dispersion_image(result, png_path, **img_p)
                        all_exported_files.append(png_path)
                        del result
                    except Exception as e:
                        import warnings
                        warnings.warn(f"Failed to render image from {npz_path}: {e}")
        
        midpoints = sorted(set(m['midpoint'] for m in all_results_meta))
        
        summary = {
            "status": "success",
            "n_results": len(all_results_meta),
            "n_midpoints": len(midpoints),
            "midpoints": midpoints,
            "files": all_exported_files,
            "organize_by": organize_by,
            "summary": summary_result.get('summary', {}),
            "workflow": self.name,
            "survey_name": self.survey_name,
            "method": method,
            "n_shots_processed": total_shots,
        }
        
        self._report_progress(total_shots, total_shots, "Complete!")
        
        return summary


def run_standard_masw(
    config_path: str,
    output_dir: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Dict[str, Any]:
    """Convenience function to run standard MASW workflow.
    
    Parameters
    ----------
    config_path : str
        Path to configuration JSON file
    output_dir : str, optional
        Output directory (overrides config)
    progress_callback : callable, optional
        Progress callback function(current, total, message)
    
    Returns
    -------
    dict
        Workflow results summary
    """
    workflow = StandardMASWWorkflow(config_path)
    if progress_callback:
        workflow.set_progress_callback(progress_callback)
    return workflow.run(output_dir=output_dir)
