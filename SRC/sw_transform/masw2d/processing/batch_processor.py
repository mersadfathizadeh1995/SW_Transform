"""Batch processing of sub-arrays for dispersion curves.

Processes extracted sub-arrays using the existing SW_Transform
processing methods (FK, FDBF, PS, SS).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from ..extraction.subarray_extractor import ExtractedSubArray


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
    power_threshold: float = 0.1,
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
    
    Returns
    -------
    DispersionResult
        Dispersion analysis result
    """
    from sw_transform.processing.registry import METHODS, dyn
    
    data = extracted.data
    dt = extracted.dt
    dx = extracted.dx
    
    if method not in METHODS:
        raise ValueError(f"Unknown method: {method}. Available: {list(METHODS.keys())}")
    
    cfg = METHODS[method]
    step3 = dyn(cfg["step3"])
    step4 = dyn(cfg["step4"])
    
    # Process based on method
    if method == "fk":
        f, k, P = step3(data, dt, dx, fmin=0, fmax=freq_max, numk=grid_n)
        f, k, pnorm, vmax, wav = step4(f, k, P, tol=tol, power_threshold=power_threshold,
                                        velocity_min=velocity_min, velocity_max=velocity_max)
        pnorm = np.abs(pnorm)
        
        # Convert to velocity space for consistent output
        nv = 400
        velocities = np.linspace(max(1.0, velocity_min), velocity_max, nv)
        power = np.zeros((nv, len(f)))
        for i, fi in enumerate(f):
            if fi > 0:
                k_need = 2 * np.pi * fi / velocities
                power[:, i] = np.interp(k_need, k, pnorm[:, i], left=0.0, right=0.0)
        
        frequencies = f
        
    elif method == "fdbf":
        fs = 1.0 / dt
        weight_mode = 'invamp' if source_type == 'vibrosis' else 'none'
        R, f = step3(data, fs, max_frequency=freq_max,
                     do_tra_subsample=True, keep_below_10=True,
                     desired_number=400, weight_mode=weight_mode)
        k, pnorm, vmax, wav = step4(R, f, dx, cylindrical=False,
                                     numk=grid_n, min_velocity=100,
                                     max_velocity=5000, tol=tol)
        pnorm = np.abs(pnorm)
        
        # Convert to velocity space
        nv = 400
        velocities = np.linspace(max(1.0, velocity_min), velocity_max, nv)
        power = np.zeros((nv, len(f)))
        for i, fi in enumerate(f):
            if fi > 0:
                k_need = 2 * np.pi * fi / velocities
                power[:, i] = np.interp(k_need, k, pnorm[:, i], left=0.0, right=0.0)
        
        frequencies = f
        
    elif method == "ps":
        f, vels, P = step3(data, dt, dx, fmin=0, fmax=freq_max,
                          nvel=grid_n, vmin=100, vmax=5000, vspace=vspace)
        pnorm, vmax, wav, f = step4(f, vels, P)
        pnorm = np.abs(pnorm)
        
        frequencies = f
        velocities = vels
        power = pnorm
        
    else:  # ss (slant stack)
        f, vels, P = step3(data, dt, dx, fmin=0, fmax=freq_max,
                          nvel=grid_n, vmin=100, vmax=5000, vspace=vspace)
        pnorm, vmax, wav, f = step4(f, vels, P)
        pnorm = np.abs(pnorm)
        
        frequencies = f
        velocities = vels
        power = pnorm
    
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
