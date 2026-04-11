"""Renderer functions for the survey canvas.

Each ``render_*`` function creates pyqtgraph items and returns them
so the caller can track / remove them later.  Functions never import
Qt widgets — only ``pyqtgraph`` drawing primitives.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np
import pyqtgraph as pg

# ── Colour palette ────────────────────────────────────────────────
CLR_GEO_ACTIVE = "#2ca02c"       # green — active geophone
CLR_GEO_INACTIVE = "#c8c8c8"     # light gray — inactive geophone
CLR_SOURCE_ACTIVE = "#d62728"    # red — selected source
CLR_SOURCE_DIM = "#e8a0a0"       # dim pink — other sources
CLR_SPAN_FILL = (44, 160, 44, 40)   # green, semi-transparent
CLR_SPAN_BORDER = "#2ca02c"
CLR_MIDPOINT = "#b03060"         # maroon — midpoint marker
CLR_TRACE_ACTIVE = "#1f77b4"     # blue
CLR_TRACE_INACTIVE = "#d0d0d0"   # very light gray
CLR_OFFSET_LINE = "#888888"
CLR_GROUND = "#555555"
CLR_DROP_LINE = "#cc9999"        # faint red for source drop lines

# ── Layout constants ──────────────────────────────────────────────
Y_RECEIVER = 0.0                 # geophone y-position
Y_SOURCE = 0.18                  # source line y-position (above receivers)
Y_RANGE = (-0.15, 0.38)         # schematic y-range (room for labels)

# ── Marker symbols ────────────────────────────────────────────────
SYM_GEOPHONE = "t"    # upward triangle
SYM_SOURCE = "d"       # diamond


def render_ground_line(
    plot: pg.PlotItem,
    x_min: float,
    x_max: float,
) -> List[pg.PlotDataItem]:
    """Draw a thin horizontal ground line at y=0."""
    pad = (x_max - x_min) * 0.05
    item = pg.PlotDataItem(
        [x_min - pad, x_max + pad], [Y_RECEIVER, Y_RECEIVER],
        pen=pg.mkPen(CLR_GROUND, width=1, style=pg.QtCore.Qt.PenStyle.DashLine),
    )
    plot.addItem(item)
    return [item]


def render_source_line(
    plot: pg.PlotItem,
    x_min: float,
    x_max: float,
) -> List[pg.PlotDataItem]:
    """Draw a thin horizontal source line above the ground line."""
    pad = (x_max - x_min) * 0.05
    item = pg.PlotDataItem(
        [x_min - pad, x_max + pad], [Y_SOURCE, Y_SOURCE],
        pen=pg.mkPen(CLR_DROP_LINE, width=0.5,
                     style=pg.QtCore.Qt.PenStyle.DotLine),
    )
    plot.addItem(item)
    return [item]


def render_geophones(
    plot: pg.PlotItem,
    positions: np.ndarray,
    active_indices: Optional[Set[int]] = None,
    visible_indices: Optional[Set[int]] = None,
    size: float = 12.0,
) -> List[pg.ScatterPlotItem]:
    """Draw geophone markers along the survey line.

    Parameters
    ----------
    plot : pg.PlotItem
        Target plot.
    positions : np.ndarray
        All geophone positions (m).
    active_indices : set of int, optional
        Indices of active (highlighted) geophones.  If None, all active.
    visible_indices : set of int, optional
        Indices of visible geophones (layer panel filter).  If None, all visible.
    size : float
        Marker size in pixels.

    Returns
    -------
    list of ScatterPlotItem
        Created items.
    """
    items: List[pg.ScatterPlotItem] = []
    n = len(positions)

    if active_indices is None:
        active_indices = set(range(n))
    if visible_indices is None:
        visible_indices = set(range(n))

    # Inactive geophones (visible but not active)
    inactive_idx = sorted(i for i in visible_indices if i not in active_indices and i < n)
    if inactive_idx:
        inactive_pos = positions[inactive_idx]
        s = pg.ScatterPlotItem(
            inactive_pos,
            np.full(len(inactive_pos), Y_RECEIVER),
            symbol=SYM_GEOPHONE,
            size=size * 0.8,
            pen=pg.mkPen(CLR_GEO_INACTIVE, width=0.5),
            brush=pg.mkBrush(CLR_GEO_INACTIVE),
        )
        plot.addItem(s)
        items.append(s)

    # Active geophones (visible and active)
    active_list = sorted(i for i in active_indices if i in visible_indices and i < n)
    if active_list:
        active_pos = positions[active_list]
        s = pg.ScatterPlotItem(
            active_pos,
            np.full(len(active_pos), Y_RECEIVER),
            symbol=SYM_GEOPHONE,
            size=size,
            pen=pg.mkPen("#1a7a1a", width=1),
            brush=pg.mkBrush(CLR_GEO_ACTIVE),
        )
        plot.addItem(s)
        items.append(s)

    return items


def render_sources(
    plot: pg.PlotItem,
    source_positions: Sequence[float],
    highlight_index: Optional[int] = None,
    visible_indices: Optional[Set[int]] = None,
    size: float = 14.0,
) -> List[Any]:
    """Draw source markers on a parallel line above the survey line.

    Parameters
    ----------
    plot : pg.PlotItem
        Target plot.
    source_positions : sequence of float
        All source positions (m).
    highlight_index : int, optional
        Index of the source to highlight in bright red.
    visible_indices : set of int, optional
        Indices of visible sources (layer panel filter).  If None, all visible.
    size : float
        Marker size in pixels.

    Returns
    -------
    list
        Created items (scatter + drop lines).
    """
    items: List[Any] = []
    positions = list(source_positions)
    n = len(positions)

    if visible_indices is None:
        visible_indices = set(range(n))

    # Drop lines from source position to ground line
    for i in sorted(visible_indices):
        if i >= n:
            continue
        x = positions[i]
        is_highlight = (i == highlight_index)
        clr = CLR_SOURCE_ACTIVE if is_highlight else CLR_DROP_LINE
        w = 1.2 if is_highlight else 0.6
        drop = pg.PlotDataItem(
            [x, x], [Y_SOURCE, Y_RECEIVER],
            pen=pg.mkPen(clr, width=w,
                         style=pg.QtCore.Qt.PenStyle.DashLine),
        )
        plot.addItem(drop)
        items.append(drop)

    # Dim sources (visible, not highlighted)
    dim_idx = sorted(i for i in visible_indices if i != highlight_index and i < n)
    if dim_idx:
        dim_pos = [positions[i] for i in dim_idx]
        s = pg.ScatterPlotItem(
            dim_pos,
            [Y_SOURCE] * len(dim_pos),
            symbol=SYM_SOURCE,
            size=size * 0.85,
            pen=pg.mkPen(CLR_SOURCE_DIM, width=0.5),
            brush=pg.mkBrush(CLR_SOURCE_DIM),
        )
        plot.addItem(s)
        items.append(s)

    # Highlighted source
    if highlight_index is not None and highlight_index in visible_indices and 0 <= highlight_index < n:
        s = pg.ScatterPlotItem(
            [positions[highlight_index]],
            [Y_SOURCE],
            symbol=SYM_SOURCE,
            size=size,
            pen=pg.mkPen("#a01010", width=1.5),
            brush=pg.mkBrush(CLR_SOURCE_ACTIVE),
        )
        plot.addItem(s)
        items.append(s)

    return items


def render_subarray_span(
    plot: pg.PlotItem,
    start_pos: float,
    end_pos: float,
    midpoint: float,
    label: str = "",
    y_base: float = -0.10,
    height: float = 0.04,
) -> List[Any]:
    """Draw a semi-transparent span rectangle for a sub-array.

    Parameters
    ----------
    plot : pg.PlotItem
        Target plot.
    start_pos, end_pos : float
        Sub-array extent (m).
    midpoint : float
        Sub-array midpoint for the marker.
    label : str
        Text label inside the span.
    y_base : float
        Bottom y-coordinate of the span.
    height : float
        Height of the span rectangle.

    Returns
    -------
    list
        Created items (LinearRegionItem + TextItem + midpoint marker).
    """
    items: List[Any] = []

    # Span rectangle via LinearRegionItem (horizontal)
    region = pg.LinearRegionItem(
        values=[start_pos, end_pos],
        orientation="vertical",
        movable=False,
        brush=pg.mkBrush(*CLR_SPAN_FILL),
        pen=pg.mkPen(CLR_SPAN_BORDER, width=1.5),
    )
    plot.addItem(region)
    items.append(region)

    # Midpoint vertical dashed line
    mid_line = pg.InfiniteLine(
        pos=midpoint,
        angle=90,
        pen=pg.mkPen(CLR_MIDPOINT, width=1, style=pg.QtCore.Qt.PenStyle.DashLine),
    )
    plot.addItem(mid_line)
    items.append(mid_line)

    # Label
    if label:
        font = pg.QtGui.QFont()
        font.setPointSize(7)
        txt = pg.TextItem(label, color=CLR_SPAN_BORDER, anchor=(0.5, 0.0))
        txt.setFont(font)
        txt.setPos(midpoint, y_base - 0.01)
        plot.addItem(txt)
        items.append(txt)

    return items


def render_offset_annotation(
    plot: pg.PlotItem,
    source_pos: float,
    nearest_edge: float,
    offset_m: float,
    direction: str,
    y_pos: float = 0.28,
) -> List[Any]:
    """Draw a dimensioned line showing the source offset distance.

    Parameters
    ----------
    plot : pg.PlotItem
        Target plot.
    source_pos : float
        Source position (m).
    nearest_edge : float
        Nearest sub-array edge position (m).
    offset_m : float
        Offset distance (m).
    direction : str
        ``"forward"`` or ``"reverse"``.
    y_pos : float
        Y-coordinate for the annotation.

    Returns
    -------
    list
        Created items.
    """
    items: List[Any] = []

    # Horizontal line
    line = pg.PlotDataItem(
        [source_pos, nearest_edge], [y_pos, y_pos],
        pen=pg.mkPen(CLR_OFFSET_LINE, width=1.5),
    )
    plot.addItem(line)
    items.append(line)

    # End ticks
    tick_h = 0.02
    for x in (source_pos, nearest_edge):
        tick = pg.PlotDataItem(
            [x, x], [y_pos - tick_h, y_pos + tick_h],
            pen=pg.mkPen(CLR_OFFSET_LINE, width=1.5),
        )
        plot.addItem(tick)
        items.append(tick)

    # Label
    mid_x = (source_pos + nearest_edge) / 2.0
    font = pg.QtGui.QFont()
    font.setPointSize(8)
    txt = pg.TextItem(
        f"{offset_m:.1f} m ({direction})",
        color=CLR_OFFSET_LINE,
        anchor=(0.5, 0.0),
    )
    txt.setFont(font)
    txt.setPos(mid_x, y_pos + 0.01)
    plot.addItem(txt)
    items.append(txt)

    return items


def render_waterfall(
    plot: pg.PlotItem,
    positions: np.ndarray,
    time: np.ndarray,
    data: np.ndarray,
    active_indices: Optional[Set[int]] = None,
    is_vibrosis: bool = False,
    max_time: Optional[float] = None,
) -> List[pg.PlotDataItem]:
    """Draw a wiggle-trace waterfall plot.

    Parameters
    ----------
    plot : pg.PlotItem
        Target plot.
    positions : np.ndarray
        Geophone positions (m), length = n_channels.
    time : np.ndarray
        Time (or frequency) vector.
    data : np.ndarray
        Trace matrix, shape ``(n_samples, n_channels)``.
    active_indices : set of int, optional
        Indices to highlight.  If None, all active.
    is_vibrosis : bool
        If True, y-axis is Frequency (Hz) instead of Time (s).
    max_time : float, optional
        If given, clip the waterfall to ``[0, max_time]``.

    Returns
    -------
    list of PlotDataItem
        Created trace items.
    """
    items: List[pg.PlotDataItem] = []

    # Clip to max_time if requested
    if max_time is not None and max_time > 0 and len(time) > 1:
        mask = time <= max_time
        if mask.any():
            time = time[mask]
            data = data[mask, :]

    n_channels = data.shape[1]

    if active_indices is None:
        active_indices = set(range(n_channels))

    # Normalize each trace independently
    traces = data.T.copy().astype(float)  # (n_channels, n_samples)
    for i in range(n_channels):
        mx = np.max(np.abs(traces[i]))
        if mx > 0:
            traces[i] /= mx

    # Scale factor: half the average geophone spacing
    if len(positions) > 1:
        spacing = float(np.mean(np.diff(positions)))
    else:
        spacing = 1.0
    scale = 0.45 * spacing

    for i in range(n_channels):
        if i >= len(positions):
            break
        x0 = positions[i]
        is_active = i in active_indices
        color = CLR_TRACE_ACTIVE if is_active else CLR_TRACE_INACTIVE
        width = 0.8 if is_active else 0.3

        x_vals = traces[i] * scale + x0
        item = pg.PlotDataItem(
            x_vals, time,
            pen=pg.mkPen(color, width=width),
        )
        plot.addItem(item)
        items.append(item)

    # Invert y-axis (time goes downward, frequency goes downward)
    plot.invertY(True)
    plot.setLabel("left", "Frequency (Hz)" if is_vibrosis else "Time (s)")
    plot.setLabel("bottom", "Distance (m)")

    # Set explicit Y-range if max_time given
    if max_time is not None and max_time > 0:
        plot.setYRange(0, max_time)

    return items


def render_coverage_heatmap(
    plot: pg.PlotItem,
    subarrays: list,
    x_min: float,
    x_max: float,
    n_bins: int = 200,
    y_base: float = -0.08,
    bar_height: float = 0.04,
) -> List[Any]:
    """Draw a coverage heatmap bar below the survey line.

    Intensity encodes the number of overlapping sub-arrays at each
    position along the survey line.

    Parameters
    ----------
    plot : pg.PlotItem
        Target plot.
    subarrays : list of SubArrayDef
        All sub-arrays.
    x_min, x_max : float
        X range of the survey.
    n_bins : int
        Horizontal resolution.
    y_base : float
        Bottom y-coordinate of the bar.
    bar_height : float
        Height of the bar.

    Returns
    -------
    list
        Created items.
    """
    items: List[Any] = []
    if not subarrays:
        return items

    edges = np.linspace(x_min, x_max, n_bins + 1)
    counts = np.zeros(n_bins, dtype=float)

    for sa in subarrays:
        mask = (edges[:-1] >= sa.start_position) & (edges[1:] <= sa.end_position)
        counts[mask] += 1.0

    if counts.max() == 0:
        return items

    counts_norm = counts / counts.max()

    # Build RGBA image (1 row × n_bins)
    cmap = pg.colormap.get("viridis")
    colors = cmap.map(counts_norm, mode="byte")  # (n_bins, 4)
    img_data = colors.reshape(1, n_bins, 4)

    img = pg.ImageItem(image=img_data)
    dx_bin = (x_max - x_min) / n_bins
    img.setRect(pg.QtCore.QRectF(x_min, y_base, x_max - x_min, bar_height))
    plot.addItem(img)
    items.append(img)

    # Count label
    txt = pg.TextItem(
        f"max overlap: {int(counts.max())}",
        color="#666666",
        anchor=(0.0, 1.0),
    )
    txt.setPos(x_min, y_base - 0.005)
    plot.addItem(txt)
    items.append(txt)

    return items


def render_filtered_spans(
    plot: pg.PlotItem,
    subarrays: list,
    config_name: Optional[str] = None,
) -> List[Any]:
    """Draw sub-array spans for a single config (or all if None).

    When ``config_name`` is given, only sub-arrays with that config
    are drawn as discrete colored spans.  Otherwise draws all but
    grouped by config with distinct colours.

    Parameters
    ----------
    plot : pg.PlotItem
        Target plot.
    subarrays : list of SubArrayDef
        All sub-arrays.
    config_name : str, optional
        If given, filter to this config only.

    Returns
    -------
    list
        All created items.
    """
    items: List[Any] = []

    # Group by config_name
    groups: Dict[str, list] = {}
    for sa in subarrays:
        if config_name is not None and sa.config_name != config_name:
            continue
        groups.setdefault(sa.config_name, []).append(sa)

    # Colour palette for different configs
    palette = [
        (44, 160, 44, 40),   # green
        (31, 119, 180, 40),  # blue
        (255, 127, 14, 40),  # orange
        (148, 103, 189, 40), # purple
        (214, 39, 40, 40),   # red
    ]
    border_palette = ["#2ca02c", "#1f77b4", "#ff7f0e", "#9467bd", "#d62728"]

    for group_idx, (name, sa_list) in enumerate(sorted(groups.items())):
        fill = palette[group_idx % len(palette)]
        border = border_palette[group_idx % len(border_palette)]

        for sa in sa_list:
            region = pg.LinearRegionItem(
                values=[sa.start_position, sa.end_position],
                orientation="vertical",
                movable=False,
                brush=pg.mkBrush(*fill),
                pen=pg.mkPen(border, width=1),
            )
            plot.addItem(region)
            items.append(region)

    return items


def render_multi_spans(
    plot: pg.PlotItem,
    subarrays: list,
    y_offset_step: float = -0.12,
) -> List[Any]:
    """Draw multiple sub-array spans (legacy — delegates to filtered_spans + heatmap)."""
    return render_filtered_spans(plot, subarrays)
