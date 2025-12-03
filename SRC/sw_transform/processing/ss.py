"""Slant-Stack (τ-p) transform based on swprocess (Vantassel 2021).

Implements McMechan & Yedlin (1981) slant-stack with:
- Trapezoidal integration in time domain
- Linear interpolation for fractional sample shifts
- Direct velocity-space output
"""

from __future__ import annotations

import numpy as np


def slant_stack_transform(data, dt, dx, fmin=0.0, fmax=100.0, nvel=400, vmin=50.0, vmax=5000.0, vspace="linear"):
    """Slant-Stack (τ-p) transform (swprocess implementation).
    
    Based on McMechan & Yedlin (1981) and Vantassel (2021) swprocess.
    Uses trapezoidal integration with linear interpolation for
    fractional sample shifts.
    
    Parameters
    ----------
    data : ndarray
        Time-domain data matrix (nsamples, nchannels)
    dt : float
        Time sampling interval (seconds)
    dx : float
        Geophone spacing (meters)
    fmin, fmax : float
        Frequency range (Hz)
    nvel : int
        Number of velocity samples
    vmin, vmax : float
        Velocity range (m/s)
    vspace : str
        'linear' or 'log' velocity spacing
        
    Returns
    -------
    frequencies : ndarray
        Frequency vector (Hz)
    velocities : ndarray
        Velocity vector (m/s)
    power : ndarray
        Normalized power spectrum (nvel, nfreq)
    """
    nsamples, nchannels = data.shape
    
    # Receiver positions
    offsets = np.arange(nchannels) * dx
    
    # Create velocity vector
    if vspace == "log":
        velocities = np.geomspace(vmin, vmax, nvel)
    else:
        velocities = np.linspace(vmin, vmax, nvel)
    
    # Compute differential distances for trapezoidal integration
    diff = offsets[1:] - offsets[:-1]
    diff = diff.reshape((len(diff), 1))
    
    # Transposed data matrix (nchannels, nsamples)
    tmatrix = data.T
    
    # Determine number of tau samples (avoid wrap-around artifacts)
    # Maximum time shift is max_offset / min_velocity
    max_shift_samples = int(np.max(offsets) / vmin / dt) + 1
    ntaus = max(1, nsamples - max_shift_samples - 1)
    
    # Initialize slant-stack array
    slant_stack_arr = np.zeros((nvel, ntaus))
    
    # Pre-compute index arrays for efficiency
    rows = np.tile(np.arange(nchannels).reshape(nchannels, 1), (1, ntaus))
    cols_base = np.tile(np.arange(ntaus).reshape(1, ntaus), (nchannels, 1))
    
    pre_float_indices = offsets.reshape(nchannels, 1) / dt
    
    # Perform slant-stack for each velocity
    for i, velocity in enumerate(velocities):
        # Time shifts for this velocity: t_shift = offset / velocity
        float_indices = pre_float_indices / velocity
        lower_indices = np.array(float_indices, dtype=int)
        delta = float_indices - lower_indices  # Fractional part for interpolation
        
        # Column indices including shift
        cols = cols_base + lower_indices
        
        # Clip indices to valid range
        cols_clipped = np.clip(cols, 0, nsamples - 2)
        cols_clipped_p1 = np.clip(cols + 1, 0, nsamples - 1)
        
        # Linear interpolation for fractional sample shifts
        amplitudes = tmatrix[rows, cols_clipped] * (1 - delta) + tmatrix[rows, cols_clipped_p1] * delta
        
        # Trapezoidal integration across array
        integral = 0.5 * diff * (amplitudes[1:, :] + amplitudes[:-1, :])
        summation = np.sum(integral, axis=0)
        slant_stack_arr[i, :] = summation
    
    # Transform to frequency domain
    power = np.abs(np.fft.fft(slant_stack_arr, n=nsamples, axis=1))
    
    # Frequency vector
    df = 1.0 / (nsamples * dt)
    freq_full = np.arange(nsamples) * df
    
    # Trim to frequency range
    keep_ids = np.where((freq_full >= fmin) & (freq_full <= fmax))[0]
    frequencies = freq_full[keep_ids]
    power = power[:, keep_ids]
    
    # Normalize per frequency
    for i in range(len(frequencies)):
        max_val = np.max(power[:, i])
        if max_val > 0:
            power[:, i] /= max_val
    
    return frequencies, velocities, power


def analyze_slant_stack(freq_sub, velocities, power, normalization="frequency-maximum", tol=0.0,
                        power_threshold=0.1, velocity_min=50.0, velocity_max=5000.0):
    """Analyze Slant-Stack spectrum and pick dispersion curve.
    
    Parameters
    ----------
    freq_sub : ndarray
        Frequency vector (Hz)
    velocities : ndarray
        Velocity vector (m/s)
    power : ndarray
        Power spectrum (nvel, nfreq)
    normalization : str
        Normalization method
    tol : float
        Tolerance for removing closely-spaced picks
    power_threshold : float
        Minimum normalized power to consider valid
    velocity_min, velocity_max : float
        Velocity bounds for filtering picks
        
    Returns
    -------
    pnorm : ndarray
        Normalized power spectrum
    vmax : ndarray
        Picked velocities
    wavelength : ndarray
        Wavelength at each frequency
    freq_out : ndarray
        Output frequency vector
    """
    # Skip DC component
    if freq_sub[0] == 0:
        freq_sub = freq_sub[1:]
        power = power[:, 1:]
    
    pnorm = np.abs(power.copy())
    
    # Store raw power for threshold check
    global_max_power = np.nanmax(pnorm) if np.nanmax(pnorm) > 0 else 1.0
    max_power_per_freq = np.nanmax(pnorm, axis=0)
    
    # Normalize
    if normalization == "none":
        pass
    elif normalization == "absolute-maximum":
        pnorm = pnorm / global_max_power
    else:  # frequency-maximum
        fac = max_power_per_freq.copy()
        fac[fac == 0] = 1.0
        fac[np.isnan(fac)] = 1.0
        pnorm = pnorm / fac
    
    # Find peaks with margin
    margin = min(5, len(velocities) // 10)
    valid_slice = slice(margin, -margin if margin > 0 else None)
    idx = np.nanargmax(pnorm[valid_slice, :], axis=0)
    vmax = velocities[valid_slice][idx].astype(float)
    
    # Apply power threshold
    normalized_freq_power = max_power_per_freq / global_max_power
    low_power_mask = normalized_freq_power < power_threshold
    vmax[low_power_mask] = np.nan
    
    # Apply velocity bounds
    vmax[(vmax < velocity_min) | (vmax > velocity_max)] = np.nan
    
    # Apply tolerance filter
    if tol > 0 and len(vmax) > 1:
        dv_min = tol * (velocities[1] - velocities[0]) if len(velocities) > 1 else 0
        last_v = None
        for i, v in enumerate(vmax):
            if np.isnan(v):
                continue
            if last_v is not None and abs(v - last_v) < dv_min:
                vmax[i] = np.nan
            else:
                last_v = v
    
    wavelength = vmax / freq_sub
    return pnorm, vmax, wavelength, freq_sub


def plot_slant_stack_dispersion(freq_sub, velocities, pnorm, vmax_picks, vmin_plot=0, vmax_plot=5000,
                                 min_frequency=0, max_frequency=None, title="Slant-Stack Dispersion", cmap="jet",
                                 offset_label="", fig_name="", power_mask_threshold=0.0,
                                 freq_tick_spacing='auto', vel_tick_spacing='auto'):
    """Plot Slant-Stack dispersion in frequency-velocity domain.
    
    Parameters
    ----------
    freq_sub : ndarray
        Frequency vector
    velocities : ndarray
        Velocity vector
    pnorm : ndarray
        Normalized power (nvel, nfreq)
    vmax_picks : ndarray
        Picked velocities
    vmin_plot : float
        Minimum velocity for plot
    vmax_plot : float
        Maximum velocity for plot
    min_frequency : float
        Minimum frequency for plot
    max_frequency : float
        Maximum frequency for plot
    title : str
        Plot title
    cmap : str
        Colormap name
    offset_label : str
        Shot offset label
    fig_name : str
        Output filename
    power_mask_threshold : float
        Threshold below which power is masked
    freq_tick_spacing : str or float
        Frequency axis tick spacing ('auto' or value in Hz)
    vel_tick_spacing : str or float
        Velocity axis tick spacing ('auto' or value in m/s)
    """
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    
    max_frequency = max_frequency or freq_sub[-1]
    min_frequency = min_frequency or 0
    
    V, F = np.meshgrid(velocities, freq_sub, indexing='ij')
    
    P_plot = pnorm.copy()
    if power_mask_threshold > 0:
        global_max = np.nanmax(P_plot)
        if global_max > 0:
            P_plot[P_plot < power_mask_threshold * global_max] = np.nan
    
    fig, ax = plt.subplots(figsize=(8, 6))
    P_masked = np.ma.masked_invalid(P_plot)
    cf = ax.contourf(F, V, P_masked, levels=30, cmap=cmap)
    plt.colorbar(cf, label="Normalized Power")
    ax.plot(freq_sub, vmax_picks, 'o', mfc='none', mec='white', ms=4, label="Dispersion Picks")
    
    ttl = title if offset_label == "" else f"{title}\nShot offset: {offset_label}"
    ax.set_title(ttl)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Phase Velocity (m/s)")
    ax.set_xlim(min_frequency, max_frequency)
    ax.set_ylim(vmin_plot, vmax_plot)
    
    # Apply custom tick spacing with adaptive font sizing
    if freq_tick_spacing != 'auto':
        try:
            spacing = float(freq_tick_spacing)
            ax.xaxis.set_major_locator(ticker.MultipleLocator(spacing))
            # Smaller font and rotation for finer spacing to prevent overlap
            if spacing <= 2:
                ax.tick_params(axis='x', labelsize=7, rotation=45)
            elif spacing <= 5:
                ax.tick_params(axis='x', labelsize=8, rotation=30)
            else:
                ax.tick_params(axis='x', labelsize=9)
        except (ValueError, TypeError):
            pass
    if vel_tick_spacing != 'auto':
        try:
            spacing = float(vel_tick_spacing)
            ax.yaxis.set_major_locator(ticker.MultipleLocator(spacing))
            # Smaller font for finer spacing to prevent overlap
            if spacing <= 25:
                ax.tick_params(axis='y', labelsize=7)
            elif spacing <= 50:
                ax.tick_params(axis='y', labelsize=8)
            else:
                ax.tick_params(axis='y', labelsize=9)
        except (ValueError, TypeError):
            pass
    
    ax.grid(alpha=0.3)
    ax.legend()
    plt.tight_layout()
    
    # Re-apply limits after tight_layout to ensure they stick
    ax.set_xlim(min_frequency, max_frequency)
    ax.set_ylim(vmin_plot, vmax_plot)
    
    if fig_name:
        plt.savefig(fig_name, bbox_inches="tight")
        plt.close()
    else:
        plt.show()
        plt.close()


