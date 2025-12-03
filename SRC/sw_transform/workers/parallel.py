"""Parallel processing utilities for batch file processing.

Provides multi-core parallel execution of transform methods using
ProcessPoolExecutor for CPU-bound tasks.
"""

from __future__ import annotations

import os
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple, Callable, Optional
from dataclasses import dataclass


@dataclass
class ParallelResult:
    """Result container for parallel processing."""
    base: str
    success: bool
    output: str
    error: Optional[str] = None


def get_optimal_workers(mode: str = 'single') -> int:
    """Get optimal number of workers based on CPU count and processing mode.
    
    Parameters
    ----------
    mode : str
        'single' for single-method processing (lighter memory)
        'compare' for 4-method comparison (heavier memory - uses fewer workers)
    
    Returns
    -------
    int
        Recommended number of workers.
        - single mode: CPU count - 1 (max 8)
        - compare mode: max 2-3 workers to avoid memory exhaustion
    """
    cpu_count = multiprocessing.cpu_count()
    
    if mode == 'compare':
        # Compare mode runs 4 transforms per file - very memory intensive
        # Each transform can use 2+ GB, so limit to 2-3 workers
        return max(1, min(cpu_count // 4, 3))
    else:
        # Single method is lighter, can use more workers
        return max(1, min(cpu_count - 1, 8))


def _worker_run_single(params: Dict[str, Any]) -> Tuple[str, bool, str]:
    """Worker function for run_single - must be at module level for pickling."""
    from sw_transform.core.service import run_single
    try:
        return run_single(params)
    except Exception as e:
        return (params.get('base', 'unknown'), False, str(e))


def _worker_run_compare(params: Dict[str, Any]) -> Tuple[str, bool, str]:
    """Worker function for run_compare - must be at module level for pickling."""
    from sw_transform.core.service import run_compare
    try:
        return run_compare(params)
    except Exception as e:
        return (params.get('base', 'unknown'), False, str(e))


def run_batch_parallel(
    params_list: List[Dict[str, Any]],
    mode: str = 'single',
    max_workers: Optional[int] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[ParallelResult]:
    """Process multiple files in parallel.
    
    Parameters
    ----------
    params_list : list of dict
        List of parameter dictionaries, one per file.
        Each dict should have at minimum: path, base, outdir, key (for single mode).
    mode : str
        'single' for run_single, 'compare' for run_compare
    max_workers : int, optional
        Maximum number of parallel workers.
        Default: CPU count - 1 (capped at 8)
    progress_callback : callable, optional
        Called after each file completes with (completed_count, total, current_base).
        Useful for updating GUI progress bars.
    
    Returns
    -------
    list of ParallelResult
        Results for each file in the same order as params_list.
    
    Example
    -------
    >>> params = [{'path': f, 'base': b, ...} for f, b in files]
    >>> results = run_batch_parallel(params, mode='single', max_workers=4)
    >>> successes = sum(1 for r in results if r.success)
    """
    if not params_list:
        return []
    
    if max_workers is None:
        max_workers = get_optimal_workers(mode=mode)
    
    # Select worker function based on mode
    worker_func = _worker_run_single if mode == 'single' else _worker_run_compare
    
    total = len(params_list)
    results: List[ParallelResult] = [None] * total  # Pre-allocate for order preservation
    
    # Create mapping from base name to index for result ordering
    base_to_idx = {p['base']: i for i, p in enumerate(params_list)}
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_base = {
            executor.submit(worker_func, params): params['base']
            for params in params_list
        }
        
        completed = 0
        for future in as_completed(future_to_base):
            base = future_to_base[future]
            idx = base_to_idx[base]
            
            try:
                base_result, success, output = future.result()
                results[idx] = ParallelResult(
                    base=base_result,
                    success=success,
                    output=output,
                    error=None if success else output
                )
            except Exception as e:
                results[idx] = ParallelResult(
                    base=base,
                    success=False,
                    output="",
                    error=str(e)
                )
            
            completed += 1
            if progress_callback:
                progress_callback(completed, total, base)
    
    return results


def run_batch_sequential(
    params_list: List[Dict[str, Any]],
    mode: str = 'single',
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[ParallelResult]:
    """Process files sequentially (fallback or for debugging).
    
    Same interface as run_batch_parallel but processes files one at a time.
    Useful when parallel processing causes issues or for debugging.
    """
    if not params_list:
        return []
    
    from sw_transform.core.service import run_single, run_compare
    
    worker_func = run_single if mode == 'single' else run_compare
    total = len(params_list)
    results = []
    
    for i, params in enumerate(params_list):
        base = params.get('base', 'unknown')
        try:
            base_result, success, output = worker_func(params)
            results.append(ParallelResult(
                base=base_result,
                success=success,
                output=output,
                error=None if success else output
            ))
        except Exception as e:
            results.append(ParallelResult(
                base=base,
                success=False,
                output="",
                error=str(e)
            ))
        
        if progress_callback:
            progress_callback(i + 1, total, base)
    
    return results


# Convenience function for simple use cases
def process_files(
    params_list: List[Dict[str, Any]],
    mode: str = 'single',
    parallel: bool = True,
    max_workers: Optional[int] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[ParallelResult]:
    """Process files with optional parallelization.
    
    Convenience wrapper that chooses parallel or sequential based on flag.
    
    Parameters
    ----------
    params_list : list of dict
        Parameters for each file
    mode : str
        'single' or 'compare'
    parallel : bool
        Whether to use parallel processing (default: True)
    max_workers : int, optional
        Number of workers for parallel mode
    progress_callback : callable, optional
        Progress callback function
    
    Returns
    -------
    list of ParallelResult
    """
    if parallel and len(params_list) > 1:
        return run_batch_parallel(
            params_list, mode=mode,
            max_workers=max_workers,
            progress_callback=progress_callback
        )
    else:
        return run_batch_sequential(
            params_list, mode=mode,
            progress_callback=progress_callback
        )
