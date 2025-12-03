# SW_Transform Copilot Instructions

## Project Overview

SW_Transform is a Python seismic-data processing package for **Multichannel Analysis of Surface Waves (MASW)**. It converts multichannel geophone recordings into dispersion curves using four transform methods: FK (Frequency-Wavenumber), FDBF (Frequency-Domain Beamformer), PS (Phase-Shift), and SS (Slant-Stack).

## Architecture

### Package Structure (`SRC/sw_transform/`)

```
core/         # Orchestration - run_single(), run_compare() in service.py
processing/   # Transforms (fk.py, fdbf.py, ps.py, ss.py) + registry.py
masw2d/       # 2D MASW for multiple dispersion curves (Phase 1 implemented)
gui/          # Tkinter GUI (simple_app.py is primary)
cli/          # Command-line interfaces (single.py, compare.py, masw2d/)
io/           # SEG-2 file handling, file assignment
workers/      # Legacy async wrappers (backward compatibility)
```

### Method Registry Pattern

New processing methods are added via `processing/registry.py`. Each method defines:
- `transform`: Tuple of `(module_path, function_name)` returning `(frequencies, velocities, power)`
- `analyze`: Returns `(pnorm, vmax, wavelength, freq)`
- `plot`: Creates contour plot with picks
- `plot_kwargs`: Default plotting parameters

```python
# Example: Adding to METHODS dict in registry.py
"new_method": {
    "label": "Display Name",
    "transform": ("sw_transform.processing.new_method", "transform_func"),
    "analyze": ("sw_transform.processing.new_method", "analyze_func"),
    "plot": ("sw_transform.processing.new_method", "plot_func"),
    "plot_kwargs": dict(cmap="jet", vmax_plot=5000),
}
```

### Data Flow

1. **SEG-2 Input** → `processing/seg2.py:load_seg2_ar()` returns `(time, data_matrix, dx, dt)`
2. **Preprocessing** → `core/service.py:_preprocess_with_cache()` handles caching
3. **Transform** → Method-specific via registry (`transform` function)
4. **Analysis** → Peak picking via registry (`analyze` function)
5. **Output** → CSV (picks), NPZ (full spectrum), PNG (plots)

## Key Conventions

### Transform Function Signature

All transforms must follow this interface:
```python
def transform_func(data, dt, dx, fmin, fmax, nvel, vmin, vmax, vspace="linear", **kwargs):
    """
    Returns:
        frequencies: ndarray (Hz)
        velocities: ndarray (m/s)
        power: ndarray shape (nvel, nfreq)
    """
```

### Vibrosis Source Handling

FDBF supports vibrosis compensation via `weighting='invamp'` parameter. This is passed through the `source_type` param in service calls:
```python
params = {"source_type": "vibrosis"}  # Triggers invamp weighting in FDBF
```

### File Naming Conventions

- Spectrum files: `{base}_{method}_{offset_tag}_spectrum.npz`
- Offset tags: `+66m` → `p66`, `-10m` → `m10`
- Combined files: `combined_{method}_spectrum.npz`

## Running the Application

```powershell
# GUI (main entry)
python run.py

# CLI single method
python -m sw_transform.cli.single <file.dat> --key fdbf --outdir ./out --offset "+10m"

# CLI compare all methods
python -m sw_transform.cli.compare <file.dat> --outdir ./out

# MASW 2D workflow
python -m sw_transform.cli.masw2d workflow run config.json -o ./output
```

## Testing

```powershell
python Test/test_masw2d.py  # Phase 1 integration tests
```

Test data location: `Test/Example_Files/` with `.dat` SEG-2 files.

## MASW 2D Module

The `masw2d/` subpackage implements 2D MASW processing:
- **Phase 1 (Complete)**: Sub-array extraction from fixed arrays
- **Phase 2 (Planned)**: Roll-along surveys
- **Phase 3 (Planned)**: CMP cross-correlation

Key workflow: `StandardMASWWorkflow` in `workflows/standard_masw.py`

Configuration is JSON-based. Generate template via CLI:
```powershell
python -m sw_transform.cli.masw2d config generate -o config.json --channels 24 --dx 2.0
```

## Documentation References

- `Context/SW_Transform Repository Context.md` - Full architecture documentation
- `MASW_2D/Plan/00_Master_Plan.md` - 2D MASW implementation roadmap
- `SPECTRUM_NPZ_FILE_FORMAT.md` - NPZ export format specification
- `VIBROSIS_IMPLEMENTATION.md` - Vibrosis compensation details
