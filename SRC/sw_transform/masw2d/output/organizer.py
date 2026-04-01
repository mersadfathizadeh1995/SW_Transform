"""Result organization and directory structure management."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from ..processing.batch_processor import DispersionResult, group_results_by_midpoint
from .export import (
    export_dispersion_csv,
    export_metadata_txt,
    export_dispersion_npz,
    export_dispersion_image,
    export_combined_npz,
    build_combined_npz_from_files
)


def export_single_result(
    result: DispersionResult,
    output_dir: str,
    organize_by: str = "midpoint",
    export_formats: Optional[List[str]] = None,
    include_images: bool = False,
    image_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Export a single DispersionResult to disk immediately.
    
    This is the streaming counterpart to organize_results(). It writes
    one result at a time so memory can be freed after each call.
    
    Parameters
    ----------
    result : DispersionResult
        Single dispersion result to export
    output_dir : str
        Base output directory
    organize_by : str
        Organization mode: 'midpoint' or 'flat'
    export_formats : list of str
        Export formats: ['csv', 'npz']
    include_images : bool
        If True, export PNG image
    image_params : dict, optional
        Parameters for image export
    
    Returns
    -------
    dict
        Exported file paths and lightweight metadata for summary building
    """
    export_formats = export_formats or ["csv"]
    image_params = image_params or {}
    
    # Determine subdirectory
    base = Path(output_dir)
    if organize_by == "midpoint":
        subdir = base / f"midpoint_{result.midpoint:.1f}m"
    else:
        subdir = base
    subdir.mkdir(parents=True, exist_ok=True)
    
    exported_files = []
    npz_path = None
    
    # Export in requested formats
    for fmt in export_formats:
        if fmt == "csv":
            filename = _generate_filename(result, ext=".csv")
            filepath = os.path.join(str(subdir), filename)
            export_dispersion_csv(result, filepath)
            exported_files.append(filepath)
            # Write metadata .txt alongside CSV
            txt_filename = _generate_filename(result, ext=".txt")
            txt_filepath = os.path.join(str(subdir), txt_filename)
            export_metadata_txt(result, txt_filepath)
            exported_files.append(txt_filepath)
        elif fmt == "npz":
            filename = _generate_filename(result, ext=".npz")
            filepath = os.path.join(str(subdir), filename)
            export_dispersion_npz(result, filepath)
            exported_files.append(filepath)
            npz_path = filepath
    
    # Export image if requested
    if include_images:
        filename = _generate_filename(result, ext=".png")
        filepath = os.path.join(str(subdir), filename)
        try:
            img_params = image_params.copy()
            if 'auto_velocity_limit' not in img_params:
                img_params['auto_velocity_limit'] = True
            if 'auto_frequency_limit' not in img_params:
                img_params['auto_frequency_limit'] = True
            export_dispersion_image(result, filepath, **img_params)
            exported_files.append(filepath)
        except Exception as e:
            import warnings
            warnings.warn(f"Failed to export image for {result.midpoint}m: {e}")
    
    return {
        'midpoint': result.midpoint,
        'subarray_config': result.subarray_config,
        'source_offset': result.source_offset,
        'source_position': getattr(result, 'source_position', 0.0),
        'direction': result.direction,
        'method': result.method,
        'shot_file': result.shot_file,
        'picked_velocities': result.picked_velocities.copy(),
        'frequencies': result.frequencies.copy(),
        'wavelengths': result.wavelengths.copy(),
        'files': exported_files,
        'npz_path': npz_path,
    }


def write_summary_from_metadata(
    results_meta: List[Dict[str, Any]],
    output_dir: str,
    summary_format: str = "csv",
    write_midpoint_summary: bool = True,
    write_all_picks: bool = True,
    write_combined_npz: bool = False,
) -> Dict[str, Any]:
    """Write summary files from lightweight metadata (no full power arrays needed).
    
    Parameters
    ----------
    results_meta : list of dict
        Lightweight metadata from export_single_result() calls
    output_dir : str
        Base output directory
    summary_format : str
        Legacy format choice: 'csv', 'npz', or 'both'. Ignored when
        individual flags are explicitly passed.
    write_midpoint_summary : bool
        Write midpoint_summary.csv
    write_all_picks : bool
        Write all_dispersion_curves.csv
    write_combined_npz : bool
        Write combined_dispersion_curves.npz from individual NPZ files
    
    Returns
    -------
    dict
        Summary info with file paths
    """
    import csv as csv_mod
    
    summary_dir = Path(output_dir) / "summary"
    summary_dir.mkdir(parents=True, exist_ok=True)
    
    exported_files = []
    summary_info = {}
    
    if write_midpoint_summary:
        # 1. Midpoint summary CSV
        summary_csv = str(summary_dir / "midpoint_summary.csv")
        grouped = {}
        for m in results_meta:
            mp = m['midpoint']
            if mp not in grouped:
                grouped[mp] = []
            grouped[mp].append(m)
        
        with open(summary_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv_mod.writer(f)
            writer.writerow(["Midpoint_m", "N_Dispersion_Curves", "Configs", "N_Forward", "N_Reverse"])
            for mp in sorted(grouped.keys()):
                items = grouped[mp]
                configs = set(m['subarray_config'] for m in items)
                n_fwd = sum(1 for m in items if m['direction'] == 'forward')
                n_rev = sum(1 for m in items if m['direction'] == 'reverse')
                writer.writerow([f"{mp:.1f}", len(items), ", ".join(sorted(configs)), n_fwd, n_rev])
        exported_files.append(summary_csv)
        summary_info["summary_csv"] = summary_csv
    
    if write_all_picks:
        # 2. All picks CSV
        all_picks_csv = str(summary_dir / "all_dispersion_curves.csv")
        with open(all_picks_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv_mod.writer(f)
            writer.writerow(["Midpoint_m", "Config", "Shot_File", "Offset_m",
                              "Direction", "Frequency_Hz", "Velocity_m_s", "Wavelength_m"])
            for m in results_meta:
                for freq, vel, wav in zip(m['frequencies'], m['picked_velocities'], m['wavelengths']):
                    if not np.isnan(vel):
                        writer.writerow([
                            f"{m['midpoint']:.1f}", m['subarray_config'],
                            Path(m['shot_file']).name, f"{m['source_offset']:.1f}",
                            m['direction'], f"{freq:.2f}", f"{vel:.2f}",
                            f"{wav:.2f}" if not np.isnan(wav) else ""
                        ])
        exported_files.append(all_picks_csv)
        summary_info["all_picks_csv"] = all_picks_csv
    
    if write_combined_npz:
        # 3. Combined NPZ from individual NPZ files
        npz_files = [m['npz_path'] for m in results_meta if m.get('npz_path')]
        if npz_files:
            combined_npz = str(summary_dir / "combined_dispersion_curves.npz")
            build_combined_npz_from_files(npz_files, combined_npz)
            exported_files.append(combined_npz)
            summary_info["combined_npz"] = combined_npz
    
    return {
        "files": exported_files,
        "summary": summary_info
    }


def write_combined_csv_per_midpoint(
    results_meta: List[Dict[str, Any]],
    output_dir: str,
    organize_by: str = "midpoint"
) -> List[str]:
    """Create combined CSV files per midpoint (one file per midpoint).
    
    When multiple source offsets produce dispersion curves at the same
    midpoint, this creates a merged CSV with columns following the normal
    transform's ``combined_{method}.csv`` convention:
    ``freq(method_offset), vel(method_offset), wav(method_offset), ...``
    
    Parameters
    ----------
    results_meta : list of dict
        Lightweight metadata from export_single_result() calls.
    output_dir : str
        Base output directory.
    organize_by : str
        Organization mode ('midpoint' or 'flat').
    
    Returns
    -------
    list of str
        Paths to created combined CSV files.
    """
    import csv as csv_mod
    from collections import defaultdict
    
    # Group by midpoint
    by_midpoint: Dict[float, List[Dict]] = defaultdict(list)
    for m in results_meta:
        by_midpoint[m['midpoint']].append(m)
    
    created_files = []
    
    for mp in sorted(by_midpoint.keys()):
        items = by_midpoint[mp]
        
        # Only create combined file if more than one result at this midpoint
        if len(items) < 2:
            continue
        
        # Determine subdirectory
        base = Path(output_dir)
        if organize_by == "midpoint":
            subdir = base / f"midpoint_{mp:.1f}m"
        else:
            subdir = base
        subdir.mkdir(parents=True, exist_ok=True)
        
        # Group by method (there may be results from different methods)
        by_method: Dict[str, List[Dict]] = defaultdict(list)
        for item in items:
            by_method[item['method']].append(item)
        
        for method, method_items in by_method.items():
            if len(method_items) < 2:
                continue
            
            # Sort by offset for consistent column ordering
            method_items.sort(key=lambda x: (x['source_offset'], x['direction']))
            
            # Build offset tag for each result using source_position
            # Format matches normal-mode convention: "-2", "+66" etc.
            # DC Cut extracts this from CSV headers and maps to NPZ p{n}/m{n} tags
            offset_tags = []
            data_columns = []  # list of (freq, vel, wav) tuples
            for item in method_items:
                src_pos = item.get('source_position', 0.0)
                pos_str = f"{src_pos:g}"
                if src_pos >= 0:
                    tag = f"+{pos_str}" if not pos_str.startswith('+') else pos_str
                else:
                    tag = pos_str  # already has minus sign
                offset_tags.append(tag)
                
                freqs = item['frequencies']
                vels = item['picked_velocities']
                wavs = item['wavelengths']
                
                # Filter NaN values
                valid = ~np.isnan(vels)
                data_columns.append((
                    freqs[valid].tolist(),
                    vels[valid].tolist(),
                    wavs[valid].tolist() if wavs is not None else []
                ))
            
            # Build CSV
            filename = f"combined_mid{mp:.1f}m_{method}.csv"
            filepath = os.path.join(str(subdir), filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv_mod.writer(f)
                
                # Header: freq(method_offset), vel(method_offset), wav(method_offset), ...
                header = []
                for tag in offset_tags:
                    header.extend([
                        f"freq({method}_{tag})",
                        f"vel({method}_{tag})",
                        f"wav({method}_{tag})"
                    ])
                writer.writerow(header)
                
                # Data rows — pad shorter columns with empty strings
                max_len = max(len(d[0]) for d in data_columns) if data_columns else 0
                for i in range(max_len):
                    row = []
                    for freqs, vels, wavs in data_columns:
                        row.append(f"{freqs[i]:.4f}" if i < len(freqs) else "")
                        row.append(f"{vels[i]:.4f}" if i < len(vels) else "")
                        row.append(f"{wavs[i]:.4f}" if i < len(wavs) and wavs else "")
                    writer.writerow(row)
            
            created_files.append(filepath)
    
    return created_files


def write_combined_npz_per_midpoint(
    results_meta: List[Dict[str, Any]],
    output_dir: str,
    organize_by: str = "midpoint"
) -> List[str]:
    """Create combined NPZ files per midpoint (one per midpoint per method).
    
    When multiple source offsets produce results at the same midpoint,
    this reads each individual NPZ from disk and merges them into a single
    combined NPZ following the normal-mode convention with per-offset keys.
    
    Parameters
    ----------
    results_meta : list of dict
        Lightweight metadata from export_single_result() calls.
    output_dir : str
        Base output directory.
    organize_by : str
        Organization mode ('midpoint' or 'flat').
    
    Returns
    -------
    list of str
        Paths to created combined NPZ files.
    """
    from collections import defaultdict
    
    # Group by midpoint
    by_midpoint: Dict[float, List[Dict]] = defaultdict(list)
    for m in results_meta:
        by_midpoint[m['midpoint']].append(m)
    
    created_files = []
    
    for mp in sorted(by_midpoint.keys()):
        items = by_midpoint[mp]
        
        if len(items) < 2:
            continue
        
        # Determine subdirectory
        base = Path(output_dir)
        if organize_by == "midpoint":
            subdir = base / f"midpoint_{mp:.1f}m"
        else:
            subdir = base
        subdir.mkdir(parents=True, exist_ok=True)
        
        # Group by method
        by_method: Dict[str, List[Dict]] = defaultdict(list)
        for item in items:
            by_method[item['method']].append(item)
        
        for method, method_items in by_method.items():
            if len(method_items) < 2:
                continue
            
            # Only items that have NPZ files
            npz_items = [it for it in method_items if it.get('npz_path')]
            if len(npz_items) < 2:
                continue
            
            # Sort by offset for consistent ordering
            npz_items.sort(key=lambda x: (x['source_offset'], x['direction']))
            
            # Build combined data from individual NPZ files (memory efficient)
            combined: Dict[str, Any] = {
                'method': method,
                'midpoint': float(mp),
                'export_date': datetime.now().isoformat(),
                'version': '1.0',
                'num_offsets': len(npz_items),
            }
            
            offset_tags = []
            for item in npz_items:
                # Use normal-mode tag format: source_position → p{n}/m{n}
                src_pos = item.get('source_position', 0.0)
                pos_abs = abs(src_pos)
                pos_str = f"{pos_abs:g}"  # compact number without trailing zeros
                tag = f"m{pos_str}" if src_pos < 0 else f"p{pos_str}"
                offset_tags.append(tag)
                
                npz_path = item['npz_path']
                try:
                    with np.load(npz_path, allow_pickle=True) as data:
                        # Core data arrays (same as normal combined)
                        combined[f'frequencies_{tag}'] = np.asarray(
                            data['frequencies'], dtype=np.float32)
                        combined[f'velocities_{tag}'] = np.asarray(
                            data['velocities'], dtype=np.float32)
                        combined[f'power_{tag}'] = np.asarray(
                            data['power'], dtype=np.float32)
                        combined[f'picked_velocities_{tag}'] = np.asarray(
                            data['picked_velocities'], dtype=np.float32)
                        # Forward per-offset metadata (matching normal combined)
                        for meta_key in ('file_type', 'vibrosis_mode', 'vspace',
                                         'weighting', 'steering'):
                            if meta_key in data:
                                combined[f'{meta_key}_{tag}'] = data[meta_key]
                        # MASW 2D extras
                        if 'wavelengths' in data:
                            combined[f'wavelengths_{tag}'] = np.asarray(
                                data['wavelengths'], dtype=np.float32)
                except Exception:
                    continue
            
            combined['offsets'] = np.array(offset_tags, dtype=object)
            
            filename = f"combined_mid{mp:.1f}m_{method}_spectrum.npz"
            filepath = os.path.join(str(subdir), filename)
            np.savez_compressed(filepath, **combined)
            created_files.append(filepath)
    
    return created_files


def create_output_structure(
    output_dir: str,
    organize_by: str = "midpoint",
    midpoints: Optional[List[float]] = None
) -> Dict[str, str]:
    """Create output directory structure.
    
    Parameters
    ----------
    output_dir : str
        Base output directory
    organize_by : str
        Organization mode: 'midpoint', 'shot', or 'flat'
    midpoints : list of float, optional
        List of midpoint positions (used when organize_by='midpoint')
    
    Returns
    -------
    dict
        Mapping of subdirectory names to paths
    """
    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)
    
    dirs = {"base": str(base)}
    
    if organize_by == "midpoint" and midpoints:
        for mp in midpoints:
            subdir = base / f"midpoint_{mp:.1f}m"
            subdir.mkdir(exist_ok=True)
            dirs[f"midpoint_{mp:.1f}m"] = str(subdir)
    elif organize_by == "flat":
        pass  # All files in base directory
    
    # Always create summary directory
    summary_dir = base / "summary"
    summary_dir.mkdir(exist_ok=True)
    dirs["summary"] = str(summary_dir)
    
    return dirs


def _generate_filename(
    result: DispersionResult,
    suffix: str = "",
    ext: str = ".csv"
) -> str:
    """Generate filename for a dispersion result.
    
    Format: DC_<config>_mid<midpoint>_src<position>(off<offset>m)_<direction><suffix>.<ext>
    
    The source position is relative to the full line's first geophone:
    negative means left of line start.
    """
    # Format source position with sign
    src_pos = getattr(result, 'source_position', 0.0)
    if src_pos < 0:
        src_tag = f"src{src_pos:.1f}m"
    else:
        src_tag = f"src{src_pos:.1f}m"
    
    # Format offset tag
    off = result.source_offset
    off_tag = f"off{off:.0f}m"
    
    # Direction tag
    dir_tag = "fwd" if result.direction == "forward" else "rev"
    
    # Build filename
    name = f"DC_{result.subarray_config}_mid{result.midpoint:.1f}m_{src_tag}({off_tag})_{dir_tag}"
    if suffix:
        name += f"_{suffix}"
    
    return name + ext


def organize_results(
    results: List[DispersionResult],
    output_dir: str,
    organize_by: str = "midpoint",
    export_formats: Optional[List[str]] = None,
    include_summary: bool = True,
    include_images: bool = False,
    image_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Organize and export dispersion results.
    
    Parameters
    ----------
    results : list of DispersionResult
        Dispersion analysis results
    output_dir : str
        Base output directory
    organize_by : str
        Organization mode: 'midpoint', 'shot', or 'flat'
    export_formats : list of str
        Export formats: ['csv', 'npz']
    include_summary : bool
        If True, create summary files
    include_images : bool
        If True, export PNG images of dispersion spectra
    image_params : dict, optional
        Parameters for image export (max_velocity, max_frequency, cmap, dpi)
    
    Returns
    -------
    dict
        Summary with counts, file paths, and organization info
    """
    if not results:
        return {"status": "no_results", "files": []}
    
    export_formats = export_formats or ["csv"]
    image_params = image_params or {}
    
    # Get unique midpoints
    midpoints = sorted(set(r.midpoint for r in results))
    
    # Create directory structure
    dirs = create_output_structure(output_dir, organize_by, midpoints)
    
    exported_files = []
    results_by_midpoint = group_results_by_midpoint(results)
    
    for result in results:
        # Determine output directory
        if organize_by == "midpoint":
            subdir = dirs.get(f"midpoint_{result.midpoint:.1f}m", dirs["base"])
        else:
            subdir = dirs["base"]
        
        # Export in requested formats
        for fmt in export_formats:
            if fmt == "csv":
                filename = _generate_filename(result, ext=".csv")
                filepath = os.path.join(subdir, filename)
                export_dispersion_csv(result, filepath)
                exported_files.append(filepath)
            elif fmt == "npz":
                filename = _generate_filename(result, ext=".npz")
                filepath = os.path.join(subdir, filename)
                export_dispersion_npz(result, filepath)
                exported_files.append(filepath)
        
        # Export image if requested
        if include_images:
            filename = _generate_filename(result, ext=".png")
            filepath = os.path.join(subdir, filename)
            try:
                # Default to auto velocity/frequency limit if not specified
                img_params = image_params.copy()
                if 'auto_velocity_limit' not in img_params:
                    img_params['auto_velocity_limit'] = True
                if 'auto_frequency_limit' not in img_params:
                    img_params['auto_frequency_limit'] = True
                export_dispersion_image(result, filepath, **img_params)
                exported_files.append(filepath)
            except Exception as e:
                import warnings
                warnings.warn(f"Failed to export image for {result.midpoint}m: {e}")
    
    # Create summary files
    summary_info = {}
    if include_summary:
        summary_dir = dirs.get("summary", output_dir)
        
        # Summary CSV with all midpoints and their DC counts
        summary_csv = os.path.join(summary_dir, "midpoint_summary.csv")
        _write_midpoint_summary(results_by_midpoint, summary_csv)
        exported_files.append(summary_csv)
        summary_info["summary_csv"] = summary_csv
        
        # All picks in one file (CSV)
        all_picks_csv = os.path.join(summary_dir, "all_dispersion_curves.csv")
        _write_all_picks_csv(results, all_picks_csv)
        exported_files.append(all_picks_csv)
        summary_info["all_picks_csv"] = all_picks_csv
        
        # Combined NPZ file for refinement workflow
        combined_npz = os.path.join(summary_dir, "combined_dispersion_curves.npz")
        export_combined_npz(results, combined_npz)
        exported_files.append(combined_npz)
        summary_info["combined_npz"] = combined_npz
    
    return {
        "status": "success",
        "n_results": len(results),
        "n_midpoints": len(midpoints),
        "midpoints": midpoints,
        "files": exported_files,
        "organize_by": organize_by,
        "summary": summary_info
    }


def _write_midpoint_summary(
    results_by_midpoint: Dict[float, List[DispersionResult]],
    filepath: str
) -> None:
    """Write summary of results per midpoint."""
    import csv
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Midpoint_m",
            "N_Dispersion_Curves",
            "Configs",
            "N_Forward",
            "N_Reverse"
        ])
        
        for mp in sorted(results_by_midpoint.keys()):
            results = results_by_midpoint[mp]
            configs = set(r.subarray_config for r in results)
            n_fwd = sum(1 for r in results if r.direction == "forward")
            n_rev = sum(1 for r in results if r.direction == "reverse")
            
            writer.writerow([
                f"{mp:.1f}",
                len(results),
                ", ".join(sorted(configs)),
                n_fwd,
                n_rev
            ])


def _write_all_picks_csv(
    results: List[DispersionResult],
    filepath: str
) -> None:
    """Write all picked dispersion curves to a single CSV."""
    import csv
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Midpoint_m",
            "Config",
            "Shot_File",
            "Offset_m",
            "Direction",
            "Frequency_Hz",
            "Velocity_m_s",
            "Wavelength_m"
        ])
        
        for result in results:
            for freq, vel, wav in zip(
                result.frequencies,
                result.picked_velocities,
                result.wavelengths
            ):
                if not np.isnan(vel):
                    writer.writerow([
                        f"{result.midpoint:.1f}",
                        result.subarray_config,
                        Path(result.shot_file).name,
                        f"{result.source_offset:.1f}",
                        result.direction,
                        f"{freq:.2f}",
                        f"{vel:.2f}",
                        f"{wav:.2f}" if not np.isnan(wav) else ""
                    ])
