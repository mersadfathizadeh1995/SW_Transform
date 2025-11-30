"""Configuration handling for MASW 2D surveys.

Provides:
- Configuration schema and validation
- Config file loading and saving
- Templates for common survey types
"""

from .schema import validate_config, SURVEY_CONFIG_SCHEMA
from .loader import load_config, save_config, apply_defaults
from .templates import generate_standard_masw_template

__all__ = [
    "validate_config",
    "SURVEY_CONFIG_SCHEMA",
    "load_config",
    "save_config",
    "apply_defaults",
    "generate_standard_masw_template",
]
