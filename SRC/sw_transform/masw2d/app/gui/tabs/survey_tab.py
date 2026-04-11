"""Tab ① — Survey & Shots.

Left panel (35%): array geometry + shot table + pattern generator.
Right panel (65%): SurveyCanvas showing array schematic + waterfall,
with a collapsible layer panel on the far right.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Set

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from sw_transform.masw2d.app.api.models import ShotDef, ShotPreview, SurveyConfig
from sw_transform.masw2d.app.api import survey_api, preview_api
from sw_transform.masw2d.app.gui.canvas.survey_canvas import SurveyCanvas
from sw_transform.masw2d.app.gui.widgets.layer_panel import LayerPanel
from sw_transform.masw2d.app.gui.widgets.shot_table import ShotTable

logger = logging.getLogger(__name__)


class SurveyTab(QWidget):
    """Tab ① — define array geometry and load shot files.

    Signals
    -------
    survey_changed()
        Emitted when array geometry or shot list changes.
    """

    survey_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._survey = SurveyConfig()
        self._selected_shot_idx: int = 0
        self._user_edited_array: bool = False
        self._build_ui()
        self._connect_signals()
        self._refresh_canvas()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # ── Left panel (scrollable controls) ──────────────────────────
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setMinimumWidth(280)
        left_scroll.setMaximumWidth(500)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(4, 4, 4, 4)

        # Array geometry group
        grp_array = QGroupBox("Array Geometry")
        form = QFormLayout(grp_array)

        self._spin_n_channels = QSpinBox()
        self._spin_n_channels.setRange(2, 256)
        self._spin_n_channels.setValue(24)
        form.addRow("N Channels:", self._spin_n_channels)

        self._spin_dx = QDoubleSpinBox()
        self._spin_dx.setRange(0.1, 100.0)
        self._spin_dx.setDecimals(2)
        self._spin_dx.setValue(2.0)
        self._spin_dx.setSuffix(" m")
        form.addRow("Spacing (dx):", self._spin_dx)

        self._spin_first = QDoubleSpinBox()
        self._spin_first.setRange(-1000.0, 1000.0)
        self._spin_first.setDecimals(2)
        self._spin_first.setValue(0.0)
        self._spin_first.setSuffix(" m")
        form.addRow("First Position:", self._spin_first)

        self._btn_detect = QPushButton("Detect from File")
        self._btn_detect.setToolTip("Read n_channels and dx from the first loaded shot file")
        form.addRow(self._btn_detect)

        self._lbl_array_info = QLabel("Array: 0.0 → 46.0 m  (46.0 m)")
        self._lbl_array_info.setStyleSheet("color: #666;")
        form.addRow(self._lbl_array_info)

        left_layout.addWidget(grp_array)

        # Display window control
        grp_display = QGroupBox("Waterfall Display")
        disp_form = QFormLayout(grp_display)

        self._spin_max_time = QDoubleSpinBox()
        self._spin_max_time.setRange(0.1, 5.0)
        self._spin_max_time.setDecimals(2)
        self._spin_max_time.setValue(1.0)
        self._spin_max_time.setSuffix(" s")
        self._spin_max_time.setToolTip("Maximum time displayed in the waterfall plot")
        disp_form.addRow("Display Window:", self._spin_max_time)

        left_layout.addWidget(grp_display)

        # Pattern generator group
        grp_pattern = QGroupBox("Shot Position Pattern")
        pat_layout = QFormLayout(grp_pattern)

        self._spin_pat_start = QDoubleSpinBox()
        self._spin_pat_start.setRange(-500.0, 500.0)
        self._spin_pat_start.setDecimals(1)
        self._spin_pat_start.setValue(-6.0)
        self._spin_pat_start.setSuffix(" m")
        pat_layout.addRow("Start Position:", self._spin_pat_start)

        self._spin_pat_count = QSpinBox()
        self._spin_pat_count.setRange(1, 200)
        self._spin_pat_count.setValue(1)
        pat_layout.addRow("Number of Shots:", self._spin_pat_count)

        self._spin_pat_step = QDoubleSpinBox()
        self._spin_pat_step.setRange(0.1, 200.0)
        self._spin_pat_step.setDecimals(1)
        self._spin_pat_step.setValue(6.0)
        self._spin_pat_step.setSuffix(" m")
        pat_layout.addRow("Shot Spacing:", self._spin_pat_step)

        self._btn_gen_positions = QPushButton("Apply Positions to Table")
        pat_layout.addRow(self._btn_gen_positions)

        left_layout.addWidget(grp_pattern)

        # Shot table
        grp_shots = QGroupBox("Shot Files")
        shots_layout = QVBoxLayout(grp_shots)
        self._shot_table = ShotTable()
        shots_layout.addWidget(self._shot_table)
        left_layout.addWidget(grp_shots)

        left_layout.addStretch()
        left_scroll.setWidget(left)

        # ── Right panel (canvas + layer panel) ────────────────────────
        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self._canvas = SurveyCanvas(show_waterfall=True)
        self._canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        right_layout.addWidget(self._canvas, 1)

        self._layer_panel = LayerPanel()
        right_layout.addWidget(self._layer_panel, 0)

        splitter.addWidget(left_scroll)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._spin_n_channels.valueChanged.connect(self._on_array_edited)
        self._spin_dx.valueChanged.connect(self._on_array_edited)
        self._spin_first.valueChanged.connect(self._on_array_changed)
        self._spin_max_time.valueChanged.connect(self._on_display_changed)
        self._btn_detect.clicked.connect(self._on_detect_from_file)
        self._btn_gen_positions.clicked.connect(self._on_generate_positions)
        self._shot_table.data_changed.connect(self._on_shots_changed)
        self._shot_table.row_selected.connect(self._on_shot_row_selected)
        self._layer_panel.receivers_changed.connect(self._on_layer_visibility_changed)
        self._layer_panel.sources_changed.connect(self._on_layer_visibility_changed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_survey(self) -> SurveyConfig:
        """Return current array geometry."""
        return SurveyConfig(
            n_channels=self._spin_n_channels.value(),
            dx=self._spin_dx.value(),
            first_position=self._spin_first.value(),
        )

    def get_shots(self) -> List[ShotDef]:
        """Return current shot definitions."""
        return self._shot_table.get_shots()

    def validate(self) -> tuple[bool, str]:
        """Check if we have enough data to proceed to Tab ②."""
        shots = self.get_shots()
        if not shots:
            return False, "Add at least one shot file."
        valid_files = [s for s in shots if s.file]
        if not valid_files:
            return False, "At least one shot must have a data file."
        return True, ""

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_array_edited(self) -> None:
        """User manually edited n_channels or dx — mark as user-edited."""
        self._user_edited_array = True
        self._on_array_changed()

    def _on_array_changed(self) -> None:
        survey = self.get_survey()
        self._lbl_array_info.setText(
            f"Array: {survey.first_position:.1f} → "
            f"{survey.array_end:.1f} m  ({survey.array_length:.1f} m)"
        )
        self._update_layer_panel()
        self._refresh_canvas()
        self.survey_changed.emit()

    def _on_display_changed(self) -> None:
        self._refresh_canvas()

    def _on_detect_from_file(self) -> None:
        shots = self.get_shots()
        if not shots:
            QMessageBox.information(self, "Detect", "Load shot files first.")
            return
        first_file = next((s.file for s in shots if s.file), None)
        if not first_file:
            QMessageBox.information(self, "Detect", "No valid file paths found.")
            return
        try:
            n_ch, dx = survey_api.auto_detect_array(first_file)
            self._user_edited_array = True
            self._spin_n_channels.setValue(n_ch)
            self._spin_dx.setValue(dx)
            logger.info("Auto-detected: %d channels, %.2f m spacing", n_ch, dx)
        except Exception as exc:
            QMessageBox.warning(self, "Detect Error", str(exc))

    def _auto_detect_if_needed(self) -> None:
        """Auto-detect array geometry from the first file if not manually edited."""
        if self._user_edited_array:
            return
        shots = self.get_shots()
        first_file = next((s.file for s in shots if s.file), None)
        if not first_file:
            return
        try:
            n_ch, dx = survey_api.auto_detect_array(first_file)
            self._spin_n_channels.blockSignals(True)
            self._spin_dx.blockSignals(True)
            self._spin_n_channels.setValue(n_ch)
            self._spin_dx.setValue(dx)
            self._spin_n_channels.blockSignals(False)
            self._spin_dx.blockSignals(False)
            self._on_array_changed()
            logger.info("Auto-detected from load: %d ch, %.2f m", n_ch, dx)
        except Exception:
            pass

    def _on_generate_positions(self) -> None:
        """Apply pattern positions to existing table rows (or create rows)."""
        start = self._spin_pat_start.value()
        count = self._spin_pat_count.value()
        step = self._spin_pat_step.value()

        positions = [start + i * step for i in range(count)]
        current_shots = self._shot_table.get_shots()

        if current_shots:
            for i, shot in enumerate(current_shots):
                if i < len(positions):
                    shot.source_position = positions[i]
            for i in range(len(current_shots), len(positions)):
                current_shots.append(ShotDef(source_position=positions[i]))
            self._shot_table.set_shots(current_shots)
        else:
            new_shots = [ShotDef(source_position=p) for p in positions]
            self._shot_table.set_shots(new_shots)

    def _on_shots_changed(self) -> None:
        self._auto_detect_if_needed()
        # Auto-set pattern count to match loaded files
        n_rows = self._shot_table.row_count()
        if n_rows > 0:
            self._spin_pat_count.blockSignals(True)
            self._spin_pat_count.setValue(n_rows)
            self._spin_pat_count.blockSignals(False)
        self._update_layer_panel()
        self._refresh_canvas()
        self.survey_changed.emit()

    def _on_shot_row_selected(self, row: int) -> None:
        """Load the selected shot's data for waterfall preview."""
        self._selected_shot_idx = row
        shots = self.get_shots()
        if 0 <= row < len(shots):
            self._refresh_canvas(selected_shot_idx=row)

    def _on_layer_visibility_changed(self, _indices: object) -> None:
        """Update canvas visibility from layer panel changes."""
        self._canvas.set_visible_receivers(
            self._layer_panel.get_visible_receivers()
        )
        self._canvas.set_visible_sources(
            self._layer_panel.get_visible_sources()
        )
        self._refresh_canvas(selected_shot_idx=self._selected_shot_idx)

    # ------------------------------------------------------------------
    # Layer panel helpers
    # ------------------------------------------------------------------

    def _update_layer_panel(self) -> None:
        """Refresh layer panel items from current survey and shots."""
        survey = self.get_survey()
        positions = survey.positions

        receivers = [
            (f"Ch {i}", float(positions[i]))
            for i in range(len(positions))
        ]
        self._layer_panel.set_receivers(receivers)

        shots = self.get_shots()
        sources = [
            (s.file, s.source_position)
            for s in shots
        ]
        self._layer_panel.set_sources(sources)

    # ------------------------------------------------------------------
    # Canvas refresh
    # ------------------------------------------------------------------

    def _refresh_canvas(self, selected_shot_idx: int = 0) -> None:
        survey = self.get_survey()
        positions = survey.positions
        shots = self.get_shots()
        source_positions = [s.source_position for s in shots]

        # Try loading shot data for waterfall
        time_data, trace_data, is_vib = None, None, False
        highlight_idx = None
        if shots:
            idx = min(selected_shot_idx, len(shots) - 1)
            highlight_idx = idx if idx >= 0 else None
            if idx >= 0 and shots[idx].file:
                try:
                    preview = preview_api.load_shot_preview(shots[idx].file)
                    time_data = preview.time
                    trace_data = preview.data
                    is_vib = preview.is_vibrosis
                except Exception as exc:
                    logger.debug("Could not load preview: %s", exc)

        max_time = self._spin_max_time.value()

        self._canvas.draw_overview(
            positions=positions,
            source_positions=source_positions,
            time=time_data,
            data=trace_data,
            is_vibrosis=is_vib,
            title="Survey Line",
            highlight_source_idx=highlight_idx,
            max_time=max_time,
        )
