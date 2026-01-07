# Phase 2: SourceConfigPanel Implementation

## Summary

Created new `SourceConfigPanel` component with embedded file table for per-file source position management.

## Files Created

- `SRC/sw_transform/gui/components/source_config_panel.py`
- `Test/gui_config_separation/test_phase2_source_config.py`

## Files Modified

- `SRC/sw_transform/gui/components/__init__.py` - Added SourceConfigPanel export
- `SRC/sw_transform/gui/simple_app.py` - Integrated SourceConfigPanel

## Key Features

### SourceConfigPanel

- **Collapsible** header with summary
- **Mode selector**: Standard (auto from filenames) / Custom (manual edit)
- **Interior shot side**: Left / Right / Both
- **Embedded Treeview table**: File, Offset, Source Pos (m), Shot Type
- **Double-click editing** in Custom mode
- **Shot type calculation**: exterior_left, exterior_right, edge_left, edge_right, interior

### Integration

- Synced with FileTreePanel via `update_files()`
- Synced with ReceiverConfigPanel via `update_receiver_positions()`
- Auto-forces custom mode when receiver uses non-standard channel selection
- Clears when files cleared

## Methods

| Method | Description |
|--------|-------------|
| `update_files(file_info)` | Populate from FileTreePanel |
| `update_receiver_positions(positions)` | Update shot types |
| `get_source_positions()` | Returns dict[base, float] |
| `get_interior_side()` | Returns interior side setting |
| `is_custom_mode()` | Check if custom mode |
| `set_mode(mode)` | Set standard/custom |
| `force_custom_mode()` | Force custom mode |
| `clear()` | Clear all data |

## Test Results

```
12 passed (3 environment errors due to Tcl in pytest)
```

Manual verification passed via python -c commands.

## Test File

- `Test/gui_config_separation/test_phase2_source_config.py`
