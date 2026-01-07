# Geophone Configuration Tests

QC tests for the geophone array configuration implementation.

## Related Plan

See: `Plan/geophone_config/geophone_full_config.md`

## Test Structure

| File | Phase | Description |
|------|-------|-------------|
| `test_phase1_array_config.py` | Phase 1 | ArrayConfig dataclass - channel selection, positions, shot classification |
| `test_phase2_transforms.py` | Phase 2 | Transform updates for non-uniform spacing (TODO) |
| `test_phase3_gui.py` | Phase 3 | GUI array config panel (TODO) |

## Running Tests

```powershell
# From Test/geophone_config folder
python run_tests.py

# Or with pytest directly
python -m pytest Test/geophone_config -v

# Run only Phase 1 tests
python run_tests.py --phase1
```

## Test Coverage Summary

### Phase 1: Core Data Structure (`test_phase1_array_config.py`)

**Channel Selection Modes (Section 4.1)**
- [x] `all` - Use all channels
- [x] `first_n` - Use first N channels  
- [x] `last_n` - Use last N channels
- [x] `range` - Use channel range [start, end)
- [x] `custom` - Use specific indices

**Spacing/Position Modes (Section 4.2)**
- [x] Uniform spacing with dx
- [x] Custom positions array
- [x] Min spacing calculation for aliasing

**Shot Type Handling (Section 4.3)**
- [x] `exterior_left` - Source before array
- [x] `exterior_right` - Source after array
- [x] `edge_left` - Source at first geophone
- [x] `edge_right` - Source at last geophone
- [x] `interior` - Source within array

**Interior Shot Options (Section 4.4)**
- [x] Split both sides
- [x] Left side only (reversed)
- [x] Right side only
- [x] Minimum channel count enforcement

**Additional Tests**
- [x] Data extraction with `get_effective_data()`
- [x] Serialization `to_dict()`/`from_dict()`
- [x] Factory functions
- [x] Spec compliance tests (Section 7)

## Status

| Phase | Status | Tests |
|-------|--------|-------|
| Phase 1 | ✅ Implemented | 50+ tests |
| Phase 2 | ⬜ Not started | - |
| Phase 3 | ⬜ Not started | - |
| Phase 4 | ⬜ Not started | - |
| Phase 5 | ⬜ Not started | - |
| Phase 6 | ⬜ Not started | - |
