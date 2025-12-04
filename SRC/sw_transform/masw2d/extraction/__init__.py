"""Data extraction methods for MASW 2D.

Provides:
- Sub-array extraction from shot gathers
- Vibrosis sub-array extraction from .mat files
- (Future) Roll-along extraction
- (Future) CMP cross-correlation extraction
"""

from .subarray_extractor import (
    ExtractedSubArray,
    extract_subarray,
    extract_all_subarrays_from_shot,
)

from .vibrosis_extractor import (
    ExtractedVibrosisSubArray,
    extract_vibrosis_subarray,
    extract_all_vibrosis_subarrays_from_shot,
    extract_all_vibrosis_subarrays,
    extract_all_vibrosis_subarrays_from_file,
    load_vibrosis_for_masw2d,
)

__all__ = [
    # SEG-2 extraction
    "ExtractedSubArray",
    "extract_subarray",
    "extract_all_subarrays_from_shot",
    # Vibrosis .mat extraction
    "ExtractedVibrosisSubArray",
    "extract_vibrosis_subarray",
    "extract_all_vibrosis_subarrays_from_shot",
    "extract_all_vibrosis_subarrays",
    "extract_all_vibrosis_subarrays_from_file",
    "load_vibrosis_for_masw2d",
]
