"""Configuration schema definitions and validation.

Defines the structure and validation rules for MASW 2D survey configurations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


# Schema definition (for documentation and reference)
SURVEY_CONFIG_SCHEMA = {
    "survey_name": "string - Name of the survey",
    "version": "string - Config version (default: 1.0)",
    "array": {
        "n_channels": "int - Total number of geophones",
        "dx": "float - Geophone spacing in meters",
        "first_channel_position": "float - Position of first geophone (default: 0.0)"
    },
    "shots": [
        {
            "file": "string - Path to shot file (.dat)",
            "source_position": "float - Source position in meters",
            "label": "string (optional) - Label for this shot"
        }
    ],
    "subarray_configs": [
        {
            "n_channels": "int - Number of channels in sub-array",
            "slide_step": "int (optional) - Slide step in channels (default: 1)",
            "name": "string (optional) - Name for this configuration"
        }
    ],
    "processing": {
        "method": "string - Processing method: fk, fdbf, ps, ss",
        "freq_min": "float - Minimum frequency (Hz)",
        "freq_max": "float - Maximum frequency (Hz)",
        "velocity_min": "float - Minimum velocity (m/s)",
        "velocity_max": "float - Maximum velocity (m/s)",
        "grid_n": "int (optional) - Grid size for transform (default: 4000)",
        "tol": "float (optional) - Peak picking tolerance (default: 0.01)",
        "vspace": "string (optional) - Velocity spacing: log or linear (default: log)"
    },
    "output": {
        "directory": "string - Output directory path",
        "organize_by": "string - Organization: midpoint, shot, or flat (default: midpoint)",
        "export_formats": "list - Export formats: csv, npz (default: [csv])"
    }
}


def validate_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate configuration against schema.
    
    Parameters
    ----------
    config : dict
        Configuration dictionary to validate
    
    Returns
    -------
    tuple
        (is_valid: bool, errors: list of error messages)
    """
    errors = []
    
    # Required top-level fields
    if "survey_name" not in config:
        errors.append("Missing required field: survey_name")
    
    # Array configuration
    if "array" not in config:
        errors.append("Missing required field: array")
    else:
        array = config["array"]
        if "n_channels" not in array:
            errors.append("Missing required field: array.n_channels")
        elif not isinstance(array["n_channels"], int) or array["n_channels"] < 2:
            errors.append("array.n_channels must be an integer >= 2")
        
        if "dx" not in array:
            errors.append("Missing required field: array.dx")
        elif not isinstance(array["dx"], (int, float)) or array["dx"] <= 0:
            errors.append("array.dx must be a positive number")
    
    # Shots configuration
    if "shots" not in config:
        errors.append("Missing required field: shots")
    elif not isinstance(config["shots"], list):
        errors.append("shots must be a list")
    elif len(config["shots"]) == 0:
        errors.append("shots list cannot be empty")
    else:
        for i, shot in enumerate(config["shots"]):
            if "file" not in shot:
                errors.append(f"shots[{i}]: missing required field 'file'")
            if "source_position" not in shot:
                errors.append(f"shots[{i}]: missing required field 'source_position'")
            elif not isinstance(shot["source_position"], (int, float)):
                errors.append(f"shots[{i}]: source_position must be a number")
    
    # Sub-array configurations
    if "subarray_configs" not in config:
        errors.append("Missing required field: subarray_configs")
    elif not isinstance(config["subarray_configs"], list):
        errors.append("subarray_configs must be a list")
    elif len(config["subarray_configs"]) == 0:
        errors.append("subarray_configs list cannot be empty")
    else:
        array_n = config.get("array", {}).get("n_channels", 0)
        for i, sa_cfg in enumerate(config["subarray_configs"]):
            if "n_channels" not in sa_cfg:
                errors.append(f"subarray_configs[{i}]: missing required field 'n_channels'")
            elif not isinstance(sa_cfg["n_channels"], int) or sa_cfg["n_channels"] < 2:
                errors.append(f"subarray_configs[{i}]: n_channels must be an integer >= 2")
            elif array_n > 0 and sa_cfg["n_channels"] > array_n:
                errors.append(f"subarray_configs[{i}]: n_channels ({sa_cfg['n_channels']}) cannot exceed array.n_channels ({array_n})")
            
            if "slide_step" in sa_cfg:
                if not isinstance(sa_cfg["slide_step"], int) or sa_cfg["slide_step"] < 1:
                    errors.append(f"subarray_configs[{i}]: slide_step must be a positive integer")
    
    # Processing configuration (optional but validate if present)
    if "processing" in config:
        proc = config["processing"]
        if "method" in proc:
            valid_methods = ["fk", "fdbf", "ps", "ss"]
            if proc["method"] not in valid_methods:
                errors.append(f"processing.method must be one of: {valid_methods}")
        
        for key in ["freq_min", "freq_max", "velocity_min", "velocity_max"]:
            if key in proc and not isinstance(proc[key], (int, float)):
                errors.append(f"processing.{key} must be a number")
        
        if "freq_min" in proc and "freq_max" in proc:
            if proc["freq_min"] >= proc["freq_max"]:
                errors.append("processing.freq_min must be less than freq_max")
        
        if "velocity_min" in proc and "velocity_max" in proc:
            if proc["velocity_min"] >= proc["velocity_max"]:
                errors.append("processing.velocity_min must be less than velocity_max")
    
    # Output configuration (optional but validate if present)
    if "output" in config:
        out = config["output"]
        if "organize_by" in out:
            valid_org = ["midpoint", "shot", "flat"]
            if out["organize_by"] not in valid_org:
                errors.append(f"output.organize_by must be one of: {valid_org}")
        
        if "export_formats" in out:
            if not isinstance(out["export_formats"], list):
                errors.append("output.export_formats must be a list")
            else:
                valid_formats = ["csv", "npz", "image", "dinver"]
                for fmt in out["export_formats"]:
                    if fmt not in valid_formats:
                        errors.append(f"output.export_formats: unknown format '{fmt}'")
    
    return len(errors) == 0, errors


def validate_shot_files_exist(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Check that all shot files in config exist.
    
    Parameters
    ----------
    config : dict
        Configuration dictionary
    
    Returns
    -------
    tuple
        (all_exist: bool, missing_files: list)
    """
    import os
    
    missing = []
    for shot in config.get("shots", []):
        fpath = shot.get("file", "")
        if fpath and not os.path.isfile(fpath):
            missing.append(fpath)
    
    return len(missing) == 0, missing
