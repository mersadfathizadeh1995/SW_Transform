# Fixes Applied to SW_Transform Package

**Date:** Oct 16, 2025  
**Package:** `D:\Research\Narm_Afzar\4_Wave\SW_Transform\SRC\sw_transform`

---

## Issue #1: Combined CSV Generation Not Working

### Problem
When running "Run All" in single-method mode, the GUI created individual per-shot CSV files but did not aggregate them into a combined CSV file across all shots/offsets. Similarly, compare mode created per-file CSVs but no master combined file.

### Root Cause
The `run_single_processing()` and `run_compare_processing()` methods in `gui/simple_app.py` had no post-processing step to aggregate the individual CSVs after the processing loop completed.

### Solution Implemented
Added two new methods to `SimpleMASWGUI` class:

1. **`_create_combined_csv_single_method(key, paths)`** (lines 498-562)
   - Aggregates all per-shot CSVs for a given method (FK, FDBF, PS, SS)
   - Searches for pattern: `*_{method}_*.csv`
   - Parses filenames to extract base name and offset
   - Creates `combined_{method}.csv` with columns:
     - `freq(method_offset1), vel(method_offset1), wav(method_offset1), ...`
   - Example: `combined_fk.csv` with data from all shots

2. **`_create_combined_csv_compare_mode(paths)`** (lines 564-613)
   - Aggregates all per-file compare CSVs
   - Searches for pattern: `*_compare.csv`
   - Creates `combined_compare_all.csv` combining all 4-method data
   - Preserves per-file headers and aligns data row-by-row

### Integration
- Called after success in `run_single_processing()` (lines 412-422)
- Called after success in `run_compare_processing()` (lines 476-486)
- Logs success/failure messages to GUI logbox
- Graceful error handling with try-except

---

## Issue #2: Icon Display Problems

### Problem
Icons were not displaying properly in the GUI. Asset files had `@180x180` suffix (e.g., `ic_open@180x180.png`) but the code was looking for exact matches without this suffix.

### Root Causes
1. **Filename mismatch:** Code requested `ic_open.png` but file was `ic_open@180x180.png`
2. **Case-sensitive matching:** Fallback search used exact case matching
3. **Poor icon scaling:** Icons were being stretched/distorted using `ImageOps.fit()`
4. **Small size:** Icons were only 44x44 pixels, too small for modern displays

### Solutions Implemented

#### 1. Improved Asset Path Resolution (lines 591-759)
- Added docstring explaining the function handles `@NxN` variants
- Made prefix matching **case-insensitive**: `fn.lower().startswith(prefix.lower())`
- Searches for largest PNG file matching the prefix
- Example: Request `ic_open.png` → finds `ic_open@180x180.png`

#### 2. Better Icon Loading with Proper Scaling (lines 761-788)
- **Removed distortion:** Replaced `ImageOps.fit()` with `thumbnail()` to maintain aspect ratio
- **Added padding:** 5% padding around icon for breathing room
- **Center alignment:** Icons are centered on white background
- **Better quality:** Uses `Image.Resampling.LANCZOS` for high-quality downscaling
- **Transparent margin removal:** Auto-crops transparent borders before resizing

#### 3. Increased Icon Size (lines 102, 172, 179, 234)
- Changed from 44x44 → **48x48 pixels**
- Better visibility on modern displays
- More professional appearance

---

## Files Modified

### Primary Changes
- **`SRC/sw_transform/gui/simple_app.py`**
  - Added: `_create_combined_csv_single_method()` method
  - Added: `_create_combined_csv_compare_mode()` method
  - Modified: `_asset_path()` - improved asset finding
  - Modified: `_load_icon()` - better scaling/rendering
  - Modified: Icon size 44→48 in 4 locations
  - Modified: Integration in processing workflows

---

## Testing Recommendations

### Test Combined CSV Generation
1. **Single Method Mode:**
   - Select multiple SEG-2 files with different offsets
   - Run "Run All" for FK method
   - Verify `combined_fk.csv` created in output folder
   - Check columns: `freq(fk_+66), vel(fk_+66), wav(fk_+66), freq(fk_-5), ...`
   - Repeat for FDBF, PS, SS methods

2. **Compare Mode:**
   - Select multiple SEG-2 files
   - Run "Compare All"
   - Verify `combined_compare_all.csv` created
   - Check it contains all 4 methods × all files

3. **Error Handling:**
   - Run with empty output folder (should skip gracefully)
   - Check log messages appear in GUI logbox

### Test Icon Display
1. Launch GUI: `python run.py`
2. Verify icons appear on:
   - "Open SEG-2..." button (folder icon)
   - "Run Selected" / "Run All" buttons (play icon)
   - "Compare Selected" / "Compare All" buttons (compare icon)
   - "Create PPT" button (PowerPoint icon)
3. Icons should be:
   - Crisp and clear (not pixelated)
   - Properly centered in buttons
   - Not stretched or distorted
   - 48×48 pixels with proper padding

---

## Benefits

### Combined CSV Feature
- ✅ Matches legacy GUI behavior
- ✅ Easier data analysis across multiple shots
- ✅ Single file for Excel/MATLAB import
- ✅ Preserves all offset information in column headers
- ✅ Handles variable-length frequency arrays gracefully

### Icon Improvements
- ✅ Professional, polished appearance
- ✅ Better visibility on high-DPI displays
- ✅ Works with any icon naming convention
- ✅ Maintains aspect ratio (no distortion)
- ✅ Consistent padding and centering
- ✅ Efficient caching (icons loaded once)

---

## Known Limitations

1. **Combined CSV assumes consistent frequency arrays**
   - If different files have vastly different frequency ranges, some cells may be empty
   - This is expected behavior (matches legacy system)

2. **Icon fallback behavior**
   - If no icon file found, button displays without icon (text only)
   - No error shown to user (graceful degradation)

3. **CSV parsing relies on filename convention**
   - Expects format: `<base>_<method>_<offset>.csv`
   - May not work if users manually rename files

---

## Future Enhancements (Optional)

1. **Add progress indicator** for combined CSV generation (currently silent)
2. **Validate CSV data** before aggregation (check for malformed rows)
3. **Add "Export to Excel"** button for direct XLSX export
4. **Icon theme support** (allow user to choose icon set)
5. **Configurable icon size** in settings

---

## Compatibility

- ✅ Python 3.8+
- ✅ Windows (primary target)
- ✅ Linux/macOS (should work, not tested)
- ✅ Requires Pillow (PIL) for icon rendering
- ✅ Backward compatible with existing CSV files

---

**End of Document**
