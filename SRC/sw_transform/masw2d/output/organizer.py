"""Result organization and directory structure management."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from ..processing.batch_processor import DispersionResult, group_results_by_midpoint
from .export import (
    export_dispersion_csv,
    export_dispersion_npz,
    export_dispersion_image,
    export_combined_npz
)


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
    
    Format: DC_<config>_mid<midpoint>_off<offset>_<direction><suffix>.<ext>
    """
    # Clean up shot filename
    shot_name = Path(result.shot_file).stem
    
    # Format offset tag
    off = result.source_offset
    off_tag = f"off{off:.0f}m"
    
    # Direction tag
    dir_tag = "fwd" if result.direction == "forward" else "rev"
    
    # Build filename
    name = f"DC_{result.subarray_config}_mid{result.midpoint:.1f}m_{off_tag}_{dir_tag}"
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
                # Default to auto velocity limit if not specified
                img_params = image_params.copy()
                if 'auto_velocity_limit' not in img_params:
                    img_params['auto_velocity_limit'] = True
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
