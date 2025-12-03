"""Vibrosis .MAT file loader for Signal Calc transfer function data.

Loads transfer function data from Signal Calc exported .mat files,
computes cross-spectral matrix R for FDBF processing.

.MAT File Format (Signal Calc export):
- Variables G25_1, G25_2, ..., G25_N (one per channel)
- Each variable is (nfreq, 2) array:
  - Column 0: frequency (Hz)
  - Column 1: complex transfer function

Reference: UofA_MASWMultiProcessV2Cyl.m
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional

import numpy as np

try:
    from scipy.io import loadmat
except ImportError:
    loadmat = None


@dataclass
class VibrosisData:
    """Container for loaded vibrosis transfer function data."""
    frequencies: np.ndarray       # (nfreq,) frequency vector in Hz
    transfer_functions: np.ndarray  # (nfreq, nchannels) complex TF matrix
    R: np.ndarray                   # (nchannels, nchannels, nfreq) cross-spectral matrix
    n_channels: int                 # number of channels
    source_file: str                # original .mat file path
    channel_names: list[str]        # original variable names from .mat


def load_vibrosis_mat(filepath: str, prefix: str = "G25_") -> VibrosisData:
    """Load vibrosis transfer function data from a Signal Calc .mat file.
    
    Parameters
    ----------
    filepath : str
        Path to the .mat file
    prefix : str
        Variable name prefix (default "G25_" for Signal Calc export)
        
    Returns
    -------
    VibrosisData
        Container with frequencies, transfer functions, and cross-spectral matrix
        
    Raises
    ------
    ImportError
        If scipy is not installed
    ValueError
        If file format is invalid or no matching variables found
    """
    if loadmat is None:
        raise ImportError("scipy is required to load .mat files. Install with: pip install scipy")
    
    # Load .mat file
    mat_data = loadmat(filepath, squeeze_me=False)
    
    # Find all G25_* variables and sort by channel number
    channel_vars = []
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
    
    for key in mat_data.keys():
        if key.startswith("_"):  # Skip MATLAB metadata
            continue
        match = pattern.match(key)
        if match:
            channel_num = int(match.group(1))
            channel_vars.append((channel_num, key))
    
    if not channel_vars:
        raise ValueError(f"No variables matching '{prefix}*' found in {filepath}")
    
    # Sort by channel number
    channel_vars.sort(key=lambda x: x[0])
    channel_names = [var[1] for var in channel_vars]
    n_channels = len(channel_vars)
    
    # Extract frequency vector from first channel
    first_data = mat_data[channel_names[0]]
    if first_data.ndim == 1:
        raise ValueError(f"Expected 2D array for {channel_names[0]}, got 1D")
    
    # Handle potential shape variations
    if first_data.shape[1] == 2:
        frequencies = first_data[:, 0].real.flatten()
    elif first_data.shape[0] == 2:
        # Transposed format
        frequencies = first_data[0, :].real.flatten()
        first_data = first_data.T
    else:
        raise ValueError(f"Unexpected shape {first_data.shape} for {channel_names[0]}")
    
    nfreq = len(frequencies)
    
    # Build transfer function matrix (nfreq, nchannels)
    transfer_functions = np.zeros((nfreq, n_channels), dtype=complex)
    
    for i, var_name in enumerate(channel_names):
        data = mat_data[var_name]
        
        # Handle shape variations
        if data.shape[1] == 2:
            tf = data[:, 1]
        elif data.shape[0] == 2:
            tf = data[1, :]
        else:
            raise ValueError(f"Unexpected shape {data.shape} for {var_name}")
        
        # Ensure complex
        if not np.iscomplexobj(tf):
            tf = tf.astype(complex)
        
        transfer_functions[:, i] = tf.flatten()
    
    # Sort by frequency (ascending) - some .mat files store freq descending
    if len(frequencies) > 1 and frequencies[0] > frequencies[-1]:
        sort_idx = np.argsort(frequencies)
        frequencies = frequencies[sort_idx]
        transfer_functions = transfer_functions[sort_idx, :]
    
    # Compute cross-spectral matrix R
    # R[j, i, f] = TF[f, i] / TF[f, j]  (reference: UofA_MASWMultiProcessV2Cyl.m)
    R = compute_cross_spectral_matrix(transfer_functions)
    
    return VibrosisData(
        frequencies=frequencies,
        transfer_functions=transfer_functions,
        R=R,
        n_channels=n_channels,
        source_file=filepath,
        channel_names=channel_names
    )


def compute_cross_spectral_matrix(transfer_functions: np.ndarray) -> np.ndarray:
    """Compute cross-spectral matrix from transfer functions.
    
    R[j, i, f] = TF[f, i] / TF[f, j]
    
    This represents the phase relationship between channels i and j
    at each frequency, used for beamforming.
    
    Parameters
    ----------
    transfer_functions : ndarray
        Complex transfer function matrix (nfreq, nchannels)
        
    Returns
    -------
    R : ndarray
        Cross-spectral matrix (nchannels, nchannels, nfreq)
    """
    nfreq, nchannels = transfer_functions.shape
    
    # R[j, i, f] = TF[f, i] / TF[f, j]
    # Using broadcasting: TF[:, i] / TF[:, j] for all i, j pairs
    
    # TF transposed to (nfreq, nchannels) - already correct
    # We need R[j, i, :] = TF[:, i] / TF[:, j]
    
    # Expand for broadcasting
    # TF_i shape: (nfreq, 1, nchannels) - numerator
    # TF_j shape: (nfreq, nchannels, 1) - denominator
    TF_i = transfer_functions[:, np.newaxis, :]  # (nfreq, 1, nchannels)
    TF_j = transfer_functions[:, :, np.newaxis]  # (nfreq, nchannels, 1)
    
    # R shape after broadcast: (nfreq, nchannels, nchannels)
    # R[f, j, i] = TF[f, i] / TF[f, j]
    with np.errstate(divide='ignore', invalid='ignore'):
        R_fji = TF_i / TF_j
        # Handle division by zero - set to 0 where denominator is 0
        R_fji = np.where(np.isfinite(R_fji), R_fji, 0.0 + 0j)
    
    # Transpose to (nchannels, nchannels, nfreq) = (j, i, f)
    R = np.transpose(R_fji, (1, 2, 0))
    
    return R


def detect_array_from_mat(filepath: str, prefix: str = "G25_") -> dict:
    """Detect array configuration from .mat file.
    
    Parameters
    ----------
    filepath : str
        Path to .mat file
    prefix : str
        Variable name prefix
        
    Returns
    -------
    dict
        Dictionary with:
        - n_channels: number of detected channels
        - n_freq: number of frequency points
        - freq_min: minimum frequency (Hz)
        - freq_max: maximum frequency (Hz)
        - freq_step: frequency step (Hz)
    """
    data = load_vibrosis_mat(filepath, prefix)
    
    freq = data.frequencies
    df = np.mean(np.diff(freq)) if len(freq) > 1 else 0
    
    return {
        'n_channels': data.n_channels,
        'n_freq': len(freq),
        'freq_min': float(freq[0]) if len(freq) > 0 else 0,
        'freq_max': float(freq[-1]) if len(freq) > 0 else 0,
        'freq_step': float(df),
        'channel_names': data.channel_names
    }


def parse_offset_from_filename(filename: str) -> Optional[float]:
    """Attempt to parse source offset from filename.
    
    Looks for patterns like:
    - DPsv00001.mat -> offset 1 (if sequential numbering)
    - offset_p66.mat -> +66
    - offset_m12.mat -> -12
    - src_+24m.mat -> +24
    
    Parameters
    ----------
    filename : str
        Filename (with or without path)
        
    Returns
    -------
    float or None
        Parsed offset in meters, or None if not detected
    """
    base = os.path.splitext(os.path.basename(filename))[0]
    
    # Pattern 1: explicit offset markers (p/m or +/-)
    patterns = [
        r'[_-]p(\d+(?:\.\d+)?)',   # _p66 or -p66 -> +66
        r'[_-]m(\d+(?:\.\d+)?)',   # _m12 or -m12 -> -12
        r'[_-]\+(\d+(?:\.\d+)?)',  # _+24 -> +24
        r'[_-]-(\d+(?:\.\d+)?)',   # _-24 -> -24
        r'offset[_-]?(\d+(?:\.\d+)?)',  # offset12 or offset_12
    ]
    
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, base, re.IGNORECASE)
        if match:
            val = float(match.group(1))
            # Patterns with 'm' prefix are negative
            if i == 1:  # _m pattern
                val = -val
            elif i == 3:  # _- pattern
                val = -val
            return val
    
    return None


def get_vibrosis_file_info(filepath: str) -> dict:
    """Get summary information about a vibrosis .mat file.
    
    Parameters
    ----------
    filepath : str
        Path to .mat file
        
    Returns
    -------
    dict
        Summary information including channel count, frequency range, etc.
    """
    try:
        info = detect_array_from_mat(filepath)
        info['file_path'] = filepath
        info['file_name'] = os.path.basename(filepath)
        info['parsed_offset'] = parse_offset_from_filename(filepath)
        info['valid'] = True
        info['error'] = None
    except Exception as e:
        info = {
            'file_path': filepath,
            'file_name': os.path.basename(filepath),
            'valid': False,
            'error': str(e),
            'n_channels': 0,
            'parsed_offset': None
        }
    
    return info
