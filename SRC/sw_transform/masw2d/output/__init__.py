"""Output management for MASW 2D results.

Provides:
- Result organization by midpoint or shot
- Export to CSV, NPZ, and PNG formats
- Dispersion curve merging
- Combined export for refinement workflow
"""

from .organizer import organize_results, create_output_structure
from .export import (
    export_dispersion_csv,
    export_dispersion_npz,
    export_dispersion_image,
    export_batch_csv,
    export_combined_npz,
    export_for_dinver
)

__all__ = [
    "organize_results",
    "create_output_structure",
    "export_dispersion_csv",
    "export_dispersion_npz",
    "export_dispersion_image",
    "export_batch_csv",
    "export_combined_npz",
    "export_for_dinver",
]
