"""Slant-Stack (native) transform, analysis, and plotting."""

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


def slant_stack(data_t_x, dt, spacing, *, fmin=0.0, fmax=100.0, nvel=1200, vmin=100.0, vmax=5000.0, vspace="linear"):
    import numpy as np
    nt, nch = data_t_x.shape
    offsets = np.arange(nch) * spacing
    velocities = np.linspace(vmin, vmax, nvel)
    shifts = np.round(offsets[None, :] / velocities[:, None] / dt).astype(int)
    sl = np.zeros((nvel, nt))
    dx = np.diff(offsets, prepend=0)
    for i in range(nvel):
        acc = np.zeros(nt)
        for ch in range(nch):
            acc += np.roll(data_t_x[:, ch], -shifts[i, ch]) * dx[ch]
        sl[i, :] = acc / (offsets[-1] if offsets[-1] != 0 else 1.0)
    return sl, velocities


def slant_stack_transform(data_t_x, dt, spacing, *, fmin=0.0, fmax=100.0, nvel=1200, vmin=100.0, vmax=5000.0, vspace="linear"):
    import numpy as np
    from scipy.fft import rfft, rfftfreq
    nt, nch = data_t_x.shape
    velocities = np.linspace(vmin, vmax, nvel)
    # time-domain slant stack then FFT
    sl, velocities = slant_stack(data_t_x, dt, spacing, fmin=fmin, fmax=fmax, nvel=nvel, vmin=vmin, vmax=vmax, vspace=vspace)
    spec = rfft(sl, axis=1)
    power = np.abs(spec)
    freqs = rfftfreq(nt, dt)
    keep = (freqs >= fmin) & (freqs <= fmax)
    return freqs[keep], velocities, power[:, keep]


def analyze_slant_stack(freq, velocities, power, normalise="frequency-maximum", tol: float = 0.0):
    import numpy as np
    if freq[0] == 0.0:
        freq = freq[1:]
        power = power[:, 1:]
    if normalise == "none":
        pnorm = power.copy()
    elif normalise == "absolute-maximum":
        fac = np.max(np.abs(power)) or 1.0
        pnorm = np.abs(power) / fac
    else:
        fac = np.max(np.abs(power), axis=0)
        fac[fac == 0] = 1.0
        pnorm = np.abs(power) / fac
    margin = 5
    idx = np.argmax(pnorm[margin:-margin if margin else None, :], axis=0)
    vmax = velocities[margin:-margin if margin else None][idx]
    if tol > 0.0 and len(vmax) > 1:
        dv = (velocities[1]-velocities[0]) * tol
        last_v = None
        for i, v in enumerate(vmax):
            if last_v is not None and abs(v - last_v) < dv:
                vmax[i] = np.nan
            else:
                last_v = v
    wavelength = vmax / freq
    return pnorm, vmax, wavelength, freq


def plot_slant_stack_dispersion(freq, velocities, pnorm, vmax, *, vmax_plot=5000, title="Slant‑Stack Dispersion", cmap="jet", offset_label="", fig_name="", rasterize=False):
    import numpy as np
    import matplotlib.pyplot as plt
    V, F = np.meshgrid(velocities, freq, indexing='ij')
    plt.figure(figsize=(8, 6))
    cf = plt.contourf(F, V, pnorm, levels=30, cmap=cmap)
    plt.plot(freq, vmax, 'o', mfc='none', mec='white', ms=4, label="Dispersion Picks")
    ttl = (title or "Slant‑Stack Dispersion") if offset_label == "" else f"{(title or 'Slant‑Stack Dispersion')}\nShot offset: {offset_label}"
    plt.title(ttl)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Phase Velocity (m/s)")
    plt.xlim(freq[0], freq[-1])
    plt.ylim(0, vmax_plot)
    plt.colorbar(cf, label="Normalised Power")
    plt.grid(alpha=0.3); plt.legend(); plt.tight_layout()
    if fig_name:
        plt.savefig(fig_name, bbox_inches='tight'); plt.close()
    else:
        plt.show(); plt.close()


