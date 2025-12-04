"""Extract sub-array data from Vibrosis .mat files.

Implements sub-array extraction for frequency-domain transfer function data
from Signal Calc exported .mat files.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from ..geometry.subarray import SubArrayDef
from ..geometry.shot_classifier import ShotInfo, ShotType
from ..geometry.midpoint import calculate_source_offset, is_valid_offset


@dataclass
class ExtractedVibrosisSubArray:
    """Extracted vibrosis sub-array data with metadata.
    
    Contains the cross-spectral matrix R for a sub-array extracted
    from a full vibrosis recording.
    
    Attributes
    ----------
    R : np.ndarray
        Cross-spectral matrix, shape (n_channels, n_channels, n_freq)
    frequencies : np.ndarray
        Frequency vector in Hz
    dx : float
        Geophone spacing in meters
    subarray_def : SubArrayDef
        Sub-array definition
    shot_info : ShotInfo
        Shot information
    source_offset : float
        Calculated source offset in meters
    n_channels : int
        Number of channels in sub-array
    """
    R: np.ndarray
    frequencies: np.ndarray
    dx: float
    subarray_def: SubArrayDef
    shot_info: ShotInfo
    source_offset: float
    n_channels: int
    
    @property
    def midpoint(self) -> float:
        """Midpoint position of this sub-array."""
        return self.subarray_def.midpoint
    
    @property
    def config_name(self) -> str:
        """Name of the sub-array configuration."""
        return self.subarray_def.config_name
    
    @property
    def n_freq(self) -> int:
        """Number of frequency points."""
        return len(self.frequencies)
    
    def __repr__(self) -> str:
        return (f"ExtractedVibrosisSubArray(midpoint={self.midpoint:.1f}m, "
                f"offset={self.source_offset:.1f}m, "
                f"n_ch={self.n_channels}, config='{self.config_name}')")


def extract_vibrosis_subarray(
    transfer_functions: np.ndarray,
    frequencies: np.ndarray,
    dx: float,
    subarray_def: SubArrayDef,
    shot_info: ShotInfo,
    total_channels: int
) -> ExtractedVibrosisSubArray:
    """Extract sub-array from vibrosis transfer function data.
    
    Parameters
    ----------
    transfer_functions : np.ndarray
        Full transfer function matrix, shape (n_freq, n_total_channels)
    frequencies : np.ndarray
        Frequency vector
    dx : float
        Geophone spacing
    subarray_def : SubArrayDef
        Sub-array definition with channel indices
    shot_info : ShotInfo
        Shot information
    total_channels : int
        Total number of channels in full array
        
    Returns
    -------
    ExtractedVibrosisSubArray
        Extracted sub-array data
    """
    # Get channel indices for this sub-array
    start_ch = subarray_def.start_channel
    end_ch = subarray_def.end_channel
    n_channels = end_ch - start_ch
    
    # Extract sub-array transfer functions
    tf_subarray = transfer_functions[:, start_ch:end_ch]  # (n_freq, n_channels)
    
    # Compute cross-spectral matrix for sub-array
    R = compute_subarray_cross_spectral_matrix(tf_subarray)
    
    # Calculate source offset
    source_offset = calculate_source_offset(
        shot_info.source_position,
        subarray_def.midpoint
    )
    
    return ExtractedVibrosisSubArray(
        R=R,
        frequencies=frequencies,
        dx=dx,
        subarray_def=subarray_def,
        shot_info=shot_info,
        source_offset=source_offset,
        n_channels=n_channels
    )


def compute_subarray_cross_spectral_matrix(transfer_functions: np.ndarray) -> np.ndarray:
    """Compute cross-spectral matrix from sub-array transfer functions.
    
    R[j, i, f] = TF[f, i] / TF[f, j]
    
    Parameters
    ----------
    transfer_functions : np.ndarray
        Complex transfer function matrix (n_freq, n_channels)
        
    Returns
    -------
    R : np.ndarray
        Cross-spectral matrix (n_channels, n_channels, n_freq)
    """
    nfreq, nchannels = transfer_functions.shape
    
    # TF_i shape: (nfreq, 1, nchannels) - numerator
    # TF_j shape: (nfreq, nchannels, 1) - denominator
    TF_i = transfer_functions[:, np.newaxis, :]  # (nfreq, 1, nchannels)
    TF_j = transfer_functions[:, :, np.newaxis]  # (nfreq, nchannels, 1)
    
    # R[f, j, i] = TF[f, i] / TF[f, j]
    with np.errstate(divide='ignore', invalid='ignore'):
        R_fji = TF_i / TF_j
        R_fji = np.where(np.isfinite(R_fji), R_fji, 0.0 + 0j)
    
    # Transpose to (nchannels, nchannels, nfreq) = (j, i, f)
    R = np.transpose(R_fji, (1, 2, 0))
    
    return R


def extract_all_vibrosis_subarrays_from_shot(
    transfer_functions: np.ndarray,
    frequencies: np.ndarray,
    dx: float,
    shot_info: ShotInfo,
    subarrays: List[SubArrayDef],
    total_channels: int
) -> List[ExtractedVibrosisSubArray]:
    """Extract all valid sub-arrays from a vibrosis shot.
    
    Parameters
    ----------
    transfer_functions : np.ndarray
        Full transfer function matrix (n_freq, n_total_channels)
    frequencies : np.ndarray
        Frequency vector
    dx : float
        Geophone spacing
    shot_info : ShotInfo
        Shot information
    subarrays : list of SubArrayDef
        Sub-array definitions to extract
    total_channels : int
        Total channels in full array
        
    Returns
    -------
    list of ExtractedVibrosisSubArray
        All successfully extracted sub-arrays
    """
    results = []
    
    for subarray_def in subarrays:
        # Check if sub-array fits within data
        if subarray_def.end_channel > total_channels:
            continue
        
        # Check if this is a valid sub-array for this shot
        # (based on shot type and sub-array position)
        source_offset = calculate_source_offset(
            shot_info.source_position,
            subarray_def.midpoint
        )
        
        if not is_valid_offset(source_offset, shot_info.shot_type):
            continue
        
        try:
            extracted = extract_vibrosis_subarray(
                transfer_functions=transfer_functions,
                frequencies=frequencies,
                dx=dx,
                subarray_def=subarray_def,
                shot_info=shot_info,
                total_channels=total_channels
            )
            results.append(extracted)
        except Exception as e:
            import warnings
            warnings.warn(f"Failed to extract sub-array {subarray_def.config_name}: {e}")
            continue
    
    return results


def load_vibrosis_for_masw2d(
    filepath: str,
    dx: float,
    prefix: str = "G25_"
) -> Tuple[np.ndarray, np.ndarray, int]:
    """Load vibrosis .mat file for MASW 2D processing.
    
    Parameters
    ----------
    filepath : str
        Path to .mat file
    dx : float
        Sensor spacing in meters
    prefix : str
        Variable name prefix in .mat file
        
    Returns
    -------
    transfer_functions : np.ndarray
        Transfer function matrix (n_freq, n_channels)
    frequencies : np.ndarray
        Frequency vector
    n_channels : int
        Number of channels
    """
    from sw_transform.processing.vibrosis import load_vibrosis_mat
    
    data = load_vibrosis_mat(filepath, prefix)
    
    return data.transfer_functions, data.frequencies, data.n_channels


def extract_all_vibrosis_subarrays(
    vibrosis_data,
    dx: float,
    subarrays: List[SubArrayDef],
    shot_info: Optional[ShotInfo] = None
) -> List[ExtractedVibrosisSubArray]:
    """Extract all valid sub-arrays from loaded vibrosis data.
    
    This is a convenience wrapper that handles VibrosisData objects.
    
    Parameters
    ----------
    vibrosis_data : VibrosisData
        Loaded vibrosis data from load_vibrosis_mat()
    dx : float
        Geophone spacing in meters
    subarrays : list of SubArrayDef
        Sub-array definitions to extract
    shot_info : ShotInfo, optional
        Shot information (created from vibrosis_data if not provided)
        
    Returns
    -------
    list of ExtractedVibrosisSubArray
        All successfully extracted sub-arrays
    """
    # Create default shot info if not provided
    if shot_info is None:
        shot_info = ShotInfo(
            file="vibrosis.mat",
            source_position=0.0,
            receiver_start=0.0
        )
    
    return extract_all_vibrosis_subarrays_from_shot(
        transfer_functions=vibrosis_data.transfer_functions,
        frequencies=vibrosis_data.frequencies,
        dx=dx,
        shot_info=shot_info,
        subarrays=subarrays,
        total_channels=vibrosis_data.n_channels
    )


def extract_all_vibrosis_subarrays_from_file(
    filepath: str,
    dx: float,
    subarrays: List[SubArrayDef],
    shot_info: Optional[ShotInfo] = None
) -> List[ExtractedVibrosisSubArray]:
    """Load a .mat file and extract all sub-arrays.
    
    Convenience function that loads the file and extracts sub-arrays.
    
    Parameters
    ----------
    filepath : str
        Path to .mat file
    dx : float
        Geophone spacing in meters
    subarrays : list of SubArrayDef
        Sub-array definitions to extract
    shot_info : ShotInfo, optional
        Shot information (created from filepath if not provided)
        
    Returns
    -------
    list of ExtractedVibrosisSubArray
        All successfully extracted sub-arrays
    """
    from sw_transform.processing.vibrosis import load_vibrosis_mat
    
    # Load vibrosis data
    vibrosis_data = load_vibrosis_mat(filepath)
    
    # Create shot info if not provided
    if shot_info is None:
        shot_info = ShotInfo(
            file=filepath,
            source_position=0.0,
            receiver_start=0.0
        )
    
    return extract_all_vibrosis_subarrays(
        vibrosis_data, dx, subarrays, shot_info
    )
