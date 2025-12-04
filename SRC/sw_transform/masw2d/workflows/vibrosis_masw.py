"""Vibrosis MASW workflow: Processing .mat files from Signal Calc.

This workflow processes vibrosis .mat files containing transfer functions
(G25_* variables) and generates dispersion curves using FDBF method.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .base import BaseWorkflow
from ..config.loader import load_config
from ..geometry.shot_classifier import ShotInfo, ShotType
from ..geometry.subarray import SubArrayDef, get_all_subarrays_from_config, flatten_subarrays
from ..extraction.vibrosis_extractor import (
    ExtractedVibrosisSubArray,
    extract_all_vibrosis_subarrays,
    extract_all_vibrosis_subarrays_from_file,
)
from ..processing.batch_processor import (
    DispersionResult,
    process_vibrosis_subarray,
    process_vibrosis_batch,
)
from ..output.organizer import organize_results


class VibrosisMASWWorkflow(BaseWorkflow):
    """Workflow for MASW with vibrosis .mat files.
    
    This workflow:
    1. Loads configuration (from file or dict)
    2. For each .mat file:
       a. Loads vibrosis data (transfer functions)
       b. Builds cross-spectral matrix R
       c. Extracts sub-arrays based on configuration
       d. Processes each sub-array using FDBF (only valid method)
    3. Organizes and exports results
    
    Parameters
    ----------
    config : dict or str
        Survey configuration dictionary or path to JSON config file
    
    Notes
    -----
    - Only FDBF method is supported for vibrosis .mat files
    - Cylindrical steering is enabled by default (recommended)
    - File must contain G25_* variables with transfer functions
    
    Examples
    --------
    >>> workflow = VibrosisMASWWorkflow("vibrosis_config.json")
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
        
        # Force FDBF method for vibrosis
        if "processing" not in config:
            config["processing"] = {}
        config["processing"]["method"] = "fdbf"
        
        super().__init__(config)
        self._subarray_defs = None
    
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
        # Get .mat files from config
        mat_files = self.config.get("mat_files", [])
        n_files = len(mat_files)
        
        n_subarrays = len(self.subarray_defs)
        
        # Unique midpoints
        midpoints = sorted(set(sa.midpoint for sa in self.subarray_defs))
        
        return {
            "survey_name": self.survey_name,
            "workflow": "vibrosis_masw",
            "array": self.config.get("array", {}),
            "n_mat_files": n_files,
            "n_subarray_configs": len(self.config.get("subarray_configs", [])),
            "n_subarrays_per_file": n_subarrays,
            "n_unique_midpoints": len(midpoints),
            "midpoints": midpoints,
            "expected_results": n_files * n_subarrays,
            "processing_method": "fdbf (vibrosis)"
        }
    
    def run(
        self,
        mat_files: Optional[List[str]] = None,
        output_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Dict[str, Any]:
        """Execute the vibrosis workflow.
        
        Parameters
        ----------
        mat_files : list of str, optional
            List of .mat file paths (overrides config if provided)
        output_dir : str, optional
            Output directory (overrides config if provided)
        progress_callback : callable, optional
            Progress callback function(current, total, message)
            
        Returns
        -------
        dict
            Summary including status, counts, file paths, etc.
        """
        from sw_transform.processing.vibrosis import load_vibrosis_mat
        
        # Use provided callback or instance callback
        if progress_callback:
            self.set_progress_callback(progress_callback)
        
        # Determine output directory
        output_dir = output_dir or self.config.get("output", {}).get("directory", "./output_2d/")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Get .mat files
        if mat_files is None:
            mat_files = self.config.get("mat_files", [])
        
        if not mat_files:
            return {
                "status": "error",
                "error": "No .mat files provided",
                "n_results": 0
            }
        
        # Get sub-array definitions
        subarrays = self.subarray_defs
        if not subarrays:
            return {
                "status": "error",
                "error": "No sub-array definitions found",
                "n_results": 0
            }
        
        # Get processing parameters
        proc_params = self.config.get("processing", {})
        # Ensure cylindrical steering is enabled for vibrosis
        proc_params.setdefault("cylindrical", True)
        
        # Get dx from config
        dx = self.config.get("array", {}).get("dx", None)
        if dx is None:
            return {
                "status": "error",
                "error": "dx (receiver spacing) not found in config",
                "n_results": 0
            }
        
        # Process each .mat file
        all_results: List[DispersionResult] = []
        total_files = len(mat_files)
        
        # Build mapping from file path to source_position from shots config
        shots_config = self.config.get("shots", [])
        source_positions = {}
        for shot in shots_config:
            shot_file = shot.get("file", "")
            # Normalize path for comparison
            shot_file_norm = str(Path(shot_file).resolve()) if shot_file else ""
            source_positions[shot_file_norm] = shot.get("source_position", 0.0)
        
        self._report_progress(0, total_files, "Starting vibrosis processing...")
        
        for file_idx, mat_file in enumerate(mat_files):
            mat_path = Path(mat_file)
            self._report_progress(
                file_idx, total_files,
                f"Processing file {file_idx + 1}/{total_files}: {mat_path.name}"
            )
            
            try:
                # Load vibrosis data
                vibrosis_data = load_vibrosis_mat(str(mat_path))
                
                # Get source_position from shots config, default to 0.0 if not found
                mat_path_norm = str(mat_path.resolve())
                source_pos = source_positions.get(mat_path_norm, 0.0)
                
                # Create shot info for this file
                # For vibrosis we typically have source outside array
                shot_info = ShotInfo(
                    file=str(mat_path),
                    source_position=source_pos,
                    shot_type=ShotType.EXTERIOR_LEFT  # Default for vibrosis
                )
                
                # Extract all sub-arrays
                extracted = extract_all_vibrosis_subarrays(
                    vibrosis_data, dx, subarrays, shot_info
                )
                
                if not extracted:
                    import warnings
                    warnings.warn(f"No valid sub-arrays extracted from {mat_path.name}")
                    continue
                
                # Process each extracted sub-array
                results = process_vibrosis_batch(
                    extracted,
                    processing_params=proc_params
                )
                
                all_results.extend(results)
                
            except Exception as e:
                import warnings
                warnings.warn(f"Failed to process {mat_path.name}: {e}")
                continue
        
        self._report_progress(total_files, total_files, "Organizing results...")
        
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
        include_images = (
            output_config.get("include_images", False) or 
            any(fmt in export_formats for fmt in ("image", "png", "jpg", "jpeg"))
        )
        
        # Image parameters
        image_params = {
            "max_frequency": output_config.get("max_frequency", None),
            "cmap": output_config.get("cmap", "jet"),
            "dpi": output_config.get("image_dpi", 150),
            "auto_velocity_limit": output_config.get("auto_velocity_limit", True),
            "auto_frequency_limit": output_config.get("auto_frequency_limit", True)
        }
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
        summary["workflow"] = "vibrosis_masw"
        summary["survey_name"] = self.survey_name
        summary["method"] = "fdbf"
        summary["source_type"] = "vibrosis"
        summary["n_files_processed"] = total_files
        
        self._report_progress(total_files, total_files, "Complete!")
        
        return summary


def run_vibrosis_masw(
    config_path: str,
    mat_files: Optional[List[str]] = None,
    output_dir: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Dict[str, Any]:
    """Convenience function to run vibrosis MASW workflow.
    
    Parameters
    ----------
    config_path : str
        Path to configuration JSON file
    mat_files : list of str, optional
        List of .mat file paths (overrides config)
    output_dir : str, optional
        Output directory (overrides config)
    progress_callback : callable, optional
        Progress callback function(current, total, message)
    
    Returns
    -------
    dict
        Workflow results summary
    """
    workflow = VibrosisMASWWorkflow(config_path)
    if progress_callback:
        workflow.set_progress_callback(progress_callback)
    return workflow.run(mat_files=mat_files, output_dir=output_dir)


def process_mat_file_direct(
    mat_file: str,
    dx: float,
    subarray_configs: List[Dict[str, Any]],
    processing_params: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[DispersionResult]:
    """Process a single .mat file directly without config file.
    
    This is a simplified interface for GUI use.
    
    Parameters
    ----------
    mat_file : str
        Path to .mat file
    dx : float
        Receiver spacing (m)
    subarray_configs : list of dict
        Sub-array configuration dictionaries with keys:
        - n_channels: Number of channels
        - start_offset: Offset from source (m)
        - (optional) name: Configuration name
    processing_params : dict, optional
        Processing parameters (freq_min, freq_max, etc.)
    progress_callback : callable, optional
        Progress callback function(current, total, message)
        
    Returns
    -------
    list of DispersionResult
        Dispersion analysis results
    """
    from sw_transform.processing.vibrosis import load_vibrosis_mat
    
    # Load vibrosis data
    vibrosis_data = load_vibrosis_mat(mat_file)
    
    # Build sub-array definitions
    from ..geometry.subarray import SubArrayDef
    
    subarrays = []
    for cfg in subarray_configs:
        n_ch = cfg.get("n_channels", 24)
        start = cfg.get("start_offset", 0.0)
        length = (n_ch - 1) * dx
        midpoint = start + length / 2
        name = cfg.get("name", f"{n_ch}ch_{start}m")
        
        subarrays.append(SubArrayDef(
            name=name,
            n_channels=n_ch,
            start_offset=start,
            length=length,
            midpoint=midpoint
        ))
    
    # Create shot info
    shot_info = ShotInfo(
        file=mat_file,
        source_position=0.0,
        shot_type=ShotType.EXTERIOR_LEFT
    )
    
    # Extract all sub-arrays
    extracted = extract_all_vibrosis_subarrays(
        vibrosis_data, dx, subarrays, shot_info
    )
    
    if not extracted:
        return []
    
    # Process
    params = processing_params.copy() if processing_params else {}
    params.setdefault("cylindrical", True)
    
    return process_vibrosis_batch(extracted, processing_params=params)
