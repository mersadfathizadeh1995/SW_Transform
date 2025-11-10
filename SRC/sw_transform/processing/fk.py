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


def analyze_fk_spectrum(freq_sub, ktrial, power_fk, normalization="frequency-maximum", tol=0.0):
    import numpy as np
    if freq_sub[0] == 0:
        freq_sub = freq_sub[1:]
        power_fk = power_fk[:, 1:]
    if normalization == "none":
        pnorm = np.abs(power_fk)
    elif normalization == "absolute-maximum":
        fac = np.max(np.abs(power_fk)) or 1.0
        pnorm = np.abs(power_fk) / fac
    else:
        fac = np.max(np.abs(power_fk), axis=0)
        fac[fac == 0] = 1.0
        pnorm = np.abs(power_fk) / fac
    kmax = ktrial[np.argmax(pnorm, axis=0)]
    kmax[kmax == 0] = np.nan
    omega = 2 * np.pi * freq_sub
    vmax = omega / kmax
    if tol > 0 and len(vmax) > 1:
        dv_min = tol * (omega[0]/ktrial[1] - omega[0]/ktrial[0])
        last = None
        for i, v in enumerate(vmax):
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


