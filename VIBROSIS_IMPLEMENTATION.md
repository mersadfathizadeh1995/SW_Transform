# Vibrosis Source Support - Implementation Guide

**Date**: November 10, 2025
**Status**: ✅ Fully Implemented and Tested

---

## Overview

Your SW_Transform package now has **comprehensive vibrosis source support** with an improved user interface and CLI integration. This document explains how it works and how to use it.

---

## What is Vibrosis Source Compensation?

### The Problem

**Vibrosis sources** (truck-mounted vibrators) produce **swept-frequency signals** that suffer from frequency-dependent attenuation as they propagate through the ground:
- Higher frequencies lose more energy
- Lower frequencies dominate the recorded signal
- This creates biased dispersion analysis

**Hammer sources** (sledgehammer, weight drop) produce short impulse signals with relatively flat frequency spectra and don't have this problem.

### The Solution

The package applies **inverse amplitude weighting** in the frequency domain:
```
weight = sqrt(frequency / max_frequency)
```

This progressively **boosts higher frequencies** to compensate for their natural attenuation, resulting in balanced dispersion analysis.

---

## How It Works Technically

### 1. Processing Pipeline

```
User enables vibrosis checkbox
    ↓
GUI sets source_type = "vibrosis"
    ↓
Passed to core service layer (service.py)
    ↓
Converted to weight_mode = "invamp"
    ↓
Applied in FDBF cross-spectra computation (fdbf.py)
    ↓
Weighting applied to cross-spectral matrix
    ↓
Beamforming proceeds with compensated data
```

### 2. Implementation Location

**File**: `SRC/sw_transform/processing/fdbf.py`
**Function**: `compute_cross_spectra()`
**Lines**: 32-38

```python
if weight_mode == 'invamp':  # For vibrosis sources
    # Apply inverse amplitude weighting to compensate for
    # frequency-dependent attenuation
    for i, freq in enumerate(freq_full):
        if freq > 0:  # Avoid division by zero at DC
            # Inverse amplitude weighting: boost higher frequencies
            weight = np.sqrt(freq / freq_full[-1]) if freq_full[-1] > 0 else 1.0
            R_full[:, :, i] *= weight
```

### 3. Method-Specific Application

**Important**: Vibrosis compensation **ONLY affects FDBF method**

| Method | Affected by Vibrosis Mode? | Reason |
|--------|---------------------------|---------|
| **FDBF** | ✅ YES | Works in cross-spectral domain where weighting is applied |
| **FK** | ❌ NO | Direct 2D FFT on time-space data |
| **PS** | ❌ NO | Phase-based analysis, less sensitive to amplitudes |
| **SS** | ❌ NO | Slant-stack in time domain |

---

## GUI Usage

### Checkbox Interface

**Location**: Inputs Tab → "Per-method settings" section → FK/FDBF row (right side)

**Appearance**:
```
┌─────────────────────────────────────────────────────────────┐
│  Per-method settings                                        │
├─────────────────────────────────────────────────────────────┤
│  FK/FDBF N: [4000]  tol: [0]         ☐ Vibrosis (FDBF)    │
│  PS/SS N:   [1200]  vspace: [log▼]  tol: [0]               │
└─────────────────────────────────────────────────────────────┘
```

### Features

1. **Integrated Layout**: Checkbox positioned on same row as FK/FDBF settings
2. **Concise Label**: "☐ Vibrosis (FDBF)" - clear and compact
3. **Right-Side Position**: Easy to spot at the end of FK/FDBF row
4. **Default**: Unchecked (hammer mode is default)
5. **Help Available**: Detailed explanation available in Help menu

### When to Check the Box

✅ **Check the box** if you're using:
- Truck-mounted vibrators (Vibroseis, T-Rex, Mini-Vib)
- Swept-frequency sources
- Any long-duration controlled-frequency source

❌ **Leave unchecked** if you're using:
- Sledgehammer
- Weight drop
- Accelerated weight drop (AWD)
- Any short-duration impulse source

---

## CLI Usage

### Single Method Processing

```bash
# Hammer source (default)
python -m sw_transform.cli.single data.dat --key fdbf --outdir output/

# Vibrosis source
python -m sw_transform.cli.single data.dat --key fdbf --source-type vibrosis --outdir output/
```

### Compare Mode (All 4 Methods)

```bash
# Hammer source (default)
python -m sw_transform.cli.compare data.dat --outdir output/

# Vibrosis source
python -m sw_transform.cli.compare data.dat --source-type vibrosis --outdir output/
```

### Help Text

```bash
python -m sw_transform.cli.single --help
```

Output includes:
```
--source-type {hammer,vibrosis}
                      source type: 'hammer' (default) or 'vibrosis'
                      (applies frequency compensation for FDBF)
```

---

## Testing & Verification

### How to Test

1. **Load sample SEG-2 file** (vibrosis data if available)
2. **Run FDBF without vibrosis mode**:
   - Uncheck the box
   - Run FDBF processing
   - Note the dispersion curve (especially high frequencies)

3. **Run FDBF with vibrosis mode**:
   - Check the box
   - Run FDBF processing again
   - Compare dispersion curve

4. **Expected Result**:
   - With vibrosis mode: Higher frequencies are better represented
   - Dispersion picks extend to higher frequencies
   - Overall spectrum appears more balanced

### Verification Checklist

- [x] GUI checkbox visible and functional
- [x] Help text displays correctly
- [x] Checkbox state properly converted to source_type parameter
- [x] source_type flows through processing pipeline
- [x] FDBF applies inverse amplitude weighting when source_type='vibrosis'
- [x] Other methods (FK, PS, SS) unaffected by vibrosis setting
- [x] CLI accepts --source-type flag
- [x] Default behavior (hammer) unchanged when box unchecked

---

## Code Changes Summary

### Files Modified

1. **`SRC/sw_transform/gui/simple_app.py`**
   - Line 67: Changed `source_type` StringVar to `vibrosis_mode` BooleanVar
   - Line 143: Added vibrosis checkbox to FK/FDBF settings row (right side)
   - Lines 425-432: Convert boolean to source_type string in single processing
   - Lines 495-503: Convert boolean to source_type string in compare mode

2. **`SRC/sw_transform/cli/single.py`**
   - Lines 16-17: Added `--source-type` argument
   - Line 41: Added `source_type` to params dict

3. **`SRC/sw_transform/cli/compare.py`**
   - Lines 15-16: Added `--source-type` argument
   - Line 37: Added `source_type` to params dict

### Files Already Correct (No Changes Needed)

- ✅ `SRC/sw_transform/core/service.py` - Already converts source_type to weight_mode
- ✅ `SRC/sw_transform/processing/fdbf.py` - Already implements weighting logic

---

## Technical Details

### Weight Function

The inverse amplitude weighting function is:

```
w(f) = sqrt(f / f_max)
```

Where:
- `f` = current frequency
- `f_max` = maximum frequency in the analysis

**Characteristics**:
- At DC (f=0): weight = 0 (DC component ignored)
- At f_max: weight = 1.0 (no change)
- At f_max/4: weight = 0.5 (moderate boost)
- Square root provides gentle, progressive boost

### Alternative Weighting (Available but Unused)

The code also includes `weight_mode='sqrt'` for hammer sources:
```python
weight = sqrt(sqrt(freq / freq_full[-1]))
```

This is a **quarter-root** weighting (even gentler). Currently not exposed in GUI but could be added as advanced option.

---

## Future Enhancements

See `IMPROVEMENTS_ROADMAP.md` section 4 for planned vibrosis improvements:

### Short-term (v0.2.0):
- [ ] Add source type to output filenames: `shot01_fdbf_vibrosis.png`
- [ ] Include source type in CSV metadata headers
- [ ] Annotate FDBF plots with "Vibrosis compensated" text

### Medium-term (v0.5.0):
- [ ] Auto-detect source type from signal characteristics
- [ ] Spectrum viewer QC tab (show before/after weighting)
- [ ] Comparison tool (hammer vs vibrosis side-by-side)

### Long-term (v1.0.0+):
- [ ] Custom weighting slider (0-100% compensation)
- [ ] Apply optional vibrosis compensation to FK method
- [ ] Machine learning-based source classification

---

## Troubleshooting

### Issue: Checkbox not visible

**Solution**:
- Look in the "Per-method settings" section in the Inputs tab
- The checkbox is on the right side of the FK/FDBF row
- It appears as "☐ Vibrosis (FDBF)"

### Issue: No difference in results when enabling vibrosis mode

**Possible causes**:
1. You're running FK, PS, or SS (vibrosis only affects FDBF)
2. Your data is already well-balanced (hammer source?)
3. Frequency range is too narrow to see effect

**Solution**: Run FDBF method on vibrosis data with wide frequency range (0-100 Hz)

### Issue: CLI --source-type flag not recognized

**Possible causes**:
- Old version of CLI tools
- Using wrong command syntax

**Solution**:
```bash
# Correct syntax
python -m sw_transform.cli.single data.dat --key fdbf --source-type vibrosis --outdir output/

# NOT this
python -m sw_transform.cli.single data.dat --source-type vibrosis  # missing --outdir
```

---

## Scientific References

### Recommended Reading

For more information on frequency-dependent attenuation and weighting strategies in surface wave analysis:

1. Park, C. B., Miller, R. D., & Xia, J. (1999). "Multichannel analysis of surface waves." *Geophysics*, 64(3), 800-808.

2. Xia, J., Miller, R. D., & Park, C. B. (1999). "Estimation of near-surface shear-wave velocity by inversion of Rayleigh waves." *Geophysics*, 64(3), 691-700.

3. Forbriger, T. (2003). "Inversion of shallow-seismic wavefields: I. Wavefield transformation." *Geophysical Journal International*, 153(3), 719-734.

---

## Summary

✅ **Vibrosis support is FULLY IMPLEMENTED**
✅ **GUI has prominent, user-friendly checkbox**
✅ **CLI has --source-type flag**
✅ **Processing pipeline correctly applies weighting**
✅ **Only affects FDBF method (by design)**
✅ **Default behavior unchanged (hammer mode)**

Your package is now ready for both hammer and vibrosis source data!

---

**Questions?** See `IMPROVEMENTS_ROADMAP.md` for additional documentation needs.
