"""Worker entrypoints (to be refactored to call core.service)."""

from .single import run_single  # type: ignore
from .compare import run_compare  # type: ignore

__all__ = ["run_single", "run_compare"]



