"""Midpoint and source offset calculations.

Provides utilities for calculating the effective source offset
for each sub-array and validating offset quality.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from .subarray import SubArrayDef
from .shot_classifier import ShotInfo, ShotType


def get_array_bounds(array_config: Dict[str, Any]) -> Tuple[float, float]:
    """Get array start and end positions from config.
    
    Parameters
    ----------
    array_config : dict
        Array configuration with 'n_channels', 'dx', optionally 'first_channel_position'
    
    Returns
    -------
    tuple
        (array_start, array_end) positions in meters
    """
    first_pos = array_config.get("first_channel_position", 0.0)
    n_ch = array_config["n_channels"]
    dx = array_config["dx"]
    
    array_start = first_pos
    array_end = first_pos + (n_ch - 1) * dx
    
    return array_start, array_end


def calculate_source_offset(
    shot: ShotInfo,
    subarray: SubArrayDef
) -> Tuple[float, str]:
    """Calculate source offset for a sub-array.
    
    The offset is the distance from the source to the nearest edge
    of the sub-array. Direction indicates wave propagation.
    
    Parameters
    ----------
    shot : ShotInfo
        Shot information including position and type
    subarray : SubArrayDef
        Sub-array definition
    
    Returns
    -------
    tuple
        (offset: float, direction: str) where direction is "forward" or "reverse"
    
    Raises
    ------
    ValueError
        If shot is interior (not supported in Phase 1)
    
    Examples
    --------
    >>> shot = ShotInfo("shot.dat", -10.0, ShotType.EXTERIOR_LEFT)
    >>> sa = SubArrayDef(0, 12, 12, 0.0, 22.0, 11.0, 22.0, "shallow")
    >>> calculate_source_offset(shot, sa)
    (10.0, 'forward')
    """
    if shot.shot_type == ShotType.INTERIOR:
        raise ValueError(
            f"Interior shots not supported in Phase 1. "
            f"Shot at {shot.source_position}m is inside sub-array "
            f"({subarray.start_position}m - {subarray.end_position}m)"
        )
    
    if shot.shot_type in (ShotType.EXTERIOR_LEFT, ShotType.EDGE_LEFT):
        # Source is before/at start of array (forward propagation)
        offset = subarray.start_position - shot.source_position
        direction = "forward"
    else:
        # Source is after/at end of array (reverse propagation)
        offset = shot.source_position - subarray.end_position
        direction = "reverse"
    
    return abs(offset), direction


def is_valid_offset(
    offset: float,
    subarray_length: float,
    min_ratio: float = 0.3,
    max_ratio: float = 2.0
) -> bool:
    """Check if source offset is within acceptable range.
    
    The recommended offset is approximately L/2 where L is the sub-array
    length. Acceptable range is typically 0.3L to 2L.
    
    Parameters
    ----------
    offset : float
        Source offset in meters
    subarray_length : float
        Length of sub-array in meters
    min_ratio : float
        Minimum acceptable offset/length ratio (default: 0.3)
    max_ratio : float
        Maximum acceptable offset/length ratio (default: 2.0)
    
    Returns
    -------
    bool
        True if offset is within acceptable range
    
    Examples
    --------
    >>> is_valid_offset(10.0, 22.0)  # ratio = 0.45
    True
    >>> is_valid_offset(2.0, 22.0)   # ratio = 0.09
    False
    """
    if subarray_length <= 0:
        return False
    
    ratio = offset / subarray_length
    return min_ratio <= ratio <= max_ratio


def calculate_optimal_offset(subarray_length: float) -> float:
    """Calculate optimal source offset for a sub-array.
    
    The optimal offset is approximately L/2 where L is the sub-array length.
    
    Parameters
    ----------
    subarray_length : float
        Length of sub-array in meters
    
    Returns
    -------
    float
        Optimal offset in meters
    """
    return subarray_length / 2.0


def offset_quality_score(
    offset: float,
    subarray_length: float,
    optimal_ratio: float = 0.5
) -> float:
    """Calculate quality score for a source offset.
    
    Score is 1.0 when offset equals optimal (L/2), decreasing as
    offset deviates from optimal.
    
    Parameters
    ----------
    offset : float
        Source offset in meters
    subarray_length : float
        Length of sub-array in meters
    optimal_ratio : float
        Optimal offset/length ratio (default: 0.5)
    
    Returns
    -------
    float
        Quality score between 0 and 1
    """
    if subarray_length <= 0:
        return 0.0
    
    ratio = offset / subarray_length
    optimal = optimal_ratio
    
    # Score decreases as ratio deviates from optimal
    deviation = abs(ratio - optimal)
    
    # Use exponential decay: score = exp(-k * deviation^2)
    # k chosen so score ≈ 0.5 when deviation = 0.5
    k = 2.77  # -ln(0.5) / 0.5^2
    score = max(0.0, min(1.0, 2.718 ** (-k * deviation * deviation)))
    
    return score


def get_offset_info(
    shot: ShotInfo,
    subarray: SubArrayDef
) -> Dict[str, Any]:
    """Get comprehensive offset information for a shot/sub-array pair.
    
    Parameters
    ----------
    shot : ShotInfo
        Shot information
    subarray : SubArrayDef
        Sub-array definition
    
    Returns
    -------
    dict
        Dictionary with offset details
    """
    try:
        offset, direction = calculate_source_offset(shot, subarray)
        is_valid = is_valid_offset(offset, subarray.length)
        quality = offset_quality_score(offset, subarray.length)
        
        return {
            "offset": offset,
            "direction": direction,
            "is_valid": is_valid,
            "quality_score": quality,
            "optimal_offset": calculate_optimal_offset(subarray.length),
            "offset_ratio": offset / subarray.length if subarray.length > 0 else 0,
            "error": None
        }
    except ValueError as e:
        return {
            "offset": None,
            "direction": None,
            "is_valid": False,
            "quality_score": 0.0,
            "optimal_offset": calculate_optimal_offset(subarray.length),
            "offset_ratio": None,
            "error": str(e)
        }
