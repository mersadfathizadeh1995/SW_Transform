# SW_Transform

**Surface Wave Dispersion Analysis Toolkit**

SW_Transform is a Python package for extracting dispersion curves from multichannel surface wave recordings using multiple transform methods. It automates the **Multichannel Analysis of Surface Waves (MASW)** workflow — from reading SEG-2 field data through preprocessing, dispersion-curve extraction, and result export. The package provides both a graphical user interface (Tkinter) and a command-line interface for batch processing.

---

## Features

### Transform Methods

- **FK** — Frequency-Wavenumber transform via 2D FFT with automatic velocity conversion and peak picking
- **FDBF** — Frequency-Domain Beamforming with cross-spectral matrix computation and optional vibrosis source compensation
- **PS** — Phase-Shift stacking with complex phase-shift summation across a velocity grid
- **SS** — Slant-Stack (tau-p) transform with time-delay stacking and frequency-domain conversion

All methods share a unified interface (`transform → analyze → plot`) registered in a central method registry for dynamic lookup.

### Processing Pipeline

- **SEG-2 reader** — native binary parser for SEG-2 `.dat` files (no external dependencies)
- **Preprocessing** — time-window slicing, channel reversal for reverse shots, downsampling, and zero-padding
- **Caching** — unified preprocessing cache to avoid recomputation across repeated runs
- **Peak picking** — automatic phase-velocity extraction with configurable velocity/frequency bounds and tolerance
- **Normalization** — per-frequency or global-maximum normalization of power spectra

### MASW 2D Module

- **Sub-array extraction** from fixed arrays with multiple source offsets
- **Variable sub-array sizes** for multi-resolution analysis
- **Shot classification** — automatic detection of exterior, edge, and interior shots
- **Midpoint calculation** for pseudo-2D Vs profiling
- **Vibrosis-specific extraction** with amplitude-dependent weighting
- **Predefined workflows** for standard and vibrosis MASW processing
- **Batch processing** with organized result output and export

### Data Export

- **CSV** — per-shot dispersion picks (frequency, phase velocity, wavelength)
- **NPZ** — full power spectrum arrays (frequencies, velocities, power, picks, metadata)
- **Combined outputs** — multi-offset spectra merged into single NPZ/CSV files
- **PowerPoint** — optional report generation via python-pptx

### User Interfaces

- **GUI** (Tkinter) — interactive environment for file selection, offset assignment, method selection, preprocessing parameter tuning, raw/processed data preview, waterfall plots, single/compare mode execution, spectrum export, combined output generation, and figure galleries
- **CLI** — `single` and `compare` subcommands for scripted batch processing with JSON parameter overrides

---

## Requirements

- **Python** 3.10+
- **NumPy** >= 1.20.0
- **SciPy** >= 1.7.0
- **Matplotlib** >= 3.5.0
- **Pillow** >= 9.0.0
- **tkinter** (standard library; may need separate installation on some Linux distributions)

### Optional

- **python-pptx** >= 0.6.21 — for PowerPoint report export

---

## Installation

```bash
# Clone the repository
git clone https://github.com/mersadfathizadeh1995/SW_Transform.git
cd SW_Transform

# Create a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

### GUI

```bash
python run.py
```

The graphical interface opens with controls for:

1. Selecting SEG-2 data files and assigning offsets
2. Choosing a transform method (FK, FDBF, PS, SS)
3. Adjusting preprocessing parameters (time window, downsample, reverse)
4. Previewing raw and processed waveforms
5. Running single-method or four-method comparison
6. Exporting dispersion curves, spectra, and figures

### CLI — Single Method

```bash
python -m sw_transform.cli.single path/to/shot.dat --key fk --outdir results/ --offset +5
```

### CLI — Compare All Methods

```bash
python -m sw_transform.cli.compare path/to/shot.dat --outdir results/ --offset +5
```

Both CLI commands accept `--source-type` (`hammer` or `vibrosis`), `--no-export-spectra` to disable NPZ export, and `--params '{...}'` for JSON parameter overrides.

---

## Typical Workflow

1. **Data Collection** — acquire surface-wave recordings with a geophone array; export as SEG-2 `.dat` files
2. **File Assignment** — assign shot offsets and reverse flags (automatic 10-shot pattern detection or manual)
3. **Preprocessing** — select time window, optionally reverse channels, downsample
4. **Transform** — choose one or more methods (FK, FDBF, PS, SS)
5. **Processing** — `run_single` (one method) or `run_compare` (all four) orchestrates the full pipeline
6. **Interpretation** — view frequency-velocity contour plots with auto-picked dispersion curves
7. **Export** — save per-shot CSVs, full spectra as NPZ, or combined multi-offset outputs

---

## Project Structure

```
SW_Transform/
├── run.py                      # GUI entry point
├── requirements.txt            # Python dependencies
├── SW_Transform.bat            # Windows launcher script
├── SRC/
│   └── sw_transform/           # Main package
│       ├── __init__.py
│       ├── core/
│       │   ├── cache.py        # Preprocessing cache (key generation, load/save)
│       │   ├── service.py      # Central orchestration API (run_single, run_compare)
│       │   └── array_config.py # Array configuration utilities
│       ├── processing/
│       │   ├── registry.py     # Method registry (FK, FDBF, PS, SS)
│       │   ├── fk.py           # Frequency-Wavenumber transform
│       │   ├── fdbf.py         # Frequency-Domain Beamforming
│       │   ├── ps.py           # Phase-Shift method
│       │   ├── ss.py           # Slant-Stack (tau-p) method
│       │   ├── preprocess.py   # Time-window, downsample, reverse
│       │   ├── seg2.py         # Native SEG-2 binary reader
│       │   └── vibrosis.py     # Vibrosis source compensation
│       ├── gui/
│       │   ├── simple_app.py   # Main Tkinter GUI
│       │   ├── masw2d_tab.py   # MASW 2D processing tab
│       │   ├── components/     # Reusable GUI components
│       │   └── utils/          # GUI helper utilities
│       ├── cli/
│       │   ├── single.py       # CLI: single-method processing
│       │   ├── compare.py      # CLI: four-method comparison
│       │   └── masw2d/         # CLI: MASW 2D commands
│       ├── io/
│       │   └── file_assignment.py  # Shot offset and reverse-flag inference
│       ├── masw2d/
│       │   ├── config/         # Configuration loading, validation, templates
│       │   ├── geometry/       # Shot classification, sub-arrays, midpoints
│       │   ├── extraction/     # Sub-array and vibrosis data extraction
│       │   ├── processing/     # Batch dispersion-curve processing
│       │   ├── workflows/      # Standard and vibrosis MASW workflows
│       │   └── output/         # Result organization, merging, export
│       └── workers/            # Async worker wrappers (backward compatibility)
```

---

## License

This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m "Add my feature"`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## Author

**Mersad Fathizadeh**

---

## Acknowledgments

- [NumPy](https://numpy.org/) — numerical computation
- [SciPy](https://scipy.org/) — signal processing and scientific computing
- [Matplotlib](https://matplotlib.org/) — plotting and visualization
