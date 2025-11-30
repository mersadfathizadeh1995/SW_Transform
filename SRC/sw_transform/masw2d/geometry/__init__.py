"""Geometry calculations for MASW 2D surveys.

Provides:
- Shot classification (exterior, edge, interior)
- Sub-array definition and enumeration
- Midpoint and offset calculations
"""

from .shot_classifier import (
    ShotType,
    ShotInfo,
    classify_shot,
    classify_all_shots,
)
from .subarray import (
    SubArrayDef,
    enumerate_subarrays,
    get_all_subarrays_from_config,
)
from .midpoint import (
    calculate_source_offset,
    is_valid_offset,
    get_array_bounds,
)

__all__ = [
    "ShotType",
    "ShotInfo",
    "classify_shot",
    "classify_all_shots",
    "SubArrayDef",
    "enumerate_subarrays",
    "get_all_subarrays_from_config",
    "calculate_source_offset",
    "is_valid_offset",
    "get_array_bounds",
]
