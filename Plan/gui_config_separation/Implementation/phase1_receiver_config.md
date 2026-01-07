# Phase 1: ReceiverConfigPanel Implementation

## Summary
Renamed `ArrayConfigPanel` to `ReceiverConfigPanel` and removed source position section.

## Files Created
- `SRC/sw_transform/gui/components/receiver_config_panel.py`

## Files Modified
- `SRC/sw_transform/gui/components/__init__.py` - Added ReceiverConfigPanel export
- `SRC/sw_transform/gui/simple_app.py` - Updated to use ReceiverConfigPanel

## Key Changes

### ReceiverConfigPanel
- Title changed: "Array Configuration" → "Receiver Configuration"
- **Removed**: Source Position section (source_position_var, interior_side_var)
- **Added**: `is_custom_mode()` method to check if non-standard channel selection
- `get_config()` returns default `source_position=-10.0`, `interior_side='both'`

### Backward Compatibility
- `ArrayConfigPanel` still importable and functional
- `SimpleMASWGUI.array_config` is alias to `receiver_config`
- `_on_array_config_change()` calls `_on_receiver_config_change()`

## Test Results
```
14 passed in 1.27s
```

## Test File
- `Test/gui_config_separation/test_phase1_receiver_config.py`
