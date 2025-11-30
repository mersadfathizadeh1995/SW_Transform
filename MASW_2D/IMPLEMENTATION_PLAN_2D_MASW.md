# 2D MASW Implementation Plan for SW_Transform

## Comprehensive Workflow and Package Structure

---

## 1. Executive Summary

This document outlines the implementation plan for adding 2D MASW capabilities to the SW_Transform package. The goal is to enable:

1. Processing multiple shot records along a survey line
2. Extracting sub-arrays with consistent geometry (roll-along/recompilation)
3. Optionally using CMP cross-correlation for enhanced resolution
4. Inverting dispersion curves to 1D Vs profiles
5. Interpolating and visualizing pseudo-2D Vs cross-sections

---

## 2. High-Level Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    2D MASW PROCESSING WORKFLOW                   │
└─────────────────────────────────────────────────────────────────┘

[1] DATA INPUT
    │
    ├── Survey configuration (JSON)
    ├── Multiple SEG-2 files (shot records)
    └── Geometry parameters (dx, X₁, etc.)
    │
    ▼
[2] SUB-ARRAY EXTRACTION
    │
    ├── Roll-along: Extract from moving array data
    └── Shoot-through: Recompile fixed-array data
    │
    ▼
[3] (Optional) CMP CROSS-CORRELATION
    │
    ├── Compute pairwise correlations
    ├── Sort by midpoint and spacing
    └── Stack to form CMP-CC gathers
    │
    ▼
[4] DISPERSION ANALYSIS (per sub-array)
    │
    ├── Apply FK/FDBF/PS/SS transform
    ├── Pick dispersion curve
    └── Store with midpoint location
    │
    ▼
[5] INVERSION (per dispersion curve)
    │
    ├── Set model parameterization
    ├── Run GA/Monte-Carlo optimization
    └── Output 1D Vs profile at midpoint
    │
    ▼
[6] 2D SECTION ASSEMBLY
    │
    ├── Collect all 1D Vs profiles
    ├── Interpolate to regular grid
    └── Generate cross-section visualization
    │
    ▼
[7] OUTPUT
    │
    ├── Individual dispersion curves (CSV/NPZ)
    ├── Individual Vs profiles (CSV)
    ├── Interpolated 2D grid (NPZ/GeoTIFF)
    └── Cross-section figure (PNG)
```

---

## 3. Package Structure

### 3.1 New Directory Layout

```
sw_transform/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── cache.py
│   └── service.py          # Existing - add 2D orchestration
├── processing/
│   ├── __init__.py
│   ├── fk.py
│   ├── fdbf.py
│   ├── ps.py
│   ├── ss.py
│   ├── preprocess.py
│   ├── seg2.py
│   └── registry.py
├── masw2d/                  # ◄── NEW SUBPACKAGE
│   ├── __init__.py          # Public API
│   ├── subarray.py          # Sub-array extraction
│   ├── cmpcc.py             # CMP cross-correlation (optional)
│   ├── inversion.py         # Dispersion curve inversion (GA)
│   ├── interpolate.py       # 2D interpolation
│   └── visualize.py         # Cross-section plotting
├── cli/
│   ├── __init__.py
│   ├── single.py
│   ├── compare.py
│   └── masw2d.py            # ◄── NEW CLI ENTRY POINT
├── gui/
│   └── ...
├── io/
│   ├── __init__.py
│   ├── file_assignment.py
│   └── survey_config.py     # ◄── NEW: survey config I/O
└── workers/
    └── ...
```

### 3.2 Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `masw2d/subarray.py` | Extract sub-arrays from shot records; roll-along and shoot-through support |
| `masw2d/cmpcc.py` | CMP cross-correlation gather computation (optional enhancement) |
| `masw2d/inversion.py` | GA-based dispersion curve inversion using `disba` for forward modeling |
| `masw2d/interpolate.py` | 2D interpolation methods (linear, cubic, RBF, kriging) |
| `masw2d/visualize.py` | Cross-section plotting and export (PNG, NPZ, CSV) |
| `cli/masw2d.py` | CLI interface for batch 2D processing |
| `io/survey_config.py` | Load/save survey configuration JSON |

---

## 4. Implementation Phases

### Phase 1: Sub-Array Management (Week 1)

**Files to create:**
- `sw_transform/masw2d/__init__.py`
- `sw_transform/masw2d/subarray.py`
- `sw_transform/io/survey_config.py`

**Key functions:**

```python
# subarray.py
def extract_roll_along_subarrays(shot_records, geometry, 
                                  target_length, target_offset) -> list
def recompile_shoot_through_subarrays(shot_records, geometry,
                                       target_length) -> list
def validate_geometry(subarrays) -> bool

# survey_config.py
def load_survey_config(path: str) -> dict
def save_survey_config(config: dict, path: str) -> None
def generate_config_template(output_path: str) -> None
```

**Deliverables:**
- Survey configuration schema (JSON)
- Sub-array extraction with geometry validation
- Basic tests

---

### Phase 2: Batch Dispersion Processing (Week 2)

**Files to modify:**
- `sw_transform/core/service.py` - Add `run_single_from_array()`

**Files to create:**
- Basic `sw_transform/cli/masw2d.py`

**Key functions:**

```python
# service.py (additions)
def run_single_from_array(params: dict) -> tuple:
    """Process pre-extracted array data (no file loading)."""
    pass

def process_2d_survey(config: dict, output_dir: str, 
                      method: str = 'ps') -> list:
    """Batch process all sub-arrays from a survey."""
    pass

# cli/masw2d.py
def main(argv=None) -> int:
    """CLI entry point for 2D MASW processing."""
    pass
```

**Deliverables:**
- Batch processing of sub-arrays
- Dispersion curves with midpoint metadata
- Basic CLI for 2D processing

---

### Phase 3: Dispersion Curve Inversion (Week 3-4)

**Files to create:**
- `sw_transform/masw2d/inversion.py`

**Dependencies to add:**
- `disba` (dispersion calculation)
- Optional: `deap` (genetic algorithms)

**Key classes/functions:**

```python
# inversion.py
class LayerModel:
    """1D layered earth model."""
    def __init__(self, n_layers, ...)
    def forward(self, frequencies) -> ndarray

class GAInversion:
    """Genetic algorithm inversion."""
    def __init__(self, n_layers, vp_vs_ratio, ...)
    def invert(self, obs_vel, freqs, bounds) -> dict

def invert_dispersion_curve(freq, vel, n_layers, bounds) -> dict
def invert_batch(dispersion_curves, n_layers, bounds) -> list
```

**Deliverables:**
- Thomson-Haskell forward model (via disba)
- GA inversion with configurable parameters
- 1D Vs profiles with misfit metrics

---

### Phase 4: CMP Cross-Correlation (Week 4, Optional)

**Files to create:**
- `sw_transform/masw2d/cmpcc.py`

**Key functions:**

```python
# cmpcc.py
def compute_cmpcc_gathers(T, t, dx, max_lag=None) -> dict
def apply_transform_to_cmpcc(cmpcc_data, method, params) -> dict
```

**Deliverables:**
- CMP-CC gather computation
- Integration with existing transforms
- Enhanced lateral resolution option

---

### Phase 5: 2D Interpolation and Visualization (Week 5)

**Files to create:**
- `sw_transform/masw2d/interpolate.py`
- `sw_transform/masw2d/visualize.py`

**Key functions:**

```python
# interpolate.py
def layer_to_grid(depths, Vs, z_grid) -> ndarray
def interpolate_2d(profiles, x_grid, z_grid, method='rbf') -> ndarray

# visualize.py
def plot_vs_cross_section(x, z, Vs_2d, **kwargs) -> Figure
def plot_1d_profiles(profiles, **kwargs) -> Figure
def save_cross_section(filepath, x, z, Vs_2d, format='npz') -> None
```

**Deliverables:**
- Multiple interpolation methods
- Publication-quality cross-section plots
- Export to NPZ, CSV, optionally GeoTIFF

---

### Phase 6: CLI Completion and Integration (Week 6)

**Files to finalize:**
- `sw_transform/cli/masw2d.py`
- `sw_transform/masw2d/__init__.py` (public API)

**CLI Commands:**

```bash
# Full 2D workflow
python -m sw_transform.cli.masw2d process \
    --config survey.json \
    --outdir output/ \
    --method ps \
    --subarray-length 12

# Invert existing dispersion curves
python -m sw_transform.cli.masw2d invert \
    --input dispersion_curves/ \
    --outdir vs_profiles/ \
    --n-layers 5

# Build cross-section from inverted profiles
python -m sw_transform.cli.masw2d crosssection \
    --input vs_profiles/ \
    --outdir cross_section/ \
    --interp rbf
```

**Deliverables:**
- Complete CLI for 2D MASW workflow
- Documentation and examples
- Integration tests

---

## 5. Survey Configuration Schema

```json
{
    "survey_name": "Site_A_MASW_2D",
    "acquisition": {
        "type": "roll_along",
        "geometry": {
            "n_channels": 24,
            "dx": 2.0,
            "source_offset": 10.0,
            "roll_increment": 2.0
        }
    },
    "shots": [
        {
            "file": "shot_001.dat",
            "shot_position": 0.0,
            "first_receiver": 10.0
        },
        {
            "file": "shot_002.dat",
            "shot_position": 2.0,
            "first_receiver": 12.0
        }
    ],
    "processing": {
        "subarray_length": 12,
        "target_offset": 10.0,
        "method": "ps",
        "freq_range": [5, 80],
        "velocity_range": [100, 1500]
    },
    "inversion": {
        "n_layers": 5,
        "vs_bounds": [[50, 300], [100, 500], [150, 700], [200, 900], [300, 1200]],
        "h_bounds": [[0.5, 5], [1, 10], [2, 15], [3, 25]],
        "vp_vs_ratio": 1.73,
        "ga_population": 100,
        "ga_generations": 300
    },
    "output": {
        "interpolation_method": "rbf",
        "x_resolution": 1.0,
        "z_max": 30,
        "z_resolution": 0.5
    }
}
```

---

## 6. Dependencies

### Required (New)

```
disba>=1.0.0          # Dispersion curve calculation
```

### Optional

```
deap>=1.3.0           # Alternative GA framework
rasterio>=1.3.0       # GeoTIFF export
```

### Existing (No Change)

```
numpy
scipy
matplotlib
```

---

## 7. Testing Strategy

### Unit Tests

| Module | Test Coverage |
|--------|--------------|
| `subarray.py` | Sub-array extraction, geometry validation |
| `cmpcc.py` | Correlation computation, stacking |
| `inversion.py` | Forward model accuracy, GA convergence |
| `interpolate.py` | Interpolation methods, edge cases |
| `visualize.py` | Plot generation, export formats |

### Integration Tests

- Full pipeline from shot records to cross-section
- CLI command execution
- Configuration file parsing

### Synthetic Data Tests

- Generate synthetic Vs model
- Forward compute seismograms (if possible) or use theoretical dispersion
- Verify inversion recovers known model

---

## 8. Documentation

### User Guide Topics

1. Survey configuration setup
2. Sub-array geometry optimization
3. Processing method selection
4. Inversion parameter tuning
5. Interpreting cross-section results

### API Documentation

- Docstrings for all public functions
- Example usage in module headers
- Type hints throughout

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| `disba` dependency issues | Fallback to pysurf96 or custom Thomson-Haskell |
| GA convergence issues | Provide multiple optimization backends; configurable stopping criteria |
| Memory for large surveys | Batch processing mode; configurable array size limits |
| Edge effects in interpolation | Multiple methods; user-selectable; warning for sparse data |

---

## 10. Future Extensions (Post-Initial Release)

1. **Higher mode extraction and joint inversion**
2. **GUI integration** - Survey config wizard, interactive picking
3. **Uncertainty quantification** - Monte Carlo ensembles, confidence intervals
4. **Passive MASW integration** - Ambient noise processing
5. **Machine learning** - Automated dispersion picking, inversion initialization

---

## 11. Summary

This implementation plan adds comprehensive 2D MASW capabilities to SW_Transform through a new `masw2d` subpackage. The design prioritizes:

- **Modularity**: Each step in the workflow is a separate module
- **Flexibility**: Multiple methods for each processing step
- **CLI-first**: All functionality accessible from command line
- **Extensibility**: Clean interfaces for future GUI integration

The estimated development time is 6 weeks for CLI-complete implementation, with GUI integration as a follow-on task.
