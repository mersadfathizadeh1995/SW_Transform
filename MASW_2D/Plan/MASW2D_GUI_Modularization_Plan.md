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
├── app.py                    # Main app entry
├── simple_app.py             # Simplified (or refactored to use components)
├── masw2d_tab.py             # Thin wrapper, uses components
│
├── components/               # NEW: Reusable UI components
│   ├── __init__.py
│   ├── array_setup.py        # Array configuration panel
│   ├── file_manager.py       # Shot file treeview + import/add/clear
│   ├── subarray_config.py    # Sub-array checkboxes + preview selector
│   ├── processing_settings.py # Method, freq, velocity settings
│   ├── advanced_settings.py  # Advanced settings popup (shared)
│   ├── output_settings.py    # Output directory, parallel, export options
│   └── layout_preview.py     # Matplotlib preview canvas
│
├── dialogs/                  # NEW: Popup dialogs
│   ├── __init__.py
│   └── advanced_settings_dialog.py
│
└── utils/                    # NEW: GUI utilities
    ├── __init__.py
    ├── defaults.py           # Shared default values
    └── validators.py         # Input validation helpers
```

---

## Phase 1: Extract Shared Defaults & Utilities

### 1.1 Create `gui/utils/defaults.py`

Centralize all default values used by both `simple_app.py` and `masw2d_tab.py`:

```python
# gui/utils/defaults.py

# Transform defaults
TRANSFORM_DEFAULTS = {
    'grid_n': '4000',
    'vspace': 'log',
    'tol': '0.01',
    'power_threshold': '0.1',
}

# Preprocessing defaults
PREPROCESS_DEFAULTS = {
    'start_time': '0.0',
    'end_time': '1.0',
    'downsample': True,
    'down_factor': '16',
    'numf': '4000',
}

# Plot/export defaults
PLOT_DEFAULTS = {
    'plot_max_vel': 'auto',
    'plot_max_freq': 'auto',
    'cmap': 'jet',
    'dpi': '150',
}

# FDBF-specific defaults
FDBF_DEFAULTS = {
    'vibrosis': False,
    'cylindrical': False,
    'dx': '2.0',  # Vibrosis sensor spacing
}

# Array defaults (MASW 2D)
ARRAY_DEFAULTS = {
    'n_channels': '24',
    'dx': '2.0',
    'slide_step': '1',
    'source_type': 'hammer',
}

# Processing defaults
PROCESSING_DEFAULTS = {
    'method': 'ps',
    'freq_min': '5',
    'freq_max': '80',
    'vel_min': '100',
    'vel_max': '1500',
}
```

**Estimated effort: 1-2 hours**

---

## Phase 2: Create Reusable Components

### 2.1 `components/array_setup.py` (~80 lines)

Encapsulates:
- Total channels entry
- Spacing (dx) entry
- Source type combobox
- Array length display
- "Update Array" button

```python
class ArraySetupPanel(ttk.LabelFrame):
    def __init__(self, parent, on_update_callback=None):
        ...
    
    def get_values(self) -> dict:
        return {
            'n_channels': int(...),
            'dx': float(...),
            'source_type': str(...),
        }
    
    def set_values(self, **kwargs): ...
```

**Estimated effort: 2 hours**

---

### 2.2 `components/file_manager.py` (~150 lines)

Encapsulates:
- Treeview with columns (File, Offset, Rev, Source Pos)
- Import from project button
- Add files button
- Clear button
- File data storage

```python
class FileManagerPanel(ttk.LabelFrame):
    def __init__(self, parent, main_app=None, log_callback=None):
        ...
    
    @property
    def shot_files(self) -> List[str]: ...
    
    @property
    def shot_data(self) -> List[Dict]: ...
    
    def clear(self): ...
    def add_files(self, files: List[str]): ...
    def import_from_project(self): ...
```

**Estimated effort: 2-3 hours**

---

### 2.3 `components/subarray_config.py` (~120 lines)

Encapsulates:
- Quick select buttons (All, None, Even)
- Dynamic checkboxes grid
- Slide step entry
- Preview size combobox

```python
class SubarrayConfigPanel(ttk.LabelFrame):
    def __init__(self, parent, n_channels_var, on_preview_change=None):
        ...
    
    def get_selected_sizes(self) -> List[int]: ...
    def get_slide_step(self) -> int: ...
    def get_preview_size(self) -> int: ...
    def update_for_channels(self, n_channels: int): ...
```

**Estimated effort: 2 hours**

---

### 2.4 `components/processing_settings.py` (~80 lines)

Encapsulates:
- Method combobox (fk, ps, fdbf, ss)
- Frequency range (min-max)
- Velocity range (min-max)
- Advanced settings button (opens dialog)

```python
class ProcessingSettingsPanel(ttk.LabelFrame):
    def __init__(self, parent, on_advanced_click=None):
        ...
    
    def get_values(self) -> dict: ...
    def set_values(self, **kwargs): ...
```

**Estimated effort: 1-2 hours**

---

### 2.5 `components/advanced_settings.py` (~250 lines)

**The big one!** This creates the Advanced Settings popup that's shared between `simple_app.py` and `masw2d_tab.py`.

Encapsulates:
- Transform settings (grid_n, vspace, vibrosis, cylindrical)
- Peak picking (tol, power_threshold)
- Preprocessing (time window, downsample, FFT size)
- Image export (plot limits, cmap, dpi, tick spacing)

```python
class AdvancedSettingsManager:
    """Manages advanced settings variables and provides popup dialog."""
    
    def __init__(self):
        # All tk.StringVar / tk.BooleanVar created here
        self.grid_n_var = tk.StringVar(value=TRANSFORM_DEFAULTS['grid_n'])
        self.vibrosis_var = tk.BooleanVar(value=False)
        # ... etc
    
    def open_dialog(self, parent: tk.Widget):
        """Open the advanced settings popup."""
        ...
    
    def get_all_values(self) -> dict:
        """Return all settings as a dictionary."""
        ...
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        ...
```

**Estimated effort: 4-5 hours**

---

### 2.6 `components/output_settings.py` (~60 lines)

Encapsulates:
- Output directory entry + browse button
- Parallel checkbox + worker count
- Export images checkbox

```python
class OutputSettingsPanel(ttk.LabelFrame):
    def __init__(self, parent):
        ...
    
    def get_values(self) -> dict: ...
```

**Estimated effort: 1 hour**

---

### 2.7 `components/layout_preview.py` (~180 lines)

Encapsulates:
- Info text display
- Matplotlib canvas for layout visualization
- Update methods

```python
class LayoutPreviewPanel(ttk.Frame):
    def __init__(self, parent):
        ...
    
    def update_preview(self, layout): ...
    def update_info_text(self, text: str): ...
```

**Estimated effort: 2-3 hours**

---

## Phase 3: Refactor `masw2d_tab.py`

After creating components, `masw2d_tab.py` becomes a thin orchestrator:

```python
# masw2d_tab.py (~200 lines instead of ~950)

from sw_transform.gui.components import (
    ArraySetupPanel,
    FileManagerPanel,
    SubarrayConfigPanel,
    ProcessingSettingsPanel,
    AdvancedSettingsManager,
    OutputSettingsPanel,
    LayoutPreviewPanel,
)

class MASW2DTab:
    def __init__(self, parent, log_callback=None, main_app=None):
        self.parent = parent
        self.log = log_callback or print
        self.main_app = main_app
        
        # Advanced settings manager (shared state)
        self.advanced = AdvancedSettingsManager()
        
        self._build_ui()
    
    def _build_ui(self):
        # Create paned window
        paned = ttk.PanedWindow(self.parent, orient="horizontal")
        
        # Left panel - compose from components
        left = ttk.Frame(paned)
        self.array_panel = ArraySetupPanel(left, on_update_callback=self._on_array_update)
        self.file_panel = FileManagerPanel(left, main_app=self.main_app, log_callback=self.log)
        self.subarray_panel = SubarrayConfigPanel(left, self.array_panel.n_channels_var, 
                                                   on_preview_change=self._update_preview)
        self.processing_panel = ProcessingSettingsPanel(left, 
                                                         on_advanced_click=lambda: self.advanced.open_dialog(self.parent))
        self.output_panel = OutputSettingsPanel(left)
        
        # Right panel - preview
        right = ttk.Frame(paned)
        self.preview_panel = LayoutPreviewPanel(right)
        
        # Run button + progress
        self._build_run_section(left)
    
    def _build_config(self) -> dict:
        """Compose config from all panels."""
        return {
            "array": self.array_panel.get_values(),
            "shots": self.file_panel.shot_data,
            "subarray_configs": self._build_subarray_configs(),
            "processing": {
                **self.processing_panel.get_values(),
                **self.advanced.get_all_values(),
            },
            "output": self.output_panel.get_values(),
        }
    
    def _run_workflow(self):
        # Same as before, but cleaner
        ...
```

**Estimated effort: 3-4 hours**

---

## Phase 4: Vibrosis/FDBF Integration

### 4.1 Current Vibrosis Implementation

**In `simple_app.py`:**
- `vibrosis_mode` BooleanVar
- `cylindrical_var` BooleanVar  
- `dx_var` for sensor spacing
- Auto-link: vibrosis → cylindrical
- Settings passed to service layer

**In `masw2d_tab.py`:**
- Same variables exist in Advanced Settings popup
- Also has `source_type_var` (hammer/vibrosis)

### 4.2 Unified Vibrosis Settings Component

Create a dedicated vibrosis settings section in the shared `AdvancedSettingsManager`:

```python
# In advanced_settings.py

class AdvancedSettingsManager:
    def __init__(self):
        # ... other vars ...
        
        # FDBF / Vibrosis settings
        self.vibrosis_var = tk.BooleanVar(value=False)
        self.cylindrical_var = tk.BooleanVar(value=False)
        self.vibrosis_dx_var = tk.StringVar(value="2.0")
        
        # Auto-link vibrosis → cylindrical
        self.vibrosis_var.trace_add('write', self._on_vibrosis_changed)
    
    def _on_vibrosis_changed(self, *args):
        if self.vibrosis_var.get():
            self.cylindrical_var.set(True)
```

### 4.3 Method-Specific Settings Display

When method is "fdbf", show vibrosis options more prominently:

```python
# In processing_settings.py or advanced dialog

def _on_method_changed(self, *args):
    method = self.method_var.get()
    if method == 'fdbf':
        # Show vibrosis frame
        self.vibrosis_frame.pack(...)
    else:
        # Hide vibrosis frame  
        self.vibrosis_frame.pack_forget()
```

**Estimated effort: 2-3 hours**

---

## Phase 5: Apply to `simple_app.py` (Optional)

The same components can be reused in `simple_app.py` to reduce its size from ~1560 lines.

Key refactoring opportunities:
- Use `AdvancedSettingsManager` for the advanced popup
- Use shared defaults from `gui/utils/defaults.py`
- Extract file list management to a component

**Estimated effort: 4-6 hours (optional phase)**

---

## Implementation Order & Timeline

| Phase | Task | Est. Hours | Priority |
|-------|------|------------|----------|
| 1 | Create `utils/defaults.py` | 1-2 | High |
| 2.5 | Create `AdvancedSettingsManager` | 4-5 | High |
| 2.1 | Create `ArraySetupPanel` | 2 | High |
| 2.2 | Create `FileManagerPanel` | 2-3 | High |
| 2.3 | Create `SubarrayConfigPanel` | 2 | High |
| 2.4 | Create `ProcessingSettingsPanel` | 1-2 | High |
| 2.6 | Create `OutputSettingsPanel` | 1 | Medium |
| 2.7 | Create `LayoutPreviewPanel` | 2-3 | Medium |
| 3 | Refactor `masw2d_tab.py` | 3-4 | High |
| 4 | Vibrosis/FDBF integration | 2-3 | High |
| 5 | Apply to `simple_app.py` | 4-6 | Optional |

**Total estimated: 24-35 hours**

---

## Benefits

1. **Maintainability**: Each component is ~60-150 lines instead of one 950-line file
2. **Reusability**: Components can be used in both tabs and future GUIs
3. **Testability**: Components can be tested independently
4. **Consistency**: Shared defaults ensure same behavior across interfaces
5. **Extensibility**: Adding new features is easier when code is modular

---

## File Changes Summary

### New Files to Create:
```
gui/components/__init__.py
gui/components/array_setup.py
gui/components/file_manager.py
gui/components/subarray_config.py
gui/components/processing_settings.py
gui/components/advanced_settings.py
gui/components/output_settings.py
gui/components/layout_preview.py
gui/utils/__init__.py
gui/utils/defaults.py
gui/utils/validators.py (optional)
```

### Files to Modify:
```
gui/masw2d_tab.py         # Refactor to use components
gui/simple_app.py         # Optionally refactor (Phase 5)
gui/__init__.py           # Update exports
```

---

## Next Steps

1. **Review this plan** - Let me know if you want to:
   - Adjust the component boundaries
   - Change the priority order
   - Add/remove features
   - Simplify (fewer components)
   - Expand (more granular components)

2. **Approve and start implementation** - I'll create the components one by one, testing as we go.

---

## Questions for Review

1. Should the components be pure tkinter or should they have some business logic?
2. Do you want to keep backward compatibility with existing config files?
3. Should we add unit tests for the components?
4. Priority: Do vibrosis/FDBF integration first, or modularization first?
