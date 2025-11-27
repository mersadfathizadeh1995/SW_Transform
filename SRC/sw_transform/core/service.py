"""Processing service (central orchestration API).

Provides stable functions that the GUI and CLI call. Uses the native
implementations under ``sw_transform.processing`` and the unified cache.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Tuple, List

import importlib


def _preprocess_with_cache(path: str, rev: bool, st: float, en: float, downsample: bool, dfac: int, numf: int):
    """Load SEG-2, preprocess, and use cache via package wrappers."""
    from sw_transform.processing.seg2 import load_seg2_ar as _load
    from sw_transform.processing.preprocess import preprocess_data as _prep
    from sw_transform.core.cache import make_key as _mk, load_preprocessed as _cload, save_preprocessed as _csave
    import os as _os
    t, T, _, dx, dt, _ = _load(path)
    keyc = _mk(path, _os.path.getmtime(path), rev, st, en, downsample, dfac, numf)
    cached = _cload(keyc)
    if cached is None:
        Tpre, _, dt2 = _prep(T, t, dt, reverse_shot=rev, start_time=st, end_time=en, do_downsample=downsample, down_factor=dfac, numf=numf)
        _csave(keyc, Tpre, dt2)
    else:
        Tpre = cached["Tpre"]; dt2 = cached["dt2"]
    return Tpre, float(dx), float(dt2)


def _write_per_shot_csv(outdir: str, base: str, key: str, offset_label: str, f: List[float], vmax: List[float], wav: List[float]) -> None:
    import os as _os
    import csv as _csv
    _off = str(offset_label).strip().replace(" ", "").replace("m", "")
    if _off.startswith("+"):
        _off_tag = "p" + _off[1:]
    elif _off.startswith("-"):
        _off_tag = "m" + _off[1:]
    else:
        _off_tag = _off
    csv_name = _os.path.join(outdir, f"{base}_{key}_{_off_tag}.csv")
    _os.makedirs(_os.path.dirname(csv_name), exist_ok=True)
    with open(csv_name, "w", newline="") as fcsv:
        w = _csv.writer(fcsv)
        w.writerow(["Frequency(Hz)", "PhaseVelocity(m/s)", "Wavelength(m)"])
        for i in range(len(f)):
            w.writerow([f[i], vmax[i], wav[i] if i < len(wav) else ""])


def _save_spectrum_npz(outdir: str, base: str, key: str, offset: str,
                       frequencies, velocities, power, picked_velocities,
                       extra_metadata: Dict[str, Any] = None) -> str | None:
    """Save power spectrum data to .npz file with metadata.

    Returns the saved file path on success, None on failure (logs warning).
    """
    import numpy as np
    from datetime import datetime

    spectrum_file = os.path.join(outdir, f"{base}_{key}_spectrum.npz")

    try:
        # Prepare metadata dictionary
        metadata = {
            'frequencies': np.asarray(frequencies, dtype=np.float32),
            'velocities': np.asarray(velocities, dtype=np.float32),
            'power': np.asarray(power, dtype=np.float32),
            'picked_velocities': np.asarray(picked_velocities, dtype=np.float32),
            'method': key,
            'offset': offset,
            'export_date': datetime.now().isoformat(),
            'version': '1.0'
        }

        # Add extra metadata if provided
        if extra_metadata:
            for k, v in extra_metadata.items():
                # Convert numpy arrays to appropriate dtype
                if hasattr(v, '__len__') and not isinstance(v, str):
                    metadata[k] = np.asarray(v, dtype=np.float32)
                else:
                    metadata[k] = v

        # Save compressed
        np.savez_compressed(spectrum_file, **metadata)
        return spectrum_file
    except Exception as e:
        # Silent failure - log warning but don't crash processing
        import warnings
        warnings.warn(f"Could not save spectrum to {spectrum_file}: {e}")
        return None


def run_single(params: Dict[str, Any]) -> Tuple[str, bool, str]:
    """Run one transform for one file (headless).

    Expected params keys mirror the GUI/worker calls.
    """
    import numpy as np  # noqa: F401
    import matplotlib
    matplotlib.use("Agg")
    from sw_transform.processing.registry import METHODS, dyn as _dyn, compute_reverse_flag as _crf  # type: ignore

    # Unpack
    path = params['path']; base = params['base']; key = params['key']
    offset = params['offset']; outdir = params['outdir']
    pick_vmin = float(params['pick_vmin']); pick_vmax = float(params['pick_vmax'])
    pick_fmin = float(params['pick_fmin']); pick_fmax = float(params['pick_fmax'])
    st = float(params['st']); en = float(params['en'])
    downsample = bool(params['downsample']); dfac = int(params['dfac']); numf = int(params['numf'])
    grid_n = int(params['grid_n']); tol = float(params['tol']); vspace = params['vspace']
    fig_dpi = int(params.get('dpi', 200))
    user_rev = bool(params.get('rev', False))
    topic = (params.get('topic') or "").strip()
    source_type = params.get('source_type', 'hammer')
    export_spectra = bool(params.get('export_spectra', True))  # Default ON

    try:
        import matplotlib as mpl
        old_dpi = mpl.rcParams.get('savefig.dpi', 'figure')
        mpl.rcParams['savefig.dpi'] = fig_dpi
    except Exception:
        old_dpi = None

    try:
        os.makedirs(outdir, exist_ok=True)
        rev = user_rev  # already computed by caller
        Tpre, dx, dt2 = _preprocess_with_cache(path, rev, st, en, downsample, dfac, numf)
        cfg = METHODS[key]
        step3, step4, plot = map(_dyn, (cfg["step3"], cfg["step4"], cfg["plot"]))
        base_pkw = cfg.get("plot_kwargs", {})
        max_freq = pick_fmax
        fig_name = os.path.join(outdir, f"{base}_{key}.png")
        if key == "fk":
            f, k, P = step3(Tpre, dt2, dx, fmin=0, fmax=max_freq, numk=grid_n)
            f, k, pnorm, vmax, wav = step4(f, k, P, tol=tol)
            import numpy as np
            pnorm = np.abs(pnorm)
            # Save spectrum before masking
            if export_spectra:
                # Create uniform velocity grid for spectrum export
                nv = 400
                vaxis = np.linspace(max(1.0, pick_vmin), pick_vmax, nv)
                # Interpolate from k-space to v-space
                P_vf = np.zeros((nv, len(f)))
                for i, fi in enumerate(f):
                    k_need = 2 * np.pi * fi / vaxis
                    P_vf[:, i] = np.interp(k_need, k, pnorm[:, i], left=0.0, right=0.0)
                # Save with wavenumber metadata
                _save_spectrum_npz(outdir, base, key, offset, f, vaxis, P_vf, vmax,
                                  extra_metadata={'wavenumbers': k, 'vibrosis_mode': (source_type == 'vibrosis')})
            mask = (vmax>=pick_vmin)&(vmax<=pick_vmax)&(f>=pick_fmin)&(f<=pick_fmax)
            vmax = np.where(mask, vmax, np.nan)
            pkw = base_pkw.copy(); pkw.update(dict(vmax_plot=pick_vmax, max_frequency=pick_fmax))
            from sw_transform.processing.fk import plot_freq_velocity_uniform as _plot  # type: ignore
            _plot(f, k, pnorm, vmax, title=(topic or f"{base} FK"), offset_label=offset, fig_name=fig_name, **pkw)
        elif key == "fdbf":
            fs = 1.0/dt2
            # Determine weight mode based on source type
            weight_mode = 'invamp' if source_type == 'vibrosis' else 'none'
            R, f = step3(Tpre, fs, max_frequency=max_freq, do_tra_subsample=True, keep_below_10=True, desired_number=400, weight_mode=weight_mode)
            k, pnorm, vmax, wav = step4(R, f, dx, cylindrical=False, numk=grid_n, min_velocity=100, max_velocity=5000, tol=tol)
            import numpy as np
            pnorm = np.abs(pnorm)
            # Save spectrum before plotting
            if export_spectra:
                # Create uniform velocity grid for spectrum export
                nv = 400
                vaxis = np.linspace(max(1.0, pick_vmin), pick_vmax, nv)
                # Interpolate from k-space to v-space
                P_vf = np.zeros((nv, len(f)))
                for i, fi in enumerate(f):
                    k_need = 2 * np.pi * fi / vaxis
                    P_vf[:, i] = np.interp(k_need, k, pnorm[:, i], left=0.0, right=0.0)
                # Save with FDBF-specific metadata
                _save_spectrum_npz(outdir, base, key, offset, f, vaxis, P_vf, vmax,
                                  extra_metadata={'wavenumbers': k, 'vibrosis_mode': (source_type == 'vibrosis'),
                                                 'weight_mode': weight_mode})
            pkw = base_pkw.copy(); pkw.update(dict(max_velocity=pick_vmax, max_frequency=pick_fmax))
            from sw_transform.processing.fdbf import plot_freq_velocity_spectrum as _plot  # type: ignore
            _plot(f, k, pnorm, vmax, offset_label=offset, fig_name=fig_name, title=(topic or f"{base} FDBF"), **pkw)
        elif key == "ps":
            f0, vels, P = step3(Tpre, dt2, dx, fmin=0, fmax=max_freq, nvel=grid_n, vmin=100, vmax=5000, vspace=vspace)
            pnorm, vmax, wav, f = step4(f0, vels, P)
            import numpy as np
            pnorm = np.abs(pnorm)
            # Save spectrum (PS already in velocity space)
            if export_spectra:
                _save_spectrum_npz(outdir, base, key, offset, f, vels, pnorm, vmax,
                                  extra_metadata={'vspace': vspace, 'vibrosis_mode': (source_type == 'vibrosis')})
            pkw = base_pkw.copy(); pkw.update(dict(vmax_plot=pick_vmax))
            from sw_transform.processing.ps import plot_phase_shift_dispersion as _plot  # type: ignore
            _plot(f, vels, pnorm, vmax, title=(topic or f"{base} PS"), offset_label=offset, fig_name=fig_name, **pkw)
        else:
            f0, vels, P = step3(Tpre, dt2, dx, fmin=0, fmax=max_freq, nvel=grid_n, vmin=100, vmax=5000, vspace=vspace)
            pnorm, vmax, wav, f = step4(f0, vels, P)
            import numpy as np
            pnorm = np.abs(pnorm)
            # Save spectrum (SS already in velocity space)
            if export_spectra:
                _save_spectrum_npz(outdir, base, key, offset, f, vels, pnorm, vmax,
                                  extra_metadata={'vibrosis_mode': (source_type == 'vibrosis')})
            pkw = base_pkw.copy(); pkw.update(dict(vmax_plot=pick_vmax))
            from sw_transform.processing.ss import plot_slant_stack_dispersion as _plot  # type: ignore
            _plot(f, vels, pnorm, vmax, title=(topic or f"{base} τ–p"), offset_label=offset, fig_name=fig_name, **pkw)
        # CSV
        _write_per_shot_csv(outdir, base, key, offset, f, vmax, wav)
        return base, True, fig_name
    except Exception as e:
        return base, False, str(e)
    finally:
        try:
            import matplotlib as mpl
            if old_dpi is not None:
                mpl.rcParams['savefig.dpi'] = old_dpi
        except Exception:
            pass


def run_compare(params: Dict[str, Any]) -> Tuple[str, bool, str]:
    import numpy as np  # noqa: F401
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sw_transform.processing.registry import METHODS, dyn as _dyn  # type: ignore

    path = params['path']; base = params['base']; outdir = params['outdir']
    offset = params['offset']
    pick_vmin = float(params['pick_vmin']); pick_vmax = float(params['pick_vmax'])
    pick_fmin = float(params['pick_fmin']); pick_fmax = float(params['pick_fmax'])
    st = float(params['st']); en = float(params['en'])
    downsample = bool(params['downsample']); dfac = int(params['dfac']); numf = int(params['numf'])
    n_fk = int(params['n_fk']); tol_fk = float(params['tol_fk'])
    n_ps = int(params['n_ps']); vspace_ps = params['vspace_ps']
    topic = (params.get('topic') or '').strip()
    source_type = params.get('source_type', 'hammer')
    export_spectra = bool(params.get('export_spectra', True))  # Default ON
    # reverse flags prepared by caller per-method
    rev_fk = bool(params.get('rev_fk', False)); rev_ps = bool(params.get('rev_ps', False))
    rev_fdbf = bool(params.get('rev_fdbf', False)); rev_ss = bool(params.get('rev_ss', False))

    try:
        os.makedirs(outdir, exist_ok=True)
        fig, axs = plt.subplots(2, 2, figsize=(9, 6), dpi=130, sharex=False, sharey=False)
        ax_order = [(axs[0,0], 'fdbf'), (axs[0,1], 'fk'), (axs[1,0], 'ps'), (axs[1,1], 'ss')]
        combined = []
        # Preprocess per-method with reverse as supplied
        for ax, key in ax_order:
            rev = {'fk': rev_fk, 'ps': rev_ps, 'fdbf': rev_fdbf, 'ss': rev_ss}[key]
            Tpre, dx, dt2 = _preprocess_with_cache(path, rev, st, en, downsample, dfac, numf)
            max_freq = pick_fmax
            if key == 'fk':
                step3, step4 = _dyn(tuple(METHODS['fk']['step3'])), _dyn(tuple(METHODS['fk']['step4']))
                f, k, P = step3(Tpre, dt2, dx, fmin=0, fmax=max_freq, numk=n_fk)
                f, k, pnorm, vmax, wav = step4(f, k, P, tol=tol_fk)
                import numpy as np
                nv = 400; vaxis = np.linspace(max(1.0, pick_vmin), pick_vmax, nv)
                Z = np.zeros((nv, len(f))); mag = np.abs(pnorm)
                for i, fi in enumerate(f):
                    k_need = 2*np.pi*fi / vaxis
                    Z[:, i] = np.interp(k_need, k, mag[:, i], left=0.0, right=0.0)
                # Save spectrum in compare mode
                if export_spectra:
                    _save_spectrum_npz(outdir, base, key, offset, f, vaxis, Z, vmax,
                                      extra_metadata={'wavenumbers': k, 'vibrosis_mode': (source_type == 'vibrosis')})
                ax.contourf(f, vaxis, Z, 30, cmap='jet'); ax.plot(f, vmax, 'o', mfc='none', mec='white', ms=3)
            elif key == 'fdbf':
                fs = 1.0/dt2
                step3, step4 = _dyn(tuple(METHODS['fdbf']['step3'])), _dyn(tuple(METHODS['fdbf']['step4']))
                # Determine weight mode based on source type
                weight_mode = 'invamp' if source_type == 'vibrosis' else 'none'
                R, f = step3(Tpre, fs, max_frequency=max_freq, do_tra_subsample=True, keep_below_10=True, desired_number=400, weight_mode=weight_mode)
                k, pnorm, vmax, wav = step4(R, f, dx, cylindrical=False, numk=n_fk, min_velocity=100, max_velocity=5000, tol=tol_fk)
                import numpy as np
                nv = 400; vaxis = np.linspace(max(1.0, pick_vmin), pick_vmax, nv)
                Z = np.zeros((nv, len(f))); mag = np.abs(pnorm)
                for i, fi in enumerate(f):
                    k_need = 2*np.pi*fi / vaxis
                    Z[:, i] = np.interp(k_need, k, mag[:, i], left=0.0, right=0.0)
                # Save spectrum in compare mode
                if export_spectra:
                    _save_spectrum_npz(outdir, base, key, offset, f, vaxis, Z, vmax,
                                      extra_metadata={'wavenumbers': k, 'vibrosis_mode': (source_type == 'vibrosis'),
                                                     'weight_mode': weight_mode})
                ax.contourf(f, vaxis, Z, 30, cmap='jet'); ax.plot(f, vmax, 'o', mfc='none', mec='white', ms=3)
            elif key == 'ps':
                step3, step4 = _dyn(tuple(METHODS['ps']['step3'])), _dyn(tuple(METHODS['ps']['step4']))
                f0, vels, P = step3(Tpre, dt2, dx, fmin=0, fmax=max_freq, nvel=n_ps, vmin=100, vmax=5000, vspace=vspace_ps)
                pnorm, vmax, wav, f = step4(f0, vels, P)
                # Save spectrum in compare mode
                if export_spectra:
                    import numpy as np
                    _save_spectrum_npz(outdir, base, key, offset, f, vels, np.abs(pnorm), vmax,
                                      extra_metadata={'vspace': vspace_ps, 'vibrosis_mode': (source_type == 'vibrosis')})
                ax.contourf(f, vels, pnorm, 30, cmap='jet'); ax.plot(f, vmax, 'o', mfc='none', mec='white', ms=3)
            else:
                step3, step4 = _dyn(tuple(METHODS['ss']['step3'])), _dyn(tuple(METHODS['ss']['step4']))
                f0, vels, P = step3(Tpre, dt2, dx, fmin=0, fmax=max_freq, nvel=n_ps, vmin=100, vmax=5000, vspace=vspace_ps)
                pnorm, vmax, wav, f = step4(f0, vels, P)
                # Save spectrum in compare mode
                if export_spectra:
                    import numpy as np
                    _save_spectrum_npz(outdir, base, key, offset, f, vels, np.abs(pnorm), vmax,
                                      extra_metadata={'vibrosis_mode': (source_type == 'vibrosis')})
                ax.contourf(f, vels, pnorm, 30, cmap='jet'); ax.plot(f, vmax, 'o', mfc='none', mec='white', ms=3)
            ax.set_xlim(pick_fmin, pick_fmax); ax.set_ylim(pick_vmin, pick_vmax)
            ax.set_title(key.upper()); ax.set_xlabel('Frequency (Hz)'); ax.set_ylabel('Phase Velocity (m/s)')
            combined.append((key, f, vmax, wav))
        fig.suptitle(topic or f"{base} – Source offset {offset}")
        out_png = os.path.join(outdir, f"{base}_compare.png")
        fig.tight_layout(rect=[0,0,1,0.95]); fig.savefig(out_png, dpi=130); plt.close(fig)

        # Per-method CSVs and combined per-file CSV
        import csv as _csv
        min_len = min(len(r[1]) for r in combined)
        comb_csv = os.path.join(outdir, f"{base}_compare.csv")
        with open(comb_csv, 'w', newline='') as fcsv:
            w = _csv.writer(fcsv)
            header = []
            for m, _, _, _ in combined:
                header += [f"freq({m}_{offset})", f"vel({m}_{offset})", f"wav({m}_{offset})"]
            w.writerow(header)
            for i in range(min_len):
                row = []
                for _, frq, vel, wav in combined:
                    row += [frq[i], vel[i], wav[i] if i < len(wav) else ""]
                w.writerow(row)
        # also write per-method CSVs
        for m, frq, vel, wav in combined:
            _write_per_shot_csv(outdir, base, m, offset, frq, vel, wav)
        return base, True, out_png
    except Exception as e:
        return base, False, str(e)


