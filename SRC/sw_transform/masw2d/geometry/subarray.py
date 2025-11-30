"""Sub-array definition and enumeration.

Provides functions to define and enumerate all possible sub-arrays
from a geophone array configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class SubArrayDef:
    """Definition of a sub-array extracted from the main array.
    
    Attributes
    ----------
    start_channel : int
        Starting channel index (0-indexed)
    end_channel : int
        Ending channel index (exclusive)
    n_channels : int
        Number of channels in this sub-array
    start_position : float
        Position of first geophone in sub-array (meters)
    end_position : float
        Position of last geophone in sub-array (meters)
    midpoint : float
        Midpoint position of the sub-array (meters)
    length : float
        Total length of sub-array (meters)
    config_name : str
        Name of the sub-array configuration (e.g., "shallow", "deep")
    """
    start_channel: int
    end_channel: int
    n_channels: int
    start_position: float
    end_position: float
    midpoint: float
    length: float
    config_name: str
    
    def __repr__(self) -> str:
        return (f"SubArrayDef(ch={self.start_channel}-{self.end_channel-1}, "
                f"pos={self.start_position:.1f}-{self.end_position:.1f}m, "
                f"mid={self.midpoint:.1f}m, name='{self.config_name}')")


def enumerate_subarrays(
    total_channels: int,
    subarray_n_channels: int,
    dx: float,
    first_position: float = 0.0,
    slide_step: int = 1,
    config_name: str = ""
) -> List[SubArrayDef]:
    """Enumerate all possible sub-arrays for a given configuration.
    
    Parameters
    ----------
    total_channels : int
        Total number of channels in the full array
    subarray_n_channels : int
        Number of channels per sub-array
    dx : float
        Geophone spacing in meters
    first_position : float
        Position of first geophone in meters (default: 0.0)
    slide_step : int
        Step size for sliding window in channels (default: 1)
    config_name : str
        Name for this configuration (e.g., "shallow")
    
    Returns
    -------
    list of SubArrayDef
        All possible sub-array definitions
    
    Examples
    --------
    >>> subarrays = enumerate_subarrays(24, 12, 2.0, config_name="shallow")
    >>> len(subarrays)
    13
    >>> subarrays[0].midpoint
    11.0
    >>> subarrays[-1].midpoint
    35.0
    """
    if subarray_n_channels > total_channels:
        raise ValueError(
            f"Sub-array channels ({subarray_n_channels}) cannot exceed "
            f"total channels ({total_channels})"
        )
    
    if subarray_n_channels < 2:
        raise ValueError("Sub-array must have at least 2 channels")
    
    subarrays = []
    
    # Number of possible sub-arrays
    n_possible = (total_channels - subarray_n_channels) // slide_step + 1
    
    for i in range(n_possible):
        start_ch = i * slide_step
        end_ch = start_ch + subarray_n_channels  # exclusive
        
        # Calculate positions
        start_pos = first_position + start_ch * dx
        end_pos = first_position + (end_ch - 1) * dx
        midpoint = (start_pos + end_pos) / 2.0
        length = (subarray_n_channels - 1) * dx
        
        subarrays.append(SubArrayDef(
            start_channel=start_ch,
            end_channel=end_ch,
            n_channels=subarray_n_channels,
            start_position=start_pos,
            end_position=end_pos,
            midpoint=midpoint,
            length=length,
            config_name=config_name
        ))
    
    return subarrays


def get_all_subarrays_from_config(config: Dict[str, Any]) -> Dict[str, List[SubArrayDef]]:
    """Get all sub-arrays for all configurations in a survey config.
    
    Parameters
    ----------
    config : dict
        Survey configuration dictionary
    
    Returns
    -------
    dict
        Mapping of config_name to list of SubArrayDefs
    
    Examples
    --------
    >>> config = {
    ...     "array": {"n_channels": 24, "dx": 2.0},
    ...     "subarray_configs": [
    ...         {"n_channels": 12, "name": "shallow"},
    ...         {"n_channels": 24, "name": "deep"}
    ...     ]
    ... }
    >>> all_sa = get_all_subarrays_from_config(config)
    >>> len(all_sa["shallow"])
    13
    >>> len(all_sa["deep"])
    1
    """
    array = config["array"]
    total_channels = array["n_channels"]
    dx = array["dx"]
    first_pos = array.get("first_channel_position", 0.0)
    
    result = {}
    
    for sa_config in config.get("subarray_configs", []):
        n_ch = sa_config["n_channels"]
        slide = sa_config.get("slide_step", 1)
        name = sa_config.get("name", f"{n_ch}ch")
        
        subarrays = enumerate_subarrays(
            total_channels=total_channels,
            subarray_n_channels=n_ch,
            dx=dx,
            first_position=first_pos,
            slide_step=slide,
            config_name=name
        )
        result[name] = subarrays
    
    return result


def flatten_subarrays(subarray_dict: Dict[str, List[SubArrayDef]]) -> List[SubArrayDef]:
    """Flatten sub-array dictionary to a single list.
    
    Parameters
    ----------
    subarray_dict : dict
        Mapping of config_name to list of SubArrayDefs
    
    Returns
    -------
    list of SubArrayDef
        All sub-arrays flattened into one list
    """
    result = []
    for sa_list in subarray_dict.values():
        result.extend(sa_list)
    return result


def get_unique_midpoints(subarrays: List[SubArrayDef]) -> List[float]:
    """Get sorted list of unique midpoint positions.
    
    Parameters
    ----------
    subarrays : list of SubArrayDef
        List of sub-array definitions
    
    Returns
    -------
    list of float
        Sorted unique midpoint positions
    """
    midpoints = set(sa.midpoint for sa in subarrays)
    return sorted(midpoints)


def count_subarrays_per_config(config: Dict[str, Any]) -> Dict[str, int]:
    """Count how many sub-arrays each configuration produces.
    
    Parameters
    ----------
    config : dict
        Survey configuration
    
    Returns
    -------
    dict
        Mapping of config_name to count
    """
    array = config["array"]
    total = array["n_channels"]
    
    result = {}
    for sa_config in config.get("subarray_configs", []):
        n_ch = sa_config["n_channels"]
        slide = sa_config.get("slide_step", 1)
        name = sa_config.get("name", f"{n_ch}ch")
        count = (total - n_ch) // slide + 1
        result[name] = count
    
    return result
