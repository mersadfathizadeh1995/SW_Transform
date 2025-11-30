"""Standard MASW workflow: Fixed array with multiple source offsets.

This is the primary workflow for Phase 1 of MASW 2D implementation.
It processes multiple shots from a fixed array, extracting sub-arrays
and generating dispersion curves at multiple midpoint positions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .base import BaseWorkflow
from ..config.loader import load_config
from ..geometry.shot_classifier import classify_all_shots, ShotType, filter_exterior_shots
from ..geometry.subarray import get_all_subarrays_from_config, flatten_subarrays
from ..extraction.subarray_extractor import extract_all_subarrays_from_shot
from ..processing.batch_processor import process_batch, DispersionResult
from ..output.organizer import organize_results


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
    ) -> Dict[str, Any]:
        """Execute the workflow.
        
        Parameters
        ----------
        output_dir : str, optional
            Output directory (overrides config if provided)
        
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
        
        # Process each shot
        all_results: List[DispersionResult] = []
        total_shots = len(shots)
        
        self._report_progress(0, total_shots, "Starting processing...")
        
        for shot_idx, shot in enumerate(shots):
            self._report_progress(
                shot_idx, total_shots,
                f"Processing shot {shot_idx + 1}/{total_shots}: {Path(shot.file).name}"
            )
            
            try:
                # Load shot data
                time, data, _, file_dx, dt, _ = load_seg2_ar(shot.file)
                
                # Use dx from config (file_dx may be 0)
                dx = self.config["array"]["dx"]
                if file_dx > 0:
                    dx = file_dx
                
                # Extract all valid sub-arrays
                extracted = extract_all_subarrays_from_shot(
                    data, time, dt, dx,
                    shot, subarrays,
                    reverse_if_needed=True
                )
                
                if not extracted:
                    continue
                
                # Process
                results = process_batch(
                    extracted,
                    method=method,
                    processing_params=proc_params
                )
                
                all_results.extend(results)
                
            except Exception as e:
                import warnings
                warnings.warn(f"Failed to process {shot.file}: {e}")
                continue
        
        self._report_progress(total_shots, total_shots, "Organizing results...")
        
        if not all_results:
            return {
                "status": "error",
                "error": "No dispersion curves were extracted",
                "n_results": 0
            }
        
        # Organize and export results
        output_config = self.config.get("output", {})
        export_formats = output_config.get("export_formats", ["csv"])
        organize_by = output_config.get("organize_by", "midpoint")
        # Check both include_images flag and 'image' in export_formats
        include_images = output_config.get("include_images", False) or ("image" in export_formats)
        
        # Image parameters - only include max_velocity if explicitly set
        image_params = {
            "max_frequency": output_config.get("max_frequency", None),
            "cmap": output_config.get("cmap", "jet"),
            "dpi": output_config.get("image_dpi", 150),
            "auto_velocity_limit": output_config.get("auto_velocity_limit", True)
        }
        # Only set max_velocity if explicitly configured (not auto)
        if "max_velocity" in output_config and not output_config.get("auto_velocity_limit", True):
            image_params["max_velocity"] = output_config["max_velocity"]
        
        summary = organize_results(
            all_results,
            output_dir,
            organize_by=organize_by,
            export_formats=export_formats,
            include_summary=True,
            include_images=include_images,
            image_params=image_params
        )
        
        # Add workflow info to summary
        summary["workflow"] = self.name
        summary["survey_name"] = self.survey_name
        summary["method"] = method
        summary["n_shots_processed"] = total_shots
        
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
