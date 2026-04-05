"""Extract sub-array data from shot gathers.

Implements Method A: Sub-array extraction from fixed array data.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Dict, List, Optional, TYPE_CHECKING

import numpy as np

from ..geometry.subarray import SubArrayDef
from ..geometry.shot_classifier import ShotInfo, ShotType
from ..geometry.midpoint import calculate_source_offset, is_valid_offset

if TYPE_CHECKING:
    from ..geometry.shot_assigner import ShotAssignment, AssignmentPlan


@dataclass
class ExtractedSubArray:
    """Extracted sub-array data with metadata.
    
    Attributes
    ----------
    data : np.ndarray
        Time-domain data, shape (n_samples, n_channels)
    time : np.ndarray
        Time vector in seconds
    dt : float
        Sampling interval in seconds
    dx : float
        Geophone spacing in meters
    subarray_def : SubArrayDef
        Sub-array definition
    shot_info : ShotInfo
        Shot information
    source_offset : float
        Calculated source offset in meters
    direction : str
        Propagation direction: "forward" or "reverse"
    """
    data: np.ndarray
    time: np.ndarray
    dt: float
    dx: float
    subarray_def: SubArrayDef
    shot_info: ShotInfo
    source_offset: float
    direction: str
    
    @property
    def n_samples(self) -> int:
        """Number of time samples."""
        return self.data.shape[0]
    
    @property
    def n_channels(self) -> int:
        """Number of channels in sub-array."""
        return self.data.shape[1]
    
    @property
    def midpoint(self) -> float:
        """Midpoint position of this sub-array."""
        return self.subarray_def.midpoint
    
    @property
    def config_name(self) -> str:
        """Name of the sub-array configuration."""
        return self.subarray_def.config_name
    
    def __repr__(self) -> str:
        return (f"ExtractedSubArray(midpoint={self.midpoint:.1f}m, "
                f"offset={self.source_offset:.1f}m, "
                f"dir='{self.direction}', config='{self.config_name}')")


def extract_subarray(
    shot_data: np.ndarray,
    time: np.ndarray,
    dt: float,
    dx: float,
    subarray_def: SubArrayDef,
    shot_info: ShotInfo,
    reverse_if_needed: bool = True
) -> ExtractedSubArray:
    """Extract sub-array from shot gather.
    
    Parameters
    ----------
    shot_data : np.ndarray
        Full shot gather, shape (n_samples, n_total_channels)
    time : np.ndarray
        Time vector
    dt : float
        Sampling interval
    dx : float
        Geophone spacing
    subarray_def : SubArrayDef
        Sub-array definition
    shot_info : ShotInfo
        Shot information
    reverse_if_needed : bool
        If True, flip channel order for reverse shots so that
        channel 0 is always nearest to the (effective) source
    
    Returns
    -------
    ExtractedSubArray
        Extracted data with metadata
    
    Raises
    ------
    ValueError
        If shot is interior (not supported)
    IndexError
        If sub-array channels are out of bounds
    """
    # Calculate offset first to validate shot type
    offset, direction = calculate_source_offset(shot_info, subarray_def)
    
    # Extract channels
    start_ch = subarray_def.start_channel
    end_ch = subarray_def.end_channel
    
    if end_ch > shot_data.shape[1]:
        raise IndexError(
            f"Sub-array channels ({start_ch}-{end_ch-1}) exceed "
            f"data channels (0-{shot_data.shape[1]-1})"
        )
    
    sub_data = shot_data[:, start_ch:end_ch].copy()
    
    # Flip channel order for REVERSE shots (source on RIGHT side)
    # For FK/PS methods, data must be arranged so wave propagates from 
    # low channel index to high channel index (positive velocity)
    # - Forward shots (source left): wave travels left→right, channels correct
    # - Reverse shots (source right): wave travels right→left, need to flip
    # This ensures consistent phase velocity direction in FK/PS spectrum
    if reverse_if_needed and direction == "reverse":
        sub_data = np.fliplr(sub_data)
    
    return ExtractedSubArray(
        data=sub_data,
        time=time.copy(),
        dt=dt,
        dx=dx,
        subarray_def=subarray_def,
        shot_info=shot_info,
        source_offset=offset,
        direction=direction
    )


def extract_all_subarrays_from_shot(
    shot_data: np.ndarray,
    time: np.ndarray,
    dt: float,
    dx: float,
    shot_info: ShotInfo,
    subarray_defs: List[SubArrayDef],
    min_offset_ratio: float = 0.0,
    max_offset_ratio: float = 10.0,
    reverse_if_needed: bool = True
) -> List[ExtractedSubArray]:
    """Extract all valid sub-arrays from a single shot.
    
    Optionally filters by offset quality.
    
    Parameters
    ----------
    shot_data : np.ndarray
        Full shot gather, shape (n_samples, n_total_channels)
    time : np.ndarray
        Time vector
    dt : float
        Sampling interval
    dx : float
        Geophone spacing
    shot_info : ShotInfo
        Shot information
    subarray_defs : list of SubArrayDef
        Sub-array definitions to extract
    min_offset_ratio : float
        Minimum acceptable offset/length ratio (default: 0.0 = no minimum)
    max_offset_ratio : float
        Maximum acceptable offset/length ratio (default: 10.0 = no practical maximum)
    reverse_if_needed : bool
        If True, flip channel order for reverse shots
    
    Returns
    -------
    list of ExtractedSubArray
        Successfully extracted sub-arrays (filtered by offset if specified)
    
    Notes
    -----
    Interior shots are automatically skipped with a warning.
    """
    results = []
    
    for sa_def in subarray_defs:
        try:
            extracted = extract_subarray(
                shot_data, time, dt, dx, sa_def, shot_info,
                reverse_if_needed=reverse_if_needed
            )
            
            # Check offset quality if filtering is enabled
            if min_offset_ratio > 0 or max_offset_ratio < 10.0:
                if not is_valid_offset(
                    extracted.source_offset,
                    sa_def.length,
                    min_ratio=min_offset_ratio,
                    max_ratio=max_offset_ratio
                ):
                    continue
            
            results.append(extracted)
            
        except ValueError:
            # Skip interior shots silently
            continue
        except IndexError as e:
            # Log but continue with other sub-arrays
            import warnings
            warnings.warn(f"Could not extract sub-array: {e}")
            continue
    
    return results


def load_and_extract_from_file(
    file_path: str,
    shot_info: ShotInfo,
    subarray_defs: List[SubArrayDef],
    dx: float,
    min_offset_ratio: float = 0.0,
    max_offset_ratio: float = 10.0,
    reverse_if_needed: bool = True
) -> List[ExtractedSubArray]:
    """Load shot data from file and extract all sub-arrays.
    
    Convenience function that combines file loading and extraction.
    
    Parameters
    ----------
    file_path : str
        Path to SEG-2 file
    shot_info : ShotInfo
        Shot information (must have matching file path)
    subarray_defs : list of SubArrayDef
        Sub-array definitions
    dx : float
        Geophone spacing (used to verify against file)
    min_offset_ratio : float
        Minimum offset/length ratio filter
    max_offset_ratio : float
        Maximum offset/length ratio filter
    reverse_if_needed : bool
        If True, flip channels for reverse shots
    
    Returns
    -------
    list of ExtractedSubArray
        Extracted sub-arrays
    """
    from sw_transform.processing.seg2 import load_seg2_ar
    
    time, data, _, file_dx, dt, _ = load_seg2_ar(file_path)
    
    # Use dx from file if available and close to config dx
    actual_dx = file_dx if file_dx > 0 else dx
    
    return extract_all_subarrays_from_shot(
        data, time, dt, actual_dx,
        shot_info, subarray_defs,
        min_offset_ratio=min_offset_ratio,
        max_offset_ratio=max_offset_ratio,
        reverse_if_needed=reverse_if_needed
    )


# ---------------------------------------------------------------------------
# Assignment-based extraction (uses pre-computed direction / offset)
# ---------------------------------------------------------------------------

def extract_from_assignment(
    shot_data: np.ndarray,
    time: np.ndarray,
    dt: float,
    dx: float,
    assignment: "ShotAssignment",
    reverse_if_needed: bool = True,
) -> ExtractedSubArray:
    """Extract a sub-array using a pre-computed :class:`ShotAssignment`.

    Unlike :func:`extract_subarray` this never raises ``ValueError`` for
    interior shots because the direction and offset have already been
    resolved by the assignment engine.

    Parameters
    ----------
    shot_data : np.ndarray
        Full shot gather, shape ``(n_samples, n_total_channels)``.
    time : np.ndarray
        Time vector.
    dt : float
        Sampling interval.
    dx : float
        Geophone spacing.
    assignment : ShotAssignment
        Pre-computed assignment from the shot-assigner engine.
    reverse_if_needed : bool
        If True, flip channel order for reverse shots.

    Returns
    -------
    ExtractedSubArray

    Raises
    ------
    IndexError
        If the sub-array channels are out of bounds.
    """
    sa_def = assignment.subarray_def
    start_ch = sa_def.start_channel
    end_ch = sa_def.end_channel

    if end_ch > shot_data.shape[1]:
        raise IndexError(
            f"Sub-array channels ({start_ch}-{end_ch - 1}) exceed "
            f"data channels (0-{shot_data.shape[1] - 1})"
        )

    sub_data = shot_data[:, start_ch:end_ch].copy()

    if reverse_if_needed and assignment.direction == "reverse":
        sub_data = np.fliplr(sub_data)

    shot_info = ShotInfo(
        file=assignment.shot_file,
        source_position=assignment.shot_position,
        shot_type=ShotType.EXTERIOR_LEFT if assignment.direction == "forward" else ShotType.EXTERIOR_RIGHT,
    )

    return ExtractedSubArray(
        data=sub_data,
        time=time.copy(),
        dt=dt,
        dx=dx,
        subarray_def=sa_def,
        shot_info=shot_info,
        source_offset=assignment.source_offset,
        direction=assignment.direction,
    )


def extract_all_from_plan(
    shot_data_map: Dict[str, tuple],
    plan: "AssignmentPlan",
    dx: float,
    reverse_if_needed: bool = True,
) -> List[ExtractedSubArray]:
    """Extract all sub-arrays described by an :class:`AssignmentPlan`.

    Parameters
    ----------
    shot_data_map : dict
        Mapping of shot file path to ``(time, data, dt)`` tuples where
        *data* has shape ``(n_samples, n_total_channels)``.
    plan : AssignmentPlan
        Complete assignment plan.
    dx : float
        Geophone spacing in metres.
    reverse_if_needed : bool
        If True, flip channel order for reverse shots.

    Returns
    -------
    list of ExtractedSubArray
    """
    results: List[ExtractedSubArray] = []

    for assignment in plan.assignments:
        shot_key = assignment.shot_file
        if shot_key not in shot_data_map:
            warnings.warn(f"Shot file not loaded: {shot_key}")
            continue

        time, data, dt = shot_data_map[shot_key]
        try:
            extracted = extract_from_assignment(
                data, time, dt, dx, assignment,
                reverse_if_needed=reverse_if_needed,
            )
            results.append(extracted)
        except IndexError as e:
            warnings.warn(f"Could not extract sub-array: {e}")
            continue

    return results
