"""Processing module for MASW 2D dispersion curve extraction.

Provides:
- Batch processing of multiple sub-arrays
- Dispersion curve management and organization
- Quality metrics and filtering
"""

from .batch_processor import (
    DispersionResult,
    process_subarray,
    process_batch,
)

__all__ = [
    "DispersionResult",
    "process_subarray",
    "process_batch",
]
