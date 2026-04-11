"""Preview data loading API with LRU caching.

Loads SEG-2 and vibrosis .MAT files for the preview canvas,
caching results so switching between sub-arrays is instant.
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from sw_transform.masw2d.app.api.models import ShotPreview
from sw_transform.masw2d.geometry.subarray import SubArrayDef


_MAX_CACHE_SIZE = 20
_cache: OrderedDict[str, ShotPreview] = OrderedDict()


def clear_cache() -> None:
    """Drop all cached shot previews."""
    _cache.clear()


def load_shot_preview(filepath: str) -> ShotPreview:
    """Load a shot file for preview rendering.

    Parameters
    ----------
    filepath : str
        Path to a SEG-2 ``.dat`` or vibrosis ``.mat`` file.

    Returns
    -------
    ShotPreview
        Loaded data ready for rendering.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file cannot be read.
    """
    if filepath in _cache:
        _cache.move_to_end(filepath)
        return _cache[filepath]

    p = Path(filepath)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    if p.suffix.lower() == ".mat":
        preview = _load_vibrosis(filepath)
    else:
        preview = _load_seg2(filepath)

    _cache[filepath] = preview
    if len(_cache) > _MAX_CACHE_SIZE:
        _cache.popitem(last=False)

    return preview


def extract_subarray_traces(
    preview: ShotPreview,
    sa: SubArrayDef,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Slice trace data for a sub-array's channel range.

    Parameters
    ----------
    preview : ShotPreview
        Full shot data from :func:`load_shot_preview`.
    sa : SubArrayDef
        Sub-array definition.

    Returns
    -------
    tuple of (np.ndarray, np.ndarray, np.ndarray)
        ``(time, subarray_data, active_indices)`` where
        ``subarray_data`` has shape ``(n_samples, sa.n_channels)``
        and ``active_indices`` is the channel indices within the
        full array that belong to this sub-array.
    """
    start = sa.start_channel
    end = min(sa.end_channel, preview.n_channels)
    sub_data = preview.data[:, start:end].copy()
    active_indices = np.arange(start, end)
    return preview.time.copy(), sub_data, active_indices


# ------------------------------------------------------------------
# Internal loaders
# ------------------------------------------------------------------

def _load_seg2(filepath: str) -> ShotPreview:
    """Load a SEG-2 .dat file."""
    from sw_transform.processing.seg2 import load_seg2_ar

    time, data, _sp, spacing, dt, _ = load_seg2_ar(filepath)
    return ShotPreview(
        time=time,
        data=data,
        dx=float(spacing) if spacing > 0 else 2.0,
        dt=float(dt),
        n_channels=data.shape[1],
        is_vibrosis=False,
        filepath=filepath,
    )


def _load_vibrosis(filepath: str) -> ShotPreview:
    """Load a vibrosis .mat file."""
    from sw_transform.processing.vibrosis import load_vibrosis_mat

    vib = load_vibrosis_mat(filepath)
    tf_mag = np.abs(vib.transfer_functions)  # (n_freq, n_channels)
    return ShotPreview(
        time=vib.frequencies,
        data=tf_mag,
        dx=2.0,
        dt=None,
        n_channels=vib.n_channels,
        is_vibrosis=True,
        filepath=filepath,
    )
