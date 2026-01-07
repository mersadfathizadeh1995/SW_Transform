# Phase 1: Core Data Structure - COMPLETED

**Date:** January 7, 2026  
**Status:** ✅ Complete

## Files Created

| File | Description |
|------|-------------|
| `SRC/sw_transform/core/array_config.py` | ArrayConfig dataclass |
| `Test/test_array_config.py` | Unit tests (35 tests) |

## ArrayConfig Features

- **Channel Selection**: `all`, `first_n`, `last_n`, `range`, `custom`
- **Spacing Modes**: `uniform`, `custom` positions
- **Shot Classification**: `exterior_left/right`, `edge_left/right`, `interior`
- **Interior Shot Split**: Automatic left/right splitting with min 6 channels
- **Serialization**: `to_dict()` / `from_dict()` for persistence

## Key Methods

| Method | Purpose |
|--------|---------|
| `get_selected_indices()` | Returns channel indices to use |
| `get_positions()` | Returns geophone positions (meters) |
| `get_effective_data(data)` | Extracts selected channels from array |
| `classify_shot()` | Determines shot type from source position |
| `needs_reverse()` | Checks if data reversal needed |
| `split_interior_shot()` | Splits interior shot into virtual shots |
| `get_min_spacing()` | Returns minimum spacing (for aliasing) |

## Factory Functions

- `create_default_config(n_channels, dx, source_offset)`
- `create_first_n_config(n_file, n_use, dx, source_offset)`
- `create_custom_positions_config(n_file, positions, source_pos)`

## Test Results

```
35 passed in 0.29s
```

All channel selection modes, position calculations, shot classification, interior splitting, and serialization tested.
