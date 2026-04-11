"""Tab ④ — Process & Export.

Left panel (35%): processing params, output config, run/save buttons.
Right panel (65%): log + progress bar + results summary.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sw_transform.masw2d.app.api.models import (
    AssignmentConfig,
    OutputConfig,
    ProcessingParams,
    ShotDef,
    SubArraySpec,
    SurveyConfig,
)

logger = logging.getLogger(__name__)


class ProcessTab(QWidget):
    """Tab ④ — configure processing, run workflow, view results.

    Signals
    -------
    run_requested(dict)
        Emitted with a dict containing ``config``, ``output_dir``,
        ``parallel``, ``max_workers`` when the user clicks Run.
    save_config_requested()
        Emitted when the user clicks Save Config JSON.
    """

    run_requested = pyqtSignal(dict)
    save_config_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
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

        # ── Left panel (scrollable controls) ──────────────────────────
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setMinimumWidth(280)
        left_scroll.setMaximumWidth(420)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(4, 4, 4, 4)

        # Processing group
        grp_proc = QGroupBox("Processing")
        proc_form = QFormLayout(grp_proc)

        self._combo_method = QComboBox()
        self._combo_method.addItems(["ps", "fk", "fdbf", "ss"])
        proc_form.addRow("Method:", self._combo_method)

        self._spin_fmin = QDoubleSpinBox()
        self._spin_fmin.setRange(0.1, 500.0)
        self._spin_fmin.setValue(5.0)
        self._spin_fmin.setSuffix(" Hz")
        proc_form.addRow("Freq Min:", self._spin_fmin)

        self._spin_fmax = QDoubleSpinBox()
        self._spin_fmax.setRange(1.0, 1000.0)
        self._spin_fmax.setValue(80.0)
        self._spin_fmax.setSuffix(" Hz")
        proc_form.addRow("Freq Max:", self._spin_fmax)

        self._spin_vmin = QDoubleSpinBox()
        self._spin_vmin.setRange(1.0, 10000.0)
        self._spin_vmin.setValue(100.0)
        self._spin_vmin.setSuffix(" m/s")
        proc_form.addRow("Vel Min:", self._spin_vmin)

        self._spin_vmax = QDoubleSpinBox()
        self._spin_vmax.setRange(10.0, 50000.0)
        self._spin_vmax.setValue(1500.0)
        self._spin_vmax.setSuffix(" m/s")
        proc_form.addRow("Vel Max:", self._spin_vmax)

        self._btn_advanced = QPushButton("⚙ Advanced Settings…")
        proc_form.addRow(self._btn_advanced)

        left_layout.addWidget(grp_proc)

        # Output group
        grp_out = QGroupBox("Output")
        out_layout = QVBoxLayout(grp_out)

        dir_row = QHBoxLayout()
        self._lbl_outdir = QLabel("(not set)")
        self._lbl_outdir.setStyleSheet("color: #666;")
        self._btn_browse = QPushButton("Browse…")
        dir_row.addWidget(QLabel("Directory:"))
        dir_row.addWidget(self._lbl_outdir, 1)
        dir_row.addWidget(self._btn_browse)
        out_layout.addLayout(dir_row)

        self._chk_csv = QCheckBox("CSV")
        self._chk_csv.setChecked(True)
        self._chk_npz = QCheckBox("NPZ")
        self._chk_npz.setChecked(True)
        self._chk_images = QCheckBox("Images (PNG)")
        self._chk_images.setChecked(True)
        self._chk_combined = QCheckBox("Combined per midpoint")
        self._chk_combined.setChecked(True)
        self._chk_summary = QCheckBox("Summary files")
        self._chk_summary.setChecked(True)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(self._chk_csv)
        fmt_row.addWidget(self._chk_npz)
        fmt_row.addWidget(self._chk_images)
        out_layout.addLayout(fmt_row)
        out_layout.addWidget(self._chk_combined)
        out_layout.addWidget(self._chk_summary)

        left_layout.addWidget(grp_out)

        # Execution group
        grp_exec = QGroupBox("Execution")
        exec_form = QFormLayout(grp_exec)

        self._chk_parallel = QCheckBox("Parallel processing")
        exec_form.addRow(self._chk_parallel)

        self._combo_workers = QComboBox()
        self._combo_workers.addItems(["auto", "1", "2", "4", "8", "16"])
        exec_form.addRow("Workers:", self._combo_workers)

        left_layout.addWidget(grp_exec)

        # Action buttons
        self._btn_run = QPushButton("▶  Run Workflow")
        self._btn_run.setStyleSheet(
            "QPushButton { background: #1f77b4; color: white; font-weight: bold; "
            "font-size: 13px; padding: 10px; border-radius: 4px; }"
            "QPushButton:hover { background: #1a6699; }"
            "QPushButton:disabled { background: #aaa; }"
        )
        left_layout.addWidget(self._btn_run)

        btn_row = QHBoxLayout()
        self._btn_save_config = QPushButton("Save Config JSON")
        self._btn_open_dir = QPushButton("Open Output Dir")
        self._btn_open_dir.setEnabled(False)
        btn_row.addWidget(self._btn_save_config)
        btn_row.addWidget(self._btn_open_dir)
        left_layout.addLayout(btn_row)

        left_layout.addStretch()
        left_scroll.setWidget(left)

        # ── Right panel (log + progress + results) ────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(4, 4, 4, 4)

        # Log
        self._log_edit = QTextEdit()
        self._log_edit.setReadOnly(True)
        self._log_edit.setStyleSheet(
            "QTextEdit { font-family: 'Consolas', 'Courier New', monospace; "
            "font-size: 11px; background: #fafafa; }"
        )
        right_layout.addWidget(self._log_edit, stretch=3)

        # Progress bar
        prog_frame = QWidget()
        prog_layout = QVBoxLayout(prog_frame)
        prog_layout.setContentsMargins(0, 4, 0, 4)
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        prog_layout.addWidget(self._progress)
        self._lbl_progress = QLabel("Ready")
        self._lbl_progress.setStyleSheet("color: #666;")
        prog_layout.addWidget(self._lbl_progress)
        right_layout.addWidget(prog_frame)

        # Results summary
        self._lbl_results = QLabel("")
        self._lbl_results.setWordWrap(True)
        self._lbl_results.setStyleSheet(
            "QLabel { background: #e8f5e9; padding: 10px; border-radius: 4px; "
            "font-size: 12px; }"
        )
        self._lbl_results.setVisible(False)
        right_layout.addWidget(self._lbl_results)

        splitter.addWidget(left_scroll)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._btn_browse.clicked.connect(self._on_browse_output)
        self._btn_run.clicked.connect(self._on_run)
        self._btn_save_config.clicked.connect(self.save_config_requested.emit)
        self._btn_open_dir.clicked.connect(self._on_open_output)
        self._btn_advanced.clicked.connect(self._on_advanced)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_processing_params(self) -> ProcessingParams:
        """Return current processing parameters (including advanced)."""
        base = ProcessingParams(
            method=self._combo_method.currentText(),
            freq_min=self._spin_fmin.value(),
            freq_max=self._spin_fmax.value(),
            vel_min=self._spin_vmin.value(),
            vel_max=self._spin_vmax.value(),
        )
        # Merge advanced settings if they were configured
        adv = getattr(self, "_advanced_params", None)
        if adv is not None:
            base.grid_n = adv.grid_n
            base.tol = adv.tol
            base.vspace = adv.vspace
            base.source_type = adv.source_type
            base.cylindrical = adv.cylindrical
            base.start_time = adv.start_time
            base.end_time = adv.end_time
            base.downsample = adv.downsample
            base.down_factor = adv.down_factor
            base.numf = adv.numf
            base.power_threshold = adv.power_threshold
        return base

    def get_output_config(self) -> OutputConfig:
        """Return current output configuration."""
        return OutputConfig(
            directory=self._lbl_outdir.text() if self._lbl_outdir.text() != "(not set)" else "./output_2d/",
            export_csv=self._chk_csv.isChecked(),
            export_npz=self._chk_npz.isChecked(),
            export_images=self._chk_images.isChecked(),
            combined_csv_per_midpoint=self._chk_combined.isChecked(),
            combined_npz_per_midpoint=self._chk_combined.isChecked(),
            generate_summary=self._chk_summary.isChecked(),
            parallel=self._chk_parallel.isChecked(),
        )

    def get_parallel_settings(self) -> tuple[bool, int | None]:
        """Return (parallel, max_workers)."""
        parallel = self._chk_parallel.isChecked()
        val = self._combo_workers.currentText()
        workers = None if val == "auto" else int(val)
        return parallel, workers

    def log(self, message: str) -> None:
        """Append a timestamped message to the log."""
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_edit.append(f"[{ts}] {message}")
        # Auto-scroll to bottom
        sb = self._log_edit.verticalScrollBar()
        sb.setValue(sb.maximum())

    def set_progress(self, value: int, message: str = "") -> None:
        """Update the progress bar and status label."""
        self._progress.setValue(value)
        if message:
            self._lbl_progress.setText(message)

    def set_running(self, running: bool) -> None:
        """Enable/disable the Run button."""
        self._btn_run.setEnabled(not running)
        if running:
            self._lbl_results.setVisible(False)

    def show_results(self, summary: Dict[str, Any]) -> None:
        """Display the workflow results summary."""
        status = summary.get("status", "unknown")
        if status == "success":
            nr = summary.get("n_results", 0)
            nm = summary.get("n_midpoints", 0)
            mid = summary.get("midpoints", [])
            coverage = f"{mid[0]:.1f} → {mid[-1]:.1f} m" if mid else "—"
            self._lbl_results.setText(
                f"<b>✓ Complete!</b><br>"
                f"<b>{nr}</b> dispersion curves at <b>{nm}</b> midpoints<br>"
                f"Coverage: {coverage}<br>"
                f"Method: {summary.get('method', '?').upper()}"
            )
            self._lbl_results.setStyleSheet(
                "QLabel { background: #e8f5e9; padding: 10px; border-radius: 4px; }"
            )
            self._btn_open_dir.setEnabled(True)
        else:
            err = summary.get("error", "Unknown error")
            self._lbl_results.setText(f"<b>✗ Error:</b> {err}")
            self._lbl_results.setStyleSheet(
                "QLabel { background: #fce4e4; padding: 10px; border-radius: 4px; }"
            )
        self._lbl_results.setVisible(True)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_browse_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self._lbl_outdir.setText(folder)

    def _on_run(self) -> None:
        out_dir = self._lbl_outdir.text()
        if out_dir == "(not set)":
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Output", "Select an output directory first.")
            return

        parallel, workers = self.get_parallel_settings()
        self.run_requested.emit({
            "output_dir": out_dir,
            "parallel": parallel,
            "max_workers": workers,
        })

    def _on_open_output(self) -> None:
        out_dir = self._lbl_outdir.text()
        if out_dir and out_dir != "(not set)" and os.path.isdir(out_dir):
            os.startfile(out_dir)

    def _on_advanced(self) -> None:
        """Open the advanced settings dialog."""
        from sw_transform.masw2d.app.gui.dialogs.advanced_dialog import AdvancedDialog

        params = self.get_processing_params()
        dlg = AdvancedDialog(params, parent=self)
        if dlg.exec():
            self._advanced_params = dlg.get_params()
