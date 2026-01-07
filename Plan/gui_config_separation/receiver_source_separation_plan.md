# GUI Configuration Separation Plan

## Overview

Separate the current `ArrayConfigPanel` into two distinct panels:
1. **ReceiverConfigPanel** - Geophone/receiver array settings
2. **SourceConfigPanel** - Per-file source position settings

Additionally, add **Preview Open in Window** feature with proper proportional layout.

---

## Phase 1: Rename ArrayConfigPanel → ReceiverConfigPanel

### Files to Modify
- `gui/components/array_config_panel.py` → rename to `receiver_config_panel.py`
- `gui/components/__init__.py` - update exports
- `gui/simple_app.py` - update imports and usage

### Changes Required
1. Rename class `ArrayConfigPanel` → `ReceiverConfigPanel`
2. Update panel title: "Receiver Configuration"
3. **REMOVE** source position section from this panel
4. Keep only:
   - File Info display (channels, spacing)
   - Channel Selection (all, first_n, last_n, range, custom)
   - Geophone Spacing (uniform dx, custom positions)

### Key Attention Points
- Ensure `get_config()` and `set_config()` still work without source_position
- Update `ArrayConfig` dataclass or create separate `ReceiverConfig`
- Preview callback must still work after rename

---

## Phase 2: Create SourceConfigPanel

### New File
- `gui/components/source_config_panel.py`

### UI Structure
```
▶ Source Configuration  [5 files, mode=standard]
┌─────────────────────────────────────────────────────────────┐
│ Mode: ○ Standard (auto from filenames)  ○ Custom            │
│                                                              │
│ Interior shot handling: ○ Left  ○ Right  ○ Both             │
├─────────────────────────────────────────────────────────────┤
│ File          │ Source Position (m) │ Shot Type             │
├───────────────┼────────────────────┼───────────────────────┤
│ 1             │ -13.0              │ exterior_left          │
│ 2             │ +66.0              │ exterior_right         │
│ ...           │ ...                │ ...                    │
└───────────────┴────────────────────┴───────────────────────┘
```

### Features
1. **Collapsible** like ReceiverConfigPanel
2. **Embedded Treeview table** showing all loaded files
3. **Two modes**:
   - Standard: Auto-populate from filename parsing
   - Custom: User edits each row individually
4. **Shot Type column**: Auto-calculated from source position vs receiver array
5. **Sync with FileTreePanel**: When files added/removed, update table

### Key Attention Points
- Must receive file list from `FileTreePanel`
- Must receive receiver positions from `ReceiverConfigPanel` to calculate shot type
- Table must be editable only in Custom mode
- Double-click to edit source position (like current file tree offset editing)

### Data Flow
```
FileTreePanel.files → SourceConfigPanel.update_files()
ReceiverConfigPanel.get_config() → SourceConfigPanel.update_shot_types()
SourceConfigPanel.get_source_positions() → dict[base_name, float]
```

### Linking Logic
```python
if receiver_config.channel_mode != 'all':
    # Force custom source mode - standard assumptions don't apply
    source_config.set_mode('custom')
    source_config.disable_standard_mode()
```

---

## Phase 3: Preview Open in Window

### Files to Modify
- `gui/components/array_preview.py`

### New Features
1. Add "Open in Window" button next to "Preview Array / Waterfall"
2. Create `PreviewWindow` class (Toplevel)

### PreviewWindow Requirements
- **Resizable** with minimum size
- **Proportional layout** that scales with window size
- **Aligned axes**: Waterfall x-axis aligned with schematic x-axis
- **No overlapping**: Titles, legends, axis labels must not overlap

### Layout Implementation
```python
# Use constrained_layout or tight_layout with proper rect
fig = Figure(figsize=(10, 8), dpi=100, constrained_layout=True)

# Use GridSpec with shared x-axis
gs = fig.add_gridspec(2, 1, height_ratios=[1, 4], hspace=0.05)
ax_schematic = fig.add_subplot(gs[0])
ax_waterfall = fig.add_subplot(gs[1], sharex=ax_schematic)

# Hide x-axis labels on schematic (shared with waterfall)
ax_schematic.tick_params(labelbottom=False)
```

### Key Attention Points
- Store figure data so window can be reopened
- Window should update when preview updates (optional: add checkbox)
- Legend placement: outside plot area or inside with transparency
- Handle window close properly (don't crash main app)

---

## Phase 4: Integration

### simple_app.py Changes

1. **Imports**:
```python
from sw_transform.gui.components import (
    ReceiverConfigPanel,  # renamed from ArrayConfigPanel
    SourceConfigPanel,    # new
    ...
)
```

2. **Component References**:
```python
self.receiver_config: ReceiverConfigPanel | None = None
self.source_config: SourceConfigPanel | None = None
```

3. **Build Order** in `_build_inputs_tab`:
```python
# 1. Processing limits
# 2. Receiver Configuration (collapsible)
# 3. Source Configuration (collapsible)
# 4. Figure title
# 5. Advanced settings
# 6. Array preview
```

4. **Callbacks to Wire**:
```python
# When files change
self.file_tree.on_files_change = self._on_files_change

def _on_files_change(self):
    if self.source_config:
        self.source_config.update_files(self.file_tree.get_file_info())

# When receiver config changes
self.receiver_config = ReceiverConfigPanel(p, on_config_change=self._on_receiver_config_change)

def _on_receiver_config_change(self):
    # Update source config shot types
    if self.source_config and self.receiver_config:
        cfg = self.receiver_config.get_config()
        self.source_config.update_receiver_positions(cfg.get_positions())
    # Refresh preview
    self._on_array_config_change()
```

5. **Processing Integration**:
```python
# In run_single_processing and run_compare_processing
source_positions = self.source_config.get_source_positions()  # dict[base, float]

for path in paths:
    base = os.path.splitext(os.path.basename(path))[0]
    src_pos = source_positions.get(base, -10.0)
    params['source_position'] = src_pos
```

---

## Phase 5: Testing and Refinement

### Test Cases

1. **Basic Flow**:
   - Load 48-channel file
   - Set receiver to First 24
   - Verify source config forces custom mode
   - Edit source positions
   - Run processing

2. **Preview Window**:
   - Open preview in window
   - Resize window - verify proportional scaling
   - Verify traces align under receivers
   - Verify no overlapping text

3. **File Operations**:
   - Add files → verify source table updates
   - Remove files → verify source table updates
   - Clear all → verify source table clears

4. **Mode Switching**:
   - Standard → Custom: Preserve existing positions
   - Custom → Standard: Re-calculate from filenames
   - Receiver custom → Source forced custom

### Edge Cases
- Empty file list
- Single file
- Mixed .dat and .mat files
- Files with unparseable names (no offset info)
- Interior shots (source between receivers)

### Performance
- Large file list (50+ files): Verify table doesn't lag
- Frequent preview updates: Verify no memory leaks

---

## File Summary

| File | Action |
|------|--------|
| `array_config_panel.py` | Rename → `receiver_config_panel.py`, remove source section |
| `source_config_panel.py` | **NEW** - Collapsible panel with file table |
| `array_preview.py` | Add "Open in Window" button and PreviewWindow class |
| `__init__.py` | Update exports |
| `simple_app.py` | Wire new components, update callbacks |
| `core/array_config.py` | Possibly split into ReceiverConfig + SourceConfig |
