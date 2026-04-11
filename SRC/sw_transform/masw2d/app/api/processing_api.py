"""Processing and workflow execution API.

Builds the JSON config dict expected by the engine workflows
and provides a thin wrapper around ``StandardMASWWorkflow.run()``.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from sw_transform.masw2d.app.api.models import (
    AssignmentConfig,
    OutputConfig,
    ProcessingParams,
    ShotDef,
    SubArraySpec,
    SurveyConfig,
)


def build_workflow_config(
    survey: SurveyConfig,
    shots: List[ShotDef],
    specs: List[SubArraySpec],
    params: ProcessingParams,
    output: OutputConfig,
    assignment: Optional[AssignmentConfig] = None,
) -> Dict[str, Any]:
    """Build the JSON config dict that the engine workflows expect.

    Parameters
    ----------
    survey : SurveyConfig
        Array geometry.
    shots : list of ShotDef
        Shot definitions with valid file paths.
    specs : list of SubArraySpec
        Sub-array specifications.
    params : ProcessingParams
        Transform / preprocessing parameters.
    output : OutputConfig
        Export preferences.
    assignment : AssignmentConfig, optional
        Assignment strategy. If None, uses exterior_only.

    Returns
    -------
    dict
        Config dict ready for ``StandardMASWWorkflow(config)``.
    """
    shots_cfg = [
        {"file": s.file, "source_position": s.source_position}
        for s in shots
        if s.file
    ]

    sa_configs = []
    seen: set = set()
    for spec in specs:
        if spec.name not in seen:
            seen.add(spec.name)
            sa_configs.append({
                "n_channels": spec.n_channels,
                "slide_step": spec.slide_step,
                "name": spec.name,
            })

    export_formats = ["csv"]
    if output.export_npz:
        export_formats.append("npz")
    if output.export_images:
        export_formats.append("image")

    config: Dict[str, Any] = {
        "survey_name": "MASW_2D_Profiler",
        "version": "1.0",
        "array": {
            "n_channels": survey.n_channels,
            "dx": survey.dx,
            "first_channel_position": survey.first_position,
        },
        "shots": shots_cfg,
        "subarray_configs": sa_configs,
        "processing": {
            "method": params.method,
            "freq_min": params.freq_min,
            "freq_max": params.freq_max,
            "velocity_min": params.vel_min,
            "velocity_max": params.vel_max,
            "grid_n": params.grid_n,
            "tol": params.tol,
            "power_threshold": params.power_threshold,
            "vspace": params.vspace,
            "source_type": params.source_type,
            "cylindrical": params.cylindrical,
            "start_time": params.start_time,
            "end_time": params.end_time,
            "downsample": params.downsample,
            "down_factor": params.down_factor,
            "numf": params.numf,
        },
        "output": {
            "directory": output.directory,
            "organize_by": "midpoint",
            "export_formats": export_formats,
            "include_images": output.export_images,
            "export_individual_npz": output.export_npz,
            "export_combined_csv_per_midpoint": output.combined_csv_per_midpoint,
            "export_combined_npz_per_midpoint": output.combined_npz_per_midpoint,
            "generate_summary": output.generate_summary,
            "export_midpoint_summary": output.generate_summary,
            "export_all_picks": output.generate_summary,
            "export_combined_npz": False,
            "auto_velocity_limit": output.auto_velocity_limit,
            "auto_frequency_limit": output.auto_frequency_limit,
            "cmap": output.cmap,
            "image_dpi": output.image_dpi,
            "fig_width": output.fig_width,
            "fig_height": output.fig_height,
            "contour_levels": output.contour_levels,
            "plot_style": output.plot_style,
        },
    }

    if assignment is not None:
        config["assignment"] = assignment.to_config_dict()

    return config


def run_masw2d(
    config: Dict[str, Any],
    output_dir: str,
    parallel: bool = False,
    max_workers: Optional[int] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Dict[str, Any]:
    """Execute the MASW 2D workflow.

    Parameters
    ----------
    config : dict
        Config dict from :func:`build_workflow_config`.
    output_dir : str
        Output directory (overrides config value).
    parallel : bool
        Process sub-arrays in parallel.
    max_workers : int, optional
        Worker count (None = auto).
    progress_callback : callable, optional
        ``(current, total, message)`` progress reporter.

    Returns
    -------
    dict
        Workflow summary with keys ``status``, ``n_results``,
        ``n_midpoints``, ``files``, etc.
    """
    # Detect vibrosis mode
    mat_files = [
        s["file"] for s in config.get("shots", [])
        if s.get("file", "").lower().endswith(".mat")
    ]

    if mat_files:
        from sw_transform.masw2d.workflows import VibrosisMASWWorkflow

        config["processing"]["cylindrical"] = True
        config["mat_files"] = mat_files
        wf = VibrosisMASWWorkflow(config)
        if progress_callback:
            wf.set_progress_callback(progress_callback)
        return wf.run(mat_files=mat_files, output_dir=output_dir)

    # Standard or Assigned workflow
    use_assigned = "assignment" in config
    if use_assigned:
        from sw_transform.masw2d.workflows import AssignedMASWWorkflow
        wf = AssignedMASWWorkflow(config)
    else:
        from sw_transform.masw2d.workflows import StandardMASWWorkflow
        wf = StandardMASWWorkflow(config)

    if progress_callback:
        wf.set_progress_callback(progress_callback)

    return wf.run(
        output_dir=output_dir,
        parallel=parallel,
        max_workers=max_workers,
    )
