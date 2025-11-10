"""SW Transform package (scaffold).

This src-layout package will gradually absorb the legacy scripts under
Previous/4_wave_cursor into clean modules under:
 - sw_transform.core
 - sw_transform.processing
 - sw_transform.gui
 - sw_transform.io
 - sw_transform.workers
 - sw_transform.cli

During the transition, thin wrappers import from the legacy code to
preserve behavior while we refactor behind stable APIs.
"""

__all__ = ["gui", "core", "processing", "io", "workers", "cli"]



