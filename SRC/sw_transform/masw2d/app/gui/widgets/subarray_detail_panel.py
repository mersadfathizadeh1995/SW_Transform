"""Collapsible detail panel for a selected sub-array in Tab 2.

Shows two tree groups:
- **Receivers**: channel indices + positions belonging to the sub-array.
- **Assigned Shots**: source files with offset, direction, and position.

Clicking a shot entry emits ``shot_clicked`` so the parent tab can
highlight that source on the canvas and load its waterfall preview.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional, Set

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


# ── Data carriers ─────────────────────────────────────────────────

@dataclass
class ReceiverEntry:
    """One receiver channel in a sub-array."""

    channel_index: int
    position: float


@dataclass
class ShotEntry:
    """One assigned shot for a sub-array."""

    shot_index: int
    file: str
    source_position: float
    source_offset: float
    direction: str
    is_checked: bool = True


# ── Colours ───────────────────────────────────────────────────────

_CLR_FWD = QColor("#e8f5e9")   # light green
_CLR_REV = QColor("#e3f2fd")   # light blue
_CLR_SEL = QColor("#fff9c4")   # light yellow — selected shot

# ── Role constants ────────────────────────────────────────────────

_ROLE_TYPE = Qt.ItemDataRole.UserRole           # "receiver" | "shot"
_ROLE_INDEX = Qt.ItemDataRole.UserRole + 1      # channel_index or shot_index


class SubArrayDetailPanel(QWidget):
    """Collapsible right-side panel showing detail for a selected sub-array.

    Signals
    -------
    shot_clicked(int)
        Emitted with the shot_index when a shot entry is clicked.
    receivers_visibility_changed(object)
        Emitted with set of visible channel indices (or None = all).
    """

    shot_clicked = pyqtSignal(int)
    receivers_visibility_changed = pyqtSignal(object)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._collapsed = True
        self._receiver_items: List[QTreeWidgetItem] = []
        self._shot_items: List[QTreeWidgetItem] = []
        self._selected_shot_idx: Optional[int] = None
        self._build_ui()
        self._connect_signals()
        self._apply_collapsed_state()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toggle button (always visible)
        self._btn_toggle = QPushButton("\u00bb")
        self._btn_toggle.setFixedWidth(20)
        self._btn_toggle.setToolTip("Toggle sub-array detail panel")
        self._btn_toggle.setStyleSheet(
            "QPushButton { background: #e0e0e0; border: none; "
            "font-weight: bold; font-size: 12px; }"
            "QPushButton:hover { background: #c8c8c8; }"
        )

        # Content area
        self._content = QWidget()
        content_layout = QVBoxLayout(self._content)
        content_layout.setContentsMargins(2, 2, 2, 2)
        content_layout.setSpacing(2)

        # Tree widget
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Item", "Offset (m)", "Direction"])
        self._tree.setColumnCount(3)
        self._tree.setAlternatingRowColors(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setSelectionMode(
            QTreeWidget.SelectionMode.SingleSelection,
        )
        self._tree.setMinimumWidth(200)
        self._tree.setMaximumWidth(400)

        header = self._tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2):
            header.setSectionResizeMode(
                col, QHeaderView.ResizeMode.ResizeToContents,
            )

        # Group items
        self._grp_receivers = QTreeWidgetItem(self._tree, ["Receivers"])
        self._grp_receivers.setFlags(
            self._grp_receivers.flags() | Qt.ItemFlag.ItemIsUserCheckable
        )
        self._grp_receivers.setCheckState(0, Qt.CheckState.Checked)
        self._grp_receivers.setExpanded(True)

        self._grp_shots = QTreeWidgetItem(self._tree, ["Assigned Shots"])
        self._grp_shots.setExpanded(True)

        content_layout.addWidget(self._tree)

        layout.addWidget(self._btn_toggle)
        layout.addWidget(self._content)

    def _connect_signals(self) -> None:
        self._btn_toggle.clicked.connect(self._toggle)
        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.itemChanged.connect(self._on_item_changed)

    def _apply_collapsed_state(self) -> None:
        self._content.setVisible(not self._collapsed)
        self._btn_toggle.setText("\u00ab" if not self._collapsed else "\u00bb")

    def _toggle(self) -> None:
        self._collapsed = not self._collapsed
        self._apply_collapsed_state()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_receivers(self, entries: List[ReceiverEntry]) -> None:
        """Populate the Receivers group for a selected sub-array.

        Parameters
        ----------
        entries : list of ReceiverEntry
            One per channel in the sub-array.
        """
        self._tree.blockSignals(True)
        while self._grp_receivers.childCount():
            self._grp_receivers.removeChild(self._grp_receivers.child(0))
        self._receiver_items.clear()

        for entry in entries:
            label = f"Ch {entry.channel_index}  ({entry.position:.1f} m)"
            child = QTreeWidgetItem(self._grp_receivers, [label, "", ""])
            child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            child.setCheckState(0, Qt.CheckState.Checked)
            child.setData(0, _ROLE_TYPE, "receiver")
            child.setData(0, _ROLE_INDEX, entry.channel_index)
            self._receiver_items.append(child)

        self._grp_receivers.setCheckState(0, Qt.CheckState.Checked)
        self._grp_receivers.setText(
            0, f"Receivers ({len(entries)})",
        )
        self._tree.blockSignals(False)

    def set_shots(self, entries: List[ShotEntry]) -> None:
        """Populate the Assigned Shots group for a selected sub-array.

        Parameters
        ----------
        entries : list of ShotEntry
            One per assigned shot.
        """
        self._tree.blockSignals(True)
        while self._grp_shots.childCount():
            self._grp_shots.removeChild(self._grp_shots.child(0))
        self._shot_items.clear()
        self._selected_shot_idx = None

        for entry in entries:
            fname = (
                os.path.basename(entry.file)
                if entry.file
                else f"Shot {entry.shot_index + 1}"
            )
            label = f"{fname}  ({entry.source_position:+.1f} m)"
            child = QTreeWidgetItem(self._grp_shots, [
                label,
                f"{entry.source_offset:.1f}",
                entry.direction,
            ])
            child.setData(0, _ROLE_TYPE, "shot")
            child.setData(0, _ROLE_INDEX, entry.shot_index)

            bg = _CLR_FWD if entry.direction == "forward" else _CLR_REV
            for col in range(3):
                child.setBackground(col, QBrush(bg))

            self._shot_items.append(child)

        self._grp_shots.setText(
            0, f"Assigned Shots ({len(entries)})",
        )
        self._tree.blockSignals(False)

    def clear_detail(self) -> None:
        """Clear both groups (no sub-array selected)."""
        self._tree.blockSignals(True)
        while self._grp_receivers.childCount():
            self._grp_receivers.removeChild(self._grp_receivers.child(0))
        while self._grp_shots.childCount():
            self._grp_shots.removeChild(self._grp_shots.child(0))
        self._receiver_items.clear()
        self._shot_items.clear()
        self._selected_shot_idx = None
        self._grp_receivers.setText(0, "Receivers")
        self._grp_shots.setText(0, "Assigned Shots")
        self._tree.blockSignals(False)

    def get_visible_receivers(self) -> Optional[Set[int]]:
        """Return set of checked receiver channel indices, or None if all."""
        checked: Set[int] = set()
        for item in self._receiver_items:
            if item.checkState(0) == Qt.CheckState.Checked:
                checked.add(item.data(0, _ROLE_INDEX))
        if len(checked) == len(self._receiver_items):
            return None
        return checked

    def highlight_shot(self, shot_index: int) -> None:
        """Visually highlight a specific shot entry in the tree."""
        for item in self._shot_items:
            idx = item.data(0, _ROLE_INDEX)
            if idx == shot_index:
                for col in range(3):
                    item.setBackground(col, QBrush(_CLR_SEL))
                self._tree.setCurrentItem(item)
            else:
                # Restore original colour
                direction = item.text(2)
                bg = _CLR_FWD if direction == "forward" else _CLR_REV
                for col in range(3):
                    item.setBackground(col, QBrush(bg))

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        item_type = item.data(0, _ROLE_TYPE)
        if item_type == "shot":
            shot_idx = item.data(0, _ROLE_INDEX)
            self._selected_shot_idx = shot_idx
            self.highlight_shot(shot_idx)
            self.shot_clicked.emit(shot_idx)

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle checkbox changes — propagate parent↔child states."""
        self._tree.blockSignals(True)

        if item is self._grp_receivers:
            state = item.checkState(0)
            for child in self._receiver_items:
                child.setCheckState(0, state)
        elif item.data(0, _ROLE_TYPE) == "receiver":
            # Child toggled → update parent tri-state
            states = [
                self._receiver_items[i].checkState(0)
                for i in range(len(self._receiver_items))
            ]
            if all(s == Qt.CheckState.Checked for s in states):
                self._grp_receivers.setCheckState(0, Qt.CheckState.Checked)
            elif all(s == Qt.CheckState.Unchecked for s in states):
                self._grp_receivers.setCheckState(0, Qt.CheckState.Unchecked)
            else:
                self._grp_receivers.setCheckState(
                    0, Qt.CheckState.PartiallyChecked,
                )

        self._tree.blockSignals(False)
        self.receivers_visibility_changed.emit(self.get_visible_receivers())
