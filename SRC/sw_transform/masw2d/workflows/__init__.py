"""Predefined workflows for MASW 2D processing.

Provides:
- Standard MASW workflow (fixed array, multiple source offsets)
- (Future) Roll-along workflow
- (Future) Refraction reuse workflow
"""

from .standard_masw import StandardMASWWorkflow

__all__ = [
    "StandardMASWWorkflow",
]
