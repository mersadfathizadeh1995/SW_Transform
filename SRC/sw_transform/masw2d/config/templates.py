"""Configuration templates for common survey scenarios."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def generate_standard_masw_template(
    n_channels: int = 24,
    dx: float = 2.0,
    shot_files: Optional[List[str]] = None,
    shot_positions: Optional[List[float]] = None,
    subarray_sizes: Optional[List[int]] = None,
    survey_name: str = "Standard_MASW_Survey"
) -> Dict[str, Any]:
    """Generate configuration template for standard MASW survey.
    
    Standard MASW: Fixed array with multiple source offsets on both sides.
    
    Parameters
    ----------
    n_channels : int
        Total number of geophones (default: 24)
    dx : float
        Geophone spacing in meters (default: 2.0)
    shot_files : list of str, optional
        List of shot file paths
    shot_positions : list of float, optional
        List of source positions (same length as shot_files)
    subarray_sizes : list of int, optional
        Sub-array channel counts (default: [12, n_channels])
    survey_name : str
        Name for the survey
    
    Returns
    -------
    dict
        Configuration dictionary ready for use or saving
    
    Example
    -------
    >>> template = generate_standard_masw_template(
    ...     n_channels=24,
    ...     dx=2.0,
    ...     shot_files=["shot1.dat", "shot2.dat"],
    ...     shot_positions=[-10.0, -20.0]
    ... )
    """
    # Default sub-array sizes: half-array and full array
    if subarray_sizes is None:
        subarray_sizes = [n_channels // 2, n_channels]
    
    # Build sub-array configs
    subarray_configs = []
    for i, n_ch in enumerate(subarray_sizes):
        name = "shallow" if n_ch < n_channels else "deep"
        if len(subarray_sizes) > 2:
            name = f"config_{i+1}"
        subarray_configs.append({
            "n_channels": n_ch,
            "slide_step": 1,
            "name": name
        })
    
    template = {
        "survey_name": survey_name,
        "version": "1.0",
        
        "array": {
            "n_channels": n_channels,
            "dx": dx,
            "first_channel_position": 0.0
        },
        
        "shots": [],
        
        "subarray_configs": subarray_configs,
        
        "processing": {
            "method": "ps",
            "freq_min": 5.0,
            "freq_max": 80.0,
            "velocity_min": 100.0,
            "velocity_max": 1500.0,
            "grid_n": 4000,
            "tol": 0.01,
            "vspace": "log"
        },
        
        "output": {
            "directory": "./output_2d/",
            "organize_by": "midpoint",
            "export_formats": ["csv", "npz"]
        }
    }
    
    # Add shots if provided
    if shot_files and shot_positions:
        if len(shot_files) != len(shot_positions):
            raise ValueError("shot_files and shot_positions must have same length")
        
        for fpath, pos in zip(shot_files, shot_positions):
            template["shots"].append({
                "file": fpath,
                "source_position": pos
            })
    
    return template


def generate_template_from_file_assignment(
    rows: List[Any],
    n_channels: int = 24,
    dx: float = 2.0,
    subarray_sizes: Optional[List[int]] = None,
    survey_name: str = "Auto_MASW_Survey"
) -> Dict[str, Any]:
    """Generate config template from file_assignment rows.
    
    Uses the output of sw_transform.io.file_assignment.assign_files()
    to automatically populate shot files and positions.
    
    Parameters
    ----------
    rows : list
        List of assignment rows from assign_files()
    n_channels : int
        Total number of geophones
    dx : float
        Geophone spacing in meters
    subarray_sizes : list of int, optional
        Sub-array channel counts
    survey_name : str
        Name for the survey
    
    Returns
    -------
    dict
        Configuration dictionary
    """
    shot_files = []
    shot_positions = []
    
    for row in rows:
        # Support both legacy and native row types
        file_path = getattr(row, "file_path", None)
        if file_path is None:
            continue
        
        offset_m = getattr(row, "offset_m", None)
        if offset_m is None:
            continue
        
        shot_files.append(str(file_path))
        shot_positions.append(float(offset_m))
    
    if not shot_files:
        raise ValueError("No valid shots found in assignment rows")
    
    return generate_standard_masw_template(
        n_channels=n_channels,
        dx=dx,
        shot_files=shot_files,
        shot_positions=shot_positions,
        subarray_sizes=subarray_sizes,
        survey_name=survey_name
    )
