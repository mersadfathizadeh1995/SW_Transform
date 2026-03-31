"""Export functions for dispersion curves."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from ..processing.batch_processor import DispersionResult


def export_dispersion_csv(
    result: DispersionResult,
    filepath: str,
    include_header: bool = True
) -> str:
    """Export dispersion curve picks to CSV file.
    
    Parameters
    ----------
    result : DispersionResult
        Dispersion analysis result
    filepath : str
        Output file path
    include_header : bool
        If True, include column headers
    
    Returns
    -------
    str
        Path to exported file
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        if include_header:
            writer.writerow(["Frequency(Hz)", "PhaseVelocity(m/s)", "Wavelength(m)"])
        
        for freq, vel, wav in zip(
            result.frequencies,
            result.picked_velocities,
            result.wavelengths
        ):
            if not np.isnan(vel):
                writer.writerow([
                    f"{freq:.4f}",
                    f"{vel:.4f}",
                    f"{wav:.4f}" if not np.isnan(wav) else ""
                ])
    
    return filepath


def export_metadata_txt(
    result: DispersionResult,
    filepath: str
) -> str:
    """Export metadata for a dispersion result to a plain text file.
    
    Parameters
    ----------
    result : DispersionResult
        Dispersion analysis result
    filepath : str
        Output file path (.txt)
    
    Returns
    -------
    str
        Path to exported file
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    lines = [
        f"Midpoint: {result.midpoint:.1f} m",
        f"Config: {result.subarray_config}",
        f"Shot: {Path(result.shot_file).name}",
        f"Source Offset: {result.source_offset:.1f} m ({result.direction})",
        f"Method: {result.method}",
    ]
    
    # Add optional metadata if available
    meta = result.metadata or {}
    if 'n_channels' in meta:
        lines.append(f"N Channels: {meta['n_channels']}")
    if 'dx' in meta:
        lines.append(f"Geophone Spacing: {meta['dx']} m")
    if 'freq_min' in meta and 'freq_max' in meta:
        lines.append(f"Freq Range: {meta['freq_min']} - {meta['freq_max']} Hz")
    if 'vel_min' in meta and 'vel_max' in meta:
        lines.append(f"Velocity Range: {meta['vel_min']} - {meta['vel_max']} m/s")
    
    lines.append(f"Export Date: {datetime.now().isoformat()}")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    
    return filepath


def export_dispersion_npz(
    result: DispersionResult,
    filepath: str
) -> str:
    """Export full dispersion spectrum and picks to NPZ file.
    
    Parameters
    ----------
    result : DispersionResult
        Dispersion analysis result
    filepath : str
        Output file path
    
    Returns
    -------
    str
        Path to exported file
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare metadata
    data = {
        'frequencies': np.asarray(result.frequencies, dtype=np.float32),
        'velocities': np.asarray(result.velocities, dtype=np.float32),
        'power': np.asarray(result.power, dtype=np.float32),
        'picked_velocities': np.asarray(result.picked_velocities, dtype=np.float32),
        'wavelengths': np.asarray(result.wavelengths, dtype=np.float32),
        'midpoint': float(result.midpoint),
        'subarray_config': str(result.subarray_config),
        'shot_file': str(result.shot_file),
        'source_offset': float(result.source_offset),
        'direction': str(result.direction),
        'method': str(result.method),
        'export_date': datetime.now().isoformat(),
        'version': '1.0'
    }
    
    # Add metadata dict entries
    for key, val in result.metadata.items():
        if isinstance(val, (int, float, str, bool)):
            data[f'meta_{key}'] = val
        elif isinstance(val, (list, np.ndarray)):
            data[f'meta_{key}'] = np.asarray(val, dtype=np.float32)
    
    np.savez_compressed(filepath, **data)
    
    return filepath


def export_dispersion_image(
    result: DispersionResult,
    filepath: str,
    max_velocity: Optional[float] = None,
    max_frequency: Optional[float] = None,
    min_frequency: Optional[float] = None,
    cmap: str = "jet",
    dpi: int = 150,
    auto_velocity_limit: bool = True,
    auto_frequency_limit: bool = True,
    fill_nan: bool = True,
    nan_color: str = "lightgray",
    power_mask_threshold: float = 0.0,
    smooth_sigma: float = 0.0
) -> str:
    """Export dispersion spectrum as PNG image.
    
    Parameters
    ----------
    result : DispersionResult
        Dispersion analysis result
    filepath : str
        Output file path (.png)
    max_velocity : float, optional
        Maximum velocity for plot axis. If None and auto_velocity_limit is True,
        automatically determined from picked velocities.
    max_frequency : float, optional
        Maximum frequency for plot axis
    min_frequency : float, optional
        Minimum frequency for plot axis (default: from result metadata or 5 Hz)
    cmap : str
        Colormap name
    dpi : int
        Image resolution
    auto_velocity_limit : bool
        If True and max_velocity is None, automatically determine velocity limit
        from picks (max pick velocity + 20% margin, rounded to nice number)
    auto_frequency_limit : bool
        If True and max_frequency is None, automatically determine frequency limit
        from the data range (max frequency with significant power + margin)
    fill_nan : bool
        If True, fill NaN/masked regions with nan_color instead of white
    nan_color : str
        Color for NaN regions (default: 'lightgray')
    power_mask_threshold : float
        Minimum normalized power for display. Values below this fraction of the
        global max are set to NaN (shown as nan_color). Default: 0.0 (disabled).
        Set to e.g. 0.02 to mask very low-power regions.
    smooth_sigma : float
        If > 0, apply Gaussian smoothing (sigma in grid cells) to the power
        spectrum before display to reduce visual noise. Default: 0.0 (no smoothing).
    
    Returns
    -------
    str
        Path to exported file
    """
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    freqs = np.asarray(result.frequencies)
    vels = np.asarray(result.velocities)
    power = np.asarray(result.power)
    picks = np.asarray(result.picked_velocities)
    
    # Get frequency limits from metadata or use defaults
    if min_frequency is None:
        min_frequency = result.metadata.get('freq_min', 5.0)
    
    # Auto-detect max frequency from data if requested
    data_max_freq = freqs[-1] if len(freqs) > 0 else 80.0
    if max_frequency is None and auto_frequency_limit:
        # Find max frequency with significant power
        power_threshold_detect = 0.05
        max_pwr = np.nanmax(power)
        if max_pwr > 0 and len(freqs) > 0:
            # Check each frequency column for significant power
            sig_power_per_freq = np.nanmax(power, axis=0)  # Max power at each frequency
            sig_mask = sig_power_per_freq > power_threshold_detect * max_pwr
            if np.any(sig_mask):
                max_f_idx = np.max(np.where(sig_mask)[0])
                detected_max_f = freqs[min(max_f_idx + 2, len(freqs) - 1)]  # Add small margin
                # Also consider picks
                valid_picks_mask = ~np.isnan(picks)
                if np.any(valid_picks_mask):
                    max_pick_freq = freqs[np.max(np.where(valid_picks_mask)[0])]
                    detected_max_f = max(detected_max_f, max_pick_freq * 1.1)
                max_frequency = _round_freq_to_nice_number(detected_max_f * 1.05)
                # Never exceed the actual data range
                max_frequency = min(max_frequency, data_max_freq)
            else:
                max_frequency = result.metadata.get('freq_max', data_max_freq)
        else:
            max_frequency = result.metadata.get('freq_max', data_max_freq)
    elif max_frequency is None:
        max_frequency = result.metadata.get('freq_max', data_max_freq)
    # Final safeguard: never show axis beyond the data
    max_frequency = min(max_frequency, data_max_freq)
    
    # Get velocity limits - prefer metadata, then auto-detect
    if max_velocity is None:
        max_velocity = result.metadata.get('velocity_max', None)
    
    if max_velocity is None and auto_velocity_limit:
        # Auto-detect from data
        power_threshold_detect = 0.05
        max_pwr = np.nanmax(power)
        if max_pwr > 0:
            sig_mask = power > power_threshold_detect * max_pwr
            if np.any(sig_mask):
                v_indices = np.any(sig_mask, axis=1)
                max_v_idx = np.max(np.where(v_indices)[0]) if np.any(v_indices) else len(vels) - 1
                detected_max_v = vels[min(max_v_idx + 5, len(vels) - 1)]
                valid_picks = picks[~np.isnan(picks)]
                if len(valid_picks) > 0:
                    detected_max_v = max(detected_max_v, np.max(valid_picks) * 1.1)
                max_velocity = _round_to_nice_number(detected_max_v * 1.1)
            else:
                max_velocity = 1000.0
        else:
            max_velocity = 1000.0
    
    max_velocity = max(max_velocity or 1000.0, 200.0)
    
    # Create uniform velocity grid for plotting
    nv = 400
    v_min = max(10.0, result.metadata.get('velocity_min', 50.0))
    vaxis = np.linspace(v_min, max_velocity, nv)
    
    # Interpolate power to uniform velocity grid
    n_f = len(freqs)
    P_vf = np.full((nv, n_f), np.nan)
    
    for i in range(n_f):
        if i < power.shape[1]:
            P_vf[:, i] = np.interp(vaxis, vels, power[:, i], left=np.nan, right=np.nan)
    
    # Optional Gaussian smoothing to reduce visual noise
    if smooth_sigma > 0:
        try:
            from scipy.ndimage import gaussian_filter
            valid_mask_arr = ~np.isnan(P_vf)
            P_filled = np.where(valid_mask_arr, P_vf, 0.0)
            P_vf = gaussian_filter(P_filled, sigma=smooth_sigma)
            P_vf[~valid_mask_arr] = np.nan
        except ImportError:
            pass  # scipy not available, skip smoothing
    
    # Apply power threshold for display
    max_power = np.nanmax(P_vf)
    if max_power > 0:
        P_vf[P_vf < power_mask_threshold * max_power] = np.nan
    
    # Plot using pcolormesh for proper NaN handling
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Create colormap with NaN color
    cmap_obj = plt.cm.get_cmap(cmap).copy()
    if fill_nan:
        cmap_obj.set_bad(color=nan_color)
    else:
        cmap_obj.set_bad(color='white')
    
    # Use pcolormesh for better NaN handling
    X, Y = np.meshgrid(freqs, vaxis)
    valid_power = P_vf[~np.isnan(P_vf)]
    if len(valid_power) > 0:
        vmin = power_mask_threshold * max_power
        vmax = np.max(valid_power)
    else:
        vmin, vmax = 0, 1
    
    pcm = ax.pcolormesh(X, Y, P_vf, cmap=cmap_obj, vmin=vmin, vmax=vmax, shading='auto')
    plt.colorbar(pcm, ax=ax, label="Normalized Power")
    
    # Plot picks
    valid_mask = ~np.isnan(picks)
    ax.plot(freqs[valid_mask], picks[valid_mask], 'o', 
            mfc='none', mec='white', ms=4, mew=1.5, label="Picks")
    
    # Title with metadata and offset quality
    title = f"{result.method.upper()} Dispersion - Midpoint {result.midpoint:.1f}m"
    subarray_length = result.metadata.get('subarray_length', 0)
    offset_ratio_str = ""
    if subarray_length > 0 and result.source_offset > 0:
        ratio = result.source_offset / subarray_length
        offset_ratio_str = f", d/L={ratio:.2f}"
        if ratio > 1.5:
            offset_ratio_str += " (far)"
    subtitle = (f"Config: {result.subarray_config}, "
                f"Offset: {result.source_offset:.1f}m ({result.direction}){offset_ratio_str}")
    ax.set_title(f"{title}\n{subtitle}", fontsize=10)
    
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Phase Velocity (m/s)")
    ax.set_xlim(min_frequency, max_frequency)
    ax.set_ylim(v_min, max_velocity)
    ax.grid(alpha=0.3)
    ax.legend(loc='upper right')
    
    plt.tight_layout()
    fig.savefig(filepath, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    return filepath


def _round_to_nice_number(value: float) -> float:
    """Round a value up to a 'nice' number for axis limits.
    
    Nice numbers: 100, 200, 250, 300, 400, 500, 600, 750, 800, 1000, etc.
    """
    if value <= 0:
        return 100.0
    
    # Find the order of magnitude
    import math
    magnitude = 10 ** math.floor(math.log10(value))
    
    # Normalized value (1-10 range)
    normalized = value / magnitude
    
    # Round up to nice normalized values
    nice_values = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.5, 8.0, 10.0]
    
    for nice in nice_values:
        if normalized <= nice:
            return nice * magnitude
    
    return 10.0 * magnitude


def _round_freq_to_nice_number(value: float) -> float:
    """Round a frequency value up to a 'nice' number for axis limits.
    
    Nice numbers for frequency: 10, 15, 20, 25, 30, 40, 50, 60, 80, 100 Hz etc.
    """
    if value <= 0:
        return 10.0
    
    # Common nice frequency values
    nice_freqs = [5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100, 120, 150, 200]
    
    for nice in nice_freqs:
        if value <= nice:
            return float(nice)
    
    # For larger values, round up to nearest 50
    import math
    return float(math.ceil(value / 50) * 50)


def export_batch_csv(
    results: List[DispersionResult],
    filepath: str,
    format: str = "long"
) -> str:
    """Export multiple dispersion curves to a single CSV.
    
    Parameters
    ----------
    results : list of DispersionResult
        Dispersion results to export
    filepath : str
        Output file path
    format : str
        Format: 'long' (one row per point) or 'wide' (one column per curve)
    
    Returns
    -------
    str
        Path to exported file
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    if format == "long":
        return _export_long_format(results, filepath)
    else:
        return _export_wide_format(results, filepath)


def _export_long_format(
    results: List[DispersionResult],
    filepath: str
) -> str:
    """Export in long format (one row per frequency-velocity point)."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Midpoint_m",
            "Config",
            "Shot",
            "Offset_m",
            "Direction",
            "Method",
            "Frequency_Hz",
            "Velocity_m_s",
            "Wavelength_m"
        ])
        
        for result in results:
            shot_name = Path(result.shot_file).name
            for freq, vel, wav in zip(
                result.frequencies,
                result.picked_velocities,
                result.wavelengths
            ):
                if not np.isnan(vel):
                    writer.writerow([
                        f"{result.midpoint:.1f}",
                        result.subarray_config,
                        shot_name,
                        f"{result.source_offset:.1f}",
                        result.direction,
                        result.method,
                        f"{freq:.4f}",
                        f"{vel:.4f}",
                        f"{wav:.4f}" if not np.isnan(wav) else ""
                    ])
    
    return filepath


def _export_wide_format(
    results: List[DispersionResult],
    filepath: str
) -> str:
    """Export in wide format (one column per curve)."""
    if not results:
        return filepath
    
    # Find common frequency grid (use first result as reference)
    ref_freqs = results[0].frequencies
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header row
        header = ["Frequency_Hz"]
        for r in results:
            label = f"mid{r.midpoint:.0f}_{r.subarray_config}_{r.direction[:3]}"
            header.append(f"Vel_{label}")
        writer.writerow(header)
        
        # Data rows
        for i, freq in enumerate(ref_freqs):
            row = [f"{freq:.4f}"]
            for r in results:
                if i < len(r.picked_velocities):
                    vel = r.picked_velocities[i]
                    row.append(f"{vel:.4f}" if not np.isnan(vel) else "")
                else:
                    row.append("")
            writer.writerow(row)
    
    return filepath


def export_combined_npz(
    results: List[DispersionResult],
    filepath: str
) -> str:
    """Export all dispersion curves to a single combined NPZ file.
    
    This format is compatible with the refinement workflow.
    
    Parameters
    ----------
    results : list of DispersionResult
        All dispersion results to combine
    filepath : str
        Output file path
    
    Returns
    -------
    str
        Path to exported file
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    if not results:
        np.savez_compressed(filepath, n_curves=0)
        return filepath
    
    # Collect all data
    n_curves = len(results)
    
    # Use first result to determine array sizes
    n_freq = len(results[0].frequencies)
    n_vel = len(results[0].velocities)
    
    # Initialize arrays
    all_frequencies = np.zeros((n_curves, n_freq), dtype=np.float32)
    all_velocities = np.zeros((n_curves, n_vel), dtype=np.float32)
    all_power = np.zeros((n_curves, n_vel, n_freq), dtype=np.float32)
    all_picks = np.zeros((n_curves, n_freq), dtype=np.float32)
    all_wavelengths = np.zeros((n_curves, n_freq), dtype=np.float32)
    
    # Metadata arrays
    midpoints = np.zeros(n_curves, dtype=np.float32)
    offsets = np.zeros(n_curves, dtype=np.float32)
    configs = []
    directions = []
    shot_files = []
    methods = []
    
    for i, result in enumerate(results):
        # Handle variable array sizes
        nf = min(n_freq, len(result.frequencies))
        nv = min(n_vel, len(result.velocities))
        
        all_frequencies[i, :nf] = result.frequencies[:nf]
        all_velocities[i, :nv] = result.velocities[:nv]
        
        power = np.asarray(result.power)
        pv, pf = min(nv, power.shape[0]), min(nf, power.shape[1])
        all_power[i, :pv, :pf] = power[:pv, :pf]
        
        all_picks[i, :nf] = result.picked_velocities[:nf]
        all_wavelengths[i, :nf] = result.wavelengths[:nf]
        
        midpoints[i] = result.midpoint
        offsets[i] = result.source_offset
        configs.append(result.subarray_config)
        directions.append(result.direction)
        shot_files.append(Path(result.shot_file).name)
        methods.append(result.method)
    
    # Save
    np.savez_compressed(
        filepath,
        # Data arrays
        frequencies=all_frequencies,
        velocities=all_velocities,
        power=all_power,
        picked_velocities=all_picks,
        wavelengths=all_wavelengths,
        # Metadata arrays
        midpoints=midpoints,
        source_offsets=offsets,
        configs=np.array(configs, dtype=object),
        directions=np.array(directions, dtype=object),
        shot_files=np.array(shot_files, dtype=object),
        methods=np.array(methods, dtype=object),
        # Scalar metadata
        n_curves=n_curves,
        n_frequencies=n_freq,
        n_velocities=n_vel,
        export_date=datetime.now().isoformat(),
        version='1.0'
    )
    
    return filepath


def build_combined_npz_from_files(
    npz_files: List[str],
    output_path: str
) -> str:
    """Build combined NPZ from individual NPZ files without loading all into RAM.
    
    Reads each file one at a time to determine sizes, then builds combined
    arrays incrementally. Much more memory-efficient than export_combined_npz()
    for large datasets.
    
    Parameters
    ----------
    npz_files : list of str
        Paths to individual NPZ files (from export_dispersion_npz)
    output_path : str
        Output path for combined NPZ
    
    Returns
    -------
    str
        Path to exported file
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    if not npz_files:
        np.savez_compressed(output_path, n_curves=0)
        return output_path
    
    # Read first file to get array dimensions
    with np.load(npz_files[0], allow_pickle=True) as first:
        n_freq = len(first['frequencies'])
        n_vel = len(first['velocities'])
    
    n_curves = len(npz_files)
    
    # Build lightweight metadata arrays (small)
    all_picks = np.zeros((n_curves, n_freq), dtype=np.float32)
    all_wavelengths = np.zeros((n_curves, n_freq), dtype=np.float32)
    all_frequencies = np.zeros((n_curves, n_freq), dtype=np.float32)
    all_velocities = np.zeros((n_curves, n_vel), dtype=np.float32)
    midpoints = np.zeros(n_curves, dtype=np.float32)
    offsets = np.zeros(n_curves, dtype=np.float32)
    configs = []
    directions = []
    shot_files = []
    methods = []
    
    # Also build full power array — but one file at a time
    all_power = np.zeros((n_curves, n_vel, n_freq), dtype=np.float32)
    
    for i, npz_path in enumerate(npz_files):
        with np.load(npz_path, allow_pickle=True) as data:
            nf = min(n_freq, len(data['frequencies']))
            nv = min(n_vel, len(data['velocities']))
            
            all_frequencies[i, :nf] = data['frequencies'][:nf]
            all_velocities[i, :nv] = data['velocities'][:nv]
            
            power = data['power']
            pv, pf = min(nv, power.shape[0]), min(nf, power.shape[1])
            all_power[i, :pv, :pf] = power[:pv, :pf]
            
            all_picks[i, :nf] = data['picked_velocities'][:nf]
            all_wavelengths[i, :nf] = data['wavelengths'][:nf]
            
            midpoints[i] = float(data['midpoint'])
            offsets[i] = float(data['source_offset'])
            configs.append(str(data['subarray_config']))
            directions.append(str(data['direction']))
            shot_files.append(str(data.get('shot_file', '')))
            methods.append(str(data['method']))
    
    np.savez_compressed(
        output_path,
        frequencies=all_frequencies,
        velocities=all_velocities,
        power=all_power,
        picked_velocities=all_picks,
        wavelengths=all_wavelengths,
        midpoints=midpoints,
        source_offsets=offsets,
        configs=np.array(configs, dtype=object),
        directions=np.array(directions, dtype=object),
        shot_files=np.array(shot_files, dtype=object),
        methods=np.array(methods, dtype=object),
        n_curves=n_curves,
        n_frequencies=n_freq,
        n_velocities=n_vel,
        export_date=datetime.now().isoformat(),
        version='1.0'
    )
    
    return output_path


def export_for_dinver(
    result: DispersionResult,
    filepath: str,
    error_percent: float = 10.0
) -> str:
    """Export dispersion curve in format suitable for Dinver/Geopsy.
    
    Format: frequency velocity error
    
    Parameters
    ----------
    result : DispersionResult
        Dispersion analysis result
    filepath : str
        Output file path
    error_percent : float
        Error as percentage of velocity (default: 10%)
    
    Returns
    -------
    str
        Path to exported file
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        # Dinver format header
        f.write("# Dispersion curve for Dinver\n")
        f.write(f"# Midpoint: {result.midpoint:.1f} m\n")
        f.write(f"# Config: {result.subarray_config}\n")
        f.write("# Format: frequency(Hz) slowness(s/m) error(s/m)\n")
        f.write("# or: frequency(Hz) velocity(m/s) error(m/s)\n")
        
        for freq, vel in zip(result.frequencies, result.picked_velocities):
            if not np.isnan(vel) and vel > 0:
                error = vel * error_percent / 100.0
                f.write(f"{freq:.6f} {vel:.6f} {error:.6f}\n")
    
    return filepath
