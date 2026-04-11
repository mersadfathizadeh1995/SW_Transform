"""Main window for the MASW 2D Profiler application.

4-tab wizard with Next/Back navigation, status bar, and menu bar.
Each tab is a self-contained panel; the main window wires them together
via signals and passes data between tabs when the user navigates.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtGui import QAction

from sw_transform.masw2d.app.api import processing_api, export_api
from sw_transform.masw2d.app.gui.tabs.survey_tab import SurveyTab
from sw_transform.masw2d.app.gui.tabs.subarray_tab import SubArrayTab
from sw_transform.masw2d.app.gui.tabs.preview_tab import PreviewTab
from sw_transform.masw2d.app.gui.tabs.process_tab import ProcessTab
from sw_transform.masw2d.app.gui.workers.workflow_worker import WorkflowWorker

logger = logging.getLogger(__name__)

_TAB_SURVEY = 0
_TAB_SUBARRAY = 1
_TAB_PREVIEW = 2
_TAB_PROCESS = 3


class MainWindow(QMainWindow):
    """MASW 2D Profiler main window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MASW 2D Profiler — SW_Transform")
        self.setMinimumSize(1100, 750)

        self._worker: Optional[WorkflowWorker] = None

        self._build_menu()
        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _build_menu(self) -> None:
        menu = self.menuBar()

        file_menu = menu.addMenu("&File")

        act_load = QAction("Load Config JSON…", self)
        act_load.triggered.connect(self._on_load_config)
        file_menu.addAction(act_load)

        act_save = QAction("Save Config JSON…", self)
        act_save.triggered.connect(self._on_save_config)
        file_menu.addAction(act_save)

        file_menu.addSeparator()

        act_exit = QAction("Exit", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        help_menu = menu.addMenu("&Help")
        act_about = QAction("About", self)
        act_about.triggered.connect(self._on_about)
        help_menu.addAction(act_about)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)

        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.North)

        self._tab_survey = SurveyTab()
        self._tab_subarray = SubArrayTab()
        self._tab_preview = PreviewTab()
        self._tab_process = ProcessTab()

        self._tabs.addTab(self._tab_survey, "① Survey && Shots")
        self._tabs.addTab(self._tab_subarray, "② Sub-Arrays")
        self._tabs.addTab(self._tab_preview, "③ Review && Preview")
        self._tabs.addTab(self._tab_process, "④ Process")

        main_layout.addWidget(self._tabs, stretch=1)

        # Navigation bar
        nav_bar = QHBoxLayout()
        nav_bar.addStretch()

        self._btn_back = QPushButton("◀ Back")
        self._btn_back.setMinimumWidth(100)
        nav_bar.addWidget(self._btn_back)

        self._btn_next = QPushButton("Next ▶")
        self._btn_next.setMinimumWidth(100)
        self._btn_next.setStyleSheet(
            "QPushButton { background: #1f77b4; color: white; font-weight: bold; }"
            "QPushButton:hover { background: #1a6699; }"
        )
        nav_bar.addWidget(self._btn_next)

        main_layout.addLayout(nav_bar)

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._update_status()

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._btn_back.clicked.connect(self._on_back)
        self._btn_next.clicked.connect(self._on_next)
        self._tabs.currentChanged.connect(self._on_tab_changed)

        self._tab_survey.survey_changed.connect(self._update_status)
        self._tab_subarray.config_changed.connect(self._update_status)

        self._tab_process.run_requested.connect(self._on_run_workflow)
        self._tab_process.save_config_requested.connect(self._on_save_config)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _on_back(self) -> None:
        idx = self._tabs.currentIndex()
        if idx > 0:
            self._tabs.setCurrentIndex(idx - 1)

    def _on_next(self) -> None:
        idx = self._tabs.currentIndex()

        # Validate current tab before advancing
        if idx == _TAB_SURVEY:
            ok, msg = self._tab_survey.validate()
            if not ok:
                QMessageBox.warning(self, "Validation", msg)
                return
        elif idx == _TAB_SUBARRAY:
            ok, msg = self._tab_subarray.validate()
            if not ok:
                QMessageBox.warning(self, "Validation", msg)
                return

        if idx < self._tabs.count() - 1:
            self._tabs.setCurrentIndex(idx + 1)

    def _on_tab_changed(self, index: int) -> None:
        """Sync data between tabs when navigating."""
        # Update Back/Next button states
        self._btn_back.setEnabled(index > 0)
        self._btn_next.setEnabled(index < self._tabs.count() - 1)

        if index == _TAB_SUBARRAY:
            # Push survey + shots into sub-array tab
            self._tab_subarray.set_survey_and_shots(
                self._tab_survey.get_survey(),
                self._tab_survey.get_shots(),
            )

        elif index == _TAB_PREVIEW:
            # Push everything into preview tab
            self._tab_preview.set_data(
                survey=self._tab_survey.get_survey(),
                shots=self._tab_survey.get_shots(),
                subarrays=self._tab_subarray.get_subarrays(),
                plan=self._tab_subarray.get_plan(),
            )

        self._update_status()

    # ------------------------------------------------------------------
    # Workflow execution
    # ------------------------------------------------------------------

    def _on_run_workflow(self, params: Dict[str, Any]) -> None:
        """Build config and start the workflow on a background thread."""
        survey = self._tab_survey.get_survey()
        shots = self._tab_survey.get_shots()
        specs = self._tab_subarray.get_specs()
        proc_params = self._tab_process.get_processing_params()
        out_config = self._tab_process.get_output_config()
        assignment = self._tab_subarray.get_assignment_config()

        if not shots or not specs:
            QMessageBox.warning(
                self, "Missing Data",
                "Complete the Survey and Sub-Array tabs before processing.",
            )
            return

        config = processing_api.build_workflow_config(
            survey, shots, specs, proc_params, out_config, assignment,
        )

        output_dir = params["output_dir"]
        parallel = params.get("parallel", False)
        max_workers = params.get("max_workers")

        self._tab_process.set_running(True)
        self._tab_process.log(f"Starting MASW 2D workflow…")
        self._tab_process.log(f"  Method: {proc_params.method.upper()}")
        self._tab_process.log(f"  Array: {survey.n_channels} ch @ {survey.dx} m")
        self._tab_process.log(f"  Shots: {len(shots)}")
        self._tab_process.log(f"  Sub-arrays: {len(specs)} configs")
        self._tab_process.log(f"  Output: {output_dir}")
        self._tab_process.set_progress(0, "Starting…")

        self._worker = WorkflowWorker(
            config=config,
            output_dir=output_dir,
            parallel=parallel,
            max_workers=max_workers,
        )
        self._worker.progress.connect(self._on_worker_progress)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()

    def _on_worker_progress(self, current: int, total: int, message: str) -> None:
        pct = int(current / total * 100) if total > 0 else 0
        self._tab_process.set_progress(pct, message)
        self._tab_process.log(message)

    def _on_worker_finished(self, result: Dict[str, Any]) -> None:
        self._tab_process.set_running(False)
        self._tab_process.set_progress(100, "Complete!")
        self._tab_process.show_results(result)

        nr = result.get("n_results", 0)
        nm = result.get("n_midpoints", 0)
        self._tab_process.log(f"Complete: {nr} curves at {nm} midpoints.")
        self._status.showMessage(f"Workflow complete: {nr} curves at {nm} midpoints")
        self._worker = None

    def _on_worker_error(self, message: str) -> None:
        self._tab_process.set_running(False)
        self._tab_process.set_progress(0, "Error")
        self._tab_process.log(f"ERROR: {message}")
        self._tab_process.show_results({"status": "error", "error": message[:200]})
        QMessageBox.critical(self, "Workflow Error", message[:500])
        self._worker = None

    # ------------------------------------------------------------------
    # Config save / load
    # ------------------------------------------------------------------

    def _on_save_config(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Config JSON", "", "JSON (*.json);;All (*.*)",
        )
        if not path:
            return
        try:
            export_api.save_config_json(
                filepath=path,
                survey=self._tab_survey.get_survey(),
                shots=self._tab_survey.get_shots(),
                specs=self._tab_subarray.get_specs(),
                params=self._tab_process.get_processing_params(),
                output=self._tab_process.get_output_config(),
                assignment=self._tab_subarray.get_assignment_config(),
            )
            self._status.showMessage(f"Config saved: {path}")
        except Exception as exc:
            QMessageBox.warning(self, "Save Error", str(exc))

    def _on_load_config(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Config JSON", "", "JSON (*.json);;All (*.*)",
        )
        if not path:
            return
        try:
            raw = export_api.load_config_json(path)
            models = export_api.config_to_models(raw)

            # Populate Tab ① (survey + shots)
            survey = models["survey"]
            self._tab_survey._spin_n_channels.setValue(survey.n_channels)
            self._tab_survey._spin_dx.setValue(survey.dx)
            self._tab_survey._spin_first.setValue(survey.first_position)
            self._tab_survey._shot_table.set_shots(models["shots"])

            self._status.showMessage(f"Config loaded: {Path(path).name}")
            self._tabs.setCurrentIndex(_TAB_SURVEY)
        except Exception as exc:
            QMessageBox.warning(self, "Load Error", str(exc))

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------

    def _update_status(self) -> None:
        survey = self._tab_survey.get_survey()
        shots = self._tab_survey.get_shots()
        n_sa = len(self._tab_subarray.get_subarrays())
        self._status.showMessage(
            f"  {survey.n_channels} ch @ {survey.dx} m  │  "
            f"{len(shots)} shots  │  "
            f"{n_sa} sub-arrays"
        )

    # ------------------------------------------------------------------
    # Help
    # ------------------------------------------------------------------

    def _on_about(self) -> None:
        QMessageBox.about(
            self,
            "About MASW 2D Profiler",
            "<b>MASW 2D Profiler</b> v0.1.0<br><br>"
            "Multi-channel Analysis of Surface Waves — 2D Profiling<br>"
            "Part of the SW_Transform package.<br><br>"
            "PyQt6 + pyqtgraph GUI with tab-wizard workflow.",
        )
