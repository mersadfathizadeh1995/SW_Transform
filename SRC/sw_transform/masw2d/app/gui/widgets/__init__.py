"""Reusable widgets for the MASW 2D Profiler GUI."""

from sw_transform.masw2d.app.gui.widgets.assignment_table import AssignmentTable
from sw_transform.masw2d.app.gui.widgets.assignment_tree import AssignmentTree
from sw_transform.masw2d.app.gui.widgets.collapsible_section import CollapsibleSection
from sw_transform.masw2d.app.gui.widgets.layer_panel import LayerPanel
from sw_transform.masw2d.app.gui.widgets.shot_table import ShotTable
from sw_transform.masw2d.app.gui.widgets.subarray_detail_panel import (
    SubArrayDetailPanel,
)

__all__ = [
    "AssignmentTable",
    "AssignmentTree",
    "CollapsibleSection",
    "LayerPanel",
    "ShotTable",
    "SubArrayDetailPanel",
]
