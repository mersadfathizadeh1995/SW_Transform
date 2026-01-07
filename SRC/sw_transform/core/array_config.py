"""Flexible geophone array configuration for MASW processing.

This module provides the ArrayConfig dataclass that encapsulates all array
configuration options including channel selection, positions, and source handling.

Supports:
- Channel selection: all, first_n, last_n, range, custom
- Spacing modes: uniform, custom positions
- Shot types: exterior, edge, interior
- Interior shot splitting for left/right processing
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Tuple
import numpy as np


@dataclass
class ArrayConfig:
    """Flexible geophone array configuration.
    
    Attributes
    ----------
    n_channels_file : int
        Total channels detected in file
    dx_file : float
        Spacing from file header (meters)
    channel_mode : str
        Channel selection mode: 'all', 'first_n', 'last_n', 'range', 'custom'
    n_channels_use : int
        Number of channels for first_n/last_n modes
    channel_start : int
        Start index for range mode (0-indexed)
    channel_end : int
        End index for range mode (exclusive)
    channel_indices : List[int]
        Specific indices for custom mode
    spacing_mode : str
        'uniform' or 'custom'
    dx : float
        Uniform spacing (meters)
    custom_positions : List[float]
        Custom geophone positions (meters)
    source_position : float
        Source position in meters
    interior_side : str
        For interior shots: 'left', 'right', or 'both'
    """
    
    n_channels_file: int = 24
    dx_file: float = 2.0
    
    channel_mode: Literal['all', 'first_n', 'last_n', 'range', 'custom'] = 'all'
    n_channels_use: int = 24
    channel_start: int = 0
    channel_end: int = 24
    channel_indices: List[int] = field(default_factory=list)
    
    spacing_mode: Literal['uniform', 'custom'] = 'uniform'
    dx: float = 2.0
    custom_positions: List[float] = field(default_factory=list)
    
    source_position: float = -10.0
    interior_side: Literal['left', 'right', 'both'] = 'both'
    
    def get_selected_indices(self) -> np.ndarray:
        """Get indices of selected channels (0-indexed).
        
        Returns
        -------
        np.ndarray
            Array of channel indices to use
        """
        if self.channel_mode == 'all':
            return np.arange(self.n_channels_file)
        elif self.channel_mode == 'first_n':
            n = min(self.n_channels_use, self.n_channels_file)
            return np.arange(n)
        elif self.channel_mode == 'last_n':
            n = min(self.n_channels_use, self.n_channels_file)
            start = max(0, self.n_channels_file - n)
            return np.arange(start, self.n_channels_file)
        elif self.channel_mode == 'range':
            start = max(0, self.channel_start)
            end = min(self.channel_end, self.n_channels_file)
            return np.arange(start, end)
        elif self.channel_mode == 'custom':
            valid = [i for i in self.channel_indices if 0 <= i < self.n_channels_file]
            return np.array(sorted(valid), dtype=int)
        return np.arange(self.n_channels_file)
    
    def get_positions(self) -> np.ndarray:
        """Get positions for selected channels.
        
        Returns
        -------
        np.ndarray
            Position array in meters for selected channels
        """
        indices = self.get_selected_indices()
        n_selected = len(indices)
        
        if self.spacing_mode == 'uniform':
            all_positions = np.arange(self.n_channels_file) * self.dx
            return all_positions[indices]
        else:
            positions = np.array(self.custom_positions, dtype=float)
            if len(positions) >= n_selected:
                return positions[:n_selected]
            else:
                extra_start = positions[-1] + self.dx if len(positions) > 0 else 0.0
                extra = extra_start + np.arange(n_selected - len(positions)) * self.dx
                return np.concatenate([positions, extra])
    
    def get_effective_data(self, full_data: np.ndarray) -> np.ndarray:
        """Extract selected channels from full data array.
        
        Parameters
        ----------
        full_data : np.ndarray
            Full data array (nsamples, nchannels)
            
        Returns
        -------
        np.ndarray
            Selected data (nsamples, n_selected_channels)
        """
        indices = self.get_selected_indices()
        if full_data.ndim == 1:
            return full_data[indices]
        return full_data[:, indices]
    
    def get_n_selected(self) -> int:
        """Get number of selected channels."""
        return len(self.get_selected_indices())
    
    def get_array_length(self) -> float:
        """Get total length of selected array in meters."""
        positions = self.get_positions()
        if len(positions) < 2:
            return 0.0
        return float(positions[-1] - positions[0])
    
    def get_min_spacing(self) -> float:
        """Get minimum spacing between adjacent geophones.
        
        Important for aliasing calculations.
        """
        positions = self.get_positions()
        if len(positions) < 2:
            return self.dx
        diffs = np.diff(positions)
        return float(np.min(diffs)) if len(diffs) > 0 else self.dx
    
    def classify_shot(self) -> str:
        """Classify shot type based on source position.
        
        Returns
        -------
        str
            One of: 'exterior_left', 'exterior_right', 'edge_left', 
            'edge_right', 'interior'
        """
        positions = self.get_positions()
        if len(positions) == 0:
            return 'exterior_left'
        
        array_start = positions[0]
        array_end = positions[-1]
        tolerance = 0.01 * self.dx
        
        if abs(self.source_position - array_start) < tolerance:
            return 'edge_left'
        elif abs(self.source_position - array_end) < tolerance:
            return 'edge_right'
        elif self.source_position < array_start:
            return 'exterior_left'
        elif self.source_position > array_end:
            return 'exterior_right'
        else:
            return 'interior'
    
    def needs_reverse(self) -> bool:
        """Check if data needs reversal for correct wave direction."""
        shot_type = self.classify_shot()
        return shot_type in ('exterior_right', 'edge_right')
    
    def split_interior_shot(self) -> List['ArrayConfig']:
        """Split interior shot into left and right virtual shots.
        
        Returns
        -------
        List[ArrayConfig]
            One or two configs for left/right sides. Returns [self] if not interior.
        """
        if self.classify_shot() != 'interior':
            return [self]
        
        positions = self.get_positions()
        indices = self.get_selected_indices()
        
        configs = []
        min_channels = 6
        
        if self.interior_side in ('left', 'both'):
            left_mask = positions < self.source_position
            if np.sum(left_mask) >= min_channels:
                left_indices = indices[left_mask][::-1].tolist()
                left_positions = positions[left_mask][::-1].tolist()
                left_config = ArrayConfig(
                    n_channels_file=self.n_channels_file,
                    dx_file=self.dx_file,
                    channel_mode='custom',
                    channel_indices=left_indices,
                    spacing_mode='custom',
                    custom_positions=left_positions,
                    source_position=self.source_position,
                    dx=self.dx
                )
                configs.append(left_config)
        
        if self.interior_side in ('right', 'both'):
            right_mask = positions > self.source_position
            if np.sum(right_mask) >= min_channels:
                right_indices = indices[right_mask].tolist()
                right_positions = positions[right_mask].tolist()
                right_config = ArrayConfig(
                    n_channels_file=self.n_channels_file,
                    dx_file=self.dx_file,
                    channel_mode='custom',
                    channel_indices=right_indices,
                    spacing_mode='custom',
                    custom_positions=right_positions,
                    source_position=self.source_position,
                    dx=self.dx
                )
                configs.append(right_config)
        
        return configs if configs else [self]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'n_channels_file': self.n_channels_file,
            'dx_file': self.dx_file,
            'channel_mode': self.channel_mode,
            'n_channels_use': self.n_channels_use,
            'channel_start': self.channel_start,
            'channel_end': self.channel_end,
            'channel_indices': list(self.channel_indices),
            'spacing_mode': self.spacing_mode,
            'dx': self.dx,
            'custom_positions': list(self.custom_positions),
            'source_position': self.source_position,
            'interior_side': self.interior_side
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> 'ArrayConfig':
        """Create from dictionary."""
        return cls(**d)
    
    def __repr__(self) -> str:
        n_sel = self.get_n_selected()
        shot = self.classify_shot()
        return f"ArrayConfig({n_sel}/{self.n_channels_file} channels, {shot}, dx={self.dx}m)"


def create_default_config(n_channels: int, dx: float, source_offset: float = -10.0) -> ArrayConfig:
    """Create default config from file info.
    
    Parameters
    ----------
    n_channels : int
        Number of channels in file
    dx : float
        Geophone spacing from file
    source_offset : float
        Source offset (negative = before array, positive = after array)
    
    Returns
    -------
    ArrayConfig
        Default configuration using all channels
    """
    array_length = (n_channels - 1) * dx
    if source_offset < 0:
        source_pos = source_offset
    else:
        source_pos = array_length + source_offset
    
    return ArrayConfig(
        n_channels_file=n_channels,
        dx_file=dx,
        dx=dx,
        n_channels_use=n_channels,
        channel_end=n_channels,
        source_position=source_pos
    )


def create_first_n_config(n_channels_file: int, n_use: int, dx: float, 
                          source_offset: float = -10.0) -> ArrayConfig:
    """Create config using first N channels.
    
    Parameters
    ----------
    n_channels_file : int
        Total channels in file
    n_use : int
        Number of channels to use
    dx : float
        Geophone spacing
    source_offset : float
        Source offset
    
    Returns
    -------
    ArrayConfig
        Configuration for first N channels
    """
    if source_offset < 0:
        source_pos = source_offset
    else:
        array_length = (n_use - 1) * dx
        source_pos = array_length + source_offset
    
    return ArrayConfig(
        n_channels_file=n_channels_file,
        dx_file=dx,
        channel_mode='first_n',
        n_channels_use=n_use,
        dx=dx,
        source_position=source_pos
    )


def create_custom_positions_config(n_channels_file: int, positions: List[float],
                                   source_position: float) -> ArrayConfig:
    """Create config with custom geophone positions.
    
    Parameters
    ----------
    n_channels_file : int
        Total channels in file
    positions : List[float]
        Custom positions in meters
    source_position : float
        Source position in meters
    
    Returns
    -------
    ArrayConfig
        Configuration with custom positions
    """
    n_use = len(positions)
    dx_est = np.mean(np.diff(positions)) if len(positions) > 1 else 2.0
    
    return ArrayConfig(
        n_channels_file=n_channels_file,
        dx_file=dx_est,
        channel_mode='first_n',
        n_channels_use=n_use,
        spacing_mode='custom',
        custom_positions=list(positions),
        dx=dx_est,
        source_position=source_position
    )
