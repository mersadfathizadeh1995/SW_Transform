"""Survey-level API: array geometry, shot classification, auto-detection.

All functions are pure Python — no Qt imports.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from sw_transform.masw2d.app.api.models import ShotDef, SurveyConfig
from sw_transform.masw2d.geometry.shot_classifier import (
    ShotInfo,
    ShotType,
    classify_all_shots,
    filter_exterior_shots,
)


def auto_detect_array(filepath: str) -> Tuple[int, float]:
    """Read geometry from first data file.

    Parameters
    ----------
    filepath : str
        Path to a SEG-2 ``.dat`` or vibrosis ``.mat`` file.

    Returns
    -------
    tuple of (int, float)
        ``(n_channels, dx)`` detected from the file.

    Raises
    ------
    ValueError
        If the file format is not recognised or geometry cannot be read.
    """
    p = Path(filepath)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    if p.suffix.lower() == ".mat":
        from sw_transform.processing.vibrosis import get_vibrosis_file_info

        info = get_vibrosis_file_info(filepath)
        if not info.get("valid"):
            raise ValueError(f"Invalid vibrosis file: {filepath}")
        n_ch = int(info.get("n_channels", 0))
        dx = float(info.get("dx", 0) or 2.0)
        return n_ch, dx

    # SEG-2
    from sw_transform.processing.seg2 import load_seg2_ar

    _, data, _, spacing, _, _ = load_seg2_ar(filepath)
    n_ch = data.shape[1]
    dx = float(spacing) if spacing > 0 else 2.0
    return n_ch, dx


def classify_shots(
    survey: SurveyConfig,
    shots: List[ShotDef],
) -> List[ShotInfo]:
    """Classify shots relative to the array.

    Parameters
    ----------
    survey : SurveyConfig
        Array geometry.
    shots : list of ShotDef
        Shot definitions.

    Returns
    -------
    list of ShotInfo
        Classified shots with ``shot_type`` set.
    """
    shots_dict = [
        {"file": s.file, "source_position": s.source_position, "label": s.label}
        for s in shots
    ]
    array_dict = {
        "n_channels": survey.n_channels,
        "dx": survey.dx,
        "first_channel_position": survey.first_position,
    }
    return classify_all_shots(shots_dict, array_dict)


def get_exterior_shots(
    survey: SurveyConfig,
    shots: List[ShotDef],
) -> List[ShotInfo]:
    """Return only exterior (outside-array) shots.

    Parameters
    ----------
    survey : SurveyConfig
        Array geometry.
    shots : list of ShotDef
        Shot definitions.

    Returns
    -------
    list of ShotInfo
        Exterior shots only.
    """
    return filter_exterior_shots(classify_shots(survey, shots))


def compute_source_offset(
    source_position: float,
    subarray_start: float,
    subarray_end: float,
) -> Tuple[float, str]:
    """Compute offset and direction for a source relative to a sub-array.

    Parameters
    ----------
    source_position : float
        Source position (m).
    subarray_start : float
        Start position of the sub-array (m).
    subarray_end : float
        End position of the sub-array (m).

    Returns
    -------
    tuple of (float, str)
        ``(offset_m, direction)`` where direction is ``"forward"``,
        ``"reverse"``, or ``"interior"``.
    """
    if source_position < subarray_start:
        return subarray_start - source_position, "forward"
    elif source_position > subarray_end:
        return source_position - subarray_end, "reverse"
    else:
        return min(
            source_position - subarray_start,
            subarray_end - source_position,
        ), "interior"
