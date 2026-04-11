"""Sub-array enumeration and shot-assignment API.

Wraps ``sw_transform.masw2d.geometry`` for the GUI layer.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from sw_transform.masw2d.app.api.models import (
    AssignmentConfig,
    ShotDef,
    SubArraySpec,
    SurveyConfig,
)
from sw_transform.masw2d.geometry.subarray import (
    SubArrayDef,
    enumerate_subarrays,
)


def enumerate_all_subarrays(
    survey: SurveyConfig,
    specs: List[SubArraySpec],
) -> List[SubArrayDef]:
    """Enumerate sub-arrays for every spec.

    Parameters
    ----------
    survey : SurveyConfig
        Array geometry.
    specs : list of SubArraySpec
        One entry per sub-array size to enumerate.

    Returns
    -------
    list of SubArrayDef
        Flat list of all enumerated sub-arrays across all specs.
    """
    result: List[SubArrayDef] = []
    for spec in specs:
        sas = enumerate_subarrays(
            total_channels=survey.n_channels,
            subarray_n_channels=spec.n_channels,
            dx=survey.dx,
            first_position=survey.first_position,
            slide_step=spec.slide_step,
            config_name=spec.name,
        )
        result.extend(sas)
    return result


def build_assignment_plan(
    survey: SurveyConfig,
    shots: List[ShotDef],
    specs: List[SubArraySpec],
    assignment: AssignmentConfig,
) -> Any:
    """Build an assignment plan mapping shots → sub-arrays.

    Parameters
    ----------
    survey : SurveyConfig
        Array geometry.
    shots : list of ShotDef
        Shot definitions.
    specs : list of SubArraySpec
        Sub-array specifications.
    assignment : AssignmentConfig
        Assignment strategy and constraints.

    Returns
    -------
    AssignmentPlan or None
        The plan object from the engine, or None if it cannot be built.
    """
    if not shots or not specs:
        return None

    shots_cfg = [
        {"file": s.file or f"_shot{i}", "source_position": s.source_position}
        for i, s in enumerate(shots)
    ]
    sa_configs = []
    seen_names: set = set()
    for spec in specs:
        if spec.name not in seen_names:
            seen_names.add(spec.name)
            sa_configs.append({
                "n_channels": spec.n_channels,
                "slide_step": spec.slide_step,
                "name": spec.name,
            })

    cfg: Dict[str, Any] = {
        "array": {
            "n_channels": survey.n_channels,
            "dx": survey.dx,
            "first_channel_position": survey.first_position,
        },
        "shots": shots_cfg,
        "subarray_configs": sa_configs,
        "assignment": assignment.to_config_dict(),
    }

    try:
        from sw_transform.masw2d.geometry.shot_assigner import (
            generate_plan_from_config,
        )
        return generate_plan_from_config(cfg)
    except Exception:
        return None


def get_assignments_for_subarray(
    plan: Any,
    sa: SubArrayDef,
    shots: List[ShotDef],
) -> List[Dict[str, Any]]:
    """Extract assignment info for a single sub-array from a plan.

    Parameters
    ----------
    plan : AssignmentPlan
        The plan object.
    sa : SubArrayDef
        Target sub-array.
    shots : list of ShotDef
        Shot definitions (for file path lookup).

    Returns
    -------
    list of dict
        Each dict has keys: ``source_position``, ``direction``,
        ``source_offset``, ``shot_index``, ``file``.
    """
    if plan is None:
        return []

    result: List[Dict[str, Any]] = []
    for a in plan.assignments:
        if (
            a.subarray_def.start_channel == sa.start_channel
            and a.subarray_def.end_channel == sa.end_channel
            and a.subarray_def.config_name == sa.config_name
        ):
            file_path = ""
            if a.shot_index < len(shots):
                file_path = shots[a.shot_index].file
            result.append({
                "source_position": a.shot_position,
                "direction": a.direction,
                "source_offset": a.source_offset,
                "shot_index": a.shot_index,
                "file": file_path,
            })
    return result


def generate_specs_from_range(
    min_channels: int,
    max_channels: int,
    step: int,
    total_channels: int,
    slide_step: int = 1,
) -> List[SubArraySpec]:
    """Generate a list of SubArraySpec from a channel-count range.

    Parameters
    ----------
    min_channels : int
        Minimum sub-array size.
    max_channels : int
        Maximum sub-array size.
    step : int
        Channel increment between sizes.
    total_channels : int
        Total channels in the array (for validation).
    slide_step : int
        Sliding window step in channels.

    Returns
    -------
    list of SubArraySpec
        Specs for each valid size in the range.
    """
    specs: List[SubArraySpec] = []
    ch = min_channels
    while ch <= min(max_channels, total_channels):
        specs.append(SubArraySpec(
            n_channels=ch,
            slide_step=slide_step,
            name=f"{ch}ch",
        ))
        ch += step
    return specs


def generate_specs_from_list(
    channel_counts: List[int],
    slide_step: int = 1,
) -> List[SubArraySpec]:
    """Generate specs from a user-selected list of channel counts (Mode 1).

    Parameters
    ----------
    channel_counts : list of int
        Selected channel counts.
    slide_step : int
        Sliding window step in channels.

    Returns
    -------
    list of SubArraySpec
    """
    return [
        SubArraySpec(n_channels=n, slide_step=slide_step, name=f"{n}ch")
        for n in sorted(set(channel_counts))
        if n >= 4
    ]


def _depth_to_min_channels(
    min_depth: float,
    dx: float,
    depth_factor: float = 2.0,
) -> int:
    """Convert depth of investigation to minimum channel count.

    Rule of thumb: ``max_depth ≈ subarray_length / depth_factor``,
    so ``min_subarray_length = min_depth × depth_factor``.
    """
    min_length = min_depth * depth_factor
    return max(4, math.ceil(min_length / dx) + 1)


def _profiling_range(
    n_channels: int,
    survey: SurveyConfig,
) -> Tuple[float, float]:
    """Midpoint range for a sub-array of given size within the survey."""
    half_span = (n_channels - 1) * survey.dx / 2.0
    mid_min = survey.first_position + half_span
    mid_max = survey.array_end - half_span
    return mid_min, mid_max


def compute_npoint_configs(
    survey: SurveyConfig,
    n_points: int,
    min_depth: float,
    max_channels: Optional[int] = None,
    depth_factor: float = 2.0,
) -> Tuple[List[SubArraySpec], List[SubArrayDef]]:
    """Mode 3 — compute optimal sub-arrays for N evenly-spaced midpoints.

    Maximises both coverage (biggest profiling line) and depth (largest
    possible sub-array per midpoint).

    Parameters
    ----------
    survey : SurveyConfig
        Array geometry.
    n_points : int
        Desired number of midpoints (dispersion curves).
    min_depth : float
        Minimum depth of investigation (m).
    max_channels : int, optional
        Maximum sub-array size (defaults to ``survey.n_channels``).
    depth_factor : float
        Depth factor: ``min_subarray_length = min_depth × depth_factor``.

    Returns
    -------
    tuple of (list[SubArraySpec], list[SubArrayDef])
        Specs and their concrete placements.
    """
    if max_channels is None:
        max_channels = survey.n_channels
    max_channels = min(max_channels, survey.n_channels)

    min_ch = _depth_to_min_channels(min_depth, survey.dx, depth_factor)
    min_ch = min(min_ch, max_channels)

    n_points = max(1, n_points)

    # Compute midpoint positions — use the largest sub-array's profiling range
    mid_min_big, mid_max_big = _profiling_range(max_channels, survey)
    # Also compute range for the smallest acceptable sub-array
    mid_min_small, mid_max_small = _profiling_range(min_ch, survey)

    # Use the widest possible range (from the smallest sub-array)
    # then assign the largest sub-array that covers each midpoint
    if n_points == 1:
        midpoints = [(mid_min_small + mid_max_small) / 2.0]
    else:
        step = (mid_max_small - mid_min_small) / (n_points - 1)
        midpoints = [mid_min_small + i * step for i in range(n_points)]

    specs_set: Dict[int, SubArraySpec] = {}
    placements: List[SubArrayDef] = []

    for mp in midpoints:
        # Find the largest channel count whose profiling range covers mp
        best_ch = min_ch
        for ch in range(max_channels, min_ch - 1, -1):
            mp_lo, mp_hi = _profiling_range(ch, survey)
            if mp_lo <= mp + 0.001 and mp >= mp_lo - 0.001 and mp <= mp_hi + 0.001:
                best_ch = ch
                break

        if best_ch not in specs_set:
            spec = SubArraySpec(n_channels=best_ch, slide_step=1,
                                name=f"{best_ch}ch")
            specs_set[best_ch] = spec

        # Compute the start channel for this midpoint
        half_span = (best_ch - 1) * survey.dx / 2.0
        start_pos = mp - half_span
        start_ch = round((start_pos - survey.first_position) / survey.dx)
        start_ch = max(0, min(start_ch, survey.n_channels - best_ch))

        s_pos = survey.first_position + start_ch * survey.dx
        e_pos = survey.first_position + (start_ch + best_ch - 1) * survey.dx
        sa = SubArrayDef(
            start_channel=start_ch,
            end_channel=start_ch + best_ch,
            n_channels=best_ch,
            start_position=s_pos,
            end_position=e_pos,
            midpoint=(s_pos + e_pos) / 2.0,
            length=e_pos - s_pos,
            config_name=f"{best_ch}ch",
        )
        placements.append(sa)

    specs = sorted(specs_set.values(), key=lambda s: s.n_channels)
    return specs, placements


def compute_line_depth_configs(
    survey: SurveyConfig,
    desired_length: float,
    min_depth: float,
    slide_step: int = 1,
    depth_factor: float = 2.0,
) -> Tuple[List[SubArraySpec], List[SubArrayDef]]:
    """Mode 4 — compute sub-arrays for a desired profile length and depth.

    Parameters
    ----------
    survey : SurveyConfig
        Array geometry.
    desired_length : float
        Desired profile length (m).
    min_depth : float
        Minimum depth of investigation (m).
    slide_step : int
        Sliding window step in channels.
    depth_factor : float
        Depth factor for depth-to-length conversion.

    Returns
    -------
    tuple of (list[SubArraySpec], list[SubArrayDef])
        Specs and their concrete placements.
    """
    min_ch = _depth_to_min_channels(min_depth, survey.dx, depth_factor)
    min_ch = min(min_ch, survey.n_channels)

    # Profiling range for the minimum-sized sub-array
    mid_min, mid_max = _profiling_range(min_ch, survey)
    max_possible_length = mid_max - mid_min

    effective_length = min(desired_length, max_possible_length)
    if effective_length <= 0:
        effective_length = max_possible_length

    # Center the profile on the array
    center = (mid_min + mid_max) / 2.0
    profile_start = center - effective_length / 2.0
    profile_end = center + effective_length / 2.0

    # Clamp to valid range
    profile_start = max(mid_min, profile_start)
    profile_end = min(mid_max, profile_end)

    all_specs: Dict[int, SubArraySpec] = {}
    all_placements: List[SubArrayDef] = []

    # Generate sub-arrays at min_ch that cover the desired window
    spec_min = SubArraySpec(n_channels=min_ch, slide_step=slide_step,
                            name=f"{min_ch}ch")
    all_specs[min_ch] = spec_min

    sas_min = enumerate_subarrays(
        total_channels=survey.n_channels,
        subarray_n_channels=min_ch,
        dx=survey.dx,
        first_position=survey.first_position,
        slide_step=slide_step,
        config_name=f"{min_ch}ch",
    )
    for sa in sas_min:
        if profile_start <= sa.midpoint <= profile_end:
            all_placements.append(sa)

    # For deeper investigation: also add larger sub-arrays whose midpoints
    # fall within the desired profile window
    for ch in range(min_ch + 1, survey.n_channels + 1):
        mp_lo, mp_hi = _profiling_range(ch, survey)
        if mp_lo > profile_end or mp_hi < profile_start:
            continue

        spec = SubArraySpec(n_channels=ch, slide_step=slide_step,
                            name=f"{ch}ch")
        all_specs[ch] = spec

        sas = enumerate_subarrays(
            total_channels=survey.n_channels,
            subarray_n_channels=ch,
            dx=survey.dx,
            first_position=survey.first_position,
            slide_step=slide_step,
            config_name=f"{ch}ch",
        )
        for sa in sas:
            if profile_start <= sa.midpoint <= profile_end:
                all_placements.append(sa)

    specs = sorted(all_specs.values(), key=lambda s: s.n_channels)
    return specs, all_placements
