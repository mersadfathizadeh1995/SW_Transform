"""MASW 2D Processing Module.

Provides functionality for extracting multiple dispersion curves from
surface wave data for pseudo-2D Vs profiling.

Main features:
- Sub-array extraction from fixed arrays with multiple source offsets
- Variable sub-array sizes for multi-resolution analysis
- Support for different shot types (exterior, edge, interior)
- Batch processing and result organization

Subpackages:
- config: Configuration loading, validation, and templates
- geometry: Shot classification, sub-array definition, midpoint calculations
- extraction: Data extraction methods (sub-array, roll-along, CMP-CC)
- processing: Batch processing, dispersion curve management
- workflows: Predefined processing workflows
- output: Result organization, merging, and export
"""

from __future__ import annotations

__version__ = "0.1.0"

# Public API - will be populated as modules are implemented
__all__ = [
    "__version__",
]
