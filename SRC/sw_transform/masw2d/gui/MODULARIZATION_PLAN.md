# MASW 2D GUI Modularization Plan

## Overview

Refactor `masw2d_tab.py` (~950 lines) into modular components within the `masw2d` module.

**Goal**: Reduce to ~250-300 lines by extracting components into `masw2d/gui/`.

---

## Current Structure

```
sw_transform/
├── gui/
│   ├── simple_app.py       # Main app
│   └── masw2d_tab.py       # MASW 2D tab (~950 lines) ← TO REFACTOR
│
└── masw2d/                 # MASW 2D module (already separated)
    ├── config/
    ├── geometry/
    ├── extraction/
    ├── processing/
    ├── workflows/
    └── output/
```

## Proposed Structure

```
sw_transform/
├── gui/
│   ├── simple_app.py       # Main app (uses its own components)
│   └── masw2d_tab.py       # Thin wrapper (~250 lines)
│
└── masw2d/
    ├── config/
    ├── geometry/
    ├── extraction/
    ├── processing/
    ├── workflows/
    ├── output/
    │
    └── gui/                # NEW: MASW 2D specific GUI components
        ├── __init__.py
        ├── defaults.py             # MASW 2D default values (~40 lines)
        ├── array_setup.py          # Array config panel (~100 lines)
        ├── file_manager.py         # Shot file tree + import (~130 lines)
        ├── subarray_config.py      # Sub-array checkboxes (~130 lines)
        ├── processing_panel.py     # Method + freq/vel settings (~80 lines)
        ├── advanced_settings.py    # MASW 2D advanced settings (~200 lines)
        ├── output_panel.py         # Output + parallel settings (~70 lines)
        ├── layout_preview.py       # Matplotlib layout preview (~180 lines)
        └── info_panel.py           # Info text display (~40 lines)
```

---

## Component Details

### 1. `masw2d/gui/defaults.py` (~40 lines)

MASW 2D specific defaults:

```python
MASW2D_DEFAULTS = {
    # Array
    'n_channels': '24',
    'dx': '2.0',
    'source_type': 'hammer',
    
    # Sub-array
    'slide_step': '1',
    
    # Processing
    'method': 'ps',
    'freq_min': '5',
    'freq_max': '80',
    'vel_min': '100',
    'vel_max': '1500',
    
    # Transform
    'grid_n': '4000',
    'vspace': 'log',
    'tol': '0.01',
    'power_threshold': '0.1',
    'vibrosis': False,
    'cylindrical': False,
    
    # Preprocessing
    'start_time': '0.0',
    'end_time': '1.0',
    'downsample': True,
    'down_factor': '16',
    'numf': '4000',
    
    # Export
    'plot_max_vel': 'auto',
    'plot_max_freq': 'auto',
    'cmap': 'jet',
    'dpi': '150',
}
```

---

### 2. `masw2d/gui/array_setup.py` (~100 lines)

Array configuration panel:

```python
class ArraySetupPanel(ttk.LabelFrame):
    """Array Setup: channels, spacing, source type."""
    
    def __init__(self, parent, on_update_callback=None):
        super().__init__(parent, text="Array Setup")
        
        self.n_channels_var = tk.StringVar(value="24")
        self.dx_var = tk.StringVar(value="2.0")
        self.source_type_var = tk.StringVar(value="hammer")
        
        self.on_update = on_update_callback
        self._build_ui()
    
    def get_values(self) -> dict:
        return {
            'n_channels': int(self.n_channels_var.get()),
            'dx': float(self.dx_var.get()),
            'source_type': self.source_type_var.get(),
            'array_length': self._calculate_length(),
        }
    
    def _calculate_length(self) -> float:
        n = int(self.n_channels_var.get())
        dx = float(self.dx_var.get())
        return (n - 1) * dx
```

---

### 3. `masw2d/gui/file_manager.py` (~130 lines)

Shot file management:

```python
class FileManagerPanel(ttk.LabelFrame):
    """Shot file treeview with import/add/clear."""
    
    def __init__(self, parent, main_app=None, log_callback=None):
        super().__init__(parent, text="Shot Files")
        
        self.main_app = main_app
        self.log = log_callback or print
        
        self.shot_files: List[str] = []
        self.shot_data: List[dict] = []  # {file, offset, reverse, source_position}
        
        self._build_ui()
    
    def import_from_project(self): ...
    def add_files(self): ...
    def clear(self): ...
    
    @property
    def files(self) -> List[str]: ...
    @property
    def data(self) -> List[dict]: ...
```

---

### 4. `masw2d/gui/subarray_config.py` (~130 lines)

Sub-array configuration:

```python
class SubarrayConfigPanel(ttk.LabelFrame):
    """Sub-array sizes with checkboxes and preview selector."""
    
    def __init__(self, parent, n_channels_var: tk.StringVar, 
                 on_preview_change=None):
        super().__init__(parent, text="Sub-Array Configurations")
        
        self.n_channels_var = n_channels_var
        self.on_preview_change = on_preview_change
        
        self.slide_step_var = tk.StringVar(value="1")
        self.preview_size_var = tk.StringVar()
        self.size_checks: Dict[int, tk.BooleanVar] = {}
        
        self._build_ui()
    
    def get_selected_sizes(self) -> List[int]: ...
    def get_slide_step(self) -> int: ...
    def get_preview_size(self) -> int: ...
    def update_for_channels(self, n_channels: int): ...
    
    # Quick select buttons
    def select_all(self): ...
    def select_none(self): ...
    def select_even(self): ...
```

---

### 5. `masw2d/gui/processing_panel.py` (~80 lines)

Processing method and limits:

```python
class ProcessingPanel(ttk.LabelFrame):
    """Method selection and frequency/velocity limits."""
    
    def __init__(self, parent, on_advanced_click=None):
        super().__init__(parent, text="Processing")
        
        self.method_var = tk.StringVar(value="ps")
        self.freq_min_var = tk.StringVar(value="5")
        self.freq_max_var = tk.StringVar(value="80")
        self.vel_min_var = tk.StringVar(value="100")
        self.vel_max_var = tk.StringVar(value="1500")
        
        self.on_advanced_click = on_advanced_click
        self._build_ui()
    
    def get_values(self) -> dict: ...
```

---

### 6. `masw2d/gui/advanced_settings.py` (~200 lines)

MASW 2D advanced settings manager:

```python
class MASW2DAdvancedSettings:
    """Advanced settings for MASW 2D processing."""
    
    def __init__(self):
        # Transform
        self.grid_n_var = tk.StringVar(value="4000")
        self.vspace_var = tk.StringVar(value="log")
        self.vibrosis_var = tk.BooleanVar(value=False)
        self.cylindrical_var = tk.BooleanVar(value=False)
        
        # Preprocessing
        self.start_time_var = tk.StringVar(value="0.0")
        self.end_time_var = tk.StringVar(value="1.0")
        self.downsample_var = tk.BooleanVar(value=True)
        self.down_factor_var = tk.StringVar(value="16")
        
        # Export
        self.plot_max_vel_var = tk.StringVar(value="auto")
        self.cmap_var = tk.StringVar(value="jet")
        self.dpi_var = tk.StringVar(value="150")
        
        self._setup_traces()
    
    def get_all_values(self) -> dict: ...
    def reset_to_defaults(self): ...
    def open_dialog(self, parent): ...
```

---

### 7. `masw2d/gui/output_panel.py` (~70 lines)

Output and parallel settings:

```python
class OutputPanel(ttk.LabelFrame):
    """Output directory and parallel processing settings."""
    
    def __init__(self, parent):
        super().__init__(parent, text="Output")
        
        self.output_dir_var = tk.StringVar()
        self.parallel_var = tk.BooleanVar(value=True)
        self.worker_var = tk.StringVar(value="auto")
        self.include_images_var = tk.BooleanVar(value=True)
        
        self._build_ui()
    
    def get_values(self) -> dict: ...
    def select_directory(self): ...
```

---

### 8. `masw2d/gui/layout_preview.py` (~180 lines)

Matplotlib layout visualization:

```python
class LayoutPreviewPanel(ttk.Frame):
    """Layout preview with info text and matplotlib canvas."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.canvas_widget = None
        self.current_layout = None
        
        self._build_ui()
    
    def update_preview(self, layout): ...
    def update_info_text(self, summary: str): ...
    
    def _plot_layout_on_axes(self, layout, ax_layout, ax_depth): ...
```

---

### 9. `masw2d/gui/info_panel.py` (~40 lines)

Info text display:

```python
class InfoPanel(ttk.LabelFrame):
    """Read-only text display for configuration info."""
    
    def __init__(self, parent, title="Configuration Info"):
        super().__init__(parent, text=title)
        self._build_ui()
    
    def set_text(self, text: str): ...
    def clear(self): ...
```

---

## Refactored `gui/masw2d_tab.py` (~250 lines)

```python
"""MASW 2D Tab - thin wrapper using masw2d.gui components."""

from sw_transform.masw2d.gui import (
    ArraySetupPanel, FileManagerPanel, SubarrayConfigPanel,
    ProcessingPanel, MASW2DAdvancedSettings, OutputPanel,
    LayoutPreviewPanel
)


class MASW2DTab:
    """MASW 2D processing tab widget."""
    
    def __init__(self, parent, log_callback=None, main_app=None):
        self.parent = parent
        self.log = log_callback or print
        self.main_app = main_app
        
        # Settings manager
        self.settings = MASW2DAdvancedSettings()
        
        self._build_ui()
    
    def _build_ui(self):
        paned = ttk.PanedWindow(self.parent, orient="horizontal")
        paned.pack(fill="both", expand=True)
        
        left = self._build_left_panel()
        right = self._build_right_panel()
        
        paned.add(left, weight=1)
        paned.add(right, weight=2)
    
    def _build_left_panel(self):
        frame = ttk.Frame()
        
        # Array setup
        self.array_panel = ArraySetupPanel(frame, on_update_callback=self._on_array_update)
        self.array_panel.pack(fill="x", padx=4, pady=4)
        
        # File manager
        self.file_panel = FileManagerPanel(frame, main_app=self.main_app, log_callback=self.log)
        self.file_panel.pack(fill="x", padx=4, pady=4)
        
        # Sub-array config
        self.subarray_panel = SubarrayConfigPanel(
            frame, 
            n_channels_var=self.array_panel.n_channels_var,
            on_preview_change=self._update_preview
        )
        self.subarray_panel.pack(fill="x", padx=4, pady=4)
        
        # Processing
        self.processing_panel = ProcessingPanel(
            frame,
            on_advanced_click=lambda: self.settings.open_dialog(self.parent)
        )
        self.processing_panel.pack(fill="x", padx=4, pady=4)
        
        # Output
        self.output_panel = OutputPanel(frame)
        self.output_panel.pack(fill="x", padx=4, pady=4)
        
        # Run button + progress
        self._build_run_section(frame)
        
        return frame
    
    def _build_right_panel(self):
        frame = ttk.Frame()
        
        self.preview = LayoutPreviewPanel(frame)
        self.preview.pack(fill="both", expand=True)
        
        return frame
    
    def _build_config(self) -> dict:
        """Build config from all panels."""
        return {
            "array": self.array_panel.get_values(),
            "shots": self.file_panel.data,
            "subarray_configs": self._build_subarray_configs(),
            "processing": {
                **self.processing_panel.get_values(),
                **self.settings.get_all_values(),
            },
            "output": self.output_panel.get_values(),
        }
    
    def _run_workflow(self):
        """Run the 2D MASW workflow."""
        config = self._build_config()
        # ... workflow execution logic
```

---

## Implementation Timeline

| Phase | Task | Est. Hours |
|-------|------|------------|
| 1 | `masw2d/gui/defaults.py` | 0.5 |
| 2 | `masw2d/gui/array_setup.py` | 1.5 |
| 3 | `masw2d/gui/file_manager.py` | 2 |
| 4 | `masw2d/gui/subarray_config.py` | 2 |
| 5 | `masw2d/gui/processing_panel.py` | 1 |
| 6 | `masw2d/gui/advanced_settings.py` | 2.5 |
| 7 | `masw2d/gui/output_panel.py` | 1 |
| 8 | `masw2d/gui/layout_preview.py` | 2.5 |
| 9 | `masw2d/gui/info_panel.py` | 0.5 |
| 10 | Refactor `gui/masw2d_tab.py` | 2-3 |

**Total: ~15-18 hours**

---

## Files to Create

```
masw2d/gui/__init__.py
masw2d/gui/defaults.py
masw2d/gui/array_setup.py
masw2d/gui/file_manager.py
masw2d/gui/subarray_config.py
masw2d/gui/processing_panel.py
masw2d/gui/advanced_settings.py
masw2d/gui/output_panel.py
masw2d/gui/layout_preview.py
masw2d/gui/info_panel.py
```

## Files to Modify

```
gui/masw2d_tab.py  # Major refactor (thin wrapper)
masw2d/__init__.py # Add gui exports
```

---

## Benefits of Separate MASW 2D GUI

1. **Follows existing pattern** - MASW 2D already has config/, geometry/, workflows/
2. **Independent development** - Can be developed/tested separately
3. **Clear ownership** - All MASW 2D code in one place
4. **Easier navigation** - Developers know where to look
5. **Future extensibility** - Easy to add more MASW 2D GUI features
