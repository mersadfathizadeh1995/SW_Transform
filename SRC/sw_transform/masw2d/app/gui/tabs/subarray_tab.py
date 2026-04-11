"""Tab ② — Sub-Arrays & Assignment.

Left panel (narrow, ~280-320 px): sub-array generation modes + assignment
config with either/or offset toggle.
Right area: canvas on top, assignment tree + detail panel on bottom.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from sw_transform.masw2d.app.api.models import (
    AssignmentConfig,
    ShotDef,
    SubArraySpec,
    SurveyConfig,
)
from sw_transform.masw2d.app.api import preview_api, subarray_api
from sw_transform.masw2d.app.gui.canvas.survey_canvas import SurveyCanvas
from sw_transform.masw2d.app.gui.widgets.assignment_tree import (
    AssignmentTree,
    RelationInfo,
    SubArrayInfo,
)
from sw_transform.masw2d.app.gui.widgets.subarray_detail_panel import (
    ReceiverEntry,
    ShotEntry,
    SubArrayDetailPanel,
)
from sw_transform.masw2d.geometry.subarray import SubArrayDef

logger = logging.getLogger(__name__)

_BTN_GREEN_SS = (
    "QPushButton { background: #2ca02c; color: white; font-weight: bold; "
    "padding: 6px; border-radius: 3px; }"
    "QPushButton:hover { background: #259225; }"
)

# Offset mode constants
_OFFSET_ABSOLUTE = 0
_OFFSET_RATIO = 1


class SubArrayTab(QWidget):
    """Tab ② — configure sub-array sizes, assignment strategy, review tree.

    Signals
    -------
    config_changed()
        Emitted when sub-array configuration or assignment changes.
    """

    config_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._subarrays: List[SubArrayDef] = []
        self._specs: List[SubArraySpec] = []
        self._plan: Any = None
        self._survey = SurveyConfig()
        self._shots: List[ShotDef] = []
        self._global_assignment = AssignmentConfig()
        self._custom_overrides: Dict[str, AssignmentConfig] = {}
        self._selected_config: Optional[str] = None
        self._selected_sa: Optional[SubArrayDef] = None
        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)

        main_split = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(main_split)

        # ── Left panel (narrow, scrollable) ───────────────────────────
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setMinimumWidth(280)
        left_scroll.setMaximumWidth(420)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(4, 4, 4, 4)

        # Shared depth factor
        grp_shared = QGroupBox("Shared Settings")
        shared_form = QFormLayout(grp_shared)

        self._spin_depth_factor = QDoubleSpinBox()
        self._spin_depth_factor.setRange(1.5, 3.0)
        self._spin_depth_factor.setDecimals(1)
        self._spin_depth_factor.setValue(2.0)
        self._spin_depth_factor.setToolTip(
            "Depth factor: min_subarray_length = min_depth × factor"
        )
        shared_form.addRow("Depth Factor:", self._spin_depth_factor)
        left_layout.addWidget(grp_shared)

        # ── Mode tabs ────────────────────────────────────────────────
        self._mode_tabs = QTabWidget()
        self._mode_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self._build_mode1()
        self._build_mode2()
        self._build_mode3()
        self._build_mode4()
        left_layout.addWidget(self._mode_tabs)

        # Generate buttons
        btn_row = QHBoxLayout()
        self._btn_generate = QPushButton("Generate && Assign")
        self._btn_generate.setStyleSheet(_BTN_GREEN_SS)
        btn_row.addWidget(self._btn_generate)

        self._btn_reassign = QPushButton("Re-assign Only")
        btn_row.addWidget(self._btn_reassign)
        left_layout.addLayout(btn_row)

        # ── Assignment config ────────────────────────────────────────
        self._grp_assign = QGroupBox("Assignment")
        assign_form = QFormLayout(self._grp_assign)

        # Scope radio
        scope_row = QHBoxLayout()
        self._radio_global = QRadioButton("Global")
        self._radio_global.setChecked(True)
        self._radio_custom = QRadioButton("Custom for selected")
        scope_row.addWidget(self._radio_global)
        scope_row.addWidget(self._radio_custom)
        assign_form.addRow("Scope:", scope_row)

        self._combo_strategy = QComboBox()
        self._combo_strategy.addItems([
            "exterior_only", "balanced",
            "both_sides_priority", "offset_optimized",
        ])
        assign_form.addRow("Strategy:", self._combo_strategy)

        # Offset mode toggle: Absolute vs Ratio
        self._combo_offset_mode = QComboBox()
        self._combo_offset_mode.addItems(["Absolute (m)", "Ratio (×L)"])
        assign_form.addRow("Offset Mode:", self._combo_offset_mode)

        # Absolute offset widgets
        self._spin_min_offset = QDoubleSpinBox()
        self._spin_min_offset.setRange(0.0, 500.0)
        self._spin_min_offset.setDecimals(2)
        self._spin_min_offset.setValue(0.01)
        self._spin_min_offset.setSuffix(" m")
        assign_form.addRow("Min Offset:", self._spin_min_offset)

        self._spin_max_offset = QDoubleSpinBox()
        self._spin_max_offset.setRange(0.0, 9999.0)
        self._spin_max_offset.setDecimals(1)
        self._spin_max_offset.setValue(0.0)
        self._spin_max_offset.setSuffix(" m")
        self._spin_max_offset.setSpecialValueText("unlimited")
        assign_form.addRow("Max Offset:", self._spin_max_offset)

        # Ratio offset widgets
        self._spin_min_ratio = QDoubleSpinBox()
        self._spin_min_ratio.setRange(0.0, 10.0)
        self._spin_min_ratio.setDecimals(2)
        self._spin_min_ratio.setValue(0.0)
        assign_form.addRow("Min Ratio:", self._spin_min_ratio)

        self._spin_max_ratio = QDoubleSpinBox()
        self._spin_max_ratio.setRange(0.1, 10.0)
        self._spin_max_ratio.setDecimals(1)
        self._spin_max_ratio.setValue(2.0)
        assign_form.addRow("Max Ratio:", self._spin_max_ratio)

        # Start with Absolute mode visible
        self._apply_offset_mode(_OFFSET_ABSOLUTE)

        self._spin_max_shots = QSpinBox()
        self._spin_max_shots.setRange(0, 100)
        self._spin_max_shots.setValue(0)
        self._spin_max_shots.setSpecialValueText("unlimited")
        assign_form.addRow("Max Shots/SubArray:", self._spin_max_shots)

        self._chk_both_sides = QCheckBox("Require Both Sides")
        assign_form.addRow(self._chk_both_sides)

        self._chk_interior = QCheckBox("Allow Interior Shots")
        assign_form.addRow(self._chk_interior)

        self._lbl_exterior_note = QLabel(
            "<i>Only exterior shots (offset &gt; 0) are assigned.</i>"
        )
        self._lbl_exterior_note.setStyleSheet("color: #888; font-size: 10px;")
        assign_form.addRow(self._lbl_exterior_note)

        left_layout.addWidget(self._grp_assign)

        # Summary
        self._lbl_summary = QLabel("Generate sub-arrays to see summary.")
        self._lbl_summary.setWordWrap(True)
        self._lbl_summary.setStyleSheet(
            "QLabel { background: #f5f5f5; padding: 8px; border-radius: 3px; }"
        )
        left_layout.addWidget(self._lbl_summary)

        left_layout.addStretch()
        left_scroll.setWidget(left)

        # ── Right area ────────────────────────────────────────────────
        right_v_split = QSplitter(Qt.Orientation.Vertical)

        # Canvas (top)
        self._canvas = SurveyCanvas(show_waterfall=True)
        self._canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding,
        )
        right_v_split.addWidget(self._canvas)

        # Bottom: assignment tree + detail panel
        bottom_h_split = QSplitter(Qt.Orientation.Horizontal)
        self._assign_tree = AssignmentTree()
        self._detail_panel = SubArrayDetailPanel()
        bottom_h_split.addWidget(self._assign_tree)
        bottom_h_split.addWidget(self._detail_panel)
        bottom_h_split.setStretchFactor(0, 40)
        bottom_h_split.setStretchFactor(1, 60)

        right_v_split.addWidget(bottom_h_split)
        right_v_split.setStretchFactor(0, 40)
        right_v_split.setStretchFactor(1, 60)

        # Assemble main splitter
        main_split.addWidget(left_scroll)
        main_split.addWidget(right_v_split)
        main_split.setStretchFactor(0, 0)
        main_split.setStretchFactor(1, 1)

    # ── Mode page builders ────────────────────────────────────────────

    def _build_mode1(self) -> None:
        """Mode 1: Pick from List."""
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(4, 4, 4, 4)

        lay.addWidget(QLabel("Select channel counts:"))
        self._list_pick = QListWidget()
        self._list_pick.setSelectionMode(
            QListWidget.SelectionMode.NoSelection,
        )
        lay.addWidget(self._list_pick, 1)

        row = QFormLayout()
        self._spin_pick_slide = QSpinBox()
        self._spin_pick_slide.setRange(1, 48)
        self._spin_pick_slide.setValue(1)
        row.addRow("Slide Step:", self._spin_pick_slide)
        lay.addLayout(row)

        self._mode_tabs.addTab(page, "Pick List")

    def _build_mode2(self) -> None:
        """Mode 2: Min/Max Range."""
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(4, 4, 4, 4)

        self._spin_rng_min = QSpinBox()
        self._spin_rng_min.setRange(4, 256)
        self._spin_rng_min.setValue(12)
        form.addRow("Min Channels:", self._spin_rng_min)

        self._spin_rng_max = QSpinBox()
        self._spin_rng_max.setRange(4, 256)
        self._spin_rng_max.setValue(24)
        form.addRow("Max Channels:", self._spin_rng_max)

        self._spin_rng_step = QSpinBox()
        self._spin_rng_step.setRange(1, 48)
        self._spin_rng_step.setValue(4)
        form.addRow("Channel Step:", self._spin_rng_step)

        self._spin_rng_slide = QSpinBox()
        self._spin_rng_slide.setRange(1, 48)
        self._spin_rng_slide.setValue(1)
        form.addRow("Slide Step:", self._spin_rng_slide)

        self._mode_tabs.addTab(page, "Range")

    def _build_mode3(self) -> None:
        """Mode 3: N-Point Smart Extraction."""
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(4, 4, 4, 4)

        self._spin_npt_n = QSpinBox()
        self._spin_npt_n.setRange(1, 100)
        self._spin_npt_n.setValue(5)
        form.addRow("N Midpoints:", self._spin_npt_n)

        self._spin_npt_depth = QDoubleSpinBox()
        self._spin_npt_depth.setRange(1.0, 500.0)
        self._spin_npt_depth.setDecimals(1)
        self._spin_npt_depth.setValue(15.0)
        self._spin_npt_depth.setSuffix(" m")
        form.addRow("Min Depth:", self._spin_npt_depth)

        self._spin_npt_maxch = QSpinBox()
        self._spin_npt_maxch.setRange(4, 256)
        self._spin_npt_maxch.setValue(24)
        form.addRow("Max Channels:", self._spin_npt_maxch)

        self._mode_tabs.addTab(page, "N-Point")

    def _build_mode4(self) -> None:
        """Mode 4: Line Length + Depth Target."""
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(4, 4, 4, 4)

        self._spin_ld_length = QDoubleSpinBox()
        self._spin_ld_length.setRange(1.0, 5000.0)
        self._spin_ld_length.setDecimals(1)
        self._spin_ld_length.setValue(30.0)
        self._spin_ld_length.setSuffix(" m")
        form.addRow("Profile Length:", self._spin_ld_length)

        self._spin_ld_depth = QDoubleSpinBox()
        self._spin_ld_depth.setRange(1.0, 500.0)
        self._spin_ld_depth.setDecimals(1)
        self._spin_ld_depth.setValue(15.0)
        self._spin_ld_depth.setSuffix(" m")
        form.addRow("Min Depth:", self._spin_ld_depth)

        self._spin_ld_slide = QSpinBox()
        self._spin_ld_slide.setRange(1, 48)
        self._spin_ld_slide.setValue(1)
        form.addRow("Slide Step:", self._spin_ld_slide)

        self._mode_tabs.addTab(page, "Line+Depth")

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._btn_generate.clicked.connect(self._on_generate)
        self._btn_reassign.clicked.connect(self._on_reassign)
        self._assign_tree.config_selected.connect(self._on_tree_config_selected)
        self._assign_tree.subarray_selected.connect(self._on_tree_sa_selected)
        self._assign_tree.relation_toggled.connect(self._on_relation_toggled)
        self._radio_global.toggled.connect(self._on_scope_changed)
        self._radio_custom.toggled.connect(self._on_scope_changed)
        self._combo_offset_mode.currentIndexChanged.connect(
            self._apply_offset_mode,
        )
        self._detail_panel.shot_clicked.connect(self._on_detail_shot_clicked)
        self._detail_panel.receivers_visibility_changed.connect(
            self._on_detail_receivers_changed,
        )

    # ------------------------------------------------------------------
    # Offset mode visibility
    # ------------------------------------------------------------------

    def _apply_offset_mode(self, mode: int) -> None:
        """Show/hide absolute vs ratio spin boxes."""
        show_abs = mode == _OFFSET_ABSOLUTE
        self._spin_min_offset.setVisible(show_abs)
        self._spin_max_offset.setVisible(show_abs)
        self._spin_min_ratio.setVisible(not show_abs)
        self._spin_max_ratio.setVisible(not show_abs)

        # Hide the QLabel for each row via the form layout
        form = self._grp_assign.layout()
        if isinstance(form, QFormLayout):
            for row_idx in range(form.rowCount()):
                label_item = form.itemAt(row_idx, QFormLayout.ItemRole.LabelRole)
                field_item = form.itemAt(row_idx, QFormLayout.ItemRole.FieldRole)
                if field_item and field_item.widget() in (
                    self._spin_min_offset, self._spin_max_offset,
                ):
                    if label_item and label_item.widget():
                        label_item.widget().setVisible(show_abs)
                elif field_item and field_item.widget() in (
                    self._spin_min_ratio, self._spin_max_ratio,
                ):
                    if label_item and label_item.widget():
                        label_item.widget().setVisible(not show_abs)

    # ------------------------------------------------------------------
    # Public API (called by MainWindow when switching tabs)
    # ------------------------------------------------------------------

    def set_survey_and_shots(
        self, survey: SurveyConfig, shots: List[ShotDef],
    ) -> None:
        """Update the survey and shots from Tab ①."""
        self._survey = survey
        self._shots = shots
        n = survey.n_channels
        # Clamp spin boxes
        for spin in (self._spin_rng_max, self._spin_npt_maxch):
            spin.setMaximum(n)
            if spin.value() > n:
                spin.setValue(n)
        self._spin_rng_min.setMaximum(n)
        # Populate pick-list
        self._populate_pick_list()

    def get_specs(self) -> List[SubArraySpec]:
        return list(self._specs)

    def get_subarrays(self) -> List[SubArrayDef]:
        return list(self._subarrays)

    def get_assignment_config(
        self, config_name: Optional[str] = None,
    ) -> AssignmentConfig:
        """Return assignment config — custom override if exists, else global."""
        if config_name and config_name in self._custom_overrides:
            return self._custom_overrides[config_name]
        return self._read_assignment_widgets()

    def get_plan(self) -> Any:
        return self._plan

    def validate(self) -> tuple[bool, str]:
        if not self._subarrays:
            return False, "Generate sub-arrays first."
        return True, ""

    # ------------------------------------------------------------------
    # Pick list helpers
    # ------------------------------------------------------------------

    def _populate_pick_list(self) -> None:
        self._list_pick.clear()
        n = self._survey.n_channels
        for ch in range(n, 3, -1):
            item = QListWidgetItem(f"{ch} channels")
            item.setData(Qt.ItemDataRole.UserRole, ch)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self._list_pick.addItem(item)

    def _get_checked_channels(self) -> List[int]:
        result: List[int] = []
        for i in range(self._list_pick.count()):
            item = self._list_pick.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                result.append(item.data(Qt.ItemDataRole.UserRole))
        return result

    # ------------------------------------------------------------------
    # Assignment widget read / write
    # ------------------------------------------------------------------

    def _read_assignment_widgets(self) -> AssignmentConfig:
        """Read assignment config from widgets, respecting offset mode."""
        max_shots = self._spin_max_shots.value()
        mode = self._combo_offset_mode.currentIndex()

        if mode == _OFFSET_ABSOLUTE:
            max_off = self._spin_max_offset.value()
            return AssignmentConfig(
                strategy=self._combo_strategy.currentText(),
                min_offset=self._spin_min_offset.value(),
                max_offset=max_off if max_off > 0 else None,
                min_offset_ratio=0.0,
                max_offset_ratio=2.0,
                max_shots_per_subarray=max_shots if max_shots > 0 else None,
                require_both_sides=self._chk_both_sides.isChecked(),
                allow_interior_shots=self._chk_interior.isChecked(),
            )
        else:
            return AssignmentConfig(
                strategy=self._combo_strategy.currentText(),
                min_offset=0.0,
                max_offset=None,
                min_offset_ratio=self._spin_min_ratio.value(),
                max_offset_ratio=self._spin_max_ratio.value(),
                max_shots_per_subarray=max_shots if max_shots > 0 else None,
                require_both_sides=self._chk_both_sides.isChecked(),
                allow_interior_shots=self._chk_interior.isChecked(),
            )

    def _write_assignment_widgets(self, cfg: AssignmentConfig) -> None:
        idx = self._combo_strategy.findText(cfg.strategy)
        if idx >= 0:
            self._combo_strategy.setCurrentIndex(idx)
        self._spin_min_offset.setValue(cfg.min_offset)
        self._spin_max_offset.setValue(cfg.max_offset or 0.0)
        self._spin_min_ratio.setValue(cfg.min_offset_ratio)
        self._spin_max_ratio.setValue(cfg.max_offset_ratio)
        self._spin_max_shots.setValue(cfg.max_shots_per_subarray or 0)
        self._chk_both_sides.setChecked(cfg.require_both_sides)
        self._chk_interior.setChecked(cfg.allow_interior_shots)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_generate(self) -> None:
        """Generate sub-arrays from the active mode, then assign."""
        mode = self._mode_tabs.currentIndex()
        depth_factor = self._spin_depth_factor.value()

        if mode == 0:  # Pick from List
            selected = self._get_checked_channels()
            if not selected:
                return
            slide = self._spin_pick_slide.value()
            self._specs = subarray_api.generate_specs_from_list(
                selected, slide_step=slide,
            )
            self._subarrays = subarray_api.enumerate_all_subarrays(
                self._survey, self._specs,
            )

        elif mode == 1:  # Range
            self._specs = subarray_api.generate_specs_from_range(
                min_channels=self._spin_rng_min.value(),
                max_channels=self._spin_rng_max.value(),
                step=self._spin_rng_step.value(),
                total_channels=self._survey.n_channels,
                slide_step=self._spin_rng_slide.value(),
            )
            self._subarrays = subarray_api.enumerate_all_subarrays(
                self._survey, self._specs,
            )

        elif mode == 2:  # N-Point
            self._specs, self._subarrays = subarray_api.compute_npoint_configs(
                survey=self._survey,
                n_points=self._spin_npt_n.value(),
                min_depth=self._spin_npt_depth.value(),
                max_channels=self._spin_npt_maxch.value(),
                depth_factor=depth_factor,
            )

        elif mode == 3:  # Line + Depth
            self._specs, self._subarrays = (
                subarray_api.compute_line_depth_configs(
                    survey=self._survey,
                    desired_length=self._spin_ld_length.value(),
                    min_depth=self._spin_ld_depth.value(),
                    slide_step=self._spin_ld_slide.value(),
                    depth_factor=depth_factor,
                )
            )

        self._selected_sa = None
        self._detail_panel.clear_detail()
        self._rebuild_plan()
        self._refresh_canvas()
        self.config_changed.emit()

    def _on_reassign(self) -> None:
        """Re-assign with current strategy (no re-enumeration)."""
        if not self._specs:
            return
        self._selected_sa = None
        self._detail_panel.clear_detail()
        self._rebuild_plan()
        self._refresh_canvas()
        self.config_changed.emit()

    def _on_scope_changed(self) -> None:
        """Switch between global and custom scope."""
        if self._radio_custom.isChecked() and self._selected_config:
            cfg = self._custom_overrides.get(
                self._selected_config, self._global_assignment,
            )
            self._write_assignment_widgets(cfg)
            self._grp_assign.setTitle(
                f"Assignment — {self._selected_config}"
            )
        else:
            self._write_assignment_widgets(self._global_assignment)
            self._grp_assign.setTitle("Assignment")

    def _on_tree_config_selected(self, config_name: str) -> None:
        """Config node clicked in tree — update assignment panel context."""
        self._selected_config = config_name
        self._selected_sa = None
        self._detail_panel.clear_detail()
        if self._radio_custom.isChecked():
            cfg = self._custom_overrides.get(
                config_name, self._global_assignment,
            )
            self._write_assignment_widgets(cfg)
        self._grp_assign.setTitle(f"Assignment — {config_name}")
        self._refresh_canvas(filter_config=config_name)

    def _on_tree_sa_selected(self, config_name: str, sa_idx: int) -> None:
        """Sub-array node clicked in tree — highlight on canvas + populate detail."""
        self._selected_config = config_name

        # Find matching SubArrayDef
        sa_list = [
            s for s in self._subarrays if s.config_name == config_name
        ]
        if sa_idx >= len(sa_list):
            return
        target_sa = sa_list[sa_idx]
        self._selected_sa = target_sa

        # Populate detail panel
        self._populate_detail_panel(target_sa)

        # Draw detail view (no specific shot highlighted yet)
        self._draw_sa_detail(target_sa)
        self._grp_assign.setTitle(f"Assignment — {config_name}")

    def _on_relation_toggled(
        self,
        config_name: str,
        sa_idx: int,
        shot_index: int,
        is_checked: bool,
    ) -> None:
        """Shot checkbox toggled in the assignment tree."""
        logger.debug(
            "Relation toggled: %s sa=%d shot=%d checked=%s",
            config_name, sa_idx, shot_index, is_checked,
        )

    def _on_detail_shot_clicked(self, shot_index: int) -> None:
        """A shot was clicked in the detail panel — highlight on canvas."""
        if self._selected_sa is None:
            return
        sa = self._selected_sa
        self._draw_sa_detail(sa, highlight_shot_index=shot_index)

    def _on_detail_receivers_changed(self, _indices: object) -> None:
        """Receiver visibility changed in detail panel — update canvas."""
        if self._selected_sa is not None:
            self._draw_sa_detail(self._selected_sa)

    # ------------------------------------------------------------------
    # Detail panel helpers
    # ------------------------------------------------------------------

    def _populate_detail_panel(self, sa: SubArrayDef) -> None:
        """Fill the detail panel with receivers and assigned shots."""
        positions = self._survey.positions

        # Receivers for this sub-array
        receivers = [
            ReceiverEntry(
                channel_index=ch,
                position=float(positions[ch]),
            )
            for ch in range(sa.start_channel, sa.end_channel)
            if ch < len(positions)
        ]
        self._detail_panel.set_receivers(receivers)

        # Assigned shots for this sub-array
        shots: List[ShotEntry] = []
        if self._plan is not None:
            assigned = subarray_api.get_assignments_for_subarray(
                self._plan, sa, self._shots,
            )
            for a in assigned:
                shots.append(ShotEntry(
                    shot_index=a["shot_index"],
                    file=a.get("file", ""),
                    source_position=a["source_position"],
                    source_offset=a["source_offset"],
                    direction=a["direction"],
                ))
        self._detail_panel.set_shots(shots)

    def _get_assigned_source_positions(
        self, sa: SubArrayDef,
    ) -> List[float]:
        """Return source positions assigned to a specific sub-array."""
        if self._plan is None:
            return []
        assigned = subarray_api.get_assignments_for_subarray(
            self._plan, sa, self._shots,
        )
        return [a["source_position"] for a in assigned]

    # ------------------------------------------------------------------
    # Plan building
    # ------------------------------------------------------------------

    def _rebuild_plan(self) -> None:
        """Build assignment plan and populate the tree."""
        current_cfg = self._read_assignment_widgets()
        if self._radio_custom.isChecked() and self._selected_config:
            self._custom_overrides[self._selected_config] = current_cfg
        else:
            self._global_assignment = current_cfg

        assignment = self._global_assignment
        self._plan = subarray_api.build_assignment_plan(
            self._survey, self._shots, self._specs, assignment,
        )

        self._populate_tree()
        self._update_summary()

    def _populate_tree(self) -> None:
        """Fill assignment tree from current plan and sub-arrays."""
        sa_by_config: Dict[str, List[SubArrayDef]] = {}
        for sa in self._subarrays:
            sa_by_config.setdefault(sa.config_name, []).append(sa)

        tree_data: Dict[str, List[SubArrayInfo]] = {}
        for config_name, sa_list in sa_by_config.items():
            infos: List[SubArrayInfo] = []
            for sa in sa_list:
                relations: List[RelationInfo] = []
                if self._plan is not None:
                    assigned = subarray_api.get_assignments_for_subarray(
                        self._plan, sa, self._shots,
                    )
                    for a in assigned:
                        relations.append(RelationInfo(
                            shot_index=a["shot_index"],
                            shot_file=a.get("file", ""),
                            shot_position=a["source_position"],
                            source_offset=a["source_offset"],
                            direction=a["direction"],
                            is_valid=True,
                        ))
                infos.append(SubArrayInfo(
                    config_name=config_name,
                    start_channel=sa.start_channel,
                    end_channel=sa.end_channel,
                    midpoint=sa.midpoint,
                    n_channels=sa.end_channel - sa.start_channel,
                    relations=relations,
                ))
            tree_data[config_name] = infos

        self._assign_tree.populate(tree_data)

    def _update_summary(self) -> None:
        n_sa = len(self._subarrays)
        n_assign = 0
        if self._plan is not None:
            n_assign = len(self._plan.assignments)
        configs = sorted({s.name for s in self._specs})
        midpoints = sorted({sa.midpoint for sa in self._subarrays})
        coverage = (
            f"{midpoints[0]:.1f} → {midpoints[-1]:.1f} m"
            if midpoints else "—"
        )
        self._lbl_summary.setText(
            f"<b>{n_sa}</b> sub-arrays across {len(configs)} configs "
            f"({', '.join(configs)})<br>"
            f"<b>{n_assign}</b> assignments<br>"
            f"<b>{len(midpoints)}</b> midpoints — coverage: {coverage}"
        )

    # ------------------------------------------------------------------
    # Canvas refresh
    # ------------------------------------------------------------------

    def _refresh_canvas(self, filter_config: Optional[str] = None) -> None:
        """Draw sub-array overview with heatmap."""
        positions = self._survey.positions
        source_positions = [s.source_position for s in self._shots]

        self._canvas.draw_subarray_overview(
            positions=positions,
            source_positions=source_positions,
            subarrays=self._subarrays if self._subarrays else None,
            filter_config=filter_config,
            title=f"Sub-Array Layout — {len(self._subarrays)} sub-arrays",
        )

    def _draw_sa_detail(
        self,
        sa: SubArrayDef,
        highlight_shot_index: Optional[int] = None,
    ) -> None:
        """Draw detail view for a specific sub-array, optionally highlighting a shot."""
        positions = self._survey.positions
        active = set(range(sa.start_channel, sa.end_channel))

        # Use only sources assigned to this sub-array
        assigned_positions = self._get_assigned_source_positions(sa)

        # Determine which source to highlight and its offset/direction
        highlight_idx: Optional[int] = None
        source_offset: Optional[float] = None
        direction = ""
        time_data = None
        trace_data = None
        is_vib = False

        if highlight_shot_index is not None and self._plan is not None:
            assigned = subarray_api.get_assignments_for_subarray(
                self._plan, sa, self._shots,
            )
            for i, a in enumerate(assigned):
                if a["shot_index"] == highlight_shot_index:
                    highlight_idx = i
                    source_offset = a["source_offset"]
                    direction = a["direction"]
                    # Load waterfall preview for this shot
                    if highlight_shot_index < len(self._shots):
                        shot_file = self._shots[highlight_shot_index].file
                        if shot_file:
                            try:
                                preview = preview_api.load_shot_preview(
                                    shot_file,
                                )
                                time_data = preview.time
                                trace_data = preview.data
                                is_vib = preview.is_vibrosis
                            except Exception as exc:
                                logger.debug(
                                    "Could not load preview: %s", exc,
                                )
                    break

        self._canvas.draw_detail(
            positions=positions,
            subarray_start=sa.start_position,
            subarray_end=sa.end_position,
            subarray_midpoint=sa.midpoint,
            subarray_label=(
                f"{sa.config_name}  mid={sa.midpoint:.1f}m"
            ),
            active_indices=active,
            source_positions=assigned_positions,
            highlight_source_idx=highlight_idx,
            source_offset=source_offset,
            direction=direction,
            time=time_data,
            data=trace_data,
            is_vibrosis=is_vib,
            title=(
                f"Sub-array: {sa.config_name}  "
                f"ch {sa.start_channel}–{sa.end_channel - 1}"
            ),
        )
