"""Predefined workflows for MASW 2D processing.

Provides:
- Standard MASW workflow (fixed array, multiple source offsets)
- Assignment-based MASW workflow (intelligent shot-subarray assignment)
- Vibrosis MASW workflow (.mat files from Signal Calc)
- (Future) Roll-along workflow
- (Future) Refraction reuse workflow
"""

from .standard_masw import StandardMASWWorkflow
from .assigned_masw import AssignedMASWWorkflow, run_assigned_masw
from .vibrosis_masw import (
    VibrosisMASWWorkflow,
    run_vibrosis_masw,
    process_mat_file_direct,
)

__all__ = [
    "StandardMASWWorkflow",
    # Assignment-based workflow
    "AssignedMASWWorkflow",
    "run_assigned_masw",
    # Vibrosis workflows
    "VibrosisMASWWorkflow",
    "run_vibrosis_masw",
    "process_mat_file_direct",
]
