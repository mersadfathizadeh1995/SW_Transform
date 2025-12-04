"""Batch processing of sub-arrays for dispersion curves.

Processes extracted sub-arrays using the existing SW_Transform
processing methods (FK, FDBF, PS, SS).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from ..extraction.subarray_extractor import ExtractedSubArray
from ..extraction.vibrosis_extractor import ExtractedVibrosisSubArray


@dataclass
class DispersionResult:
    """Result from dispersion analysis of a sub-array.
    
    Attributes
    ----------
    frequencies : np.ndarray
        Frequency vector (Hz)
    velocities : np.ndarray
        Velocity vector (m/s)
    power : np.ndarray
        Power spectrum, shape (n_velocities, n_frequencies)
    picked_velocities : np.ndarray
        Picked phase velocities at each frequency
    wavelengths : np.ndarray
        Calculated wavelengths (m)
    midpoint : float
        Midpoint position (m)
    subarray_config : str
        Name of sub-array configuration
    shot_file : str
        Source shot file path
    source_offset : float
        Source offset (m)
    direction : str
        Propagation direction
    method : str
        Processing method used
    metadata : dict
        Additional metadata
    """
    frequencies: np.ndarray
    velocities: np.ndarray
    power: np.ndarray
    picked_velocities: np.ndarray
    wavelengths: np.ndarray
    midpoint: float
    subarray_config: str
    shot_file: str
    source_offset: float
    direction: str
    method: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def n_frequencies(self) -> int:
        """Number of frequency points."""
        return len(self.frequencies)
    
    @property
    def n_velocities(self) -> int:
        """Number of velocity points."""
        return len(self.velocities)
    
    def get_valid_picks(self) -> tuple:
        """Get frequency and velocity arrays with invalid picks removed.
        
        Returns
        -------
        tuple
            (frequencies, velocities, wavelengths) with NaN values removed
        """
        mask = ~np.isnan(self.picked_velocities)
        return (
            self.frequencies[mask],
            self.picked_velocities[mask],
            self.wavelengths[mask]
        )
    
    def __repr__(self) -> str:
        return (f"DispersionResult(midpoint={self.midpoint:.1f}m, "
                f"config='{self.subarray_config}', method='{self.method}')")


def process_subarray(
    extracted: ExtractedSubArray,
    method: str = "ps",
    freq_min: float = 5.0,
    freq_max: float = 80.0,
    velocity_min: float = 100.0,
    velocity_max: float = 1500.0,
    grid_n: int = 4000,
    tol: float = 0.01,
    vspace: str = "log",
    source_type: str = "hammer",
    cylindrical: bool = False,
    power_threshold: float = 0.1,
    # Preprocessing parameters
    start_time: float = 0.0,
    end_time: float = 1.0,
    downsample: bool = True,
    down_factor: int = 16,
    numf: int = 4000,
    **kwargs
) -> DispersionResult:
    """Process a single extracted sub-array to get dispersion curve.
    
    Uses existing SW_Transform processing methods.
    
    Parameters
    ----------
    extracted : ExtractedSubArray
        Extracted sub-array data
    method : str
        Processing method: 'fk', 'fdbf', 'ps', 'ss'
    freq_min : float
        Minimum frequency (Hz)
    freq_max : float
        Maximum frequency (Hz)
    velocity_min : float
        Minimum velocity (m/s)
    velocity_max : float
        Maximum velocity (m/s)
    grid_n : int
        Grid size for transform
    tol : float
        Peak picking tolerance
    vspace : str
        Velocity spacing: 'log' or 'linear'
    source_type : str
        Source type: 'hammer' or 'vibrosis'
    cylindrical : bool
        If True, use cylindrical steering for FDBF (near-field correction)
    start_time : float
        Start time for windowing (seconds)
    end_time : float
        End time for windowing (seconds)
    downsample : bool
        Whether to downsample data
    down_factor : int
        Downsampling factor
    numf : int
        Number of frequency points for FFT
    
    Returns
    -------
    DispersionResult
        Dispersion analysis result
    """
    from sw_transform.processing.registry import METHODS, dyn
    from sw_transform.processing.preprocess import preprocess_data
    
    # Get raw data
    raw_data = extracted.data
    dt = extracted.dt
    dx = extracted.dx
    
    # Create time vector for preprocessing
    n_samples = raw_data.shape[0]
    time = np.arange(n_samples) * dt
    
    # Apply preprocessing (same as single transform)
    data, _, dt = preprocess_data(
        raw_data, time, dt,
        reverse_shot=False,  # Already handled in extraction
        start_time=start_time,
        end_time=end_time,
        do_downsample=downsample,
        down_factor=down_factor,
        numf=numf
    )
    
    if method not in METHODS:
        raise ValueError(f"Unknown method: {method}. Available: {list(METHODS.keys())}")
    
    cfg = METHODS[method]
    transform_func = dyn(cfg["transform"])
    analyze_func = dyn(cfg["analyze"])
    
    # Use unified transform interface: all return (frequencies, velocities, power)
    if method in ("fk", "fdbf"):
        # FK and FDBF use nvel for velocity grid
        transform_kwargs = dict(
            fmin=freq_min, fmax=freq_max,
            nvel=grid_n, vmin=velocity_min, vmax=velocity_max,
            vspace='linear'  # FK/FDBF typically use linear
        )
        # FDBF-specific: add weighting for vibrosis sources and cylindrical steering
        if method == "fdbf":
            weighting = 'invamp' if source_type == 'vibrosis' else 'none'
            steering = 'cylindrical' if cylindrical else 'plane'
            transform_kwargs['weighting'] = weighting
            transform_kwargs['steering'] = steering
        
        frequencies, velocities, power = transform_func(
            data, dt, dx, **transform_kwargs
        )
    else:
        # PS and SS
        frequencies, velocities, power = transform_func(
            data, dt, dx,
            fmin=freq_min, fmax=freq_max,
            nvel=grid_n, vmin=velocity_min, vmax=velocity_max,
            vspace=vspace
        )
    
    # Analyze: pick peaks
    pnorm, vmax, wav, frequencies = analyze_func(frequencies, velocities, power)
    pnorm = np.abs(pnorm)
    
    # Calculate wavelengths
    wavelengths = np.zeros_like(vmax)
    for i, (fi, vi) in enumerate(zip(frequencies, vmax)):
        if fi > 0 and not np.isnan(vi):
            wavelengths[i] = vi / fi
        else:
            wavelengths[i] = np.nan
    
    return DispersionResult(
        frequencies=frequencies,
        velocities=velocities,
        power=power,
        picked_velocities=vmax,
        wavelengths=wavelengths,
        midpoint=extracted.midpoint,
        subarray_config=extracted.config_name,
        shot_file=extracted.shot_info.file,
        source_offset=extracted.source_offset,
        direction=extracted.direction,
        method=method,
        metadata={
            "freq_min": freq_min,
            "freq_max": freq_max,
            "velocity_min": velocity_min,
            "velocity_max": velocity_max,
            "grid_n": grid_n,
            "source_type": source_type,
            "power_threshold": power_threshold,
            "n_channels": extracted.n_channels,
            "subarray_length": extracted.subarray_def.length
        }
    )


def process_vibrosis_subarray(
    extracted: ExtractedVibrosisSubArray,
    freq_min: float = 5.0,
    freq_max: float = 80.0,
    velocity_min: float = 100.0,
    velocity_max: float = 1500.0,
    grid_n: int = 4000,
    vspace: str = "linear",
    cylindrical: bool = True,
    power_threshold: float = 0.1,
    **kwargs
) -> DispersionResult:
    """Process a vibrosis sub-array from .mat file to get dispersion curve.
    
    Uses FDBF transform on the pre-computed cross-spectral matrix R.
    Note: Only FDBF method is supported for vibrosis .mat files.
    
    Parameters
    ----------
    extracted : ExtractedVibrosisSubArray
        Extracted vibrosis sub-array data with R matrix
    freq_min : float
        Minimum frequency (Hz)
    freq_max : float
        Maximum frequency (Hz)
    velocity_min : float
        Minimum velocity (m/s)
    velocity_max : float
        Maximum velocity (m/s)
    grid_n : int
        Number of velocity grid points
    vspace : str
        Velocity spacing: 'log' or 'linear'
    cylindrical : bool
        If True, use cylindrical steering (recommended for vibrosis)
    power_threshold : float
        Minimum normalized power for valid picks
    **kwargs
        Additional parameters (ignored)
        
    Returns
    -------
    DispersionResult
        Dispersion analysis result
    """
    from sw_transform.processing.fdbf import (
        fdbf_transform_from_R_vectorized,
        analyze_fdbf_spectrum
    )
    
    # Get pre-computed R matrix and frequencies
    R = extracted.R  # Shape: (n_channels, n_channels, n_frequencies)
    frequencies = extracted.frequencies
    dx = extracted.dx
    
    # FDBF transform from R matrix (only valid method for vibrosis)
    steering = 'cylindrical' if cylindrical else 'plane'
    freq_out, velocities, power = fdbf_transform_from_R_vectorized(
        R, frequencies, dx,
        fmin=freq_min, fmax=freq_max,
        nvel=grid_n, vmin=velocity_min, vmax=velocity_max,
        vspace=vspace, steering=steering
    )
    
    # Analyze: pick peaks
    pnorm, vmax, wav, freq_out = analyze_fdbf_spectrum(
        freq_out, velocities, power,
        normalization="frequency-maximum",
        power_threshold=power_threshold,
        velocity_min=velocity_min,
        velocity_max=velocity_max
    )
    
    # Calculate wavelengths
    wavelengths = np.zeros_like(vmax)
    for i, (fi, vi) in enumerate(zip(freq_out, vmax)):
        if fi > 0 and not np.isnan(vi):
            wavelengths[i] = vi / fi
        else:
            wavelengths[i] = np.nan
    
    # Build metadata
    shot_file = extracted.shot_info.file if extracted.shot_info else "vibrosis.mat"
    source_offset = extracted.shot_info.source_position if extracted.shot_info else 0.0
    
    return DispersionResult(
        frequencies=freq_out,
        velocities=velocities,
        power=pnorm,
        picked_velocities=vmax,
        wavelengths=wavelengths,
        midpoint=extracted.midpoint,
        subarray_config=extracted.config_name,
        shot_file=shot_file,
        source_offset=source_offset,
        direction="forward",  # Vibrosis typically forward propagation
        method="fdbf",
        metadata={
            "freq_min": freq_min,
            "freq_max": freq_max,
            "velocity_min": velocity_min,
            "velocity_max": velocity_max,
            "grid_n": grid_n,
            "source_type": "vibrosis",
            "cylindrical": cylindrical,
            "power_threshold": power_threshold,
            "n_channels": extracted.n_channels,
            "subarray_length": extracted.subarray_def.length if extracted.subarray_def else 0,
            "file_type": "mat"
        }
    )


def process_batch(
    extracted_list: List[ExtractedSubArray],
    method: str = "ps",
    processing_params: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[DispersionResult]:
    """Process multiple sub-arrays.
    
    Parameters
    ----------
    extracted_list : list of ExtractedSubArray
        List of extracted sub-arrays to process
    method : str
        Processing method
    processing_params : dict, optional
        Processing parameters (freq_min, freq_max, etc.)
    progress_callback : callable, optional
        Callback function(current, total) for progress reporting
    
    Returns
    -------
    list of DispersionResult
        Results for each sub-array
    """
    params = processing_params.copy() if processing_params else {}
    # Remove 'method' from params if present (we pass it separately)
    params.pop('method', None)
    
    results = []
    total = len(extracted_list)
    
    for i, extracted in enumerate(extracted_list):
        try:
            result = process_subarray(extracted, method=method, **params)
            results.append(result)
        except Exception as e:
            import warnings
            warnings.warn(
                f"Failed to process sub-array at midpoint {extracted.midpoint:.1f}m "
                f"from {extracted.shot_info.file}: {e}"
            )
        
        if progress_callback:
            progress_callback(i + 1, total)
    
    return results


def process_vibrosis_batch(
    extracted_list: List[ExtractedVibrosisSubArray],
    processing_params: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[DispersionResult]:
    """Process multiple vibrosis sub-arrays.
    
    Note: Only FDBF method is supported for vibrosis .mat files.
    
    Parameters
    ----------
    extracted_list : list of ExtractedVibrosisSubArray
        List of extracted vibrosis sub-arrays to process
    processing_params : dict, optional
        Processing parameters (freq_min, freq_max, etc.)
    progress_callback : callable, optional
        Callback function(current, total) for progress reporting
    
    Returns
    -------
    list of DispersionResult
        Results for each sub-array
    """
    params = processing_params.copy() if processing_params else {}
    # Remove 'method' if present - only FDBF is supported
    params.pop('method', None)
    
    results = []
    total = len(extracted_list)
    
    for i, extracted in enumerate(extracted_list):
        try:
            result = process_vibrosis_subarray(extracted, **params)
            results.append(result)
        except Exception as e:
            import warnings
            warnings.warn(
                f"Failed to process vibrosis sub-array at midpoint {extracted.midpoint:.1f}m: {e}"
            )
        
        if progress_callback:
            progress_callback(i + 1, total)
    
    return results


def process_batch_parallel(
    extracted_list: List[ExtractedSubArray],
    method: str = "ps",
    processing_params: Optional[Dict[str, Any]] = None,
    max_workers: Optional[int] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[DispersionResult]:
    """Process multiple sub-arrays in parallel.
    
    Parameters
    ----------
    extracted_list : list of ExtractedSubArray
        List of extracted sub-arrays to process
    method : str
        Processing method
    processing_params : dict, optional
        Processing parameters (freq_min, freq_max, etc.)
    max_workers : int, optional
        Number of parallel workers (default: auto)
    progress_callback : callable, optional
        Callback function(current, total, message) for progress reporting
    
    Returns
    -------
    list of DispersionResult
        Results for each sub-array
    """
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from sw_transform.workers.parallel import get_optimal_workers
    
    if not extracted_list:
        return []
    
    params = processing_params.copy() if processing_params else {}
    params.pop('method', None)
    
    if max_workers is None:
        max_workers = get_optimal_workers(mode='single')
    
    total = len(extracted_list)
    results = [None] * total
    
    # Build work items with index for result ordering
    work_items = [(i, ext, method, params) for i, ext in enumerate(extracted_list)]
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_idx = {
            executor.submit(_process_single_worker, item): item[0]
            for item in work_items
        }
        
        completed = 0
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                result = future.result()
                results[idx] = result
            except Exception as e:
                import warnings
                ext = extracted_list[idx]
                warnings.warn(f"Failed to process sub-array at {ext.midpoint:.1f}m: {e}")
            
            completed += 1
            if progress_callback:
                progress_callback(completed, total, f"midpoint {extracted_list[idx].midpoint:.1f}m")
    
    # Filter out None results (failures)
    return [r for r in results if r is not None]


def _process_single_worker(work_item):
    """Worker function for parallel processing - must be at module level."""
    idx, extracted, method, params = work_item
    return process_subarray(extracted, method=method, **params)


def group_results_by_midpoint(
    results: List[DispersionResult]
) -> Dict[float, List[DispersionResult]]:
    """Group dispersion results by midpoint position.
    
    Parameters
    ----------
    results : list of DispersionResult
        Dispersion analysis results
    
    Returns
    -------
    dict
        Mapping of midpoint position to list of results at that position
    """
    grouped = {}
    for r in results:
        if r.midpoint not in grouped:
            grouped[r.midpoint] = []
        grouped[r.midpoint].append(r)
    return grouped


def group_results_by_config(
    results: List[DispersionResult]
) -> Dict[str, List[DispersionResult]]:
    """Group dispersion results by sub-array configuration.
    
    Parameters
    ----------
    results : list of DispersionResult
        Dispersion analysis results
    
    Returns
    -------
    dict
        Mapping of config name to list of results with that config
    """
    grouped = {}
    for r in results:
        if r.subarray_config not in grouped:
            grouped[r.subarray_config] = []
        grouped[r.subarray_config].append(r)
    return grouped
