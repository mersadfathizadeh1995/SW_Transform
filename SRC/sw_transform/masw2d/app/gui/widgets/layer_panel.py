"""Collapsible layer panel for toggling visibility of receivers and sources.

Sits on the right side of the canvas area.  Starts collapsed and can be
expanded via a toggle button.  Each item shows filename + position.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Set, Tuple

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class LayerPanel(QWidget):
    """Collapsible layer visibility panel.

    Signals
    -------
    receivers_changed(set or None)
        Emitted when visible receiver indices change (None = all visible).
    sources_changed(set or None)
        Emitted when visible source indices change (None = all visible).
    """

    receivers_changed = pyqtSignal(object)
    sources_changed = pyqtSignal(object)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._collapsed = True
        self._receiver_items: List[QTreeWidgetItem] = []
        self._source_items: List[QTreeWidgetItem] = []
        self._build_ui()
        self._connect_signals()
        self._apply_collapsed_state()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toggle button (always visible)
        self._btn_toggle = QPushButton("\u00ab")
        self._btn_toggle.setFixedWidth(20)
        self._btn_toggle.setToolTip("Toggle layer panel")
        self._btn_toggle.setStyleSheet(
            "QPushButton { background: #e0e0e0; border: none; "
            "font-weight: bold; font-size: 12px; }"
            "QPushButton:hover { background: #c8c8c8; }"
        )

        # Tree widget (hidden when collapsed)
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setMinimumWidth(180)
        self._tree.setMaximumWidth(280)

        # Receivers group
        self._grp_receivers = QTreeWidgetItem(self._tree, ["Receivers"])
        self._grp_receivers.setFlags(
            self._grp_receivers.flags() | Qt.ItemFlag.ItemIsUserCheckable
        )
        self._grp_receivers.setCheckState(0, Qt.CheckState.Checked)
        self._grp_receivers.setExpanded(True)

        # Sources group
        self._grp_sources = QTreeWidgetItem(self._tree, ["Sources"])
        self._grp_sources.setFlags(
            self._grp_sources.flags() | Qt.ItemFlag.ItemIsUserCheckable
        )
        self._grp_sources.setCheckState(0, Qt.CheckState.Checked)
        self._grp_sources.setExpanded(True)

        layout.addWidget(self._btn_toggle)
        layout.addWidget(self._tree)

    def _connect_signals(self) -> None:
        self._btn_toggle.clicked.connect(self._toggle)
        self._tree.itemChanged.connect(self._on_item_changed)

    def _apply_collapsed_state(self) -> None:
        self._tree.setVisible(not self._collapsed)
        self._btn_toggle.setText("\u00bb" if self._collapsed else "\u00ab")

    def _toggle(self) -> None:
        self._collapsed = not self._collapsed
        self._apply_collapsed_state()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_receivers(
        self,
        items: List[Tuple[str, float]],
    ) -> None:
        """Populate the Receivers group.

        Parameters
        ----------
        items : list of (filename, position)
            One entry per geophone channel.
        """
        self._tree.blockSignals(True)
        # Clear old children
        while self._grp_receivers.childCount():
            self._grp_receivers.removeChild(self._grp_receivers.child(0))
        self._receiver_items.clear()

        for idx, (fname, pos) in enumerate(items):
            basename = os.path.basename(fname) if fname else f"Ch {idx}"
            label = f"{basename} ({pos:.1f} m)"
            child = QTreeWidgetItem(self._grp_receivers, [label])
            child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            child.setCheckState(0, Qt.CheckState.Checked)
            child.setData(0, Qt.ItemDataRole.UserRole, idx)
            self._receiver_items.append(child)

        self._grp_receivers.setCheckState(0, Qt.CheckState.Checked)
        self._tree.blockSignals(False)

    def set_sources(
        self,
        items: List[Tuple[str, float]],
    ) -> None:
        """Populate the Sources group.

        Parameters
        ----------
        items : list of (filename, position)
            One entry per shot.
        """
        self._tree.blockSignals(True)
        while self._grp_sources.childCount():
            self._grp_sources.removeChild(self._grp_sources.child(0))
        self._source_items.clear()

        for idx, (fname, pos) in enumerate(items):
            basename = os.path.basename(fname) if fname else f"Shot {idx + 1}"
            label = f"{basename} ({pos:+.1f} m)"
            child = QTreeWidgetItem(self._grp_sources, [label])
            child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            child.setCheckState(0, Qt.CheckState.Checked)
            child.setData(0, Qt.ItemDataRole.UserRole, idx)
            self._source_items.append(child)

        self._grp_sources.setCheckState(0, Qt.CheckState.Checked)
        self._tree.blockSignals(False)

    def get_visible_receivers(self) -> Optional[Set[int]]:
        """Return set of checked receiver indices, or None if all checked."""
        checked = set()
        for item in self._receiver_items:
            if item.checkState(0) == Qt.CheckState.Checked:
                checked.add(item.data(0, Qt.ItemDataRole.UserRole))
        if len(checked) == len(self._receiver_items):
            return None
        return checked

    def get_visible_sources(self) -> Optional[Set[int]]:
        """Return set of checked source indices, or None if all checked."""
        checked = set()
        for item in self._source_items:
            if item.checkState(0) == Qt.CheckState.Checked:
                checked.add(item.data(0, Qt.ItemDataRole.UserRole))
        if len(checked) == len(self._source_items):
            return None
        return checked

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle checkbox changes — propagate parent↔child states."""
        self._tree.blockSignals(True)

        # Parent group toggled → set all children
        if item is self._grp_receivers:
            state = item.checkState(0)
            for child in self._receiver_items:
                child.setCheckState(0, state)
        elif item is self._grp_sources:
            state = item.checkState(0)
            for child in self._source_items:
                child.setCheckState(0, state)
        else:
            # Child toggled → update parent tri-state
            parent = item.parent()
            if parent is not None:
                children = []
                for i in range(parent.childCount()):
                    children.append(parent.child(i).checkState(0))
                if all(c == Qt.CheckState.Checked for c in children):
                    parent.setCheckState(0, Qt.CheckState.Checked)
                elif all(c == Qt.CheckState.Unchecked for c in children):
                    parent.setCheckState(0, Qt.CheckState.Unchecked)
                else:
                    parent.setCheckState(0, Qt.CheckState.PartiallyChecked)

        self._tree.blockSignals(False)

        # Emit signals
        self.receivers_changed.emit(self.get_visible_receivers())
        self.sources_changed.emit(self.get_visible_sources())
