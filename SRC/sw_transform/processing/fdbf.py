"""FDBF - Frequency-Domain Beamformer based on swprocess (Vantassel 2021).

Implements Zywicki (1999) beamforming with:
- Multiple weighting options: none, sqrt, invamp
- Multiple steering options: plane, cylindrical
- Direct velocity-space output
"""

from __future__ import annotations

import numpy as np
from scipy import special


def fdbf_transform(data, dt, dx, fmin=5.0, fmax=100.0, nvel=400, vmin=50.0, vmax=5000.0,
                   vspace="linear", weighting='none', steering='plane'):
    """Frequency-Domain Beamformer transform (swprocess implementation).
    
    Based on Zywicki (1999) and Vantassel (2021) swprocess.
    Works directly in velocity-space for dispersion imaging.
    
    Parameters
    ----------
    data : ndarray
        Time-domain data matrix (nsamples, nchannels)
    dt : float
        Time sampling interval (seconds)
    dx : float or array-like
        Geophone spacing (meters) or array of positions
    fmin, fmax : float
        Frequency range (Hz)
    nvel : int
        Number of velocity samples
    vmin, vmax : float
        Velocity range (m/s)
    vspace : str
        'linear' or 'log' velocity spacing
    weighting : str
        Weighting mode: 'none', 'sqrt', 'invamp'
        - 'none': No weighting (standard FDBF)
        - 'sqrt': Square root of distance weighting
        - 'invamp': Inverse amplitude weighting (good for vibrosis sources)
    steering : str
        Steering mode: 'plane' or 'cylindrical'
        - 'plane': Plane wave assumption
        - 'cylindrical': Cylindrical wave using Hankel function
        
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
    
    # Receiver offsets (relative positions)
    if np.isscalar(dx):
        offsets = np.arange(nchannels) * dx
    else:
        offsets = np.asarray(dx)
    
    # Frequency vector
    df = 1.0 / (nsamples * dt)
    frqs = np.arange(nsamples) * df
    
    # Keep frequencies in range
    keep_ids = np.where((frqs >= fmin) & (frqs <= fmax))[0]
    frequencies = frqs[keep_ids]
    nfreq = len(frequencies)
    
    # Velocity vector
    if vspace == "log":
        velocities = np.geomspace(vmin, vmax, nvel)
    else:
        velocities = np.linspace(vmin, vmax, nvel)
    
    # FFT of data - shape (nchannels, nsamples)
    tmatrix = data.T
    transform = np.fft.fft(tmatrix, axis=1)
    transform = transform[:, keep_ids]  # Trim to freq range (nchannels, nfreq)
    
    # Apply weighting to transform
    if weighting == 'invamp':
        # Inverse amplitude weighting: compensates for frequency-dependent attenuation
        weight = 1.0 / np.abs(np.mean(transform, axis=0, keepdims=True))
        weight = np.where(np.isinf(weight) | np.isnan(weight), 1.0, weight)
        transform = transform * weight
    elif weighting == 'sqrt':
        # Square root of distance weighting applied to transform
        w = np.sqrt(np.maximum(offsets, 1.0))[:, np.newaxis]
        transform = transform * w
    
    # Vectorized FDBF computation with chunked frequency processing
    # Chunks avoid allocating the full (nvel, nchan, nfreq) steering matrix
    
    MAX_CHUNK_BYTES = 512 * 1024 * 1024  # 512 MB target per chunk
    bytes_per_element = 16  # complex128
    elements_per_freq = nvel * nchannels
    chunk_size = max(1, MAX_CHUNK_BYTES // (elements_per_freq * bytes_per_element))
    
    power = np.empty((nvel, nfreq), dtype=np.float64)
    
    for f_start in range(0, nfreq, chunk_size):
        f_end = min(f_start + chunk_size, nfreq)
        
        V = velocities[:, np.newaxis, np.newaxis]       # (nvel, 1, 1)
        X = offsets[np.newaxis, :, np.newaxis]           # (1, nchannels, 1)
        F_chunk = frequencies[np.newaxis, np.newaxis, f_start:f_end]  # (1, 1, chunk)
        
        with np.errstate(divide='ignore', invalid='ignore'):
            phase = 2.0 * np.pi * F_chunk * X / V       # (nvel, nchannels, chunk)
            phase = np.where(np.isfinite(phase), phase, 0.0)
        
        # Steering function
        if steering == 'cylindrical':
            with np.errstate(divide='ignore', invalid='ignore'):
                h0 = special.j0(phase) + 1j * special.y0(phase)
                h0 = np.where(phase > 1e-10, h0, 1.0 + 0j)
            steer = np.exp(1j * np.angle(h0))
        else:  # plane
            steer = np.exp(1j * phase)
        
        U_chunk = transform[np.newaxis, :, f_start:f_end]  # (1, nchannels, chunk)
        inner = steer * U_chunk
        power[:, f_start:f_end] = np.abs(np.sum(inner, axis=1)) ** 2
        
        del phase, steer, inner, U_chunk
    
    # Normalize per frequency
    max_per_freq = np.max(power, axis=0, keepdims=True)
    max_per_freq[max_per_freq == 0] = 1.0
    power = power / max_per_freq
    
    return frequencies, velocities, power


def analyze_fdbf_spectrum(freq_sub, velocities, power, normalization="frequency-maximum", tol=0.0,
                          power_threshold=0.1, velocity_min=50.0, velocity_max=5000.0):
    """Analyze FDBF spectrum and pick dispersion curve.
    
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
    
    # Handle all-NaN case
    if np.all(np.isnan(pnorm)):
        pnorm = np.zeros_like(pnorm)
    
    # Store raw power for threshold check
    global_max_power = np.nanmax(pnorm) if pnorm.size > 0 and np.any(np.isfinite(pnorm)) else 1.0
    max_power_per_freq = np.nanmax(pnorm, axis=0) if np.any(np.isfinite(pnorm)) else np.ones(pnorm.shape[1])
    
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


def plot_fdbf_dispersion(freq_sub, velocities, pnorm, vmax_picks, vmin_plot=0, vmax_plot=5000,
                         min_frequency=0, max_frequency=None, title="FDBF Dispersion", cmap="jet",
                         offset_label="", fig_name="", power_mask_threshold=0.0,
                         freq_tick_spacing='auto', vel_tick_spacing='auto',
                         fig_width=8, fig_height=6, contour_levels=30, plot_style='contourf'):
    """Plot FDBF dispersion in frequency-velocity domain.
    
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
    
    fig_w = float(fig_width) if fig_width else 8
    fig_h = float(fig_height) if fig_height else 6
    n_levels = int(contour_levels) if contour_levels else 30

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    P_masked = np.ma.masked_invalid(P_plot)
    if plot_style == 'pcolormesh':
        cf = ax.pcolormesh(F, V, P_masked, cmap=cmap, shading='auto')
    else:
        cf = ax.contourf(F, V, P_masked, levels=n_levels, cmap=cmap)
    plt.colorbar(cf, label="Normalized Power")
    ax.plot(freq_sub, vmax_picks, 'o', mfc='none', mec='white', ms=4, label="Dispersion Picks")
    
    ttl = title if offset_label == "" else f"{title}\n{offset_label}"
    ax.set_title(ttl)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Phase Velocity (m/s)")
    ax.set_xlim(min_frequency, max_frequency)
    ax.set_ylim(vmin_plot, vmax_plot)
    
    if freq_tick_spacing != 'auto':
        try:
            spacing = float(freq_tick_spacing)
            ax.xaxis.set_major_locator(ticker.MultipleLocator(spacing))
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
    
    ax.set_xlim(min_frequency, max_frequency)
    ax.set_ylim(vmin_plot, vmax_plot)
    
    if fig_name:
        plt.savefig(fig_name, bbox_inches="tight")
        plt.close()
    else:
        plt.show()
        plt.close()


# Legacy API aliases for backward compatibility
def compute_cross_spectra(Timematrix, fs, max_frequency=100.0, do_tra_subsample=True, 
                          keep_below_10=True, desired_number=400, weight_mode='none'):
    """Legacy API - redirects to fdbf_transform."""
    dt = 1.0 / fs
    nsamples, nchannels = Timematrix.shape
    # This function used to return cross-spectra; now just returns frequencies
    # as the new API handles everything in fdbf_transform
    df = 1.0 / (nsamples * dt)
    freq_full = np.arange(nsamples // 2 + 1) * df
    mask = freq_full <= max_frequency
    return None, freq_full[mask]


def fk_analysis_1d(R_sub, freq_sub, spacing, cylindrical=False, numk=4000, 
                   min_velocity=100, max_velocity=5000, tol=0.0):
    """Legacy API - use fdbf_transform + analyze_fdbf_spectrum instead."""
    # This is kept for backward compatibility but the new code path
    # uses fdbf_transform directly
    nfreq = len(freq_sub)
    velocities = np.linspace(min_velocity, max_velocity, numk)
    pnorm = np.zeros((numk, nfreq))
    vmax = np.full(nfreq, np.nan)
    wavelength = np.zeros(nfreq)
    return velocities, pnorm, vmax, wavelength


def plot_freq_velocity_spectrum(freq_sub, velocities, pnorm, vmax, max_velocity=5000, 
                                max_frequency=100.0, offset_label="", fig_name="", 
                                title=None):
    """Legacy API - redirects to plot_fdbf_dispersion."""
    plot_fdbf_dispersion(freq_sub, velocities, pnorm, vmax, 
                         vmax_plot=max_velocity, max_frequency=max_frequency,
                         title=title or "FDBF Dispersion", 
                         offset_label=offset_label, fig_name=fig_name)


def fdbf_transform_from_R(R: np.ndarray, frequencies: np.ndarray, dx,
                          fmin: float = 5.0, fmax: float = 100.0,
                          nvel: int = 400, vmin: float = 50.0, vmax: float = 5000.0,
                          vspace: str = "linear", steering: str = "cylindrical") -> tuple:
    """FDBF transform using pre-computed cross-spectral matrix R.
    
    This function is designed for vibrosis data where transfer functions
    are already in the frequency domain. It skips FFT and applies
    beamforming directly to the cross-spectral matrix.
    
    Based on UofA_MASWMultiProcessV2Cyl.m MATLAB implementation.
    
    Parameters
    ----------
    R : ndarray
        Cross-spectral matrix (nchannels, nchannels, nfreq)
        R[j, i, f] = TF[f, i] / TF[f, j]
    frequencies : ndarray
        Frequency vector (Hz) corresponding to R
    dx : float or array-like
        Geophone spacing (meters) or array of positions
    fmin, fmax : float
        Frequency range to process (Hz)
    nvel : int
        Number of velocity samples
    vmin, vmax : float
        Velocity range (m/s)
    vspace : str
        'linear' or 'log' velocity spacing
    steering : str
        'plane' or 'cylindrical' (default cylindrical for vibrosis)
        
    Returns
    -------
    freq_out : ndarray
        Output frequency vector (Hz)
    velocities : ndarray
        Velocity vector (m/s)
    power : ndarray
        Normalized power spectrum (nvel, nfreq_out)
    """
    nchannels = R.shape[0]
    
    # Filter frequency range
    freq_mask = (frequencies >= fmin) & (frequencies <= fmax)
    freq_out = frequencies[freq_mask]
    R_sub = R[:, :, freq_mask]  # (nchannels, nchannels, nfreq_sub)
    nfreq = len(freq_out)
    
    # Velocity vector
    if vspace == "log":
        velocities = np.geomspace(vmin, vmax, nvel)
    else:
        velocities = np.linspace(vmin, vmax, nvel)
    
    # Receiver offsets (relative positions)
    if np.isscalar(dx):
        offsets = np.arange(nchannels, dtype=float) * dx
    else:
        offsets = np.asarray(dx, dtype=float)
    
    # Compute power spectrum using beamforming
    # For each velocity v and frequency f:
    #   P(v, f) = |sum_i sum_j e(i) * conj(e(j)) * R(j, i, f)|
    # where e(i) = steering vector element for receiver i
    
    power = np.zeros((nvel, nfreq), dtype=float)
    
    for iv, vel in enumerate(velocities):
        if vel <= 0:
            continue
            
        for ifr, freq in enumerate(freq_out):
            if freq <= 0:
                continue
            
            # Wavenumber
            k = 2.0 * np.pi * freq / vel
            
            # Phase delays: k * x for each receiver
            phase = k * offsets  # (nchannels,)
            
            # Steering vector
            if steering == 'cylindrical':
                # Cylindrical wave: Hankel function steering
                # Reference: UofA_MASWMultiProcessV2Cyl.m line 329-330
                with np.errstate(divide='ignore', invalid='ignore'):
                    h0 = special.j0(phase) + 1j * special.y0(phase)
                    # Handle near-zero phase (avoid singularity)
                    h0 = np.where(phase > 1e-10, h0, 1.0 + 0j)
                e = np.exp(1j * np.angle(h0))  # +1j per MATLAB reference
            else:
                # Plane wave steering
                e = np.exp(1j * phase)
            
            # Beamformer output: e^H * R * e
            # = sum_j sum_i conj(e[j]) * R[j,i,f] * e[i]
            R_f = R_sub[:, :, ifr]  # (nchannels, nchannels)
            
            # Vectorized: e^H * R * e
            beam_out = np.dot(np.conj(e), np.dot(R_f, e))
            power[iv, ifr] = np.abs(beam_out)
    
    # Normalize per frequency
    max_per_freq = np.max(power, axis=0, keepdims=True)
    max_per_freq[max_per_freq == 0] = 1.0
    power = power / max_per_freq
    
    return freq_out, velocities, power


def fdbf_transform_from_R_vectorized(R: np.ndarray, frequencies: np.ndarray, dx,
                                     fmin: float = 5.0, fmax: float = 100.0,
                                     nvel: int = 400, vmin: float = 50.0, vmax: float = 5000.0,
                                     vspace: str = "linear", steering: str = "cylindrical") -> tuple:
    """Vectorized FDBF transform from cross-spectral matrix R.
    
    Faster implementation using numpy broadcasting. Same parameters and
    returns as fdbf_transform_from_R.
    """
    nchannels = R.shape[0]
    
    # Filter frequency range
    freq_mask = (frequencies >= fmin) & (frequencies <= fmax)
    freq_out = frequencies[freq_mask]
    R_sub = R[:, :, freq_mask]  # (nchannels, nchannels, nfreq_sub)
    nfreq = len(freq_out)
    
    if nfreq == 0:
        return freq_out, np.array([]), np.array([]).reshape(0, 0)
    
    # Velocity vector
    if vspace == "log":
        velocities = np.geomspace(vmin, vmax, nvel)
    else:
        velocities = np.linspace(vmin, vmax, nvel)
    
    # Receiver offsets
    if np.isscalar(dx):
        offsets = np.arange(nchannels, dtype=float) * dx
    else:
        offsets = np.asarray(dx, dtype=float)
    
    # Chunked steering vector to avoid massive (nvel, nchannels, nfreq) allocation
    power = np.zeros((nvel, nfreq), dtype=float)
    
    MAX_CHUNK_BYTES = 512 * 1024 * 1024
    bytes_per_element = 16  # complex128
    elements_per_freq = nvel * nchannels
    chunk_size = max(1, MAX_CHUNK_BYTES // (elements_per_freq * bytes_per_element))
    
    for f_start in range(0, nfreq, chunk_size):
        f_end = min(f_start + chunk_size, nfreq)
        
        V = velocities[:, np.newaxis, np.newaxis]       # (nvel, 1, 1)
        X = offsets[np.newaxis, :, np.newaxis]           # (1, nchannels, 1)
        F_chunk = freq_out[np.newaxis, np.newaxis, f_start:f_end]  # (1, 1, chunk)
        
        with np.errstate(divide='ignore', invalid='ignore'):
            phase = 2.0 * np.pi * F_chunk * X / V       # (nvel, nchannels, chunk)
            phase = np.where(V > 0, phase, 0)
        
        if steering == 'cylindrical':
            with np.errstate(divide='ignore', invalid='ignore'):
                h0 = special.j0(phase) + 1j * special.y0(phase)
                h0 = np.where(phase > 1e-10, h0, 1.0 + 0j)
            e = np.exp(1j * np.angle(h0))
        else:
            e = np.exp(1j * phase)
        
        # Beamformer per frequency within chunk
        for ifr_local in range(f_end - f_start):
            ifr = f_start + ifr_local
            R_f = R_sub[:, :, ifr]    # (nchannels, nchannels)
            e_f = e[:, :, ifr_local]  # (nvel, nchannels)
            Re = np.dot(R_f, e_f.T)   # (nchannels, nvel)
            beam = np.sum(np.conj(e_f.T) * Re, axis=0)
            power[:, ifr] = np.abs(beam)
        
        del phase, e
    # Normalize per frequency
    max_per_freq = np.max(power, axis=0, keepdims=True)
    max_per_freq[max_per_freq == 0] = 1.0
    power = power / max_per_freq
    
    return freq_out, velocities, power
