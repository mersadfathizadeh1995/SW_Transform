"""Survey canvas — pyqtgraph-based dual-subplot widget.

Provides two user-resizable subplots inside a ``QSplitter``:

- **Schematic** (top, ~40 %): geophones, sources, sub-array spans, annotations.
- **Waterfall** (bottom, ~60 %): wiggle-trace display of seismic data.

Both share the same x-axis (distance in metres).  The user can drag the
splitter handle to adjust the ratio, and toggle the waterfall on / off to
let the schematic occupy the full height.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QHBoxLayout, QSplitter, QVBoxLayout, QWidget

from sw_transform.masw2d.app.gui.canvas import renderers as R

# Subplot identifiers
SUBPLOT_SCHEMATIC = "schematic"
SUBPLOT_WATERFALL = "waterfall"


class SurveyCanvas(QWidget):
    """Dual-subplot canvas for survey visualization.

    Parameters
    ----------
    parent : QWidget, optional
        Parent widget.
    show_waterfall : bool
        If True, create both schematic and waterfall subplots.
        If False, create only the schematic (useful for compact views).
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        show_waterfall: bool = True,
    ):
        super().__init__(parent)
        self._show_waterfall = show_waterfall
        self._items: Dict[str, List[Any]] = {
            SUBPLOT_SCHEMATIC: [],
            SUBPLOT_WATERFALL: [],
        }
        # Layer visibility sets (None = show all)
        self._visible_receivers: Optional[Set[int]] = None
        self._visible_sources: Optional[Set[int]] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toggle checkbox row (only when waterfall is available)
        if show_waterfall:
            toggle_row = QHBoxLayout()
            toggle_row.setContentsMargins(4, 2, 4, 0)
            self._chk_waterfall = QCheckBox("Show Waterfall")
            self._chk_waterfall.setChecked(True)
            self._chk_waterfall.setStyleSheet("font-size: 10px;")
            self._chk_waterfall.toggled.connect(self._on_waterfall_toggled)
            toggle_row.addWidget(self._chk_waterfall)
            toggle_row.addStretch()
            root.addLayout(toggle_row)
        else:
            self._chk_waterfall = None

        # Vertical splitter: schematic (top) + waterfall (bottom)
        self._splitter = QSplitter(Qt.Orientation.Vertical)
        root.addWidget(self._splitter, 1)

        # Schematic plot widget
        self._sch_widget = pg.PlotWidget(background="w")
        self._schematic: pg.PlotItem = self._sch_widget.getPlotItem()
        self._schematic.setLabel("bottom", "Distance (m)")
        self._schematic.hideAxis("left")
        self._schematic.setMouseEnabled(x=True, y=False)
        self._schematic.showGrid(x=True, alpha=0.15)
        self._splitter.addWidget(self._sch_widget)

        # Waterfall plot widget
        self._waterfall: Optional[pg.PlotItem] = None
        self._wf_widget: Optional[pg.PlotWidget] = None
        if show_waterfall:
            self._wf_widget = pg.PlotWidget(background="w")
            self._waterfall = self._wf_widget.getPlotItem()
            self._waterfall.setLabel("bottom", "Distance (m)")
            self._waterfall.setLabel("left", "Time (s)")
            self._waterfall.showGrid(x=True, y=True, alpha=0.15)
            self._waterfall.setXLink(self._schematic)
            self._splitter.addWidget(self._wf_widget)

            # Default ratio: schematic 40%, waterfall 60%
            self._splitter.setStretchFactor(0, 40)
            self._splitter.setStretchFactor(1, 60)

    # ------------------------------------------------------------------
    # Waterfall toggle
    # ------------------------------------------------------------------

    def _on_waterfall_toggled(self, checked: bool) -> None:
        """Show or hide the waterfall plot widget."""
        if self._wf_widget is not None:
            self._wf_widget.setVisible(checked)

    def set_waterfall_visible(self, visible: bool) -> None:
        """Programmatically show/hide the waterfall subplot."""
        if self._chk_waterfall is not None:
            self._chk_waterfall.setChecked(visible)
        elif self._wf_widget is not None:
            self._wf_widget.setVisible(visible)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_plot(self, name: str) -> Optional[pg.PlotItem]:
        """Return the PlotItem for a subplot name."""
        if name == SUBPLOT_SCHEMATIC:
            return self._schematic
        if name == SUBPLOT_WATERFALL:
            return self._waterfall
        return None

    def clear_subplot(self, name: str) -> None:
        """Remove all tracked items from a subplot."""
        for item in self._items.get(name, []):
            plot = self.get_plot(name)
            if plot is not None:
                try:
                    plot.removeItem(item)
                except Exception:
                    pass
        self._items[name] = []

    def clear_all(self) -> None:
        """Remove all items from all subplots."""
        self.clear_subplot(SUBPLOT_SCHEMATIC)
        self.clear_subplot(SUBPLOT_WATERFALL)

    def add_items(self, name: str, items: list) -> None:
        """Track items so they can be removed later."""
        self._items.setdefault(name, []).extend(items)

    def auto_range(self, name: Optional[str] = None) -> None:
        """Auto-range one or all subplots."""
        if name:
            plot = self.get_plot(name)
            if plot:
                plot.autoRange()
        else:
            self._schematic.autoRange()
            if self._waterfall:
                self._waterfall.autoRange()

    # ------------------------------------------------------------------
    # Layer visibility
    # ------------------------------------------------------------------

    def set_visible_receivers(self, indices: Optional[Set[int]]) -> None:
        """Set which receiver indices are visible (None = all)."""
        self._visible_receivers = indices

    def set_visible_sources(self, indices: Optional[Set[int]]) -> None:
        """Set which source indices are visible (None = all)."""
        self._visible_sources = indices

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _compute_x_range(
        self,
        positions: np.ndarray,
        source_positions: list[float],
    ) -> tuple[float, float]:
        all_x = list(positions)
        if source_positions:
            all_x.extend(source_positions)
        return min(all_x), max(all_x)

    def _apply_schematic_range(
        self,
        x_min: float,
        x_max: float,
        title: str = "",
    ) -> None:
        pad = (x_max - x_min) * 0.1
        self._schematic.setXRange(x_min - pad, x_max + pad)
        self._schematic.setYRange(*R.Y_RANGE)
        if title:
            self._schematic.setTitle(title, color="#333333", size="10pt")

    # ------------------------------------------------------------------
    # High-level drawing methods
    # ------------------------------------------------------------------

    def draw_overview(
        self,
        positions: np.ndarray,
        source_positions: list[float],
        subarrays: list | None = None,
        time: np.ndarray | None = None,
        data: np.ndarray | None = None,
        is_vibrosis: bool = False,
        title: str = "",
        highlight_source_idx: int | None = None,
        max_time: float | None = None,
    ) -> None:
        """Draw the full overview: all geophones, all sources, all spans.

        Parameters
        ----------
        positions : np.ndarray
            All geophone positions (m).
        source_positions : list of float
            All source positions (m).
        subarrays : list of SubArrayDef, optional
            Sub-arrays to draw as colored spans.
        time : np.ndarray, optional
            Time/frequency vector for waterfall.
        data : np.ndarray, optional
            Trace matrix for waterfall.
        is_vibrosis : bool
            If True, waterfall y-axis = Frequency (Hz).
        title : str
            Title for the schematic.
        highlight_source_idx : int, optional
            Index of the source to highlight in red.
        max_time : float, optional
            Clip waterfall display to this time window (s).
        """
        self.clear_all()
        sch = self._schematic

        x_min, x_max = self._compute_x_range(positions, source_positions)

        # Ground line + source line
        self.add_items(SUBPLOT_SCHEMATIC,
                       R.render_ground_line(sch, x_min, x_max))
        if source_positions:
            self.add_items(SUBPLOT_SCHEMATIC,
                           R.render_source_line(sch, x_min, x_max))

        # Geophones (all active)
        self.add_items(SUBPLOT_SCHEMATIC,
                       R.render_geophones(sch, positions,
                                          visible_indices=self._visible_receivers))

        # Sources (above survey line with drop lines)
        if source_positions:
            self.add_items(SUBPLOT_SCHEMATIC,
                           R.render_sources(sch, source_positions,
                                            highlight_index=highlight_source_idx,
                                            visible_indices=self._visible_sources))

        # Sub-array spans
        if subarrays:
            self.add_items(SUBPLOT_SCHEMATIC,
                           R.render_multi_spans(sch, subarrays))

        self._apply_schematic_range(x_min, x_max, title)

        # Waterfall
        if self._waterfall is not None and time is not None and data is not None:
            items = R.render_waterfall(
                self._waterfall, positions, time, data,
                is_vibrosis=is_vibrosis,
                max_time=max_time,
            )
            self.add_items(SUBPLOT_WATERFALL, items)
            if max_time is None:
                self._waterfall.autoRange()

    def draw_subarray_overview(
        self,
        positions: np.ndarray,
        source_positions: list[float],
        subarrays: list | None = None,
        filter_config: str | None = None,
        title: str = "",
    ) -> None:
        """Draw sub-array overview with heatmap + optional filtered spans.

        Used by Tab 2 instead of ``draw_overview`` to avoid the
        overlapping-span visual clutter.

        Parameters
        ----------
        positions : np.ndarray
            All geophone positions (m).
        source_positions : list of float
            All source positions (m).
        subarrays : list of SubArrayDef, optional
            All sub-arrays.
        filter_config : str, optional
            Show spans only for this config name (None = heatmap only).
        title : str
            Title for the schematic.
        """
        self.clear_all()
        sch = self._schematic

        x_min, x_max = self._compute_x_range(positions, source_positions)

        self.add_items(SUBPLOT_SCHEMATIC,
                       R.render_ground_line(sch, x_min, x_max))
        if source_positions:
            self.add_items(SUBPLOT_SCHEMATIC,
                           R.render_source_line(sch, x_min, x_max))

        self.add_items(SUBPLOT_SCHEMATIC,
                       R.render_geophones(sch, positions))

        if source_positions:
            self.add_items(SUBPLOT_SCHEMATIC,
                           R.render_sources(sch, source_positions))

        # Coverage heatmap bar (always shown)
        if subarrays:
            self.add_items(SUBPLOT_SCHEMATIC,
                           R.render_coverage_heatmap(sch, subarrays,
                                                     x_min, x_max))
            # Filtered spans for selected config
            if filter_config:
                self.add_items(SUBPLOT_SCHEMATIC,
                               R.render_filtered_spans(sch, subarrays,
                                                        config_name=filter_config))

        self._apply_schematic_range(x_min, x_max, title)

    def draw_detail(
        self,
        positions: np.ndarray,
        subarray_start: float,
        subarray_end: float,
        subarray_midpoint: float,
        subarray_label: str,
        active_indices: Set[int],
        source_positions: list[float],
        highlight_source_idx: int | None = None,
        source_offset: float | None = None,
        direction: str = "",
        time: np.ndarray | None = None,
        data: np.ndarray | None = None,
        is_vibrosis: bool = False,
        title: str = "",
        max_time: float | None = None,
    ) -> None:
        """Draw detail view: highlighted sub-array + selected source.

        Parameters
        ----------
        positions : np.ndarray
            All geophone positions (m).
        subarray_start, subarray_end : float
            Sub-array extent (m).
        subarray_midpoint : float
            Sub-array midpoint (m).
        subarray_label : str
            Label for the sub-array span.
        active_indices : set of int
            Channel indices belonging to the sub-array.
        source_positions : list of float
            All source positions for this sub-array.
        highlight_source_idx : int, optional
            Which source to highlight.
        source_offset : float, optional
            Offset distance (m) for annotation.
        direction : str
            ``"forward"`` or ``"reverse"`` for annotation.
        time : np.ndarray, optional
            Time/frequency vector for waterfall.
        data : np.ndarray, optional
            Full trace matrix (all channels).
        is_vibrosis : bool
            If True, y-axis = Frequency (Hz).
        title : str
            Title for the schematic.
        max_time : float, optional
            Clip waterfall display to this time window (s).
        """
        self.clear_all()
        sch = self._schematic

        x_min, x_max = self._compute_x_range(positions, source_positions)

        # Ground line + source line
        self.add_items(SUBPLOT_SCHEMATIC,
                       R.render_ground_line(sch, x_min, x_max))
        if source_positions:
            self.add_items(SUBPLOT_SCHEMATIC,
                           R.render_source_line(sch, x_min, x_max))

        # Geophones with active/inactive
        self.add_items(SUBPLOT_SCHEMATIC,
                       R.render_geophones(sch, positions,
                                          active_indices=active_indices))

        # Sources
        if source_positions:
            self.add_items(SUBPLOT_SCHEMATIC,
                           R.render_sources(sch, source_positions,
                                            highlight_index=highlight_source_idx))

        # Sub-array span
        self.add_items(SUBPLOT_SCHEMATIC,
                       R.render_subarray_span(
                           sch, subarray_start, subarray_end, subarray_midpoint,
                           label=subarray_label))

        # Offset annotation
        if (
            source_offset is not None
            and highlight_source_idx is not None
            and 0 <= highlight_source_idx < len(source_positions)
        ):
            src_pos = source_positions[highlight_source_idx]
            nearest_edge = (
                subarray_start if src_pos <= subarray_start else subarray_end
            )
            self.add_items(SUBPLOT_SCHEMATIC,
                           R.render_offset_annotation(
                               sch, src_pos, nearest_edge,
                               source_offset, direction))

        self._apply_schematic_range(x_min, x_max, title)

        # Waterfall with active channels highlighted
        if self._waterfall is not None and time is not None and data is not None:
            items = R.render_waterfall(
                self._waterfall, positions, time, data,
                active_indices=active_indices,
                is_vibrosis=is_vibrosis,
                max_time=max_time,
            )
            self.add_items(SUBPLOT_WATERFALL, items)
            if max_time is None:
                self._waterfall.autoRange()
