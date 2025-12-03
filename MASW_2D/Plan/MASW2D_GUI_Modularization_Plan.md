# Complete GUI Modularization Plan

## Overview

Both main GUI files have grown too large and contain significant code duplication:
- **`masw2d_tab.py`**: ~950 lines
- **`simple_app.py`**: ~1560 lines

This plan outlines a complete modularization of the entire GUI system to:
1. Extract reusable components shared between both interfaces
2. Eliminate code duplication (especially Advanced Settings)
3. Create a maintainable, extensible GUI architecture
4. Unify vibrosis/FDBF settings across all interfaces

---

## Current State Analysis

### `simple_app.py` (~1560 lines) - Main Application
| Section | Lines (approx) | Responsibility |
|---------|----------------|----------------|
| Class init + variables | 1-130 | State, defaults, tk variables |
| `_build_menu()` | 130-145 | Menu bar |
| `_build_ui()` | 145-320 | Main layout, Inputs/Run/Figures tabs |
| File management | 320-420 | select_files, add_files, tree view |
| Advanced settings popup | 420-600 | **~180 lines - DUPLICATED** |
| Processing actions | 600-900 | run_single, run_compare |
| CSV aggregation | 900-1100 | Combined CSV creation |
| Figure gallery | 1100-1350 | Preview, zoom, PPT |
| Icon helpers | 1350-1450 | Asset loading |
| Array preview | 1450-1560 | Matplotlib waterfall |

### `masw2d_tab.py` (~950 lines) - 2D MASW Tab
| Section | Lines (approx) | Responsibility |
|---------|----------------|----------------|
| Class initialization | 1-110 | Variables, defaults |
| `_build_ui()` | 110-130 | Main layout |
| `_build_left_panel()` | 130-310 | All left panel controls |
| `_build_right_panel()` | 310-360 | Info + preview |
| Sub-array helpers | 360-440 | Checkbox management |
| Preview/plotting | 440-570 | Matplotlib preview |
| File management | 570-700 | Import, add, clear files |
| Advanced settings popup | 700-880 | **~180 lines - DUPLICATED** |
| Config building | 880-950 | `_build_config()`, run workflow |

### Key Duplications Identified
| Feature | simple_app.py | masw2d_tab.py | Lines Duplicated |
|---------|---------------|---------------|------------------|
| Advanced Settings popup | ✓ | ✓ | ~180 |
| Default values dict | ✓ | ✓ | ~30 |
| Vibrosis/cylindrical vars | ✓ | ✓ | ~15 |
| Preprocessing settings | ✓ | ✓ | ~40 |
| Image export settings | ✓ | ✓ | ~50 |
| File tree management | ✓ | ✓ | ~80 |
| Progress bar + status | ✓ | ✓ | ~20 |

**Total duplicated code: ~415 lines**

---

## Proposed Modular Architecture

```
sw_transform/gui/
├── __init__.py
├── app.py                      # Entry point (existing)
├── simple_app.py               # Main app - REFACTORED (~600 lines)
├── masw2d_tab.py               # 2D MASW tab - REFACTORED (~250 lines)
│
├── components/                 # NEW: Reusable UI components
│   ├── __init__.py
│   │
│   │ # === Shared Components (used by both apps) ===
│   ├── advanced_settings.py    # Advanced settings manager + dialog
│   ├── processing_limits.py    # Velocity/frequency/time limits panel
│   ├── file_tree.py            # File treeview with offset/reverse columns
│   ├── progress_panel.py       # Progress bar + status label
│   ├── output_settings.py      # Output dir, parallel, export options
│   │
│   │ # === MASW 2D Specific Components ===
│   ├── array_setup.py          # Array configuration (channels, dx, source)
│   ├── subarray_config.py      # Sub-array checkboxes + preview
│   ├── layout_preview.py       # Matplotlib layout visualization
│   │
│   │ # === Simple App Specific Components ===
│   ├── run_panel.py            # Run buttons (Single/Compare)
│   ├── figure_gallery.py       # Figure browser + zoom + PPT export
│   └── array_preview.py        # Waterfall preview canvas
│
├── dialogs/                    # NEW: Popup dialogs
│   ├── __init__.py
│   └── cell_edit_dialog.py     # Inline cell editing helper
│
└── utils/                      # NEW: GUI utilities
    ├── __init__.py
    ├── defaults.py             # Shared default values
    ├── validators.py           # Input validation helpers
    └── icons.py                # Icon loading and caching
```

---

## Phase 1: Foundation - Shared Utilities & Defaults

### 1.1 Create `gui/utils/defaults.py`

Centralize ALL default values used across the GUI:

```python
# gui/utils/defaults.py
"""Centralized default values for all GUI components."""

# === Transform Settings ===
TRANSFORM_DEFAULTS = {
    # FK/FDBF
    'grid_fk': '4000',
    'tol_fk': '0',
    # PS/SS
    'grid_ps': '1200',
    'vspace_ps': 'log',
    'tol_ps': '0',
    # FDBF-specific
    'vibrosis': False,
    'cylindrical': False,
}

# === Preprocessing ===
PREPROCESS_DEFAULTS = {
    'start_time': '0.0',
    'end_time': '1.0',
    'downsample': True,
    'down_factor': '16',
    'numf': '4000',
}

# === Peak Picking ===
PICKING_DEFAULTS = {
    'power_threshold': '0.1',
    'tol': '0.01',
}

# === Plot/Export Settings ===
PLOT_DEFAULTS = {
    'auto_vel_limits': True,
    'auto_freq_limits': True,
    'plot_min_vel': '0',
    'plot_max_vel': '2000',
    'plot_min_freq': '0',
    'plot_max_freq': '100',
    'freq_tick_spacing': 'auto',
    'vel_tick_spacing': 'auto',
    'cmap': 'jet',
    'dpi': '150',
    'export_spectra': True,
}

# === Vibrosis/Array Settings ===
VIBROSIS_DEFAULTS = {
    'dx': '2.0',  # Sensor spacing for .mat files
}

# === MASW 2D Specific ===
MASW2D_DEFAULTS = {
    'n_channels': '24',
    'dx': '2.0',
    'slide_step': '1',
    'source_type': 'hammer',
    'method': 'ps',
    'freq_min': '5',
    'freq_max': '80',
    'vel_min': '100',
    'vel_max': '1500',
}

# === Processing Limits ===
LIMITS_DEFAULTS = {
    'vmin': '0',
    'vmax': '5000',
    'fmin': '0',
    'fmax': '100',
}


def get_all_defaults() -> dict:
    """Return merged dictionary of all defaults."""
    return {
        **TRANSFORM_DEFAULTS,
        **PREPROCESS_DEFAULTS,
        **PICKING_DEFAULTS,
        **PLOT_DEFAULTS,
        **VIBROSIS_DEFAULTS,
    }
```

**Estimated effort: 1 hour**

---

### 1.2 Create `gui/utils/icons.py`

Extract icon loading logic from simple_app.py:

```python
# gui/utils/icons.py
"""Icon loading and caching utilities."""

import os
import tkinter as tk
from typing import Dict, Optional

_icon_cache: Dict[str, tk.PhotoImage] = {}


def get_asset_path(name: str, base_dir: str = None) -> str:
    """Locate asset file, handling @NxN suffixed variants."""
    ...


def load_icon(name: str, size: int, base_dir: str = None) -> Optional[tk.PhotoImage]:
    """Load and cache an icon with proper scaling."""
    ...


def clear_cache():
    """Clear the icon cache."""
    _icon_cache.clear()
```

**Estimated effort: 1 hour**

---

## Phase 2: Core Shared Components

### 2.1 `components/advanced_settings.py` (~300 lines)

**The most important shared component!** Used by both `simple_app.py` and `masw2d_tab.py`.

```python
# gui/components/advanced_settings.py
"""Advanced settings manager and dialog."""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Callable
from sw_transform.gui.utils.defaults import get_all_defaults


class AdvancedSettingsManager:
    """Manages all advanced settings variables."""
    
    def __init__(self, mode: str = 'full'):
        """
        Initialize settings manager.
        
        Parameters
        ----------
        mode : str
            'full' - All settings (for simple_app)
            'masw2d' - MASW 2D relevant settings only
        """
        self.mode = mode
        self._defaults = get_all_defaults()
        self._create_variables()
        self._setup_traces()
    
    def _create_variables(self):
        """Create all tk variables."""
        # Transform settings
        self.grid_fk_var = tk.StringVar(value=self._defaults['grid_fk'])
        self.tol_fk_var = tk.StringVar(value=self._defaults['tol_fk'])
        self.grid_ps_var = tk.StringVar(value=self._defaults['grid_ps'])
        self.vspace_ps_var = tk.StringVar(value=self._defaults['vspace_ps'])
        self.tol_ps_var = tk.StringVar(value=self._defaults['tol_ps'])
        
        # FDBF/Vibrosis
        self.vibrosis_var = tk.BooleanVar(value=self._defaults['vibrosis'])
        self.cylindrical_var = tk.BooleanVar(value=self._defaults['cylindrical'])
        self.dx_var = tk.StringVar(value=self._defaults['dx'])
        
        # Preprocessing
        self.start_time_var = tk.StringVar(value=self._defaults['start_time'])
        self.end_time_var = tk.StringVar(value=self._defaults['end_time'])
        self.downsample_var = tk.BooleanVar(value=self._defaults['downsample'])
        self.down_factor_var = tk.StringVar(value=self._defaults['down_factor'])
        self.numf_var = tk.StringVar(value=self._defaults['numf'])
        
        # Peak picking
        self.power_threshold_var = tk.StringVar(value=self._defaults['power_threshold'])
        
        # Plot settings
        self.auto_vel_limits_var = tk.BooleanVar(value=self._defaults['auto_vel_limits'])
        self.auto_freq_limits_var = tk.BooleanVar(value=self._defaults['auto_freq_limits'])
        self.plot_min_vel_var = tk.StringVar(value=self._defaults['plot_min_vel'])
        self.plot_max_vel_var = tk.StringVar(value=self._defaults['plot_max_vel'])
        self.plot_min_freq_var = tk.StringVar(value=self._defaults['plot_min_freq'])
        self.plot_max_freq_var = tk.StringVar(value=self._defaults['plot_max_freq'])
        self.freq_tick_spacing_var = tk.StringVar(value=self._defaults['freq_tick_spacing'])
        self.vel_tick_spacing_var = tk.StringVar(value=self._defaults['vel_tick_spacing'])
        self.cmap_var = tk.StringVar(value=self._defaults['cmap'])
        self.dpi_var = tk.StringVar(value=self._defaults['dpi'])
        self.export_spectra_var = tk.BooleanVar(value=self._defaults['export_spectra'])
    
    def _setup_traces(self):
        """Setup variable traces (e.g., vibrosis -> cylindrical)."""
        self.vibrosis_var.trace_add('write', self._on_vibrosis_changed)
    
    def _on_vibrosis_changed(self, *args):
        """Auto-enable cylindrical when vibrosis is enabled."""
        if self.vibrosis_var.get():
            self.cylindrical_var.set(True)
    
    def get_all_values(self) -> Dict[str, Any]:
        """Return all settings as a dictionary."""
        return {
            'grid_fk': int(self.grid_fk_var.get()),
            'tol_fk': float(self.tol_fk_var.get()),
            'grid_ps': int(self.grid_ps_var.get()),
            'vspace_ps': self.vspace_ps_var.get(),
            'tol_ps': float(self.tol_ps_var.get()),
            'vibrosis': self.vibrosis_var.get(),
            'cylindrical': self.cylindrical_var.get(),
            'dx': float(self.dx_var.get()),
            'start_time': float(self.start_time_var.get()),
            'end_time': float(self.end_time_var.get()),
            'downsample': self.downsample_var.get(),
            'down_factor': int(self.down_factor_var.get()),
            'numf': int(self.numf_var.get()),
            'power_threshold': float(self.power_threshold_var.get()),
            'auto_vel_limits': self.auto_vel_limits_var.get(),
            'auto_freq_limits': self.auto_freq_limits_var.get(),
            'plot_min_vel': self.plot_min_vel_var.get(),
            'plot_max_vel': self.plot_max_vel_var.get(),
            'plot_min_freq': self.plot_min_freq_var.get(),
            'plot_max_freq': self.plot_max_freq_var.get(),
            'freq_tick_spacing': self.freq_tick_spacing_var.get(),
            'vel_tick_spacing': self.vel_tick_spacing_var.get(),
            'cmap': self.cmap_var.get(),
            'dpi': int(self.dpi_var.get()),
            'export_spectra': self.export_spectra_var.get(),
        }
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        for key, value in self._defaults.items():
            var = getattr(self, f'{key}_var', None)
            if var is not None:
                var.set(value)
    
    def open_dialog(self, parent: tk.Widget, title: str = "Advanced Settings"):
        """Open the advanced settings popup dialog."""
        dialog = AdvancedSettingsDialog(parent, self, title)
        dialog.show()


class AdvancedSettingsDialog:
    """Popup dialog for advanced settings."""
    
    def __init__(self, parent: tk.Widget, manager: AdvancedSettingsManager, 
                 title: str = "Advanced Settings"):
        self.parent = parent
        self.manager = manager
        self.title = title
        self.popup = None
    
    def show(self):
        """Display the dialog."""
        self.popup = tk.Toplevel(self.parent)
        self.popup.title(self.title)
        self.popup.geometry("480x550")
        self.popup.resizable(True, True)
        self.popup.transient(self.parent)
        self.popup.grab_set()
        
        self._build_content()
        self._center_window()
    
    def _build_content(self):
        """Build the dialog content."""
        # Scrollable frame
        canvas = tk.Canvas(self.popup, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.popup, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # Build sections
        self._build_transform_section(scrollable)
        self._build_vibrosis_section(scrollable)
        self._build_preprocess_section(scrollable)
        self._build_picking_section(scrollable)
        self._build_export_section(scrollable)
        self._build_buttons(scrollable)
    
    def _build_transform_section(self, parent):
        """Build transform settings section."""
        frame = tk.LabelFrame(parent, text="Transform Settings", padx=8, pady=8)
        frame.pack(fill="x", padx=8, pady=6)
        # ... (FK/FDBF grid, PS/SS grid, spacing, etc.)
    
    def _build_vibrosis_section(self, parent):
        """Build vibrosis/FDBF section."""
        frame = tk.LabelFrame(parent, text="Vibrosis / FDBF Settings", padx=8, pady=8)
        frame.pack(fill="x", padx=8, pady=6)
        # ... (vibrosis checkbox, cylindrical, dx)
    
    # ... other section builders ...
    
    def _build_buttons(self, parent):
        """Build button row."""
        frame = tk.Frame(parent)
        frame.pack(fill="x", padx=8, pady=12)
        
        tk.Button(frame, text="Reset to Defaults",
                  command=self.manager.reset_to_defaults).pack(side="left", padx=4)
        tk.Button(frame, text="Close",
                  command=self.popup.destroy).pack(side="right", padx=4)
    
    def _center_window(self):
        """Center dialog on parent."""
        self.popup.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - self.popup.winfo_width()) // 2
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() - self.popup.winfo_height()) // 2
        self.popup.geometry(f"+{x}+{y}")
```

**Estimated effort: 4-5 hours**

---

### 2.2 `components/processing_limits.py` (~80 lines)

Shared velocity/frequency/time limits panel:

```python
# gui/components/processing_limits.py
"""Processing limits panel (velocity, frequency, time window)."""

import tkinter as tk
from tkinter import ttk


class ProcessingLimitsPanel(tk.LabelFrame):
    """Panel for velocity, frequency, and time limits."""
    
    def __init__(self, parent, include_time: bool = True, **kwargs):
        super().__init__(parent, text="Processing Limits", **kwargs)
        self.include_time = include_time
        
        # Variables
        self.vmin_var = tk.StringVar(value="0")
        self.vmax_var = tk.StringVar(value="5000")
        self.fmin_var = tk.StringVar(value="0")
        self.fmax_var = tk.StringVar(value="100")
        self.time_start_var = tk.StringVar(value="0.0")
        self.time_end_var = tk.StringVar(value="1.0")
        
        self._build_ui()
    
    def get_values(self) -> dict:
        """Return all limit values."""
        return {
            'vmin': float(self.vmin_var.get()),
            'vmax': float(self.vmax_var.get()),
            'fmin': float(self.fmin_var.get()),
            'fmax': float(self.fmax_var.get()),
            'time_start': float(self.time_start_var.get()),
            'time_end': float(self.time_end_var.get()),
        }
```

**Estimated effort: 1-2 hours**

---

### 2.3 `components/file_tree.py` (~150 lines)

Shared file treeview with editing:

```python
# gui/components/file_tree.py
"""File treeview with offset/reverse column editing."""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Callable, Optional


class FileTreePanel(tk.Frame):
    """File list with treeview and editing capabilities."""
    
    def __init__(self, parent, columns: List[str] = None,
                 on_selection_changed: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.columns = columns or ["file", "type", "offset", "rev"]
        self.on_selection_changed = on_selection_changed
        
        # Data storage
        self.files: List[str] = []
        self.file_data: Dict[str, dict] = {}  # base -> {type, offset, reverse}
        
        self._build_ui()
    
    def add_files(self, files: List[str], auto_detect: bool = True):
        """Add files to the list."""
        ...
    
    def clear(self):
        """Clear all files."""
        ...
    
    def get_selected(self) -> List[str]:
        """Get selected file paths."""
        ...
    
    def get_all_data(self) -> List[dict]:
        """Get all file data with offsets and flags."""
        ...
```

**Estimated effort: 2-3 hours**

---

### 2.4 `components/progress_panel.py` (~50 lines)

Shared progress bar + status:

```python
# gui/components/progress_panel.py
"""Progress bar with status label."""

import tkinter as tk
from tkinter import ttk


class ProgressPanel(tk.Frame):
    """Progress bar with status text."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.progress_var = tk.DoubleVar(value=0)
        self.status_var = tk.StringVar(value="Ready")
        
        self._build_ui()
    
    def set_progress(self, value: float, status: str = None):
        """Update progress and optionally status."""
        self.progress_var.set(value)
        if status:
            self.status_var.set(status)
    
    def reset(self):
        """Reset to idle state."""
        self.progress_var.set(0)
        self.status_var.set("Ready")
```

**Estimated effort: 30 minutes**

---

### 2.5 `components/output_settings.py` (~80 lines)

Output directory + parallel settings:

```python
# gui/components/output_settings.py
"""Output directory and parallel processing settings."""

import tkinter as tk
from tkinter import ttk, filedialog
import multiprocessing


class OutputSettingsPanel(tk.LabelFrame):
    """Output directory, parallel, and export settings."""
    
    def __init__(self, parent, include_export_images: bool = False, **kwargs):
        super().__init__(parent, text="Output", **kwargs)
        
        self.output_dir_var = tk.StringVar(value="")
        self.parallel_var = tk.BooleanVar(value=True)
        self.worker_var = tk.StringVar(value="auto")
        self.include_images_var = tk.BooleanVar(value=True)
        
        self.include_export_images = include_export_images
        self._build_ui()
    
    def get_values(self) -> dict:
        """Return output settings."""
        return {
            'output_dir': self.output_dir_var.get(),
            'parallel': self.parallel_var.get(),
            'workers': self.worker_var.get(),
            'include_images': self.include_images_var.get(),
        }
```

**Estimated effort: 1 hour**

---

## Phase 3: Simple App Specific Components

### 3.1 `components/run_panel.py` (~120 lines)

Run/Compare buttons with method selector:

```python
# gui/components/run_panel.py
"""Run and Compare buttons panel."""

class RunPanel(tk.Frame):
    """Panel with method selector and run/compare buttons."""
    
    def __init__(self, parent, on_run_single: Callable, on_run_compare: Callable,
                 methods: Dict[str, dict], **kwargs):
        ...
```

**Estimated effort: 2 hours**

---

### 3.2 `components/figure_gallery.py` (~250 lines)

Figure browser with zoom and PPT export:

```python
# gui/components/figure_gallery.py
"""Figure gallery with preview, zoom, and export."""

class FigureGallery(tk.Frame):
    """Figure browser with preview canvas and controls."""
    
    def __init__(self, parent, output_dir_var: tk.StringVar, **kwargs):
        ...
    
    def refresh(self):
        """Refresh the figure list."""
        ...
    
    def build_ppt(self):
        """Create PowerPoint from figures."""
        ...
```

**Estimated effort: 3-4 hours**

---

### 3.3 `components/array_preview.py` (~120 lines)

Waterfall/array schematic preview:

```python
# gui/components/array_preview.py
"""Array schematic and waterfall preview."""

class ArrayPreviewPanel(tk.LabelFrame):
    """Embedded matplotlib preview for array visualization."""
    
    def __init__(self, parent, **kwargs):
        ...
    
    def update_preview(self, path: str, offsets: dict, ...):
        """Update the preview with data from file."""
        ...
```

**Estimated effort: 2 hours**

---

## Phase 4: MASW 2D Specific Components

### 4.1 `components/array_setup.py` (~100 lines)

Already described in original plan - channels, dx, source type.

**Estimated effort: 2 hours**

---

### 4.2 `components/subarray_config.py` (~150 lines)

Already described - checkboxes, slide step, preview selector.

**Estimated effort: 2 hours**

---

### 4.3 `components/layout_preview.py` (~200 lines)

Already described - matplotlib canvas for layout visualization.

**Estimated effort: 2-3 hours**

---

## Phase 5: Refactor Main Files

### 5.1 Refactor `simple_app.py` (~1560 → ~600 lines)

```python
# simple_app.py - REFACTORED

from sw_transform.gui.components import (
    AdvancedSettingsManager,
    ProcessingLimitsPanel,
    FileTreePanel,
    ProgressPanel,
    OutputSettingsPanel,
    RunPanel,
    FigureGallery,
    ArrayPreviewPanel,
)
from sw_transform.gui.utils.icons import load_icon
from sw_transform.gui.utils.defaults import LIMITS_DEFAULTS


class SimpleMASWGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._setup_window()
        
        # Shared settings manager
        self.settings = AdvancedSettingsManager(mode='full')
        
        # State
        self.output_folder = ""
        self.method_key = tk.StringVar(value="fk")
        
        self._build_menu()
        self._build_ui()
    
    def _build_ui(self):
        # Left panel - File tree
        left = tk.Frame(self.root, width=320)
        left.pack(side="left", fill="y")
        
        self.file_panel = FileTreePanel(left, on_selection_changed=self._on_file_selected)
        self.file_panel.pack(fill="both", expand=True)
        
        # Center - Notebook
        center = tk.Frame(self.root)
        center.pack(side="left", fill="both", expand=True)
        
        nb = ttk.Notebook(center)
        self._build_inputs_tab(nb)
        self._build_run_tab(nb)
        self._build_figures_tab(nb)
        self._add_masw2d_tab(nb)
        nb.pack(fill="both", expand=True)
    
    def _build_inputs_tab(self, notebook):
        tab = tk.Frame(notebook)
        notebook.add(tab, text="Inputs")
        
        # Output settings
        self.output_panel = OutputSettingsPanel(tab)
        self.output_panel.pack(fill="x", padx=6, pady=4)
        
        # Processing limits
        self.limits_panel = ProcessingLimitsPanel(tab)
        self.limits_panel.pack(fill="x", padx=6, pady=4)
        
        # Figure title
        ...
        
        # Advanced settings button
        tk.Button(tab, text="⚙ Advanced Settings...",
                  command=lambda: self.settings.open_dialog(self.root)).pack()
        
        # Array preview
        self.preview_panel = ArrayPreviewPanel(tab)
        self.preview_panel.pack(fill="both", expand=True)
    
    def _build_run_tab(self, notebook):
        tab = tk.Frame(notebook)
        notebook.add(tab, text="Run")
        
        # Run panel with method selector
        self.run_panel = RunPanel(
            tab,
            on_run_single=self.run_single_processing,
            on_run_compare=self.run_compare_processing,
            methods=METHODS
        )
        self.run_panel.pack(fill="x")
        
        # Log box
        ...
        
        # Progress
        self.progress = ProgressPanel(tab)
        self.progress.pack(fill="x", side="bottom")
    
    def _build_figures_tab(self, notebook):
        tab = tk.Frame(notebook)
        notebook.add(tab, text="Figures")
        
        self.gallery = FigureGallery(tab, self.output_panel.output_dir_var)
        self.gallery.pack(fill="both", expand=True)
    
    def run_single_processing(self, selected_only: bool = False):
        """Run single method processing."""
        # Get values from components
        limits = self.limits_panel.get_values()
        settings = self.settings.get_all_values()
        output = self.output_panel.get_values()
        files = self.file_panel.get_all_data()
        
        # ... rest of processing logic (much cleaner now)
```

**Estimated effort: 4-5 hours**

---

### 5.2 Refactor `masw2d_tab.py` (~950 → ~250 lines)

```python
# masw2d_tab.py - REFACTORED

from sw_transform.gui.components import (
    AdvancedSettingsManager,
    FileTreePanel,
    ProgressPanel,
    OutputSettingsPanel,
    ArraySetupPanel,
    SubarrayConfigPanel,
    LayoutPreviewPanel,
)


class MASW2DTab:
    def __init__(self, parent, log_callback=None, main_app=None):
        self.parent = parent
        self.log = log_callback or print
        self.main_app = main_app
        
        # Shared settings manager
        self.settings = AdvancedSettingsManager(mode='masw2d')
        
        self._build_ui()
    
    def _build_ui(self):
        paned = ttk.PanedWindow(self.parent, orient="horizontal")
        paned.pack(fill="both", expand=True)
        
        # Left panel
        left = self._build_left_panel(paned)
        paned.add(left, weight=1)
        
        # Right panel  
        right = self._build_right_panel(paned)
        paned.add(right, weight=2)
    
    def _build_left_panel(self, parent):
        frame = ttk.Frame(parent)
        
        # Array setup
        self.array_panel = ArraySetupPanel(frame, on_update=self._on_array_update)
        self.array_panel.pack(fill="x", padx=4, pady=4)
        
        # File manager (uses shared component)
        self.file_panel = FileTreePanel(frame, columns=["File", "Offset", "Rev", "Source Pos"])
        self.file_panel.pack(fill="x", padx=4, pady=4)
        
        # Sub-array config
        self.subarray_panel = SubarrayConfigPanel(
            frame, 
            n_channels_var=self.array_panel.n_channels_var,
            on_preview_change=self._update_preview
        )
        self.subarray_panel.pack(fill="x", padx=4, pady=4)
        
        # Processing settings + Advanced button
        ...
        
        # Output settings
        self.output_panel = OutputSettingsPanel(frame, include_export_images=True)
        self.output_panel.pack(fill="x", padx=4, pady=4)
        
        # Run button + progress
        self.progress = ProgressPanel(frame)
        self.progress.pack(fill="x", padx=4, pady=4)
        
        tk.Button(frame, text="Run 2D MASW Workflow",
                  command=self._run_workflow).pack(fill="x", padx=4, pady=8)
        
        return frame
    
    def _build_right_panel(self, parent):
        frame = ttk.Frame(parent)
        
        self.preview = LayoutPreviewPanel(frame)
        self.preview.pack(fill="both", expand=True)
        
        return frame
    
    def _build_config(self) -> dict:
        """Build config from all panels."""
        return {
            "array": self.array_panel.get_values(),
            "shots": self.file_panel.get_all_data(),
            "subarray_configs": self.subarray_panel.get_configs(),
            "processing": {
                **self.processing_panel.get_values(),
                **self.settings.get_all_values(),
            },
            "output": self.output_panel.get_values(),
        }
```

**Estimated effort: 3-4 hours**

---

## Implementation Timeline

| Phase | Task | Est. Hours | Priority |
|-------|------|------------|----------|
| **1.1** | Create `utils/defaults.py` | 1 | 🔴 High |
| **1.2** | Create `utils/icons.py` | 1 | 🟡 Medium |
| **2.1** | Create `AdvancedSettingsManager` | 4-5 | 🔴 High |
| **2.2** | Create `ProcessingLimitsPanel` | 1-2 | 🔴 High |
| **2.3** | Create `FileTreePanel` | 2-3 | 🔴 High |
| **2.4** | Create `ProgressPanel` | 0.5 | 🟡 Medium |
| **2.5** | Create `OutputSettingsPanel` | 1 | 🟡 Medium |
| **3.1** | Create `RunPanel` | 2 | 🟡 Medium |
| **3.2** | Create `FigureGallery` | 3-4 | 🟡 Medium |
| **3.3** | Create `ArrayPreviewPanel` | 2 | 🟢 Low |
| **4.1** | Create `ArraySetupPanel` | 2 | 🔴 High |
| **4.2** | Create `SubarrayConfigPanel` | 2 | 🔴 High |
| **4.3** | Create `LayoutPreviewPanel` | 2-3 | 🟡 Medium |
| **5.1** | Refactor `simple_app.py` | 4-5 | 🔴 High |
| **5.2** | Refactor `masw2d_tab.py` | 3-4 | 🔴 High |

**Total estimated: 31-40 hours**

---

## Benefits Summary

| Benefit | Before | After |
|---------|--------|-------|
| `simple_app.py` lines | ~1560 | ~600 |
| `masw2d_tab.py` lines | ~950 | ~250 |
| Duplicated code | ~415 lines | ~0 lines |
| Components reusable | No | Yes |
| Settings consistency | Manual sync | Automatic |
| Testability | Hard | Easy |
| Adding new features | Complex | Simple |

---

## File Changes Summary

### New Files to Create (15 files):
```
gui/components/__init__.py
gui/components/advanced_settings.py     # ~300 lines
gui/components/processing_limits.py     # ~80 lines
gui/components/file_tree.py             # ~150 lines
gui/components/progress_panel.py        # ~50 lines
gui/components/output_settings.py       # ~80 lines
gui/components/run_panel.py             # ~120 lines
gui/components/figure_gallery.py        # ~250 lines
gui/components/array_preview.py         # ~120 lines
gui/components/array_setup.py           # ~100 lines
gui/components/subarray_config.py       # ~150 lines
gui/components/layout_preview.py        # ~200 lines
gui/utils/__init__.py
gui/utils/defaults.py                   # ~80 lines
gui/utils/icons.py                      # ~60 lines
```

### Files to Modify:
```
gui/simple_app.py      # Refactor to use components
gui/masw2d_tab.py      # Refactor to use components
gui/__init__.py        # Update exports
```

---

## Next Steps

1. **Review this plan** - Confirm the approach and priorities
2. **Start with Phase 1** - Foundation (defaults + icons)
3. **Then Phase 2.1** - AdvancedSettingsManager (biggest impact)
4. **Incremental refactoring** - One component at a time, testing as we go

---

## Questions for Review

1. Should we start with `simple_app.py` or `masw2d_tab.py` first?
2. Do you want to keep the same visual appearance or also update styling?
3. Should components have their own default styling or inherit from parent?
4. Priority: Quick wins first (ProgressPanel, defaults) or biggest impact (AdvancedSettings)?
