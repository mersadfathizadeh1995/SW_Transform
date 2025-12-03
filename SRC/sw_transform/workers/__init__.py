"""Worker entrypoints for processing."""

from .single import run_single  # type: ignore
from .compare import run_compare  # type: ignore
from .parallel import (
    run_batch_parallel,
    run_batch_sequential,
    process_files,
    get_optimal_workers,
    ParallelResult,
)

__all__ = [
    "run_single",
    "run_compare",
    "run_batch_parallel",
    "run_batch_sequential",
    "process_files",
    "get_optimal_workers",
    "ParallelResult",
]



