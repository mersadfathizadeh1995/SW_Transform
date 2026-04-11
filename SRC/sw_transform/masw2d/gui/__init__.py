"""MASW 2D GUI Components.

This package provides modular GUI components for the MASW 2D tab,
following the same patterns as sw_transform.gui.components.

Components:
- defaults: MASW2D_DEFAULTS dictionary
- array_setup: ArraySetupPanel
- file_manager: FileManagerPanel
- subarray_config: SubarrayConfigPanel
- processing_panel: ProcessingPanel
- output_panel: OutputPanel
- run_panel: MASW2DRunPanel
- layout_preview: LayoutPreviewPanel
- advanced_settings: MASW2DAdvancedSettings
"""

from sw_transform.masw2d.gui.defaults import MASW2D_DEFAULTS
from sw_transform.masw2d.gui.collapsible import CollapsibleLabelFrame
from sw_transform.masw2d.gui.array_setup import ArraySetupPanel
from sw_transform.masw2d.gui.file_manager import FileManagerPanel
from sw_transform.masw2d.gui.subarray_config import SubarrayConfigPanel
from sw_transform.masw2d.gui.processing_panel import ProcessingPanel
from sw_transform.masw2d.gui.output_panel import OutputPanel
from sw_transform.masw2d.gui.run_panel import MASW2DRunPanel
from sw_transform.masw2d.gui.layout_preview import LayoutPreviewPanel
from sw_transform.masw2d.gui.advanced_settings import MASW2DAdvancedSettings
from sw_transform.masw2d.gui.assignment_panel import AssignmentPanel
from sw_transform.masw2d.gui.shot_input_panel import ShotInputPanel
from sw_transform.masw2d.gui.geometry_preview import GeometryPreviewPanel
from sw_transform.masw2d.gui.subarray_explorer import SubarrayExplorerPanel

__all__ = [
    'MASW2D_DEFAULTS',
    'CollapsibleLabelFrame',
    'ArraySetupPanel',
    'FileManagerPanel',
    'SubarrayConfigPanel',
    'ProcessingPanel',
    'OutputPanel',
    'MASW2DRunPanel',
    'LayoutPreviewPanel',
    'MASW2DAdvancedSettings',
    'AssignmentPanel',
    'ShotInputPanel',
    'GeometryPreviewPanel',
    'SubarrayExplorerPanel',
]
