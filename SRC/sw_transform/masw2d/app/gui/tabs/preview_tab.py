"""Tab ③ — Review & Preview.

Narrow left sidebar (15%): navigator dropdowns + quick-info card.
Large right canvas (85%): schematic + waterfall for interactive review.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Set

import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from sw_transform.masw2d.app.api.models import ShotDef, SurveyConfig
from sw_transform.masw2d.app.api import preview_api, subarray_api
from sw_transform.masw2d.app.gui.canvas.survey_canvas import SurveyCanvas
from sw_transform.masw2d.geometry.subarray import SubArrayDef

logger = logging.getLogger(__name__)


class PreviewTab(QWidget):
    """Tab ③ — full-canvas interactive review of sub-array assignments.

    The user navigates through configs → midpoints → sources using
    cascading dropdowns, or steps sequentially with Prev/Next.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # State from other tabs
        self._survey = SurveyConfig()
        self._shots: List[ShotDef] = []
        self._subarrays: List[SubArrayDef] = []
        self._plan: Any = None

        # Derived navigation data
        self._config_names: List[str] = []
        self._midpoints_for_config: Dict[str, List[float]] = {}
        self._assignments_flat: List[Dict[str, Any]] = []
        self._current_flat_idx: int = -1

        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # ── Left sidebar (narrow navigator) ───────────────────────────
        sidebar = QWidget()
        sidebar.setMinimumWidth(180)
        sidebar.setMaximumWidth(260)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(4, 4, 4, 4)

        # Navigator group
        grp_nav = QGroupBox("Navigator")
        nav_form = QFormLayout(grp_nav)

        self._combo_config = QComboBox()
        self._combo_config.setToolTip("Filter by sub-array config")
        nav_form.addRow("Config:", self._combo_config)

        self._combo_midpoint = QComboBox()
        self._combo_midpoint.setToolTip("Filter by midpoint")
        nav_form.addRow("Midpoint:", self._combo_midpoint)

        self._combo_source = QComboBox()
        self._combo_source.setToolTip("Select assigned source")
        nav_form.addRow("Source:", self._combo_source)

        sb_layout.addWidget(grp_nav)

        # Quick info card
        grp_info = QGroupBox("Details")
        info_layout = QVBoxLayout(grp_info)
        self._lbl_info = QLabel("Select a sub-array to see details.")
        self._lbl_info.setWordWrap(True)
        self._lbl_info.setStyleSheet(
            "QLabel { background: #f0f4f0; padding: 8px; border-radius: 3px; "
            "font-size: 11px; }"
        )
        info_layout.addWidget(self._lbl_info)
        sb_layout.addWidget(grp_info)

        # Prev / Next buttons
        nav_btns = QHBoxLayout()
        self._btn_prev = QPushButton("◀ Prev")
        self._btn_next = QPushButton("Next ▶")
        nav_btns.addWidget(self._btn_prev)
        nav_btns.addWidget(self._btn_next)
        sb_layout.addLayout(nav_btns)

        # Overview button
        self._btn_overview = QPushButton("Show Overview")
        self._btn_overview.setStyleSheet(
            "QPushButton { padding: 6px; }"
        )
        sb_layout.addWidget(self._btn_overview)

        sb_layout.addStretch()

        # ── Right panel (massive canvas) ──────────────────────────────
        self._canvas = SurveyCanvas(show_waterfall=True)
        self._canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        splitter.addWidget(sidebar)
        splitter.addWidget(self._canvas)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._combo_config.currentIndexChanged.connect(self._on_config_changed)
        self._combo_midpoint.currentIndexChanged.connect(self._on_midpoint_changed)
        self._combo_source.currentIndexChanged.connect(self._on_source_changed)
        self._btn_prev.clicked.connect(self._on_prev)
        self._btn_next.clicked.connect(self._on_next)
        self._btn_overview.clicked.connect(self._show_overview)

    # ------------------------------------------------------------------
    # Public API (called by MainWindow when switching to this tab)
    # ------------------------------------------------------------------

    def set_data(
        self,
        survey: SurveyConfig,
        shots: List[ShotDef],
        subarrays: List[SubArrayDef],
        plan: Any,
    ) -> None:
        """Inject state from previous tabs and rebuild navigation."""
        self._survey = survey
        self._shots = shots
        self._subarrays = subarrays
        self._plan = plan
        self._build_navigation()
        self._show_overview()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _build_navigation(self) -> None:
        """Populate cascading dropdowns and flat assignment list."""
        # Build config names
        self._config_names = sorted({sa.config_name for sa in self._subarrays})

        # Midpoints per config
        self._midpoints_for_config.clear()
        for sa in self._subarrays:
            self._midpoints_for_config.setdefault(sa.config_name, set()).add(sa.midpoint)
        for key in self._midpoints_for_config:
            self._midpoints_for_config[key] = sorted(self._midpoints_for_config[key])

        # Flat assignment list for sequential navigation
        self._assignments_flat.clear()
        if self._plan is not None:
            for a in self._plan.assignments:
                sa = a.subarray_def
                shot_idx = a.shot_index
                file_path = self._shots[shot_idx].file if shot_idx < len(self._shots) else ""
                self._assignments_flat.append({
                    "subarray": sa,
                    "shot_index": shot_idx,
                    "source_position": a.shot_position,
                    "source_offset": a.source_offset,
                    "direction": a.direction,
                    "file": file_path,
                })

        # Populate config combo
        self._combo_config.blockSignals(True)
        self._combo_config.clear()
        self._combo_config.addItems(self._config_names)
        self._combo_config.blockSignals(False)

        if self._config_names:
            self._combo_config.setCurrentIndex(0)
            self._on_config_changed(0)

        self._current_flat_idx = -1

    def _on_config_changed(self, _idx: int) -> None:
        """Update midpoint combo when config changes."""
        config_name = self._combo_config.currentText()
        midpoints = self._midpoints_for_config.get(config_name, [])

        self._combo_midpoint.blockSignals(True)
        self._combo_midpoint.clear()
        self._combo_midpoint.addItems([f"{m:.1f}" for m in midpoints])
        self._combo_midpoint.blockSignals(False)

        if midpoints:
            self._combo_midpoint.setCurrentIndex(0)
            self._on_midpoint_changed(0)

    def _on_midpoint_changed(self, _idx: int) -> None:
        """Update source combo when midpoint changes."""
        config_name = self._combo_config.currentText()
        try:
            midpoint = float(self._combo_midpoint.currentText())
        except (ValueError, TypeError):
            return

        # Find matching subarray
        target_sa = None
        for sa in self._subarrays:
            if sa.config_name == config_name and abs(sa.midpoint - midpoint) < 0.01:
                target_sa = sa
                break

        if target_sa is None:
            return

        # Get assigned shots for this subarray
        assigned = subarray_api.get_assignments_for_subarray(
            self._plan, target_sa, self._shots,
        )

        self._combo_source.blockSignals(True)
        self._combo_source.clear()
        for i, a in enumerate(assigned):
            label = (
                f"#{a['shot_index'] + 1}: {a['source_offset']:.1f}m "
                f"({a['direction']})"
            )
            self._combo_source.addItem(label)
            self._combo_source.setItemData(i, a, Qt.ItemDataRole.UserRole)
        self._combo_source.blockSignals(False)

        if assigned:
            self._combo_source.setCurrentIndex(0)
            self._on_source_changed(0)

    def _on_source_changed(self, idx: int) -> None:
        """Draw the detail view for the selected source."""
        if idx < 0:
            return

        config_name = self._combo_config.currentText()
        try:
            midpoint = float(self._combo_midpoint.currentText())
        except (ValueError, TypeError):
            return

        # Find subarray
        target_sa = None
        for sa in self._subarrays:
            if sa.config_name == config_name and abs(sa.midpoint - midpoint) < 0.01:
                target_sa = sa
                break
        if target_sa is None:
            return

        # Get assignment data from combo
        a_data = self._combo_source.itemData(idx, Qt.ItemDataRole.UserRole)
        if a_data is None:
            return

        self._draw_detail(target_sa, a_data)

        # Sync flat index
        for fi, fa in enumerate(self._assignments_flat):
            if (
                fa["subarray"].start_channel == target_sa.start_channel
                and fa["subarray"].end_channel == target_sa.end_channel
                and fa["subarray"].config_name == target_sa.config_name
                and fa["shot_index"] == a_data["shot_index"]
            ):
                self._current_flat_idx = fi
                break

    def _on_prev(self) -> None:
        """Step to previous assignment."""
        if not self._assignments_flat:
            return
        self._current_flat_idx = max(0, self._current_flat_idx - 1)
        self._navigate_to_flat_index(self._current_flat_idx)

    def _on_next(self) -> None:
        """Step to next assignment."""
        if not self._assignments_flat:
            return
        self._current_flat_idx = min(
            len(self._assignments_flat) - 1,
            self._current_flat_idx + 1,
        )
        self._navigate_to_flat_index(self._current_flat_idx)

    def _navigate_to_flat_index(self, idx: int) -> None:
        """Jump to a specific flat assignment index and sync combos."""
        if idx < 0 or idx >= len(self._assignments_flat):
            return
        entry = self._assignments_flat[idx]
        sa = entry["subarray"]

        # Sync config combo
        config_idx = self._config_names.index(sa.config_name) if sa.config_name in self._config_names else 0
        self._combo_config.blockSignals(True)
        self._combo_config.setCurrentIndex(config_idx)
        self._combo_config.blockSignals(False)

        # Sync midpoint combo
        midpoints = self._midpoints_for_config.get(sa.config_name, [])
        mid_idx = 0
        for mi, m in enumerate(midpoints):
            if abs(m - sa.midpoint) < 0.01:
                mid_idx = mi
                break
        self._combo_midpoint.blockSignals(True)
        self._combo_midpoint.clear()
        self._combo_midpoint.addItems([f"{m:.1f}" for m in midpoints])
        self._combo_midpoint.setCurrentIndex(mid_idx)
        self._combo_midpoint.blockSignals(False)

        # Rebuild source combo and select matching
        self._on_midpoint_changed(mid_idx)

        # Find matching source in combo
        for si in range(self._combo_source.count()):
            sdata = self._combo_source.itemData(si, Qt.ItemDataRole.UserRole)
            if sdata and sdata.get("shot_index") == entry["shot_index"]:
                self._combo_source.setCurrentIndex(si)
                break

        self._draw_detail(sa, entry)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _show_overview(self) -> None:
        """Draw the full overview with all sub-arrays."""
        self._current_flat_idx = -1
        positions = self._survey.positions
        source_positions = [s.source_position for s in self._shots]

        # Try loading waterfall from first shot
        time_data, trace_data, is_vib = None, None, False
        for shot in self._shots:
            if shot.file and os.path.isfile(shot.file):
                try:
                    preview = preview_api.load_shot_preview(shot.file)
                    time_data = preview.time
                    trace_data = preview.data
                    is_vib = preview.is_vibrosis
                except Exception:
                    pass
                break

        self._canvas.draw_overview(
            positions=positions,
            source_positions=source_positions,
            subarrays=self._subarrays,
            time=time_data,
            data=trace_data,
            is_vibrosis=is_vib,
            title="Full Survey Overview",
        )

        self._lbl_info.setText(
            f"<b>Overview</b><br>"
            f"{len(self._subarrays)} sub-arrays<br>"
            f"{len(self._shots)} shots<br>"
            f"Click a config/midpoint/source to drill down."
        )

    def _draw_detail(self, sa: SubArrayDef, a_data: Dict[str, Any]) -> None:
        """Draw detail for a specific sub-array + source assignment."""
        positions = self._survey.positions
        active = set(range(sa.start_channel, sa.end_channel))

        # Collect all source positions assigned to this subarray
        assigned = subarray_api.get_assignments_for_subarray(
            self._plan, sa, self._shots,
        )
        all_source_pos = [a["source_position"] for a in assigned]
        if not all_source_pos:
            all_source_pos = [a_data.get("source_position", 0.0)]

        # Find highlight index
        highlight_idx = 0
        for i, a in enumerate(assigned):
            if a["shot_index"] == a_data["shot_index"]:
                highlight_idx = i
                break

        # Load waterfall data
        time_data, trace_data, is_vib = None, None, False
        filepath = a_data.get("file", "")
        if filepath and os.path.isfile(filepath):
            try:
                preview = preview_api.load_shot_preview(filepath)
                time_data = preview.time
                trace_data = preview.data
                is_vib = preview.is_vibrosis
            except Exception as exc:
                logger.debug("Could not load preview: %s", exc)

        self._canvas.draw_detail(
            positions=positions,
            subarray_start=sa.start_position,
            subarray_end=sa.end_position,
            subarray_midpoint=sa.midpoint,
            subarray_label=f"{sa.config_name}  mid={sa.midpoint:.1f}m",
            active_indices=active,
            source_positions=all_source_pos,
            highlight_source_idx=highlight_idx,
            source_offset=a_data.get("source_offset"),
            direction=a_data.get("direction", ""),
            time=time_data,
            data=trace_data,
            is_vibrosis=is_vib,
            title=(
                f"{sa.config_name}  ch {sa.start_channel}–{sa.end_channel - 1}  "
                f"mid={sa.midpoint:.1f}m"
            ),
        )

        # Update info card
        fname = os.path.basename(filepath) if filepath else "—"
        self._lbl_info.setText(
            f"<b>{sa.config_name}</b><br>"
            f"Channels: {sa.start_channel}–{sa.end_channel - 1}<br>"
            f"Midpoint: {sa.midpoint:.1f} m<br>"
            f"Offset: {a_data.get('source_offset', 0):.1f} m<br>"
            f"Direction: {a_data.get('direction', '—')}<br>"
            f"File: {fname}"
        )
