"""Clickable assignment table — sub-array ↔ shot pairings.

Read-only table showing the assignment plan.  Clicking a row emits
a signal so the canvas can highlight that particular sub-array + source.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class AssignmentRow:
    """One row in the assignment table."""

    __slots__ = (
        "config_name", "channels", "midpoint", "shot_index",
        "shot_file", "source_offset", "direction",
    )

    def __init__(
        self,
        config_name: str = "",
        channels: str = "",
        midpoint: float = 0.0,
        shot_index: int = 0,
        shot_file: str = "",
        source_offset: float = 0.0,
        direction: str = "",
    ):
        self.config_name = config_name
        self.channels = channels
        self.midpoint = midpoint
        self.shot_index = shot_index
        self.shot_file = shot_file
        self.source_offset = source_offset
        self.direction = direction


class AssignmentTable(QWidget):
    """Read-only table of sub-array ↔ shot assignments.

    Signals
    -------
    row_selected(int)
        Emitted when the user clicks a row.  The int is the row index
        in the internal ``_rows`` list.
    """

    row_selected = pyqtSignal(int)

    _COL_CONFIG = 0
    _COL_CHANNELS = 1
    _COL_MIDPOINT = 2
    _COL_SHOT = 3
    _COL_OFFSET = 4
    _COL_DIR = 5
    _HEADERS = ["Config", "Channels", "Mid (m)", "Shot #", "Offset (m)", "Dir"]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._rows: List[AssignmentRow] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget(0, len(self._HEADERS))
        self._table.setHorizontalHeaderLabels(self._HEADERS)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._table)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_rows(self, rows: List[AssignmentRow]) -> None:
        """Replace all rows."""
        self._rows = list(rows)
        self._table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self._table.setItem(i, self._COL_CONFIG, QTableWidgetItem(r.config_name))
            self._table.setItem(i, self._COL_CHANNELS, QTableWidgetItem(r.channels))
            self._table.setItem(i, self._COL_MIDPOINT, QTableWidgetItem(f"{r.midpoint:.1f}"))
            self._table.setItem(i, self._COL_SHOT, QTableWidgetItem(str(r.shot_index + 1)))
            self._table.setItem(i, self._COL_OFFSET, QTableWidgetItem(f"{r.source_offset:.1f}"))
            self._table.setItem(i, self._COL_DIR, QTableWidgetItem(r.direction))

    def clear(self) -> None:
        """Remove all rows."""
        self._rows.clear()
        self._table.setRowCount(0)

    def row_count(self) -> int:
        """Number of rows."""
        return len(self._rows)

    def get_row(self, index: int) -> Optional[AssignmentRow]:
        """Return a row by index, or None."""
        if 0 <= index < len(self._rows):
            return self._rows[index]
        return None

    def selected_row_index(self) -> int:
        """Index of the selected row, or -1."""
        sel = self._table.selectionModel().selectedRows()
        return sel[0].row() if sel else -1

    def select_row(self, index: int) -> None:
        """Programmatically select a row."""
        if 0 <= index < self._table.rowCount():
            self._table.selectRow(index)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_selection_changed(self) -> None:
        idx = self.selected_row_index()
        if idx >= 0:
            self.row_selected.emit(idx)
