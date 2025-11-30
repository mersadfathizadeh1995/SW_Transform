"""Configuration loading and saving utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Union

from .schema import validate_config


# Default values for optional fields
DEFAULTS = {
    "version": "1.0",
    "array": {
        "first_channel_position": 0.0
    },
    "subarray_configs": {
        "slide_step": 1
    },
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
        "export_formats": ["csv"]
    }
}


def apply_defaults(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply default values for optional fields.
    
    Parameters
    ----------
    config : dict
        Configuration dictionary (modified in place)
    
    Returns
    -------
    dict
        Configuration with defaults applied
    """
    # Version
    if "version" not in config:
        config["version"] = DEFAULTS["version"]
    
    # Array defaults
    if "array" in config:
        if "first_channel_position" not in config["array"]:
            config["array"]["first_channel_position"] = DEFAULTS["array"]["first_channel_position"]
    
    # Sub-array config defaults
    if "subarray_configs" in config:
        for sa_cfg in config["subarray_configs"]:
            if "slide_step" not in sa_cfg:
                sa_cfg["slide_step"] = DEFAULTS["subarray_configs"]["slide_step"]
            if "name" not in sa_cfg:
                sa_cfg["name"] = f"{sa_cfg['n_channels']}ch"
    
    # Processing defaults
    if "processing" not in config:
        config["processing"] = DEFAULTS["processing"].copy()
    else:
        for key, val in DEFAULTS["processing"].items():
            if key not in config["processing"]:
                config["processing"][key] = val
    
    # Output defaults
    if "output" not in config:
        config["output"] = DEFAULTS["output"].copy()
    else:
        for key, val in DEFAULTS["output"].items():
            if key not in config["output"]:
                config["output"][key] = val
    
    return config


def load_config(path: Union[str, Path]) -> Dict[str, Any]:
    """Load and validate survey configuration from JSON file.
    
    Parameters
    ----------
    path : str or Path
        Path to configuration JSON file
    
    Returns
    -------
    dict
        Validated configuration with defaults applied
    
    Raises
    ------
    FileNotFoundError
        If configuration file doesn't exist
    ValueError
        If configuration is invalid
    json.JSONDecodeError
        If file is not valid JSON
    """
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # Validate
    valid, errors = validate_config(config)
    if not valid:
        raise ValueError(f"Invalid configuration:\n" + "\n".join(f"  - {e}" for e in errors))
    
    # Apply defaults
    config = apply_defaults(config)
    
    return config


def save_config(config: Dict[str, Any], path: Union[str, Path], validate: bool = True) -> None:
    """Save configuration to JSON file.
    
    Parameters
    ----------
    config : dict
        Configuration dictionary
    path : str or Path
        Output path for JSON file
    validate : bool
        If True, validate config before saving
    
    Raises
    ------
    ValueError
        If validation is enabled and config is invalid
    """
    if validate:
        valid, errors = validate_config(config)
        if not valid:
            raise ValueError(f"Invalid configuration:\n" + "\n".join(f"  - {e}" for e in errors))
    
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
