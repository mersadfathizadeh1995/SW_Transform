"""3-level tree widget for shot-to-subarray assignment display.

Structure:
  Config name (e.g. "12ch")
    └─ Sub-array (channels + midpoint)
         └─ Shot–subarray relation (valid/invalid, checkbox)

Clicking items emits signals so the parent tab can highlight on the canvas
and update the assignment config panel context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import QHeaderView, QTreeWidget, QTreeWidgetItem, QWidget


# ── Data carriers ─────────────────────────────────────────────────

@dataclass
class RelationInfo:
    """Minimal data for one shot–subarray relation row."""

    shot_index: int
    shot_file: str
    shot_position: float
    source_offset: float
    direction: str
    is_valid: bool
    quality: float = 0.0


@dataclass
class SubArrayInfo:
    """Minimal data for one sub-array row."""

    config_name: str
    start_channel: int
    end_channel: int
    midpoint: float
    n_channels: int
    relations: List[RelationInfo]


# ── Colours ───────────────────────────────────────────────────────

_CLR_VALID = QColor("#e8f5e9")
_CLR_INVALID = QColor("#ffebee")
_CLR_CONFIG_BG = QColor("#f5f5f5")


# ── Role constants for item data ──────────────────────────────────

ROLE_TYPE = Qt.ItemDataRole.UserRole          # "config" | "subarray" | "relation"
ROLE_CONFIG = Qt.ItemDataRole.UserRole + 1    # config name str
ROLE_SA_IDX = Qt.ItemDataRole.UserRole + 2    # index within config
ROLE_REL = Qt.ItemDataRole.UserRole + 3       # RelationInfo


class AssignmentTree(QWidget):
    """3-level tree showing config → sub-array → shot relations.

    Signals
    -------
    config_selected(str)
        Emitted when a config-level node is clicked.
    subarray_selected(str, int)
        Emitted with (config_name, sa_local_index) on sub-array click.
    relation_toggled(str, int, int, bool)
        Emitted with (config_name, sa_local_idx, shot_index, is_checked).
    """

    config_selected = pyqtSignal(str)
    subarray_selected = pyqtSignal(str, int)
    relation_toggled = pyqtSignal(str, int, int, bool)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QVBoxLayout

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels([
            "Item", "Offset (m)", "Direction", "Quality",
        ])
        self._tree.setColumnCount(4)
        self._tree.setAlternatingRowColors(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)

        header = self._tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._tree)

        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.itemChanged.connect(self._on_item_changed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def populate(self, data: Dict[str, List[SubArrayInfo]]) -> None:
        """Fill tree from structured data.

        Parameters
        ----------
        data : dict[str, list[SubArrayInfo]]
            Keyed by config name, value is list of sub-arrays with relations.
        """
        self._tree.blockSignals(True)
        self._tree.clear()

        for config_name in sorted(data.keys()):
            sa_list = data[config_name]
            n_valid = sum(
                1 for sa in sa_list
                for r in sa.relations if r.is_valid
            )
            n_total = sum(len(sa.relations) for sa in sa_list)

            cfg_item = QTreeWidgetItem([
                f"{config_name}  ({len(sa_list)} sub-arrays, "
                f"{n_valid}/{n_total} valid)",
                "", "", "",
            ])
            cfg_item.setData(0, ROLE_TYPE, "config")
            cfg_item.setData(0, ROLE_CONFIG, config_name)
            cfg_item.setBackground(0, QBrush(_CLR_CONFIG_BG))
            cfg_item.setExpanded(False)
            self._tree.addTopLevelItem(cfg_item)

            for sa_idx, sa in enumerate(sa_list):
                valid_count = sum(1 for r in sa.relations if r.is_valid)
                sa_label = (
                    f"Ch {sa.start_channel}–{sa.end_channel - 1}  "
                    f"mid={sa.midpoint:.1f} m  "
                    f"({valid_count}/{len(sa.relations)} shots)"
                )
                sa_item = QTreeWidgetItem(cfg_item, [sa_label, "", "", ""])
                sa_item.setData(0, ROLE_TYPE, "subarray")
                sa_item.setData(0, ROLE_CONFIG, config_name)
                sa_item.setData(0, ROLE_SA_IDX, sa_idx)

                for rel in sa.relations:
                    import os
                    fname = os.path.basename(rel.shot_file) if rel.shot_file else f"Shot {rel.shot_index + 1}"
                    tag = "✓" if rel.is_valid else "✗"
                    rel_label = f"{tag} {fname} ({rel.shot_position:+.1f} m)"

                    rel_item = QTreeWidgetItem(sa_item, [
                        rel_label,
                        f"{rel.source_offset:.1f}",
                        rel.direction,
                        f"{rel.quality:.2f}",
                    ])
                    rel_item.setData(0, ROLE_TYPE, "relation")
                    rel_item.setData(0, ROLE_CONFIG, config_name)
                    rel_item.setData(0, ROLE_SA_IDX, sa_idx)
                    rel_item.setData(0, ROLE_REL, rel)

                    rel_item.setFlags(
                        rel_item.flags() | Qt.ItemFlag.ItemIsUserCheckable
                    )
                    rel_item.setCheckState(
                        0,
                        Qt.CheckState.Checked if rel.is_valid
                        else Qt.CheckState.Unchecked,
                    )

                    bg = _CLR_VALID if rel.is_valid else _CLR_INVALID
                    for col in range(4):
                        rel_item.setBackground(col, QBrush(bg))

        self._tree.blockSignals(False)

    def clear(self) -> None:
        self._tree.clear()

    def get_selected_config(self) -> Optional[str]:
        """Return config name of the currently selected item, or None."""
        item = self._tree.currentItem()
        if item is None:
            return None
        return item.data(0, ROLE_CONFIG)

    def get_checked_relations(
        self, config_name: str,
    ) -> Dict[int, Set[int]]:
        """Return checked shot indices per sub-array index for a config.

        Returns
        -------
        dict[int, set[int]]
            Keyed by sa_local_idx, values are sets of shot_index.
        """
        result: Dict[int, Set[int]] = {}
        root = self._tree.invisibleRootItem()
        for ci in range(root.childCount()):
            cfg_item = root.child(ci)
            if cfg_item.data(0, ROLE_CONFIG) != config_name:
                continue
            for si in range(cfg_item.childCount()):
                sa_item = cfg_item.child(si)
                sa_idx = sa_item.data(0, ROLE_SA_IDX)
                checked: Set[int] = set()
                for ri in range(sa_item.childCount()):
                    rel_item = sa_item.child(ri)
                    rel: RelationInfo = rel_item.data(0, ROLE_REL)
                    if rel_item.checkState(0) == Qt.CheckState.Checked:
                        checked.add(rel.shot_index)
                result[sa_idx] = checked
        return result

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        item_type = item.data(0, ROLE_TYPE)
        config_name = item.data(0, ROLE_CONFIG)

        if item_type == "config":
            self.config_selected.emit(config_name)
        elif item_type == "subarray":
            sa_idx = item.data(0, ROLE_SA_IDX)
            self.subarray_selected.emit(config_name, sa_idx)
        elif item_type == "relation":
            sa_idx = item.data(0, ROLE_SA_IDX)
            self.subarray_selected.emit(config_name, sa_idx)

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if item.data(0, ROLE_TYPE) != "relation":
            return
        rel: RelationInfo = item.data(0, ROLE_REL)
        if rel is None:
            return
        checked = item.checkState(0) == Qt.CheckState.Checked
        config_name = item.data(0, ROLE_CONFIG)
        sa_idx = item.data(0, ROLE_SA_IDX)
        self.relation_toggled.emit(config_name, sa_idx, rel.shot_index, checked)
