"""Configuration templates for common survey scenarios."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# Source Type Definitions and Depth Factors
# =============================================================================

# Depth factors relative to array length (L)
# Based on realistic field experience:
# - Factor range: (min_factor, max_factor) where depth = L * factor
SOURCE_DEPTH_FACTORS = {
    "hammer": (0.33, 0.55),           # Sledgehammer 5-8kg: 15-25m for 46m
    "heavy_hammer": (0.43, 0.65),     # Heavy sledgehammer 10+kg: 20-30m for 46m
    "weight_drop": (0.65, 1.1),       # Accelerated weight drop: 30-50m for 46m
    "vibroseis": (0.87, 1.5),         # Vibroseis/controlled source: 40-70m for 46m
}

SOURCE_LABELS = {
    "hammer": "Sledgehammer (5-8 kg)",
    "heavy_hammer": "Heavy Sledgehammer (10+ kg)",
    "weight_drop": "Accelerated Weight Drop",
    "vibroseis": "Vibroseis / Controlled Source",
}


def get_source_types() -> list:
    """Get list of available source types."""
    return list(SOURCE_DEPTH_FACTORS.keys())


def get_source_label(source_type: str) -> str:
    """Get human-readable label for source type."""
    return SOURCE_LABELS.get(source_type, source_type)


def calculate_depth_range(
    array_length: float,
    source_type: str = "hammer"
) -> Tuple[float, float]:
    """Calculate realistic depth range based on array length and source type.
    
    Parameters
    ----------
    array_length : float
        Length of the sub-array in meters
    source_type : str
        Source type: 'hammer', 'heavy_hammer', 'weight_drop', 'vibroseis'
    
    Returns
    -------
    tuple of float
        (min_depth, max_depth) in meters
    """
    if source_type not in SOURCE_DEPTH_FACTORS:
        source_type = "hammer"
    
    min_factor, max_factor = SOURCE_DEPTH_FACTORS[source_type]
    return (array_length * min_factor, array_length * max_factor)


# =============================================================================
# Sub-array Preset Generators
# =============================================================================

def get_available_subarray_sizes(
    total_channels: int,
    min_channels: int = 6,
    step: int = 1
) -> List[int]:
    """Get all valid sub-array sizes for a given total channel count.
    
    Parameters
    ----------
    total_channels : int
        Total number of channels in the array
    min_channels : int
        Minimum sub-array size (default: 6)
    step : int
        Step between sizes (1 = all, 2 = even only)
    
    Returns
    -------
    list of int
        Valid sub-array sizes from min_channels to total_channels
    """
    sizes = list(range(min_channels, total_channels + 1, step))
    if total_channels not in sizes:
        sizes.append(total_channels)
    return sorted(sizes)


def calculate_subarray_info(
    n_channels: int,
    dx: float,
    total_channels: int,
    source_type: str = "hammer"
) -> Dict[str, Any]:
    """Calculate information about a sub-array configuration.
    
    Parameters
    ----------
    n_channels : int
        Number of channels in the sub-array
    dx : float
        Geophone spacing (m)
    total_channels : int
        Total channels in the full array
    source_type : str
        Source type for depth estimation: 'hammer', 'heavy_hammer', 
        'weight_drop', 'vibroseis'
    
    Returns
    -------
    dict
        Contains: array_length, depth_range, n_midpoints, midpoint_range, etc.
    """
    array_length = (n_channels - 1) * dx
    
    # Calculate depth range based on source type
    depth_min, depth_max = calculate_depth_range(array_length, source_type)
    
    # Also keep theoretical L/2 for reference
    theoretical_depth = array_length / 2
    
    # Number of possible sub-arrays (with slide_step=1)
    n_midpoints = total_channels - n_channels + 1
    
    # Midpoint range
    first_midpoint = (n_channels - 1) * dx / 2
    last_midpoint = (total_channels - 1) * dx - first_midpoint
    
    return {
        "n_channels": n_channels,
        "array_length": array_length,
        "depth_min": depth_min,
        "depth_max": depth_max,
        "theoretical_depth": theoretical_depth,
        "source_type": source_type,
        "n_midpoints": n_midpoints,
        "first_midpoint": first_midpoint,
        "last_midpoint": last_midpoint,
        "midpoint_spacing": dx  # with slide_step=1
    }


def get_all_subarray_info(
    total_channels: int,
    dx: float,
    min_channels: int = 6,
    source_type: str = "hammer"
) -> List[Dict[str, Any]]:
    """Get info for all possible sub-array sizes.
    
    Parameters
    ----------
    total_channels : int
        Total number of channels
    dx : float
        Geophone spacing (m)
    min_channels : int
        Minimum sub-array size
    source_type : str
        Source type for depth estimation
    
    Returns
    -------
    list of dict
        Info for each valid sub-array size, sorted by n_channels
    """
    sizes = get_available_subarray_sizes(total_channels, min_channels)
    return [calculate_subarray_info(s, dx, total_channels, source_type) for s in sizes]


def generate_subarray_configs(
    sizes: List[int],
    slide_step: int = 1,
    naming: str = "auto"
) -> List[Dict[str, Any]]:
    """Generate subarray_configs list for config template.
    
    Parameters
    ----------
    sizes : list of int
        Channel counts for each sub-array config
    slide_step : int
        Sliding step in channels
    naming : str
        Naming scheme: 'auto', 'depth', 'numbered'
    
    Returns
    -------
    list of dict
        Ready-to-use subarray_configs
    """
    configs = []
    sorted_sizes = sorted(sizes)
    
    for i, n_ch in enumerate(sorted_sizes):
        if naming == "depth":
            name = f"{n_ch}ch"
        elif naming == "numbered":
            name = f"config_{i+1}"
        else:  # auto
            if len(sorted_sizes) == 1:
                name = "full"
            elif n_ch == sorted_sizes[0]:
                name = "shallow"
            elif n_ch == sorted_sizes[-1]:
                name = "deep"
            else:
                name = f"mid_{n_ch}ch"
        
        configs.append({
            "n_channels": n_ch,
            "slide_step": slide_step,
            "name": name
        })
    
    return configs


# =============================================================================
# Main Template Generators
# =============================================================================

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
            "vspace": "log",
            "start_time": 0.0,
            "end_time": 1.0,
            "downsample": True,
            "down_factor": 16,
            "numf": 4000
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
