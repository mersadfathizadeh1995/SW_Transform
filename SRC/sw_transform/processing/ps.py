"""Phase-Shift (native) transform, analysis, and plotting."""

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


def phase_shift_transform(tmatrix, dt, dx, fmin=0.0, fmax=100.0, nvel=1200, vmin=50.0, vmax=5000.0, vspace="linear"):
    import numpy as np
    nsamp, nch = tmatrix.shape
    offsets = np.arange(nch) * dx
    fft_full = np.fft.rfft(tmatrix, axis=0)
    freqs_full = np.fft.rfftfreq(nsamp, dt)
    band_mask = (freqs_full >= fmin) & (freqs_full <= fmax)
    freq_sub = freqs_full[band_mask]
    fft_band = fft_full[band_mask, :]
    velocities = np.geomspace(vmin, vmax, nvel) if vspace == "log" else np.linspace(vmin, vmax, nvel)
    power = np.empty((nvel, len(freq_sub)), dtype=float)
    for vi, v in enumerate(velocities):
        phase = 2.0 * np.pi * freq_sub[:, None] * offsets[None, :] / v
        steer = np.exp(1j * phase)
        amp = np.abs(fft_band)
        alpha = 0.5
        weight = (amp / np.maximum(amp.max(axis=1, keepdims=True), 1e-12)) ** alpha
        norm_fft = (fft_band / np.maximum(amp, 1e-12)) * weight
        inner = steer.conj() * norm_fft
        beam = 0.5 * inner[:, 0] + 0.5 * inner[:, -1] + inner[:, 1:-1].sum(axis=1)
        beam *= dx
        power[vi, :] = np.abs(beam)
    return freq_sub, velocities, power


def analyze_phase_shift(freq_sub, velocities, power, normalization="frequency-maximum", tol: float = 0.0):
    import numpy as np
    if freq_sub[0] == 0.0:
        freq_sub = freq_sub[1:]
        power = power[:, 1:]
    if normalization == "none":
        pnorm = power.copy()
    elif normalization == "absolute-maximum":
        pnorm = np.abs(power) / np.nanmax(np.abs(power))
    else:
        denom = np.nanmax(np.abs(power), axis=0, keepdims=True)
        denom[denom == 0] = 1.0
        pnorm = np.abs(power) / denom
    margin = 5
    valid_slice = slice(margin, -margin if margin != 0 else None)
    idx = np.argmax(pnorm[valid_slice, :], axis=0)
    vmax = velocities[valid_slice][idx]
    if tol <= 0.0:
        tol_local = (velocities[1]-velocities[0])*0.5 if len(velocities)>1 else 0.0
    else:
        tol_local = tol
    last_v = None
    for i,v in enumerate(vmax):
        if last_v is not None and abs(v-last_v) < tol_local:
            vmax[i] = np.nan
        else:
            last_v = v
    wavelength = vmax / freq_sub
    return pnorm, vmax, wavelength, freq_sub


def plot_phase_shift_dispersion(freq_sub, velocities, pnorm, vmax, vmax_plot=5000, title="Phase‑Shift Dispersion", cmap="jet", offset_label="", fig_name=""):
    import numpy as np
    import matplotlib.pyplot as plt
    V, F = np.meshgrid(velocities, freq_sub, indexing='ij')
    plt.figure(figsize=(8, 6))
    cf = plt.contourf(F, V, pnorm, levels=30, cmap=cmap)
    plt.colorbar(cf, label="Normalised Power")
    plt.plot(freq_sub, vmax, 'o', mfc='none', mec='white', ms=4, label="Dispersion Picks")
    ttl = (title or "Phase‑Shift Dispersion") if offset_label == "" else f"{(title or 'Phase‑Shift Dispersion')}\nShot offset: {offset_label}"
    plt.title(ttl)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Phase Velocity (m/s)")
    plt.xlim(freq_sub[0], freq_sub[-1])
    plt.ylim(0, vmax_plot)
    plt.grid(alpha=0.3)
    plt.legend(); plt.tight_layout()
    if fig_name:
        plt.savefig(fig_name, bbox_inches="tight"); plt.close()
    else:
        plt.show(); plt.close()


