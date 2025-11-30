"""Shot classification based on position relative to array.

Classifies shots as:
- EXTERIOR_LEFT: Source before the array (negative offset)
- EXTERIOR_RIGHT: Source after the array (positive offset)
- EDGE_LEFT: Source at first geophone position
- EDGE_RIGHT: Source at last geophone position
- INTERIOR: Source inside the array (between first and last geophone)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class ShotType(Enum):
    """Classification of shot position relative to geophone array."""
    
    EXTERIOR_LEFT = "exterior_left"
    """Source is before the first geophone (e.g., -10m when array starts at 0m)"""
    
    EXTERIOR_RIGHT = "exterior_right"
    """Source is after the last geophone (e.g., +56m when array ends at 46m)"""
    
    EDGE_LEFT = "edge_left"
    """Source is at the first geophone position"""
    
    EDGE_RIGHT = "edge_right"
    """Source is at the last geophone position"""
    
    INTERIOR = "interior"
    """Source is inside the array (between first and last geophone)"""


@dataclass
class ShotInfo:
    """Information about a shot including its classification.
    
    Attributes
    ----------
    file : str
        Path to the shot data file
    source_position : float
        Position of the source in meters
    shot_type : ShotType
        Classification of the shot
    label : str
        Optional label for this shot
    """
    file: str
    source_position: float
    shot_type: ShotType
    label: str = ""
    
    @property
    def is_exterior(self) -> bool:
        """True if shot is outside the array (left or right)."""
        return self.shot_type in (ShotType.EXTERIOR_LEFT, ShotType.EXTERIOR_RIGHT)
    
    @property
    def is_forward(self) -> bool:
        """True if shot propagates forward (source on left side)."""
        return self.shot_type in (ShotType.EXTERIOR_LEFT, ShotType.EDGE_LEFT)
    
    @property
    def is_reverse(self) -> bool:
        """True if shot propagates in reverse (source on right side)."""
        return self.shot_type in (ShotType.EXTERIOR_RIGHT, ShotType.EDGE_RIGHT)


def classify_shot(
    source_position: float,
    array_start: float,
    array_end: float,
    tolerance: float = 0.01
) -> ShotType:
    """Classify shot based on position relative to array.
    
    Parameters
    ----------
    source_position : float
        Position of the source in meters
    array_start : float
        Position of first geophone in meters
    array_end : float
        Position of last geophone in meters
    tolerance : float
        Tolerance for edge detection in meters
    
    Returns
    -------
    ShotType
        Classification of the shot
    
    Examples
    --------
    >>> classify_shot(-10.0, 0.0, 46.0)
    <ShotType.EXTERIOR_LEFT: 'exterior_left'>
    
    >>> classify_shot(56.0, 0.0, 46.0)
    <ShotType.EXTERIOR_RIGHT: 'exterior_right'>
    
    >>> classify_shot(23.0, 0.0, 46.0)
    <ShotType.INTERIOR: 'interior'>
    """
    if abs(source_position - array_start) < tolerance:
        return ShotType.EDGE_LEFT
    elif abs(source_position - array_end) < tolerance:
        return ShotType.EDGE_RIGHT
    elif source_position < array_start:
        return ShotType.EXTERIOR_LEFT
    elif source_position > array_end:
        return ShotType.EXTERIOR_RIGHT
    else:
        return ShotType.INTERIOR


def classify_all_shots(
    shots: List[Dict[str, Any]],
    array_config: Dict[str, Any],
    tolerance: float = 0.01
) -> List[ShotInfo]:
    """Classify all shots in a survey configuration.
    
    Parameters
    ----------
    shots : list of dict
        Shot definitions from config, each with 'file' and 'source_position'
    array_config : dict
        Array configuration with 'n_channels', 'dx', and optionally 'first_channel_position'
    tolerance : float
        Tolerance for edge detection in meters
    
    Returns
    -------
    list of ShotInfo
        Classified shot information
    
    Examples
    --------
    >>> shots = [
    ...     {"file": "shot1.dat", "source_position": -10.0},
    ...     {"file": "shot2.dat", "source_position": 56.0}
    ... ]
    >>> array_config = {"n_channels": 24, "dx": 2.0}
    >>> info = classify_all_shots(shots, array_config)
    >>> info[0].shot_type
    <ShotType.EXTERIOR_LEFT: 'exterior_left'>
    """
    # Calculate array bounds
    array_start = array_config.get("first_channel_position", 0.0)
    array_end = array_start + (array_config["n_channels"] - 1) * array_config["dx"]
    
    results = []
    for shot in shots:
        shot_type = classify_shot(
            shot["source_position"],
            array_start,
            array_end,
            tolerance
        )
        results.append(ShotInfo(
            file=shot["file"],
            source_position=shot["source_position"],
            shot_type=shot_type,
            label=shot.get("label", "")
        ))
    
    return results


def filter_exterior_shots(shots: List[ShotInfo]) -> List[ShotInfo]:
    """Filter to keep only exterior shots (outside the array).
    
    Parameters
    ----------
    shots : list of ShotInfo
        List of classified shots
    
    Returns
    -------
    list of ShotInfo
        Only exterior (left and right) shots
    """
    return [s for s in shots if s.is_exterior]


def filter_shots_by_type(shots: List[ShotInfo], shot_types: List[ShotType]) -> List[ShotInfo]:
    """Filter shots by specific types.
    
    Parameters
    ----------
    shots : list of ShotInfo
        List of classified shots
    shot_types : list of ShotType
        Types to keep
    
    Returns
    -------
    list of ShotInfo
        Filtered shots
    """
    return [s for s in shots if s.shot_type in shot_types]
