"""Config save/load and result export API."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Union

from sw_transform.masw2d.app.api.models import (
    AssignmentConfig,
    OutputConfig,
    ProcessingParams,
    ShotDef,
    SubArraySpec,
    SurveyConfig,
)
from sw_transform.masw2d.app.api.processing_api import build_workflow_config


def save_config_json(
    filepath: Union[str, Path],
    survey: SurveyConfig,
    shots: list[ShotDef],
    specs: list[SubArraySpec],
    params: ProcessingParams,
    output: OutputConfig,
    assignment: AssignmentConfig | None = None,
) -> None:
    """Save the full workflow configuration as a JSON file.

    Parameters
    ----------
    filepath : str or Path
        Target JSON file path.
    survey : SurveyConfig
        Array geometry.
    shots : list of ShotDef
        Shot definitions.
    specs : list of SubArraySpec
        Sub-array specifications.
    params : ProcessingParams
        Processing parameters.
    output : OutputConfig
        Export preferences.
    assignment : AssignmentConfig, optional
        Assignment strategy.
    """
    config = build_workflow_config(survey, shots, specs, params, output, assignment)
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def load_config_json(filepath: Union[str, Path]) -> Dict[str, Any]:
    """Load a workflow configuration from a JSON file.

    Parameters
    ----------
    filepath : str or Path
        Path to the JSON config file.

    Returns
    -------
    dict
        Raw configuration dictionary.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    json.JSONDecodeError
        If the file is not valid JSON.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def config_to_models(config: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a raw config dict back into API model instances.

    Parameters
    ----------
    config : dict
        Raw config from :func:`load_config_json`.

    Returns
    -------
    dict
        Keys: ``survey``, ``shots``, ``specs``, ``params``, ``output``,
        ``assignment`` (optional).
    """
    arr = config.get("array", {})
    survey = SurveyConfig(
        n_channels=arr.get("n_channels", 24),
        dx=arr.get("dx", 2.0),
        first_position=arr.get("first_channel_position", 0.0),
    )

    shots = [
        ShotDef(file=s.get("file", ""), source_position=s.get("source_position", 0.0))
        for s in config.get("shots", [])
    ]

    specs = [
        SubArraySpec(
            n_channels=sc.get("n_channels", 12),
            slide_step=sc.get("slide_step", 1),
            name=sc.get("name", f"{sc.get('n_channels', 12)}ch"),
        )
        for sc in config.get("subarray_configs", [])
    ]

    proc = config.get("processing", {})
    params = ProcessingParams(
        method=proc.get("method", "ps"),
        freq_min=proc.get("freq_min", 5.0),
        freq_max=proc.get("freq_max", 80.0),
        vel_min=proc.get("velocity_min", 100.0),
        vel_max=proc.get("velocity_max", 1500.0),
        grid_n=proc.get("grid_n", 4000),
        tol=proc.get("tol", 0.01),
        vspace=proc.get("vspace", "log"),
        source_type=proc.get("source_type", "hammer"),
        cylindrical=proc.get("cylindrical", False),
        start_time=proc.get("start_time", 0.0),
        end_time=proc.get("end_time", 1.0),
        downsample=proc.get("downsample", True),
        down_factor=proc.get("down_factor", 16),
        numf=proc.get("numf", 4000),
        power_threshold=proc.get("power_threshold", 0.1),
    )

    out = config.get("output", {})
    fmts = out.get("export_formats", ["csv"])
    output = OutputConfig(
        directory=out.get("directory", "./output_2d/"),
        export_csv="csv" in fmts,
        export_npz="npz" in fmts,
        export_images=out.get("include_images", False) or "image" in fmts,
        combined_csv_per_midpoint=out.get("export_combined_csv_per_midpoint", True),
        combined_npz_per_midpoint=out.get("export_combined_npz_per_midpoint", True),
        generate_summary=out.get("generate_summary", True),
        image_dpi=out.get("image_dpi", 150),
        cmap=out.get("cmap", "jet"),
        fig_width=out.get("fig_width", 8),
        fig_height=out.get("fig_height", 6),
        plot_style=out.get("plot_style", "contourf"),
        contour_levels=out.get("contour_levels", 30),
        auto_velocity_limit=out.get("auto_velocity_limit", True),
        auto_frequency_limit=out.get("auto_frequency_limit", True),
    )

    result = {
        "survey": survey,
        "shots": shots,
        "specs": specs,
        "params": params,
        "output": output,
    }

    assign = config.get("assignment")
    if assign:
        constraints = assign.get("constraints", {})
        result["assignment"] = AssignmentConfig(
            strategy=assign.get("strategy", "exterior_only"),
            max_offset=constraints.get("max_offset"),
            min_offset=constraints.get("min_offset", 0.0),
            max_offset_ratio=constraints.get("max_offset_ratio", 2.0),
            min_offset_ratio=constraints.get("min_offset_ratio", 0.0),
            max_shots_per_subarray=constraints.get("max_shots_per_subarray"),
            require_both_sides=constraints.get("require_both_sides", False),
            allow_interior_shots=constraints.get("allow_interior_shots", False),
        )

    return result
