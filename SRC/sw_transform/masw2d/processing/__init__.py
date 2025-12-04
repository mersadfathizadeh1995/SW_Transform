"""Processing module for MASW 2D dispersion curve extraction.

Provides:
- Batch processing of multiple sub-arrays
- Vibrosis .mat file processing
- Dispersion curve management and organization
- Quality metrics and filtering
"""

from .batch_processor import (
    DispersionResult,
    process_subarray,
    process_batch,
    process_vibrosis_subarray,
    process_vibrosis_batch,
)

__all__ = [
    "DispersionResult",
    "process_subarray",
    "process_batch",
    # Vibrosis processing
    "process_vibrosis_subarray",
    "process_vibrosis_batch",
]
