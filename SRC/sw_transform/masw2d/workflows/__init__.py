"""Predefined workflows for MASW 2D processing.

Provides:
- Standard MASW workflow (fixed array, multiple source offsets)
- Vibrosis MASW workflow (.mat files from Signal Calc)
- (Future) Roll-along workflow
- (Future) Refraction reuse workflow
"""

from .standard_masw import StandardMASWWorkflow
from .vibrosis_masw import (
    VibrosisMASWWorkflow,
    run_vibrosis_masw,
    process_mat_file_direct,
)

__all__ = [
    "StandardMASWWorkflow",
    # Vibrosis workflows
    "VibrosisMASWWorkflow",
    "run_vibrosis_masw",
    "process_mat_file_direct",
]
