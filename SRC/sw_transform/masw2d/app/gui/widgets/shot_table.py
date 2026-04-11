"""Editable shot-file table widget.

Columns: ``#``, ``File``, ``Source Position (m)``.
Emits signals when rows are added/removed/edited or a row is clicked.
"""

from __future__ import annotations

import os
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sw_transform.masw2d.app.api.models import ShotDef


class ShotTable(QWidget):
    """Editable table of shot files and source positions.

    Signals
    -------
    data_changed()
        Emitted whenever rows are added, removed, or edited.
    row_selected(int)
        Emitted when the user clicks a row (row index).
    """

    data_changed = pyqtSignal()
    row_selected = pyqtSignal(int)

    _COL_NUM = 0
    _COL_FILE = 1
    _COL_POS = 2
    _HEADERS = ["#", "File", "Source Pos (m)"]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._build_ui()
        self._suppress_signals = False

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Buttons
        btn_row = QHBoxLayout()
        self._btn_load = QPushButton("Load Files…")
        self._btn_load.clicked.connect(self._on_load_files)
        btn_row.addWidget(self._btn_load)

        self._btn_remove = QPushButton("Remove Selected")
        self._btn_remove.clicked.connect(self._on_remove_selected)
        btn_row.addWidget(self._btn_remove)

        self._btn_clear = QPushButton("Clear All")
        self._btn_clear.clicked.connect(self._on_clear)
        btn_row.addWidget(self._btn_clear)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Table
        self._table = QTableWidget(0, len(self._HEADERS))
        self._table.setHorizontalHeaderLabels(self._HEADERS)
        self._table.horizontalHeader().setSectionResizeMode(
            self._COL_FILE, QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            self._COL_NUM, QHeaderView.ResizeMode.ResizeToContents
        )
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self._table.cellChanged.connect(self._on_cell_changed)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._table)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_shots(self, shots: List[ShotDef]) -> None:
        """Append shots to the table."""
        self._suppress_signals = True
        for shot in shots:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._set_row(row, shot)
        self._renumber()
        self._suppress_signals = False
        self.data_changed.emit()

    def set_shots(self, shots: List[ShotDef]) -> None:
        """Replace all rows."""
        self._suppress_signals = True
        self._table.setRowCount(0)
        for i, shot in enumerate(shots):
            self._table.insertRow(i)
            self._set_row(i, shot)
        self._renumber()
        self._suppress_signals = False
        self.data_changed.emit()

    def get_shots(self) -> List[ShotDef]:
        """Read current table contents as a list of ShotDef."""
        shots: List[ShotDef] = []
        for row in range(self._table.rowCount()):
            file_item = self._table.item(row, self._COL_FILE)
            pos_item = self._table.item(row, self._COL_POS)
            filepath = file_item.data(Qt.ItemDataRole.UserRole) if file_item else ""
            try:
                pos = float(pos_item.text()) if pos_item else 0.0
            except ValueError:
                pos = 0.0
            shots.append(ShotDef(file=filepath or "", source_position=pos))
        return shots

    def row_count(self) -> int:
        """Number of rows."""
        return self._table.rowCount()

    def selected_row(self) -> int:
        """Index of the first selected row, or -1."""
        sel = self._table.selectionModel().selectedRows()
        return sel[0].row() if sel else -1

    def add_files(self, filepaths: List[str], default_position: float = 0.0) -> None:
        """Add files as new rows with a default position."""
        shots = [
            ShotDef(file=fp, source_position=default_position)
            for fp in filepaths
        ]
        self.add_shots(shots)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _set_row(self, row: int, shot: ShotDef) -> None:
        """Populate a single row."""
        # Number (read-only)
        num_item = QTableWidgetItem(str(row + 1))
        num_item.setFlags(num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._table.setItem(row, self._COL_NUM, num_item)

        # File (display basename, store full path in UserRole)
        file_item = QTableWidgetItem(os.path.basename(shot.file) if shot.file else "")
        file_item.setData(Qt.ItemDataRole.UserRole, shot.file)
        file_item.setFlags(file_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        file_item.setToolTip(shot.file)
        self._table.setItem(row, self._COL_FILE, file_item)

        # Position (editable)
        pos_item = QTableWidgetItem(f"{shot.source_position:.1f}")
        self._table.setItem(row, self._COL_POS, pos_item)

    def _renumber(self) -> None:
        """Update the # column after adds/removes."""
        for row in range(self._table.rowCount()):
            item = self._table.item(row, self._COL_NUM)
            if item:
                item.setText(str(row + 1))

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_load_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Shot Files",
            "",
            "All supported (*.dat *.mat);;SEG-2 (*.dat);;Vibrosis MAT (*.mat);;All (*.*)",
        )
        if files:
            self.add_files(files)

    def _on_remove_selected(self) -> None:
        rows = sorted(
            {idx.row() for idx in self._table.selectionModel().selectedRows()},
            reverse=True,
        )
        if not rows:
            return
        self._suppress_signals = True
        for r in rows:
            self._table.removeRow(r)
        self._renumber()
        self._suppress_signals = False
        self.data_changed.emit()

    def _on_clear(self) -> None:
        self._suppress_signals = True
        self._table.setRowCount(0)
        self._suppress_signals = False
        self.data_changed.emit()

    def _on_cell_changed(self, row: int, col: int) -> None:
        if not self._suppress_signals:
            self.data_changed.emit()

    def _on_selection_changed(self) -> None:
        row = self.selected_row()
        if row >= 0:
            self.row_selected.emit(row)
