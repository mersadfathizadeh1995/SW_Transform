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


def _load_vibrosis_mat(path: str, dx: float):
    """Load vibrosis .mat file and return data for FDBF processing.
    
    Parameters
    ----------
    path : str
        Path to .mat file
    dx : float
        Sensor spacing (meters)
        
    Returns
    -------
    R : ndarray
        Cross-spectral matrix (nchannels, nchannels, nfreq)
    frequencies : ndarray
        Frequency vector (Hz)
    n_channels : int
        Number of channels
    """
    from sw_transform.processing.vibrosis import load_vibrosis_mat
    data = load_vibrosis_mat(path)
    return data.R, data.frequencies, data.n_channels


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

    # Convert offset to tag format (same as CSV naming: +66m -> p66)
    _off = str(offset).strip().replace(" ", "").replace("m", "")
    if _off.startswith("+"):
        _off_tag = "p" + _off[1:]
    elif _off.startswith("-"):
        _off_tag = "m" + _off[1:]
    else:
        _off_tag = _off

    spectrum_file = os.path.join(outdir, f"{base}_{key}_{_off_tag}_spectrum.npz")

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


def create_combined_spectrum(outdir: str, method: str, spectrum_files: List[str]) -> str | None:
    """Create combined spectrum .npz file from multiple individual spectrum files.

    Args:
        outdir: Output directory
        method: Method name ('fk', 'fdbf', 'ps', 'ss')
        spectrum_files: List of individual spectrum .npz file paths

    Returns:
        Path to combined file on success, None on failure
    """
    import numpy as np
    from datetime import datetime
    import glob

    if not spectrum_files:
        return None

    try:
        # Load all individual spectrum files
        spectra_data = []
        for fpath in spectrum_files:
            if not os.path.isfile(fpath):
                continue
            data = np.load(fpath)
            # Extract offset tag from filename
            # Format: <base>_<method>_<offset_tag>_spectrum.npz
            fname = os.path.basename(fpath).replace('_spectrum.npz', '')
            parts = fname.split('_')
            # Find method index
            method_idx = -1
            for i, part in enumerate(parts):
                if part == method:
                    method_idx = i
                    break
            if method_idx >= 0 and method_idx < len(parts) - 1:
                offset_tag = parts[method_idx + 1]
            else:
                offset_tag = 'unknown'

            spectra_data.append({
                'offset_tag': offset_tag,
                'frequencies': data['frequencies'],
                'velocities': data['velocities'],
                'power': data['power'],
                'picked_velocities': data['picked_velocities'],
                'metadata': {k: data[k] for k in data.files if k not in
                           ['frequencies', 'velocities', 'power', 'picked_velocities']}
            })

        if not spectra_data:
            return None

        # Sort by offset tag for consistent ordering
        spectra_data.sort(key=lambda x: x['offset_tag'])

        # Build combined metadata dictionary
        combined = {
            'method': method,
            'offsets': np.array([s['offset_tag'] for s in spectra_data], dtype=object),
            'export_date': datetime.now().isoformat(),
            'version': '1.0',
            'num_offsets': len(spectra_data)
        }

        # Add per-offset data with suffix
        for spec in spectra_data:
            tag = spec['offset_tag']
            combined[f'frequencies_{tag}'] = np.asarray(spec['frequencies'], dtype=np.float32)
            combined[f'velocities_{tag}'] = np.asarray(spec['velocities'], dtype=np.float32)
            combined[f'power_{tag}'] = np.asarray(spec['power'], dtype=np.float32)
            combined[f'picked_velocities_{tag}'] = np.asarray(spec['picked_velocities'], dtype=np.float32)

            # Add method-specific metadata with suffix
            for key, val in spec['metadata'].items():
                if key not in ['method', 'offset', 'export_date', 'version']:
                    combined[f'{key}_{tag}'] = val

        # Save combined file
        combined_file = os.path.join(outdir, f"combined_{method}_spectrum.npz")
        np.savez_compressed(combined_file, **combined)
        return combined_file

    except Exception as e:
        import warnings
        warnings.warn(f"Could not create combined spectrum file: {e}")
        return None


def run_single(params: Dict[str, Any]) -> Tuple[str, bool, str]:
    """Run one transform for one file (headless).

    Expected params keys mirror the GUI/worker calls.
    Uses swprocess-inspired unified interface where all transforms
    return (frequencies, velocities, power).
    
    Supports both SEG-2 (.dat) time-domain data and vibrosis (.mat) 
    frequency-domain transfer function data.
    """
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    from sw_transform.processing.registry import METHODS, dyn as _dyn

    # Unpack params
    path = params['path']
    base = params['base']
    key = params['key']
    offset = params['offset']
    outdir = params['outdir']
    pick_vmin = float(params['pick_vmin'])
    pick_vmax = float(params['pick_vmax'])
    pick_fmin = float(params['pick_fmin'])
    pick_fmax = float(params['pick_fmax'])
    st = float(params['st'])
    en = float(params['en'])
    downsample = bool(params['downsample'])
    dfac = int(params['dfac'])
    numf = int(params['numf'])
    grid_n = int(params['grid_n'])
    tol = float(params['tol'])
    vspace = params.get('vspace', 'linear')
    fig_dpi = int(params.get('dpi', 200))
    user_rev = bool(params.get('rev', False))
    topic = (params.get('topic') or "").strip()
    source_type = params.get('source_type', 'hammer')
    cylindrical = bool(params.get('cylindrical', False))
    export_spectra = bool(params.get('export_spectra', True))
    
    # Vibrosis .mat file specific params
    file_type = params.get('file_type', 'seg2')  # 'seg2' or 'mat'
    dx_override = params.get('dx', None)  # Sensor spacing for .mat files
    
    # Plot limit params - separate auto flags for velocity and frequency
    auto_vel_limits = bool(params.get('auto_vel_limits', True))
    auto_freq_limits = bool(params.get('auto_freq_limits', True))
    plot_min_vel_param = params.get('plot_min_vel', '0')
    plot_max_vel_param = params.get('plot_max_vel', '2000')
    plot_min_freq_param = params.get('plot_min_freq', '0')
    plot_max_freq_param = params.get('plot_max_freq', '100')
    
    # Colormap and tick spacing
    cmap = params.get('cmap', 'jet')
    freq_tick_spacing = params.get('freq_tick_spacing', 'auto')
    vel_tick_spacing = params.get('vel_tick_spacing', 'auto')

    try:
        import matplotlib as mpl
        old_dpi = mpl.rcParams.get('savefig.dpi', 'figure')
        mpl.rcParams['savefig.dpi'] = fig_dpi
    except Exception:
        old_dpi = None

    try:
        os.makedirs(outdir, exist_ok=True)
        
        # Detect file type from extension if not specified
        ext = os.path.splitext(path)[1].lower()
        if file_type == 'seg2' and ext == '.mat':
            file_type = 'mat'
        
        # Get method configuration
        cfg = METHODS[key]
        analyze_func = _dyn(cfg["analyze"])
        plot_func = _dyn(cfg["plot"])
        base_pkw = cfg.get("plot_kwargs", {}).copy()
        
        fig_name = os.path.join(outdir, f"{base}_{key}.png")
        
        # === Branch by file type ===
        if file_type == 'mat':
            # Vibrosis .mat file: frequency-domain transfer function data
            # Only FDBF method is supported for .mat files
            if key != 'fdbf':
                return base, False, f"Method {key} not supported for .mat files. Use FDBF."
            
            # Get dx (sensor spacing) - required for .mat files
            if dx_override is None:
                return base, False, "Sensor spacing (dx) required for .mat files. Set in Advanced Settings."
            dx = float(dx_override)
            
            # Load vibrosis data
            R, frequencies, n_channels = _load_vibrosis_mat(path, dx)
            
            # Use FDBF from R (cross-spectral matrix)
            from sw_transform.processing.fdbf import fdbf_transform_from_R_vectorized, analyze_fdbf_spectrum
            
            steering = 'cylindrical' if cylindrical else 'plane'
            f, vels, P = fdbf_transform_from_R_vectorized(
                R, frequencies, dx,
                fmin=pick_fmin, fmax=pick_fmax,
                nvel=grid_n, vmin=max(50.0, pick_vmin), vmax=pick_vmax,
                vspace=vspace, steering=steering
            )
            
            # Analyze
            pnorm, vmax, wav, f = analyze_fdbf_spectrum(f, vels, P, tol=tol)
            weighting = 'vibrosis_mat'  # Mark as from .mat file
            
        else:
            # SEG-2 .dat file: time-domain data
            transform_func = _dyn(cfg["transform"])
            
            # Preprocess data
            Tpre, dx, dt2 = _preprocess_with_cache(path, user_rev, st, en, downsample, dfac, numf)
            
            # Common transform parameters
            transform_kwargs = dict(
                fmin=pick_fmin,
                fmax=pick_fmax,
                nvel=grid_n,
                vmin=max(50.0, pick_vmin),
                vmax=pick_vmax,
                vspace=vspace
            )
            
            # Method-specific parameters
            if key == "fdbf":
                # FDBF: add weighting and steering
                weighting = 'invamp' if source_type == 'vibrosis' else 'none'
                steering = 'cylindrical' if cylindrical else 'plane'
                transform_kwargs['weighting'] = weighting
                transform_kwargs['steering'] = steering
            else:
                weighting = 'none'
            
            # Execute transform: all return (frequencies, velocities, power)
            f, vels, P = transform_func(Tpre, dt2, dx, **transform_kwargs)
            
            # Analyze: all return (pnorm, vmax, wavelength, freq)
            pnorm, vmax, wav, f = analyze_func(f, vels, P, tol=tol)
        
        # Save spectrum if requested
        if export_spectra:
            extra_meta = {
                'vibrosis_mode': (source_type == 'vibrosis' or file_type == 'mat'),
                'vspace': vspace,
                'file_type': file_type
            }
            if key == 'fdbf':
                extra_meta['weighting'] = weighting
                extra_meta['steering'] = steering if 'steering' in dir() else 'plane'
            _save_spectrum_npz(outdir, base, key, offset, f, vels, pnorm, vmax, extra_metadata=extra_meta)
        
        # Apply velocity/frequency masks to picks for display
        mask = (vmax >= pick_vmin) & (vmax <= pick_vmax) & (f >= pick_fmin) & (f <= pick_fmax)
        vmax_display = np.where(mask, vmax, np.nan)
        
        # Compute plot limits - handle velocity and frequency separately
        valid_picks = vmax_display[~np.isnan(vmax_display)]
        valid_freqs = f[mask]
        
        # Velocity limits
        if auto_vel_limits and len(valid_picks) > 0:
            # Auto-limit mode: use 10th percentile for min, 90th for max (exclude outliers)
            p10_vel = float(np.percentile(valid_picks, 10))
            p90_vel = float(np.percentile(valid_picks, 90))
            # Add margin: 20% below min, 20% above max
            plot_vmin = max(p10_vel * 0.8, 0.0)
            plot_vmax = min(p90_vel * 1.2, pick_vmax)
            # Ensure minimum range of 200 m/s
            if plot_vmax - plot_vmin < 200:
                plot_vmax = plot_vmin + 200
        elif auto_vel_limits:
            # Auto but no valid picks - use pick range
            plot_vmin = 0.0
            plot_vmax = pick_vmax
        else:
            # Manual mode: use user-specified limits
            try:
                plot_vmin = float(plot_min_vel_param)
            except ValueError:
                plot_vmin = 0.0
            try:
                plot_vmax = float(plot_max_vel_param)
            except ValueError:
                plot_vmax = pick_vmax
        
        # Frequency limits
        if auto_freq_limits and len(valid_freqs) > 0:
            # Auto-limit mode: use min/max of valid frequencies with margin
            fmin_valid = float(np.min(valid_freqs))
            fmax_valid = float(np.max(valid_freqs))
            plot_fmin = max(fmin_valid * 0.9, 0.0)
            plot_fmax = min(fmax_valid * 1.1, pick_fmax)
            # Ensure minimum range of 10 Hz
            if plot_fmax - plot_fmin < 10:
                plot_fmax = plot_fmin + 10
        elif auto_freq_limits:
            # Auto but no valid picks - use pick range
            plot_fmin = 0.0
            plot_fmax = pick_fmax
        else:
            # Manual mode: use user-specified limits
            try:
                plot_fmin = float(plot_min_freq_param)
            except ValueError:
                plot_fmin = 0.0
            try:
                plot_fmax = float(plot_max_freq_param)
            except ValueError:
                plot_fmax = pick_fmax
        
        # Plot
        plot_kwargs = base_pkw.copy()
        plot_kwargs.update(dict(
            vmin_plot=plot_vmin,
            vmax_plot=plot_vmax,
            min_frequency=plot_fmin,
            max_frequency=plot_fmax,
            title=(topic or f"{base} {key.upper()}"),
            offset_label=offset,
            fig_name=fig_name,
            cmap=cmap,
            freq_tick_spacing=freq_tick_spacing,
            vel_tick_spacing=vel_tick_spacing
        ))
        plot_func(f, vels, pnorm, vmax_display, **plot_kwargs)
        
        # Write CSV
        _write_per_shot_csv(outdir, base, key, offset, list(f), list(vmax), list(wav))
        
        return base, True, fig_name
        
    except Exception as e:
        import traceback
        return base, False, f"{str(e)}\n{traceback.format_exc()}"
    finally:
        try:
            import matplotlib as mpl
            if old_dpi is not None:
                mpl.rcParams['savefig.dpi'] = old_dpi
        except Exception:
            pass


def run_compare(params: Dict[str, Any]) -> Tuple[str, bool, str]:
    """Run all four transforms for one file and create comparison plot.
    
    Uses swprocess-inspired unified interface where all transforms
    return (frequencies, velocities, power).
    """
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sw_transform.processing.registry import METHODS, dyn as _dyn

    # Unpack params
    path = params['path']
    base = params['base']
    outdir = params['outdir']
    offset = params['offset']
    pick_vmin = float(params['pick_vmin'])
    pick_vmax = float(params['pick_vmax'])
    pick_fmin = float(params['pick_fmin'])
    pick_fmax = float(params['pick_fmax'])
    st = float(params['st'])
    en = float(params['en'])
    downsample = bool(params['downsample'])
    dfac = int(params['dfac'])
    numf = int(params['numf'])
    n_fk = int(params['n_fk'])
    tol_fk = float(params['tol_fk'])
    n_ps = int(params['n_ps'])
    vspace_ps = params.get('vspace_ps', 'linear')
    topic = (params.get('topic') or '').strip()
    source_type = params.get('source_type', 'hammer')
    cylindrical = bool(params.get('cylindrical', False))
    export_spectra = bool(params.get('export_spectra', True))
    
    # Reverse flags per method
    rev_fk = bool(params.get('rev_fk', False))
    rev_ps = bool(params.get('rev_ps', False))
    rev_fdbf = bool(params.get('rev_fdbf', False))
    rev_ss = bool(params.get('rev_ss', False))

    try:
        os.makedirs(outdir, exist_ok=True)
        fig, axs = plt.subplots(2, 2, figsize=(9, 6), dpi=130, sharex=False, sharey=False)
        ax_order = [(axs[0, 0], 'fdbf'), (axs[0, 1], 'fk'), (axs[1, 0], 'ps'), (axs[1, 1], 'ss')]
        combined = []
        
        for ax, key in ax_order:
            # Get reverse flag for this method
            rev = {'fk': rev_fk, 'ps': rev_ps, 'fdbf': rev_fdbf, 'ss': rev_ss}[key]
            
            # Preprocess data
            Tpre, dx, dt2 = _preprocess_with_cache(path, rev, st, en, downsample, dfac, numf)
            
            # Get transform and analyze functions
            cfg = METHODS[key]
            transform_func = _dyn(cfg["transform"])
            analyze_func = _dyn(cfg["analyze"])
            
            # Common transform parameters
            nvel = n_fk if key in ('fk', 'fdbf') else n_ps
            transform_kwargs = dict(
                fmin=pick_fmin,
                fmax=pick_fmax,
                nvel=nvel,
                vmin=max(50.0, pick_vmin),
                vmax=pick_vmax,
                vspace=vspace_ps
            )
            
            # Method-specific parameters
            if key == "fdbf":
                weighting = 'invamp' if source_type == 'vibrosis' else 'none'
                steering = 'cylindrical' if cylindrical else 'plane'
                transform_kwargs['weighting'] = weighting
                transform_kwargs['steering'] = steering
            
            # Execute transform
            f, vels, P = transform_func(Tpre, dt2, dx, **transform_kwargs)
            
            # Analyze
            pnorm, vmax, wav, f = analyze_func(f, vels, P, tol=tol_fk)
            
            # Save spectrum if requested
            if export_spectra:
                extra_meta = {'vibrosis_mode': (source_type == 'vibrosis'), 'vspace': vspace_ps}
                if key == 'fdbf':
                    extra_meta['weighting'] = weighting
                    extra_meta['steering'] = steering
                _save_spectrum_npz(outdir, base, key, offset, f, vels, np.abs(pnorm), vmax, extra_metadata=extra_meta)
            
            # Plot on subplot
            V, F = np.meshgrid(vels, f, indexing='ij')
            cf = ax.contourf(F, V, np.abs(pnorm), 30, cmap='jet')
            ax.plot(f, vmax, 'o', mfc='none', mec='white', ms=3)
            ax.set_xlim(pick_fmin, pick_fmax)
            ax.set_ylim(pick_vmin, pick_vmax)
            ax.set_title(key.upper())
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Phase Velocity (m/s)')
            
            combined.append((key, list(f), list(vmax), list(wav)))
        
        fig.suptitle(topic or f"{base} – Source offset {offset}")
        out_png = os.path.join(outdir, f"{base}_compare.png")
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        fig.savefig(out_png, dpi=130)
        plt.close(fig)

        # Write combined CSV
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
        
        # Write per-method CSVs
        for m, frq, vel, wav in combined:
            _write_per_shot_csv(outdir, base, m, offset, frq, vel, wav)
        
        return base, True, out_png
        
    except Exception as e:
        import traceback
        return base, False, f"{str(e)}\n{traceback.format_exc()}"


