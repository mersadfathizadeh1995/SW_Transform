"""FDBF (native) cross-spectra + f-k analysis and plotting."""

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


def compute_cross_spectra(Timematrix, fs, max_frequency=100.0, do_tra_subsample=True, keep_below_10=True, desired_number=400, weight_mode='none'):
    import numpy as np
    from scipy.signal import csd
    num_samples, num_channels = Timematrix.shape
    R_full = np.zeros((num_channels, num_channels, num_samples // 2 + 1), dtype=complex)
    for m in range(num_channels):
        for n in range(num_channels):
            f, Pxy = csd(Timematrix[:, m], Timematrix[:, n], fs=fs, window='boxcar', nperseg=num_samples, noverlap=0)
            R_full[m, n, :] = Pxy
    freq_full = f
    
    # Apply frequency-domain weighting based on source type
    if weight_mode == 'invamp':  # For vibrosis sources
        # Apply inverse amplitude weighting to compensate for frequency-dependent attenuation
        for i, freq in enumerate(freq_full):
            if freq > 0:  # Avoid division by zero at DC
                # Inverse amplitude weighting: boost higher frequencies
                weight = np.sqrt(freq / freq_full[-1]) if freq_full[-1] > 0 else 1.0
                R_full[:, :, i] *= weight
    elif weight_mode == 'sqrt':  # Alternative weighting for hammer sources
        # Apply square root weighting
        for i, freq in enumerate(freq_full):
            if freq > 0:
                weight = np.sqrt(np.sqrt(freq / freq_full[-1])) if freq_full[-1] > 0 else 1.0
                R_full[:, :, i] *= weight
    if not do_tra_subsample:
        mask = (freq_full <= max_frequency)
        return R_full[..., mask], freq_full[mask]
    idx_setf10 = int(np.argmin(np.abs(freq_full - 10.0)))
    idx_setfmax = int(np.argmin(np.abs(freq_full - max_frequency)))
    divd = int(round((len(freq_full) - idx_setf10) / desired_number))
    if divd < 1:
        divd = 1
    part1 = list(range(0, idx_setf10 + 1)) if keep_below_10 else []
    part2 = list(range(idx_setf10 + 1, idx_setfmax + 1, divd))
    tra = part1 + part2
    return R_full[:, :, tra], freq_full[tra]


def fk_analysis_1d(R_sub, freq_sub, spacing, cylindrical=False, numk=4000, min_velocity=100, max_velocity=5000, tol=0.0):
    import numpy as np
    num_channels, _, nfreq = R_sub.shape
    position = np.arange(1, num_channels + 1) * spacing
    kalias = 2.0 * np.pi / spacing
    ktrial = np.linspace(0.0001, kalias, numk)
    Power = np.zeros((numk, nfreq), dtype=complex)
    pnorm = np.zeros((numk, nfreq), dtype=complex)
    kmax_arr = np.zeros(nfreq)
    for i in range(nfreq):
        R_f = R_sub[:, :, i]
        for j in range(numk):
            k_j = ktrial[j]
            steer = np.exp(1j * k_j * position)
            Power[j, i] = np.conjugate(steer) @ (R_f @ steer)
        max_val = np.max(np.abs(Power[:, i]))
        if max_val > 0:
            pnorm[:, i] = Power[:, i] / max_val
        kmax_arr[i] = ktrial[int(np.argmax(np.abs(Power[:, i])))]
    vmax = np.zeros(nfreq)
    for i in range(nfreq):
        if freq_sub[i] > 0 and kmax_arr[i] != 0:
            vmax[i] = (2.0 * np.pi * freq_sub[i]) / kmax_arr[i]
    if tol > 0 and len(vmax) > 1:
        dv_min = tol * (max_velocity - min_velocity) / numk
        last = None
        for i, v in enumerate(vmax):
            if last is not None and abs(v - last) < dv_min:
                vmax[i] = np.nan
            else:
                last = v
    wavelength = np.zeros(nfreq)
    for i in range(nfreq):
        if freq_sub[i] > 0:
            wavelength[i] = vmax[i] / freq_sub[i]
    return ktrial, pnorm, vmax, wavelength


def plot_freq_velocity_spectrum(freq_sub, ktrial, pnorm, vmax, max_velocity=5000, max_frequency=100.0, offset_label="", fig_name="", title: str | None = None):
    import numpy as np
    import matplotlib.pyplot as plt
    nfreq = len(freq_sub)
    numk = len(ktrial)
    velocity2d = np.zeros((numk, nfreq))
    for i in range(nfreq):
        for j in range(numk):
            if ktrial[j] != 0:
                velocity2d[j, i] = (2.0 * np.pi * freq_sub[i]) / ktrial[j]
    freq_grid = np.zeros_like(velocity2d)
    for i in range(nfreq):
        freq_grid[:, i] = freq_sub[i]
    plt.figure(figsize=(8, 6))
    cp = plt.contourf(freq_grid, velocity2d, np.abs(pnorm), levels=30, cmap='jet')
    plt.colorbar(cp, label="Normalized Power")
    plt.xlim([0, max_frequency])
    plt.ylim([0, max_velocity])
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Phase Velocity (m/s)")
    title_str = title if (title is not None and len(str(title))>0) else "3-D Dispersion (Freq vs. Velocity)"
    if offset_label:
        title_str += f"\nShot offset: {offset_label}"
    plt.title(title_str)
    plt.plot(freq_sub, vmax, 'o', markerfacecolor='none', markeredgecolor='white', markersize=5)
    plt.grid(True)
    plt.legend(["Dispersion Picks"])
    if fig_name:
        plt.savefig(fig_name, bbox_inches='tight'); plt.close()
    else:
        plt.show(); plt.close()


