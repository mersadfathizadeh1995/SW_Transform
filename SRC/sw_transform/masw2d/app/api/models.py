"""Core dataclasses for the MASW 2D Profiler API.

These are the shared data structures that flow between the API layer
and the GUI.  They are independent of both Qt and the engine internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class SurveyConfig:
    """Geophone array geometry.

    Attributes
    ----------
    n_channels : int
        Total number of geophones in the array.
    dx : float
        Geophone spacing in metres.
    first_position : float
        Position of the first geophone (m).
    """

    n_channels: int = 24
    dx: float = 2.0
    first_position: float = 0.0

    @property
    def positions(self) -> np.ndarray:
        """Geophone positions along the survey line (m)."""
        return np.arange(self.n_channels, dtype=float) * self.dx + self.first_position

    @property
    def array_length(self) -> float:
        """Total array length (m), first-to-last geophone."""
        return (self.n_channels - 1) * self.dx

    @property
    def array_end(self) -> float:
        """Position of the last geophone (m)."""
        return self.first_position + self.array_length


@dataclass
class ShotDef:
    """A single shot (source) definition.

    Attributes
    ----------
    file : str
        Absolute path to the data file (.dat or .mat).
    source_position : float
        Source position along the survey line (m).
    label : str
        Optional human-readable label.
    """

    file: str = ""
    source_position: float = 0.0
    label: str = ""


@dataclass
class SubArraySpec:
    """Sub-array size specification used to enumerate sub-arrays.

    Attributes
    ----------
    n_channels : int
        Number of channels per sub-array.
    slide_step : int
        Sliding window step in channels.
    name : str
        Human-readable label (e.g. "12ch", "shallow").
    """

    n_channels: int = 12
    slide_step: int = 1
    name: str = ""

    def __post_init__(self):
        if not self.name:
            self.name = f"{self.n_channels}ch"


@dataclass
class ProcessingParams:
    """Parameters for the dispersion transform and peak picking.

    Attributes
    ----------
    method : str
        Transform method: ``"fk"``, ``"fdbf"``, ``"ps"``, ``"ss"``.
    freq_min, freq_max : float
        Frequency band (Hz).
    vel_min, vel_max : float
        Velocity band (m/s).
    grid_n : int
        Grid size for the transform.
    tol : float
        Peak-picking tolerance.
    vspace : str
        Velocity spacing: ``"log"`` or ``"linear"``.
    source_type : str
        ``"hammer"`` or ``"vibrosis"``.
    cylindrical : bool
        If True, use cylindrical steering for FDBF.
    start_time, end_time : float
        Time window (s) for preprocessing.
    downsample : bool
        Whether to downsample before transform.
    down_factor : int
        Downsampling factor.
    numf : int
        Number of FFT frequency points.
    power_threshold : float
        Threshold for peak-picking power.
    """

    method: str = "ps"
    freq_min: float = 5.0
    freq_max: float = 80.0
    vel_min: float = 100.0
    vel_max: float = 1500.0
    grid_n: int = 4000
    tol: float = 0.01
    vspace: str = "log"
    source_type: str = "hammer"
    cylindrical: bool = False
    start_time: float = 0.0
    end_time: float = 1.0
    downsample: bool = True
    down_factor: int = 16
    numf: int = 4000
    power_threshold: float = 0.1


@dataclass
class OutputConfig:
    """Export / output preferences.

    Attributes
    ----------
    directory : str
        Output directory path.
    export_csv : bool
        Export individual CSV files.
    export_npz : bool
        Export individual NPZ files.
    export_images : bool
        Export PNG dispersion images.
    combined_csv_per_midpoint : bool
        Merge CSVs per midpoint.
    combined_npz_per_midpoint : bool
        Merge NPZs per midpoint.
    generate_summary : bool
        Write summary files.
    parallel : bool
        Run processing in parallel.
    max_workers : int or None
        Worker count (None = auto).
    image_dpi : int
        DPI for exported images.
    cmap : str
        Matplotlib colormap name.
    fig_width : int
        Figure width in inches.
    fig_height : int
        Figure height in inches.
    plot_style : str
        ``"contourf"`` or ``"pcolormesh"``.
    contour_levels : int
        Number of contour levels.
    auto_velocity_limit : bool
        Auto-scale velocity axis in images.
    auto_frequency_limit : bool
        Auto-scale frequency axis in images.
    """

    directory: str = "./output_2d/"
    export_csv: bool = True
    export_npz: bool = True
    export_images: bool = True
    combined_csv_per_midpoint: bool = True
    combined_npz_per_midpoint: bool = True
    generate_summary: bool = True
    parallel: bool = False
    max_workers: Optional[int] = None
    image_dpi: int = 150
    cmap: str = "jet"
    fig_width: int = 8
    fig_height: int = 6
    plot_style: str = "contourf"
    contour_levels: int = 30
    auto_velocity_limit: bool = True
    auto_frequency_limit: bool = True


@dataclass
class AssignmentConfig:
    """Shot-to-subarray assignment strategy.

    Attributes
    ----------
    strategy : str
        One of ``"exterior_only"``, ``"balanced"``, ``"max_coverage"``,
        ``"both_sides_priority"``, ``"offset_optimized"``, ``"manual"``.
    max_offset : float or None
        Maximum absolute source offset (m).
    min_offset : float
        Minimum absolute source offset (m).
    max_offset_ratio : float
        Max offset / subarray_length ratio.
    min_offset_ratio : float
        Min offset / subarray_length ratio.
    max_shots_per_subarray : int or None
        Cap per subarray (None = unlimited).
    require_both_sides : bool
        Must have forward + reverse shots.
    allow_interior_shots : bool
        Allow sources inside the subarray span.
    """

    strategy: str = "exterior_only"
    max_offset: Optional[float] = None
    min_offset: float = 0.01
    max_offset_ratio: float = 2.0
    min_offset_ratio: float = 0.0
    max_shots_per_subarray: Optional[int] = None
    require_both_sides: bool = False
    min_shots_per_side: int = 0
    allow_interior_shots: bool = False

    def to_config_dict(self) -> Dict[str, Any]:
        """Convert to the dict format expected by the engine."""
        return {
            "strategy": self.strategy,
            "constraints": {
                "max_offset": self.max_offset,
                "min_offset": self.min_offset,
                "max_offset_ratio": self.max_offset_ratio,
                "min_offset_ratio": self.min_offset_ratio,
                "max_shots_per_subarray": self.max_shots_per_subarray,
                "require_both_sides": self.require_both_sides,
                "min_shots_per_side": self.min_shots_per_side,
                "allow_interior_shots": self.allow_interior_shots,
            },
        }


@dataclass
class ShotPreview:
    """Cached data from a loaded shot file for preview rendering.

    Attributes
    ----------
    time : np.ndarray
        Time (or frequency) vector.
    data : np.ndarray
        Trace matrix, shape ``(n_samples, n_channels)``.
    dx : float
        Geophone spacing read from the file.
    dt : float or None
        Sampling interval (None for vibrosis).
    n_channels : int
        Number of channels in the file.
    is_vibrosis : bool
        True if the file is a vibrosis ``.mat``.
    filepath : str
        Original file path.
    """

    time: np.ndarray = field(default_factory=lambda: np.array([]))
    data: np.ndarray = field(default_factory=lambda: np.array([]))
    dx: float = 2.0
    dt: Optional[float] = None
    n_channels: int = 0
    is_vibrosis: bool = False
    filepath: str = ""
