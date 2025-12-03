"""Layout visualization for sub-array configurations.

Provides functions to visualize and understand sub-array geometry,
coverage, and expected investigation depth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


@dataclass
class LayoutInfo:
    """Complete layout information for a sub-array configuration."""
    
    # Array parameters
    total_channels: int
    dx: float
    total_length: float
    
    # Sub-array parameters
    n_channels: int
    subarray_length: float
    
    # Coverage
    n_subarrays: int
    first_midpoint: float
    last_midpoint: float
    midpoint_spacing: float
    midpoints: np.ndarray
    
    # Depth estimation (source-aware)
    depth_min: float          # Realistic minimum depth
    depth_max: float          # Realistic maximum depth
    theoretical_depth: float  # L/2 rule for reference
    source_type: str          # Source type used for calculation
    min_wavelength: float     # For reference
    
    # Quality indicators
    lateral_resolution: float
    depth_resolution_ratio: float  # depth / lateral


def calculate_layout(
    total_channels: int,
    dx: float,
    subarray_channels: int,
    slide_step: int = 1,
    source_type: str = "hammer",
    freq_max: float = 80.0,
    velocity_min: float = 100.0
) -> LayoutInfo:
    """Calculate complete layout information for a configuration.
    
    Parameters
    ----------
    total_channels : int
        Total channels in the array
    dx : float
        Geophone spacing (m)
    subarray_channels : int
        Channels in the sub-array
    slide_step : int
        Sliding step in channels
    source_type : str
        Source type: 'hammer', 'heavy_hammer', 'weight_drop', 'vibroseis'
    freq_max : float
        Maximum frequency for min wavelength calculation
    velocity_min : float
        Minimum velocity for min wavelength calculation
    
    Returns
    -------
    LayoutInfo
        Complete layout information
    """
    from sw_transform.masw2d.config.templates import calculate_depth_range
    
    if subarray_channels > total_channels:
        raise ValueError(f"subarray_channels ({subarray_channels}) > total_channels ({total_channels})")
    
    total_length = (total_channels - 1) * dx
    subarray_length = (subarray_channels - 1) * dx
    
    # Number of sub-arrays
    n_subarrays = (total_channels - subarray_channels) // slide_step + 1
    
    # Midpoint positions
    first_midpoint = (subarray_channels - 1) * dx / 2
    midpoint_spacing = slide_step * dx
    midpoints = np.array([first_midpoint + i * midpoint_spacing 
                          for i in range(n_subarrays)])
    last_midpoint = midpoints[-1] if len(midpoints) > 0 else first_midpoint
    
    # Depth estimation based on source type
    depth_min, depth_max = calculate_depth_range(subarray_length, source_type)
    theoretical_depth = subarray_length / 2  # L/2 rule for reference
    
    # Minimum wavelength (highest frequency, lowest velocity)
    min_wavelength = velocity_min / freq_max if freq_max > 0 else 0
    
    # Resolution (use average depth for ratio)
    lateral_resolution = midpoint_spacing
    avg_depth = (depth_min + depth_max) / 2
    depth_resolution_ratio = avg_depth / lateral_resolution if lateral_resolution > 0 else 0
    
    return LayoutInfo(
        total_channels=total_channels,
        dx=dx,
        total_length=total_length,
        n_channels=subarray_channels,
        subarray_length=subarray_length,
        n_subarrays=n_subarrays,
        first_midpoint=first_midpoint,
        last_midpoint=last_midpoint,
        midpoint_spacing=midpoint_spacing,
        midpoints=midpoints,
        depth_min=depth_min,
        depth_max=depth_max,
        theoretical_depth=theoretical_depth,
        source_type=source_type,
        min_wavelength=min_wavelength,
        lateral_resolution=lateral_resolution,
        depth_resolution_ratio=depth_resolution_ratio
    )


def get_subarray_bounds(
    layout: LayoutInfo,
    subarray_index: int
) -> Tuple[float, float, float]:
    """Get bounds of a specific sub-array.
    
    Returns
    -------
    tuple
        (start_position, end_position, midpoint)
    """
    if subarray_index >= layout.n_subarrays:
        raise ValueError(f"Index {subarray_index} >= n_subarrays {layout.n_subarrays}")
    
    midpoint = layout.midpoints[subarray_index]
    half_length = layout.subarray_length / 2
    return (midpoint - half_length, midpoint + half_length, midpoint)


def format_layout_summary(layout: LayoutInfo) -> str:
    """Format layout info as text summary.
    
    Returns
    -------
    str
        Multi-line text summary
    """
    from sw_transform.masw2d.config.templates import get_source_label
    
    source_label = get_source_label(layout.source_type)
    
    lines = [
        f"Sub-Array Configuration: {layout.n_channels} channels",
        f"{'='*50}",
        f"",
        f"Array Setup:",
        f"  Total channels: {layout.total_channels}",
        f"  Spacing (dx): {layout.dx:.1f} m",
        f"  Total length: {layout.total_length:.1f} m",
        f"",
        f"Sub-Array Geometry:",
        f"  Channels: {layout.n_channels}",
        f"  Length: {layout.subarray_length:.1f} m",
        f"  Number of positions: {layout.n_subarrays}",
        f"",
        f"Coverage:",
        f"  Midpoint range: {layout.first_midpoint:.1f} m - {layout.last_midpoint:.1f} m",
        f"  Lateral resolution: {layout.lateral_resolution:.1f} m",
        f"",
        f"Depth Estimation ({source_label}):",
        f"  Realistic depth: {layout.depth_min:.1f} - {layout.depth_max:.1f} m",
        f"  Theoretical (L/2): {layout.theoretical_depth:.1f} m",
        f"  Min wavelength: {layout.min_wavelength:.2f} m",
    ]
    return "\n".join(lines)


# =============================================================================
# Matplotlib Plotting (for GUI)
# =============================================================================

def plot_layout(
    layout: LayoutInfo,
    ax=None,
    highlight_index: Optional[int] = None,
    show_all_subarrays: bool = False,
    show_depth: bool = True,
    colors: Optional[Dict[str, str]] = None
):
    """Plot sub-array layout visualization.
    
    Parameters
    ----------
    layout : LayoutInfo
        Layout information
    ax : matplotlib.axes.Axes, optional
        Axes to plot on. If None, creates new figure.
    highlight_index : int, optional
        Index of sub-array to highlight (0-based)
    show_all_subarrays : bool
        If True, show all sub-array positions faintly
    show_depth : bool
        If True, show depth indicator panel
    colors : dict, optional
        Color scheme override
    
    Returns
    -------
    matplotlib.figure.Figure
        The figure object
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, FancyBboxPatch
    from matplotlib.lines import Line2D
    
    # Default colors
    c = {
        "geophone": "#2196F3",
        "geophone_face": "#BBDEFB",
        "subarray": "#4CAF50",
        "subarray_alpha": 0.3,
        "highlight": "#FF5722",
        "depth": "#795548",
        "grid": "#E0E0E0",
        "text": "#212121"
    }
    if colors:
        c.update(colors)
    
    # Create figure if needed
    if ax is None:
        if show_depth:
            fig, axes = plt.subplots(2, 1, figsize=(12, 6), 
                                     gridspec_kw={'height_ratios': [1, 1.5]})
            ax_layout, ax_depth = axes
        else:
            fig, ax_layout = plt.subplots(1, 1, figsize=(12, 3))
            ax_depth = None
    else:
        ax_layout = ax
        ax_depth = None
        fig = ax.get_figure()
    
    # =========================================================================
    # Top panel: Array layout
    # =========================================================================
    
    # Draw geophone positions
    geophone_y = 0.5
    geophone_positions = np.arange(layout.total_channels) * layout.dx
    
    ax_layout.scatter(geophone_positions, [geophone_y] * layout.total_channels,
                      s=80, c=c["geophone_face"], edgecolors=c["geophone"],
                      linewidths=1.5, zorder=10, marker='v')
    
    # Draw array line
    ax_layout.hlines(geophone_y, 0, layout.total_length, 
                     colors=c["geophone"], linewidth=2, zorder=5)
    
    # Draw sub-array positions
    subarray_y = 0.2
    
    if show_all_subarrays:
        for i in range(layout.n_subarrays):
            start, end, mid = get_subarray_bounds(layout, i)
            rect = Rectangle((start, subarray_y - 0.05), end - start, 0.1,
                            facecolor=c["subarray"], alpha=c["subarray_alpha"] * 0.3,
                            edgecolor='none', zorder=2)
            ax_layout.add_patch(rect)
    
    # Highlight selected sub-array
    if highlight_index is not None and 0 <= highlight_index < layout.n_subarrays:
        start, end, mid = get_subarray_bounds(layout, highlight_index)
        rect = Rectangle((start, subarray_y - 0.08), end - start, 0.16,
                         facecolor=c["highlight"], alpha=0.4,
                         edgecolor=c["highlight"], linewidth=2, zorder=3)
        ax_layout.add_patch(rect)
        
        # Midpoint marker
        ax_layout.plot(mid, subarray_y, 'o', color=c["highlight"], 
                       markersize=10, zorder=15)
        ax_layout.annotate(f"Mid: {mid:.1f}m", (mid, subarray_y - 0.15),
                          ha='center', fontsize=9, color=c["highlight"])
    
    # Labels
    ax_layout.set_xlim(-layout.dx, layout.total_length + layout.dx)
    ax_layout.set_ylim(-0.1, 0.8)
    ax_layout.set_xlabel("Position along array (m)", fontsize=10)
    ax_layout.set_yticks([])
    ax_layout.set_title(f"Sub-Array Layout: {layout.n_channels} channels "
                        f"({layout.n_subarrays} positions)", fontsize=11)
    
    # Add channel numbers
    for i, x in enumerate(geophone_positions):
        if i == 0 or i == layout.total_channels - 1 or i % 4 == 0:
            ax_layout.annotate(f"G{i+1}", (x, geophone_y + 0.12),
                              ha='center', fontsize=8, color=c["text"])
    
    ax_layout.spines['top'].set_visible(False)
    ax_layout.spines['right'].set_visible(False)
    ax_layout.spines['left'].set_visible(False)
    
    # =========================================================================
    # Bottom panel: Depth profile
    # =========================================================================
    
    if ax_depth is not None:
        from sw_transform.masw2d.config.templates import get_source_label
        
        # Create depth gradient - use max realistic depth
        x_range = np.linspace(layout.first_midpoint, layout.last_midpoint, 100)
        z_range = np.linspace(0, layout.depth_max * 1.2, 50)
        X, Z = np.meshgrid(x_range, z_range)
        
        # Confidence zones based on depth range
        # High confidence: 0 to depth_min
        # Medium confidence: depth_min to depth_max
        # Low confidence: beyond depth_max
        confidence = np.ones_like(Z)
        confidence = np.where(Z > layout.depth_min, 
                             1 - (Z - layout.depth_min) / (layout.depth_max - layout.depth_min + 0.01),
                             confidence)
        confidence = np.where(Z > layout.depth_max, 0.1, confidence)
        confidence = np.clip(confidence, 0, 1)
        
        # Plot gradient
        ax_depth.contourf(X, Z, confidence, levels=20, cmap='YlOrBr_r', alpha=0.7)
        
        # Depth range lines
        ax_depth.axhline(layout.depth_min, color='#4CAF50', linestyle='-', 
                         linewidth=2, label=f"Min depth ~{layout.depth_min:.1f}m")
        ax_depth.axhline(layout.depth_max, color=c["depth"], linestyle='--', 
                         linewidth=2, label=f"Max depth ~{layout.depth_max:.1f}m")
        
        # Fill the realistic depth zone
        ax_depth.axhspan(layout.depth_min, layout.depth_max, alpha=0.15, 
                        color='#4CAF50', zorder=1)
        
        # Coverage bounds
        ax_depth.axvline(layout.first_midpoint, color=c["subarray"], 
                         linestyle=':', alpha=0.7)
        ax_depth.axvline(layout.last_midpoint, color=c["subarray"], 
                         linestyle=':', alpha=0.7)
        
        # Highlight column for selected sub-array
        if highlight_index is not None and 0 <= highlight_index < layout.n_subarrays:
            mid = layout.midpoints[highlight_index]
            ax_depth.axvline(mid, color=c["highlight"], linewidth=2, alpha=0.7)
        
        ax_depth.set_xlim(0, layout.total_length)
        ax_depth.set_ylim(layout.depth_max * 1.2, 0)  # Invert y-axis
        ax_depth.set_xlabel("Position (m)", fontsize=10)
        ax_depth.set_ylabel("Depth (m)", fontsize=10)
        source_label = get_source_label(layout.source_type)
        ax_depth.set_title(f"Investigation Depth ({source_label})", fontsize=11)
        ax_depth.legend(loc='lower right', fontsize=8)
        ax_depth.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def plot_all_configs_comparison(
    total_channels: int,
    dx: float,
    subarray_sizes: List[int],
    ax=None
):
    """Plot comparison of multiple sub-array configurations.
    
    Shows depth vs lateral resolution trade-off.
    
    Parameters
    ----------
    total_channels : int
        Total channels in array
    dx : float
        Geophone spacing
    subarray_sizes : list of int
        List of sub-array sizes to compare
    ax : matplotlib.axes.Axes, optional
        Axes to plot on
    
    Returns
    -------
    matplotlib.figure.Figure
    """
    import matplotlib.pyplot as plt
    
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    else:
        fig = ax.get_figure()
    
    # Calculate info for each size
    infos = []
    for n_ch in subarray_sizes:
        if n_ch <= total_channels:
            layout = calculate_layout(total_channels, dx, n_ch)
            infos.append(layout)
    
    # Extract data
    sizes = [l.n_channels for l in infos]
    depths = [l.max_depth for l in infos]
    n_midpoints = [l.n_subarrays for l in infos]
    
    # Create bar chart
    x = np.arange(len(sizes))
    width = 0.35
    
    ax2 = ax.twinx()
    
    bars1 = ax.bar(x - width/2, depths, width, label='Max Depth (m)', 
                   color='#795548', alpha=0.8)
    bars2 = ax2.bar(x + width/2, n_midpoints, width, label='# Midpoints',
                    color='#2196F3', alpha=0.8)
    
    ax.set_xlabel('Sub-Array Size (channels)')
    ax.set_ylabel('Max Investigation Depth (m)', color='#795548')
    ax2.set_ylabel('Number of Midpoints', color='#2196F3')
    
    ax.set_xticks(x)
    ax.set_xticklabels([f"{s}ch" for s in sizes])
    
    ax.tick_params(axis='y', labelcolor='#795548')
    ax2.tick_params(axis='y', labelcolor='#2196F3')
    
    # Add values on bars
    for bar, val in zip(bars1, depths):
        ax.annotate(f'{val:.0f}m', (bar.get_x() + bar.get_width()/2, bar.get_height()),
                   ha='center', va='bottom', fontsize=8)
    
    for bar, val in zip(bars2, n_midpoints):
        ax2.annotate(f'{val}', (bar.get_x() + bar.get_width()/2, bar.get_height()),
                    ha='center', va='bottom', fontsize=8, color='#2196F3')
    
    ax.set_title(f'Depth vs Resolution Trade-off ({total_channels} total channels, dx={dx}m)')
    
    # Combined legend
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    plt.tight_layout()
    return fig
