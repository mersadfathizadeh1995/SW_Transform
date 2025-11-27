# Implementation Plan: Power Spectrum Export Feature

**Version**: 1.0
**Date**: November 10, 2025
**Target**: Add .npz spectrum export to SW_Transform package

---

## Overview

Add optional export of 2D power spectrum data to NumPy .npz format for advanced analysis, ML training, custom picking, and publication-quality figure generation.

---

## Implementation Strategy

### Design Principles
1. **Optional**: Feature is OFF by default (no change to existing workflow)
2. **Minimal overhead**: Only save when requested by user
3. **Per-method data**: Each method (FK, FDBF, PS, SS) has different spectral representation
4. **Metadata included**: Offset, vibrosis mode, processing parameters
5. **Consistent naming**: `<base>_<method>_spectrum.npz`

---

## File Structure Per Method

### FK Method
```python
{
    'frequencies': 1D array (e.g., 200 points, 0-100 Hz)
    'velocities': 1D array (e.g., 400 points, 0-5000 m/s)
    'power': 2D array (nvel × nfreq) - normalized FK spectrum
    'wavenumbers': 1D array - original k-space axis
    'picked_velocities': 1D array - dispersion curve
    'method': 'fk'
    'offset': '+66m' (string)
    'vibrosis_mode': False (boolean)
    'params': dict with processing params
}
```

### FDBF Method
```python
{
    'frequencies': 1D array (subsampled, ~400 points)
    'velocities': 1D array (computed from wavenumbers)
    'power': 2D array - beamformer power
    'wavenumbers': 1D array
    'picked_velocities': 1D array
    'method': 'fdbf'
    'offset': '+66m'
    'vibrosis_mode': True  # if used
    'weight_mode': 'invamp' or 'none'
    'params': dict
}
```

### PS Method
```python
{
    'frequencies': 1D array
    'velocities': 1D array (log or linear spaced)
    'power': 2D array - phase-shift power
    'picked_velocities': 1D array
    'method': 'ps'
    'offset': '+66m'
    'vspace': 'log' or 'linear'
    'params': dict
}
```

### SS Method
```python
{
    'frequencies': 1D array
    'velocities': 1D array
    'power': 2D array - slant-stack power
    'picked_velocities': 1D array
    'method': 'ss'
    'offset': '+66m'
    'params': dict
}
```

---

## Implementation Plan - TODO List

### Phase 1: Core Service Layer Modifications

**File**: `SRC/sw_transform/core/service.py`

- [ ] **Task 1.1**: Add `export_spectra` parameter to `run_single()` function
  - Default: `False`
  - Type: `bool`
  - Pass through from GUI/CLI

- [ ] **Task 1.2**: Create helper function `_save_spectrum_npz()`
  ```python
  def _save_spectrum_npz(outdir: str, base: str, key: str, offset: str,
                         freq: np.ndarray, vel: np.ndarray, power: np.ndarray,
                         vmax: np.ndarray, params: dict) -> None:
      """Save power spectrum to .npz file with metadata"""
  ```
  - Construct filename: `{base}_{key}_spectrum.npz`
  - Save all arrays and metadata
  - Handle errors gracefully

- [ ] **Task 1.3**: Modify FK processing section (lines ~90-99)
  - After computing `pnorm`, `vmax`, extract velocity axis from `ktrial`
  - Convert wavenumber to velocity: `v = 2π × f / k`
  - Call `_save_spectrum_npz()` if `export_spectra=True`

- [ ] **Task 1.4**: Modify FDBF processing section (lines ~100-110)
  - After computing `pnorm`, `vmax`, extract velocity from `ktrial`
  - Include `weight_mode` in metadata
  - Call `_save_spectrum_npz()`

- [ ] **Task 1.5**: Modify PS processing section (lines ~111-118)
  - After computing `pnorm`, `vmax`
  - `vels` array already exists, use directly
  - Include `vspace` in metadata
  - Call `_save_spectrum_npz()`

- [ ] **Task 1.6**: Modify SS processing section (lines ~119-126)
  - After computing `pnorm`, `vmax`
  - `vels` array already exists
  - Call `_save_spectrum_npz()`

- [ ] **Task 1.7**: Add `export_spectra` parameter to `run_compare()` function
  - Similar modifications for compare mode
  - Save spectrum for each method (FK, FDBF, PS, SS)
  - Lines ~141-234

---

### Phase 2: GUI Integration

**File**: `SRC/sw_transform/gui/simple_app.py`

- [ ] **Task 2.1**: Add BooleanVar for spectrum export
  - Line ~79: `self.export_spectra_var = tk.BooleanVar(value=False)`

- [ ] **Task 2.2**: Add checkbox in "Figure / Export" section
  - After "Figure DPI" and "Topic" fields (line ~152)
  - Text: "☐ Export power spectra (.npz)"
  - Tooltip (future): Explain what this exports

- [ ] **Task 2.3**: Pass parameter to `run_single()` in `run_single_processing()`
  - Line ~432: Add `export_spectra=self.export_spectra_var.get()` to params dict

- [ ] **Task 2.4**: Pass parameter to `run_compare()` in `run_compare_processing()`
  - Line ~503: Add `export_spectra=self.export_spectra_var.get()` to params dict

- [ ] **Task 2.5**: Add log messages when spectra are saved
  - In logbox: "Saved spectrum: shot01_fk_spectrum.npz"

---

### Phase 3: CLI Integration

**File**: `SRC/sw_transform/cli/single.py`

- [ ] **Task 3.1**: Add `--export-spectra` flag to argument parser
  - Line ~16-19: Add argument
  - Type: `action='store_true'` (boolean flag, no value needed)
  - Help text: "Export full power spectra to .npz files"

- [ ] **Task 3.2**: Pass flag to params dict
  - Line ~41: Add `export_spectra=a.export_spectra`

**File**: `SRC/sw_transform/cli/compare.py`

- [ ] **Task 3.3**: Add `--export-spectra` flag
  - Similar to single.py

- [ ] **Task 3.4**: Pass flag to params dict

---

### Phase 4: Testing & Validation

- [ ] **Task 4.1**: Unit tests for `_save_spectrum_npz()`
  - Test file creation
  - Test metadata correctness
  - Test array shapes

- [ ] **Task 4.2**: Integration test - FK method
  - Run processing with export enabled
  - Load .npz file, verify contents
  - Check: frequencies, velocities, power, picked_velocities, metadata

- [ ] **Task 4.3**: Integration test - FDBF method
  - With vibrosis mode ON
  - Verify `vibrosis_mode=True` and `weight_mode='invamp'` in file

- [ ] **Task 4.4**: Integration test - PS method
  - Check velocity spacing (log vs linear)

- [ ] **Task 4.5**: Integration test - SS method

- [ ] **Task 4.6**: Integration test - Compare mode
  - Verify 4 separate spectrum files created

- [ ] **Task 4.7**: Test GUI checkbox
  - Check ON → files created
  - Check OFF → no spectrum files

- [ ] **Task 4.8**: Test CLI flag
  - With `--export-spectra` → files created
  - Without flag → no spectrum files

---

### Phase 5: Documentation

- [ ] **Task 5.1**: Update `SPECTRUM_EXPORT_FEATURE.md` with implementation details
  - Add "How to Enable" section
  - Add example loading code

- [ ] **Task 5.2**: Create example Jupyter notebook
  - `examples/load_and_plot_spectrum.ipynb`
  - Show loading, plotting, custom picking

- [ ] **Task 5.3**: Update main README.md
  - Add section on spectrum export feature
  - Link to detailed documentation

- [ ] **Task 5.4**: Add to CHANGELOG.md
  - Feature addition in version X.X.X

---

## Technical Implementation Details

### Velocity Axis Construction

Different methods compute velocity differently:

**FK Method**:
```python
# Currently has: freq_sub, ktrial, pnorm, vmax
# Need to compute uniform velocity grid
nv = 400
vmin = 1.0
vmax_plot = 5000.0
velocity_axis = np.linspace(vmin, vmax_plot, nv)

# Interpolate power from k-space to v-space
P_vf = np.zeros((nv, len(freq_sub)))
for i, f in enumerate(freq_sub):
    k_need = 2 * np.pi * f / velocity_axis
    P_vf[:, i] = np.interp(k_need, ktrial, np.abs(pnorm[:, i]),
                           left=0.0, right=0.0)
```

**FDBF Method**:
```python
# Similar to FK, already computed in service.py lines 177-182
# Just need to save the interpolated P_vf and vaxis
```

**PS Method**:
```python
# Already has: freq_sub, vels, pnorm, vmax
# vels is the velocity axis (already in velocity space)
# Just save directly
```

**SS Method**:
```python
# Already has: freq, vels, pnorm, vmax
# Just save directly
```

### Helper Function Structure

```python
def _save_spectrum_npz(outdir: str, base: str, key: str, offset: str,
                       frequencies: np.ndarray,
                       velocities: np.ndarray,
                       power: np.ndarray,
                       picked_velocities: np.ndarray,
                       vibrosis_mode: bool = False,
                       extra_metadata: dict = None) -> None:
    """
    Save power spectrum data to .npz file.

    Parameters:
    -----------
    outdir : str
        Output directory
    base : str
        Base filename (e.g., 'shot01')
    key : str
        Method key ('fk', 'fdbf', 'ps', 'ss')
    offset : str
        Source offset label (e.g., '+66m')
    frequencies : ndarray
        1D array of frequency values (Hz)
    velocities : ndarray
        1D array of velocity values (m/s)
    power : ndarray
        2D array (nvel × nfreq) of normalized power
    picked_velocities : ndarray
        1D array of picked dispersion curve velocities
    vibrosis_mode : bool
        Whether vibrosis compensation was used (FDBF only)
    extra_metadata : dict, optional
        Additional method-specific metadata
    """
    import os
    import numpy as np
    from datetime import datetime

    # Construct filename
    spectrum_file = os.path.join(outdir, f"{base}_{key}_spectrum.npz")

    # Prepare metadata
    metadata = {
        'frequencies': frequencies,
        'velocities': velocities,
        'power': power,
        'picked_velocities': picked_velocities,
        'method': key,
        'offset': offset,
        'vibrosis_mode': vibrosis_mode,
        'export_date': datetime.now().isoformat(),
        'version': '1.0'  # spectrum format version
    }

    # Add extra metadata if provided
    if extra_metadata:
        metadata.update(extra_metadata)

    # Save compressed
    try:
        np.savez_compressed(spectrum_file, **metadata)
        return spectrum_file
    except Exception as e:
        # Log error but don't crash
        print(f"Warning: Could not save spectrum to {spectrum_file}: {e}")
        return None
```

---

## Estimated Implementation Time

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: Core Service | 7 tasks | 3-4 hours |
| Phase 2: GUI Integration | 5 tasks | 1-2 hours |
| Phase 3: CLI Integration | 4 tasks | 1 hour |
| Phase 4: Testing | 8 tasks | 2-3 hours |
| Phase 5: Documentation | 4 tasks | 2 hours |
| **Total** | **28 tasks** | **9-12 hours** |

---

## Risk Assessment

### Low Risk Items
✅ Adding parameter to functions (backward compatible)
✅ GUI checkbox (simple addition)
✅ CLI flag (simple addition)

### Medium Risk Items
⚠️ Velocity axis construction for FK/FDBF (needs interpolation logic)
⚠️ File I/O errors (need good error handling)

### Mitigation Strategies
- Test with real data early
- Add comprehensive error handling
- Provide fallback: If spectrum save fails, processing continues
- Validate array shapes before saving

---

## Success Criteria

### Must Have
- [x] Feature works in GUI (checkbox functional)
- [x] Feature works in CLI (flag functional)
- [x] All 4 methods export correct data
- [x] Files load successfully in Python/MATLAB
- [x] No crashes when export fails
- [x] Documentation complete

### Nice to Have
- [ ] Example Jupyter notebook
- [ ] Performance benchmarking (time overhead)
- [ ] File size statistics

---

## Post-Implementation

### Future Enhancements (v2.0)
- Export to MATLAB .mat format (for non-Python users)
- Export CSV version (downsampled for Excel users)
- Batch export tool (CLI command to export from existing PNG/CSV)
- GUI button to load and re-plot saved spectra

---

## Questions for Confirmation

Before starting implementation, please confirm:

1. **Format approved?** NumPy .npz with structure described above?
2. **Default OFF?** Feature disabled by default (opt-in)?
3. **Naming OK?** `<base>_<method>_spectrum.npz` naming convention?
4. **GUI placement?** Checkbox in "Figure / Export" section?
5. **Error handling?** Silent failure (log warning) vs. show error dialog?

---

**Ready to proceed?** Please review and approve this plan. I will then implement all 28 tasks systematically.
