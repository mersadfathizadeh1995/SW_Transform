"""Data extraction methods for MASW 2D.

Provides:
- Sub-array extraction from shot gathers
- (Future) Roll-along extraction
- (Future) CMP cross-correlation extraction
"""

from .subarray_extractor import (
    ExtractedSubArray,
    extract_subarray,
    extract_all_subarrays_from_shot,
)

__all__ = [
    "ExtractedSubArray",
    "extract_subarray",
    "extract_all_subarrays_from_shot",
]
