# Simple App GUI Modularization Plan

## Overview

Refactor `simple_app.py` (~1560 lines) into modular components for better maintainability.

**Goal**: Reduce to ~600-700 lines by extracting reusable components.

---

## Current Structure

```
sw_transform/gui/
├── __init__.py
├── app.py              # Entry point
├── simple_app.py       # Main app (~1560 lines) ← TO REFACTOR
└── masw2d_tab.py       # MASW 2D tab (separate plan)
```

## Proposed Structure

```
sw_transform/gui/
├── __init__.py
├── app.py                      # Entry point (unchanged)
├── simple_app.py               # Main app (~600 lines after refactor)
│
├── components/                 # NEW: Reusable UI components
│   ├── __init__.py
│   ├── advanced_settings.py    # Advanced settings manager + dialog (~250 lines)
│   ├── file_tree.py            # File treeview with editing (~120 lines)
│   ├── processing_limits.py    # Velocity/frequency/time panel (~60 lines)
│   ├── progress_panel.py       # Progress bar + status (~40 lines)
│   ├── run_panel.py            # Run/Compare buttons + method (~100 lines)
│   ├── figure_gallery.py       # Figure browser + zoom + PPT (~220 lines)
│   └── array_preview.py        # Waterfall preview canvas (~100 lines)
│
├── utils/                      # NEW: Utilities
│   ├── __init__.py
│   ├── defaults.py             # Default values (~60 lines)
│   └── icons.py                # Icon loading (~50 lines)
│
└── masw2d_tab.py               # Uses masw2d/gui/ components
```

---

## Component Details

### 1. `utils/defaults.py` (~60 lines)

Centralized default values:

```python
TRANSFORM_DEFAULTS = {
    'grid_fk': '4000', 'tol_fk': '0',
    'grid_ps': '1200', 'vspace_ps': 'log', 'tol_ps': '0',
    'vibrosis': False, 'cylindrical': False,
}

PREPROCESS_DEFAULTS = {
    'start_time': '0.0', 'end_time': '1.0',
    'downsample': True, 'down_factor': '16', 'numf': '4000',
}

PLOT_DEFAULTS = {
    'auto_vel_limits': True, 'auto_freq_limits': True,
    'plot_min_vel': '0', 'plot_max_vel': '2000',
    'cmap': 'jet', 'dpi': '200',
}

LIMITS_DEFAULTS = {
    'vmin': '0', 'vmax': '5000',
    'fmin': '0', 'fmax': '100',
}
```

---

### 2. `utils/icons.py` (~50 lines)

Icon loading extracted from simple_app.py:

```python
def get_asset_path(name: str, base_dir: str = None) -> str: ...
def load_icon(name: str, size: int) -> Optional[tk.PhotoImage]: ...
def clear_cache(): ...
```

---

### 3. `components/advanced_settings.py` (~250 lines)

**The largest component** - Advanced Settings popup:

```python
class AdvancedSettingsManager:
    """Manages all advanced settings tk variables."""
    
    def __init__(self):
        # Transform settings
        self.grid_fk_var = tk.StringVar(...)
        self.vibrosis_var = tk.BooleanVar(...)
        # Preprocessing
        self.downsample_var = tk.BooleanVar(...)
        # Plot settings
        self.cmap_var = tk.StringVar(...)
        # etc.
    
    def get_all_values(self) -> dict: ...
    def reset_to_defaults(self): ...
    def open_dialog(self, parent): ...
```

---

### 4. `components/file_tree.py` (~120 lines)

File treeview with offset/reverse editing:

```python
class FileTreePanel(tk.Frame):
    def __init__(self, parent, columns=["file","type","offset","rev"]): ...
    
    @property
    def files(self) -> List[str]: ...
    @property
    def file_data(self) -> Dict[str, dict]: ...
    
    def add_files(self, files: List[str], auto_detect=True): ...
    def clear(self): ...
    def get_selected(self) -> List[str]: ...
```

---

### 5. `components/processing_limits.py` (~60 lines)

Velocity/frequency/time limits:

```python
class ProcessingLimitsPanel(tk.LabelFrame):
    def __init__(self, parent, include_time=True): ...
    def get_values(self) -> dict: ...  # vmin, vmax, fmin, fmax, time_start, time_end
```

---

### 6. `components/progress_panel.py` (~40 lines)

Progress bar + status:

```python
class ProgressPanel(tk.Frame):
    def __init__(self, parent): ...
    def set_progress(self, value: float, status: str = None): ...
    def reset(self): ...
```

---

### 7. `components/run_panel.py` (~100 lines)

Run/Compare buttons with method selector:

```python
class RunPanel(tk.Frame):
    def __init__(self, parent, methods: dict, 
                 on_run_single, on_run_compare): ...
    
    @property
    def selected_method(self) -> str: ...
    @property
    def parallel_enabled(self) -> bool: ...
    @property
    def worker_count(self) -> str: ...
```

---

### 8. `components/figure_gallery.py` (~220 lines)

Figure browser with preview, zoom, PPT export:

```python
class FigureGallery(tk.Frame):
    def __init__(self, parent, output_dir_var: tk.StringVar): ...
    
    def refresh(self): ...
    def open_selected(self): ...
    def delete_selected(self): ...
    def build_ppt(self): ...
```

---

### 9. `components/array_preview.py` (~100 lines)

Array schematic + waterfall preview:

```python
class ArrayPreviewPanel(tk.LabelFrame):
    def __init__(self, parent): ...
    def update_preview(self, path: str, offsets: dict, settings: dict): ...
```

---

## Refactored `simple_app.py` (~600 lines)

```python
from sw_transform.gui.components import (
    AdvancedSettingsManager, FileTreePanel, ProcessingLimitsPanel,
    ProgressPanel, RunPanel, FigureGallery, ArrayPreviewPanel
)
from sw_transform.gui.utils.icons import load_icon

class SimpleMASWGUI:
    def __init__(self, root):
        self.root = root
        self._setup_window()
        
        # Settings manager
        self.settings = AdvancedSettingsManager()
        
        # State
        self.output_folder = ""
        
        self._build_menu()
        self._build_ui()
    
    def _build_ui(self):
        # Left - File tree
        self.file_panel = FileTreePanel(left)
        
        # Center - Notebook with tabs
        nb = ttk.Notebook(center)
        self._build_inputs_tab(nb)
        self._build_run_tab(nb)
        self._build_figures_tab(nb)
        self._add_masw2d_tab(nb)
    
    def _build_inputs_tab(self, nb):
        # Uses: ProcessingLimitsPanel, ArrayPreviewPanel
        # Advanced settings button → self.settings.open_dialog()
    
    def _build_run_tab(self, nb):
        # Uses: RunPanel, ProgressPanel
    
    def _build_figures_tab(self, nb):
        # Uses: FigureGallery
    
    def run_single_processing(self, selected_only=False):
        # Get values from components
        limits = self.limits_panel.get_values()
        settings = self.settings.get_all_values()
        files = self.file_panel.file_data
        # ... processing logic
    
    def run_compare_processing(self, selected_only=False):
        # Similar pattern
```

---

## Implementation Timeline

| Phase | Task | Est. Hours |
|-------|------|------------|
| 1 | `utils/defaults.py` | 0.5 |
| 2 | `utils/icons.py` | 0.5 |
| 3 | `components/advanced_settings.py` | 3-4 |
| 4 | `components/file_tree.py` | 2 |
| 5 | `components/processing_limits.py` | 1 |
| 6 | `components/progress_panel.py` | 0.5 |
| 7 | `components/run_panel.py` | 1.5 |
| 8 | `components/figure_gallery.py` | 2-3 |
| 9 | `components/array_preview.py` | 1.5 |
| 10 | Refactor `simple_app.py` | 3-4 |

**Total: ~16-20 hours**

---

## Files to Create

```
gui/utils/__init__.py
gui/utils/defaults.py
gui/utils/icons.py
gui/components/__init__.py
gui/components/advanced_settings.py
gui/components/file_tree.py
gui/components/processing_limits.py
gui/components/progress_panel.py
gui/components/run_panel.py
gui/components/figure_gallery.py
gui/components/array_preview.py
```

## Files to Modify

```
gui/simple_app.py  # Major refactor
gui/__init__.py    # Update exports
```
