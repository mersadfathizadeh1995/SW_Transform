"""Geometry calculations for MASW 2D surveys.

Provides:
- Shot classification (exterior, edge, interior)
- Sub-array definition and enumeration
- Midpoint and offset calculations
- Layout visualization
- Intelligent shot-subarray assignment engine
"""

from .shot_classifier import (
    ShotType,
    ShotInfo,
    classify_shot,
    classify_all_shots,
    classify_shot_for_subarray,
)
from .subarray import (
    SubArrayDef,
    enumerate_subarrays,
    get_all_subarrays_from_config,
)
from .midpoint import (
    calculate_source_offset,
    calculate_source_offset_for_subarray,
    is_valid_offset,
    get_array_bounds,
)
from .layout import (
    LayoutInfo,
    calculate_layout,
    get_subarray_bounds,
    format_layout_summary,
    plot_layout,
    plot_all_configs_comparison,
)
from .shot_assigner import (
    AssignmentStrategy,
    RelationType,
    AssignmentConstraints,
    SubArrayShotRelation,
    ShotAssignment,
    AssignmentPlan,
    build_compatibility_matrix,
    generate_assignment_plan,
    generate_plan_from_config,
)

__all__ = [
    "ShotType",
    "ShotInfo",
    "classify_shot",
    "classify_all_shots",
    "classify_shot_for_subarray",
    "SubArrayDef",
    "enumerate_subarrays",
    "get_all_subarrays_from_config",
    "calculate_source_offset",
    "calculate_source_offset_for_subarray",
    "is_valid_offset",
    "get_array_bounds",
    "LayoutInfo",
    "calculate_layout",
    "get_subarray_bounds",
    "format_layout_summary",
    "plot_layout",
    "plot_all_configs_comparison",
    # Shot-subarray assignment engine
    "AssignmentStrategy",
    "RelationType",
    "AssignmentConstraints",
    "SubArrayShotRelation",
    "ShotAssignment",
    "AssignmentPlan",
    "build_compatibility_matrix",
    "generate_assignment_plan",
    "generate_plan_from_config",
]
