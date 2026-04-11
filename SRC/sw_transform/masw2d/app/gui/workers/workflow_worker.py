"""QThread wrapper for running the MASW 2D workflow in the background.

Emits progress and completion signals so the GUI stays responsive.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from sw_transform.masw2d.app.api import processing_api


class WorkflowWorker(QThread):
    """Run :func:`processing_api.run_masw2d` on a background thread.

    Signals
    -------
    progress(int, int, str)
        ``(current, total, message)`` progress updates.
    finished(dict)
        Workflow summary dict on completion.
    error(str)
        Error message if the workflow fails.
    """

    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(
        self,
        config: Dict[str, Any],
        output_dir: str,
        parallel: bool = False,
        max_workers: Optional[int] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._config = config
        self._output_dir = output_dir
        self._parallel = parallel
        self._max_workers = max_workers

    def run(self) -> None:
        """Execute the workflow (called by QThread.start())."""
        try:
            def _progress_cb(current: int, total: int, message: str) -> None:
                self.progress.emit(current, total, message)

            result = processing_api.run_masw2d(
                config=self._config,
                output_dir=self._output_dir,
                parallel=self._parallel,
                max_workers=self._max_workers,
                progress_callback=_progress_cb,
            )
            self.finished.emit(result)
        except Exception as exc:
            import traceback
            self.error.emit(f"{exc}\n\n{traceback.format_exc()}")
