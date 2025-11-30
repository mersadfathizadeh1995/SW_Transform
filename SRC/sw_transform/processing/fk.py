"""FK transform/analysis (native wrappers keeping legacy-compatible API)."""

from __future__ import annotations

import os
import sys


def _legacy_base() -> str:
    here = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(here, "..", "..", "..", "Previous", "4_wave_cursor"))


def _ensure_legacy() -> None:
    base = _legacy_base()
    if base not in sys.path:
        sys.path.insert(0, base)


def fk_transform(data, dt, dx, fmin=0.0, fmax=100.0, numk=4000):
    import numpy as np
    n_samples, n_channels = data.shape
    freq_full = np.fft.rfftfreq(n_samples, dt)
    fk_full = np.fft.fft2(data, s=(n_samples, numk), axes=(0, 1))
    fk_half_t = fk_full[:n_samples//2 + 1, :numk//2 + 1]
    fk = np.abs(fk_half_t.T)
    ktrial = 2 * np.pi * np.fft.rfftfreq(numk, d=dx)
    mask = (freq_full >= fmin) & (freq_full <= fmax)
    freq_sub = freq_full[mask]
    power_fk = fk[:, mask]
    return freq_sub, ktrial, power_fk


def analyze_fk_spectrum(freq_sub, ktrial, power_fk, normalization="frequency-maximum", tol=0.0, power_threshold=0.1, velocity_min=50.0, velocity_max=5000.0):
    """Analyze FK spectrum and pick dispersion curve.
    
    Parameters
    ----------
    power_threshold : float
        Minimum normalized power to consider a valid pick (0-1). 
        Frequencies with max power below this fraction of the global maximum are set to NaN.
    velocity_min : float
        Minimum valid velocity (m/s). Picks below this are set to NaN.
    velocity_max : float
        Maximum valid velocity (m/s). Picks above this are set to NaN.
    """
    import numpy as np
    if freq_sub[0] == 0:
        freq_sub = freq_sub[1:]
        power_fk = power_fk[:, 1:]
    
    # Store raw power for threshold check BEFORE normalization
    raw_power = np.abs(power_fk)
    global_max_power = np.max(raw_power) if np.max(raw_power) > 0 else 1.0
    max_power_per_freq = np.max(raw_power, axis=0)  # Max power at each frequency
    
    # Normalize for display
    if normalization == "none":
        pnorm = raw_power
    elif normalization == "absolute-maximum":
        pnorm = raw_power / global_max_power
    else:  # frequency-maximum
        fac = max_power_per_freq.copy()
        fac[fac == 0] = 1.0
        pnorm = raw_power / fac
    
    # Find peaks
    kmax_idx = np.argmax(pnorm, axis=0)
    kmax = ktrial[kmax_idx].copy()
    
    # Check power at picked locations using RAW power relative to global max
    # This identifies frequencies where there's genuinely little signal
    normalized_freq_power = max_power_per_freq / global_max_power
    low_power_mask = normalized_freq_power < power_threshold
    kmax[low_power_mask] = np.nan
    kmax[kmax == 0] = np.nan
    
    omega = 2 * np.pi * freq_sub
    vmax = omega / kmax
    
    # Apply velocity range filter
    vmax[(vmax < velocity_min) | (vmax > velocity_max)] = np.nan
    
    if tol > 0 and len(vmax) > 1:
        # Safe division - avoid ktrial[0] if it's 0
        if ktrial[1] > 0:
            dv_min = tol * (omega[0]/ktrial[1] - omega[0]/max(ktrial[0], 1e-10))
        else:
            dv_min = 0
        last = None
        for i, v in enumerate(vmax):
            if np.isnan(v):
                continue
            if last is not None and abs(v-last) < dv_min:
                vmax[i] = np.nan
            else:
                last = v
    wavelength = vmax / freq_sub
    return freq_sub, ktrial, pnorm, vmax, wavelength


def plot_freq_velocity_uniform(freq_sub, ktrial, pnorm, vmax_picks, vmax_plot=5000, max_frequency=None, title="FK Dispersion (uniform v)", cmap="jet", nv=400, offset_label="", fig_name=""):
    import numpy as np
    import matplotlib.pyplot as plt
    n_f = len(freq_sub)
    max_frequency = max_frequency or freq_sub[-1]
    v_min = vmax_plot / nv
    vaxis = np.linspace(v_min, vmax_plot, nv)
    P_vf = np.zeros((nv, n_f))
    for i, f in enumerate(freq_sub):
        mag = np.abs(pnorm[:, i])
        k_need = 2 * np.pi * f / vaxis
        P_vf[:, i] = np.interp(k_need, ktrial, mag, left=0.0, right=0.0)
    X, Y = np.meshgrid(freq_sub, vaxis)
    plt.figure(figsize=(8, 6))
    cf = plt.contourf(X, Y, P_vf, levels=30, cmap=cmap)
    plt.colorbar(cf, label="Normalised Power")
    plt.plot(freq_sub, vmax_picks, 'o', mfc='none', mec='white', ms=4, label="Dispersion Picks")
    ttl = (title or "FK Dispersion (uniform v)") if offset_label == "" else f"{(title or 'FK Dispersion (uniform v)')}\nShot offset: {offset_label}"
    plt.title(ttl)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Phase Velocity (m/s)")
    plt.xlim(0, max_frequency)
    plt.ylim(0, vmax_plot)
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    if fig_name:
        plt.savefig(fig_name, bbox_inches="tight")
        plt.close()
    else:
        plt.show(); plt.close()


