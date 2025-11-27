# Power Spectrum .npz File Format Reference

## Overview

SW_Transform exports power spectrum data in two formats:
1. **Single .npz** - One source offset per file
2. **Combined .npz** - All source offsets in one file

Both use NumPy compressed archive format (`.npz`).

---

## File Naming Convention

**Single spectrum files:**
```
<base>_<method>_<offset_tag>_spectrum.npz
```
Examples:
- `1_fdbf_p66_spectrum.npz` (CSV: `1_fdbf_p66.csv`)
- `survey01_fk_p0_spectrum.npz` (CSV: `survey01_fk_p0.csv`)
- `data_ps_m12_spectrum.npz` (CSV: `data_ps_m12.csv`)

**Offset tag format:**
- Positive offset `+66m` → `p66`
- Zero offset `+0` → `p0`
- Negative offset `-12m` → `m12`

**Combined spectrum file:**
```
combined_<method>_spectrum.npz
```
Examples:
- `combined_fk_spectrum.npz`
- `combined_fdbf_spectrum.npz`

---

## Single .npz Structure

### File Contents

One source offset, one method.

```python
import numpy as np
data = np.load('1_fdbf_p66_spectrum.npz')

# Core arrays
frequencies = data['frequencies']          # 1D, shape (M,), dtype: float32, units: Hz
velocities = data['velocities']            # 1D, shape (N,), dtype: float32, units: m/s
power = data['power']                      # 2D, shape (N, M), dtype: float32, normalized 0-1
picked_velocities = data['picked_velocities']  # 1D, shape (M,), dtype: float32, units: m/s

# Metadata
method = str(data['method'])               # 'fk', 'fdbf', 'ps', or 'ss'
offset = str(data['offset'])               # e.g., '+66m', '+0', '-12m'
export_date = str(data['export_date'])     # ISO 8601 timestamp
version = str(data['version'])             # Format version (currently '1.0')

# Method-specific metadata (if present)
wavenumbers = data['wavenumbers']          # FK/FDBF: 1D array, dtype: float32
vibrosis_mode = bool(data['vibrosis_mode'])  # All methods: True/False
vspace = str(data['vspace'])               # PS only: 'log' or 'linear'
weight_mode = str(data['weight_mode'])     # FDBF only: weighting mode
```

### Coordinate System

**2D Power Array:**
- Shape: `(N_velocities, N_frequencies)`
- `power[i, j]` = power at velocity `velocities[i]` and frequency `frequencies[j]`
- Values normalized to range [0.0, 1.0] where 1.0 = maximum energy

**Axes:**
- X-axis (columns): Frequency (Hz) - `frequencies[0]` to `frequencies[-1]`
- Y-axis (rows): Velocity (m/s) - `velocities[0]` to `velocities[-1]`

### Example: Loading and Accessing Data

```python
import numpy as np
import matplotlib.pyplot as plt

# Load single spectrum file
data = np.load('1_fdbf_p66_spectrum.npz')

# Extract arrays
freq = data['frequencies']  # e.g., shape (512,)
vel = data['velocities']    # e.g., shape (400,)
power = data['power']       # shape (400, 512)
picked = data['picked_velocities']  # shape (512,)

# Plot spectrum
plt.figure(figsize=(10, 6))
plt.pcolormesh(freq, vel, power, shading='auto', cmap='viridis')
plt.plot(freq, picked, 'r-', linewidth=2, label='Picked curve')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Velocity (m/s)')
plt.title(f"Method: {data['method']}, Offset: {data['offset']}")
plt.colorbar(label='Normalized Power')
plt.legend()
plt.show()
```

---

## Combined .npz Structure

### File Contents

All source offsets for one method in a single file.

```python
import numpy as np
data = np.load('combined_fk_spectrum.npz')

# Global metadata
method = str(data['method'])               # 'fk', 'fdbf', 'ps', or 'ss'
offsets = data['offsets']                  # 1D array of offset tags, dtype: object
num_offsets = int(data['num_offsets'])    # Number of offsets in file
export_date = str(data['export_date'])     # ISO 8601 timestamp
version = str(data['version'])             # Format version (currently '1.0')

# Per-offset data (suffix = offset tag)
# For each offset in 'offsets' array:
#   frequencies_{tag}: 1D array, dtype: float32
#   velocities_{tag}: 1D array, dtype: float32
#   power_{tag}: 2D array, dtype: float32
#   picked_velocities_{tag}: 1D array, dtype: float32
#   ... plus method-specific metadata

# Example for offset tags ['p0', 'p66', 'p132']:
frequencies_p0 = data['frequencies_p0']
velocities_p0 = data['velocities_p0']
power_p0 = data['power_p0']
picked_velocities_p0 = data['picked_velocities_p0']

frequencies_p66 = data['frequencies_p66']
velocities_p66 = data['velocities_p66']
power_p66 = data['power_p66']
picked_velocities_p66 = data['picked_velocities_p66']

frequencies_p132 = data['frequencies_p132']
velocities_p132 = data['velocities_p132']
power_p132 = data['power_p132']
picked_velocities_p132 = data['picked_velocities_p132']

# Method-specific metadata with suffix
wavenumbers_p0 = data['wavenumbers_p0']    # FK/FDBF only
vibrosis_mode_p0 = data['vibrosis_mode_p0']  # All methods
# ... (repeat for p66, p132, etc.)
```

### Data Organization

**Structure:**
- One entry per offset for each data type
- Offset tags are sorted alphabetically (e.g., `['m12', 'p0', 'p66', 'p132']`)
- Each offset has independent frequency/velocity grids (may differ)
- Data access pattern: `data['{field}_{offset_tag}']`

### Example: Loading and Iterating All Offsets

```python
import numpy as np
import matplotlib.pyplot as plt

# Load combined spectrum file
data = np.load('combined_fk_spectrum.npz')

# Get list of offsets
offsets = data['offsets']  # e.g., array(['p0', 'p66', 'p132'], dtype=object)

print(f"Method: {data['method']}")
print(f"Number of offsets: {data['num_offsets']}")
print(f"Offsets: {list(offsets)}")

# Iterate through all offsets
fig, axes = plt.subplots(1, len(offsets), figsize=(15, 5))

for idx, offset_tag in enumerate(offsets):
    # Access data for this offset
    freq = data[f'frequencies_{offset_tag}']
    vel = data[f'velocities_{offset_tag}']
    power = data[f'power_{offset_tag}']
    picked = data[f'picked_velocities_{offset_tag}']

    # Plot
    ax = axes[idx] if len(offsets) > 1 else axes
    ax.pcolormesh(freq, vel, power, shading='auto', cmap='viridis')
    ax.plot(freq, picked, 'r-', linewidth=2)
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Velocity (m/s)')
    ax.set_title(f'Offset: {offset_tag}')

plt.tight_layout()
plt.show()
```

### Example: Extract Specific Offset

```python
import numpy as np

def load_offset_from_combined(combined_file, offset_tag):
    """Extract single offset data from combined .npz file."""
    data = np.load(combined_file)

    if offset_tag not in data['offsets']:
        raise ValueError(f"Offset '{offset_tag}' not found in file")

    return {
        'frequencies': data[f'frequencies_{offset_tag}'],
        'velocities': data[f'velocities_{offset_tag}'],
        'power': data[f'power_{offset_tag}'],
        'picked_velocities': data[f'picked_velocities_{offset_tag}'],
        'method': str(data['method']),
        'offset': offset_tag,
    }

# Usage
offset_data = load_offset_from_combined('combined_fk_spectrum.npz', 'p66')
print(f"Frequencies shape: {offset_data['frequencies'].shape}")
print(f"Power shape: {offset_data['power'].shape}")
```

---

## Comparison: Single vs. Combined

| Feature | Single .npz | Combined .npz |
|---------|-------------|---------------|
| **File count** | One per offset | One per method |
| **Naming** | `<base>_<method>_<offset>_spectrum.npz` | `combined_<method>_spectrum.npz` |
| **Data access** | Direct: `data['frequencies']` | Suffixed: `data['frequencies_p66']` |
| **Offsets stored** | One | All (listed in `data['offsets']`) |
| **Use case** | Single-offset analysis | Multi-offset comparison |
| **File size** | ~100-500 KB | ~1-5 MB (all offsets) |
| **Loading speed** | Fast | Moderate |

---

## When to Use Each Format

### Use Single .npz when:
- Working with one source offset at a time
- Memory constrained
- Quick visualization needed
- Integrating with external tools expecting single-offset data

### Use Combined .npz when:
- Comparing multiple source offsets
- Bulk processing/batch analysis
- Dispersion refinement across all offsets
- Archival storage (single file vs. many)

---

## Loading Best Practices

### Check File Contents

```python
import numpy as np

def inspect_npz(filepath):
    """Print structure of .npz file."""
    data = np.load(filepath)

    print(f"File: {filepath}")
    print(f"Keys: {list(data.keys())}")

    if 'offsets' in data:
        print(f"Type: Combined spectrum")
        print(f"Method: {data['method']}")
        print(f"Offsets: {list(data['offsets'])}")
    else:
        print(f"Type: Single spectrum")
        print(f"Method: {data['method']}")
        print(f"Offset: {data['offset']}")

    for key in data.keys():
        arr = data[key]
        if hasattr(arr, 'shape'):
            print(f"  {key}: shape {arr.shape}, dtype {arr.dtype}")
        else:
            print(f"  {key}: {arr}")

# Usage
inspect_npz('1_fdbf_p66_spectrum.npz')
inspect_npz('combined_fk_spectrum.npz')
```

### Error Handling

```python
import numpy as np

def safe_load_spectrum(filepath):
    """Safely load spectrum file with error handling."""
    try:
        data = np.load(filepath)

        # Validate required fields
        required = ['frequencies', 'velocities', 'power', 'picked_velocities', 'method']

        if 'offsets' in data:
            # Combined file - check first offset
            offset_tag = data['offsets'][0]
            required_offset = [f'{k}_{offset_tag}' for k in required[:4]]
            missing = [k for k in required_offset if k not in data]
        else:
            # Single file
            missing = [k for k in required if k not in data]

        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        return data

    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None
```

---

## Technical Notes

### Data Types
- All arrays stored as `float32` for space efficiency
- Metadata strings stored as numpy scalar objects
- Offset list stored as object array (strings)

### Compression
- Format: NumPy compressed `.npz` (zip archive with gzip compression)
- Typical compression ratio: 3-5x for power spectra
- Decompression automatic on `np.load()`

### Version Compatibility
- Current format version: `1.0`
- Future versions will maintain backward compatibility
- Check `data['version']` before processing

### Coordinate Mapping
```
power[i, j] corresponds to:
  - Velocity: velocities[i]
  - Frequency: frequencies[j]
  - Power: power[i, j]
```

### Grid Sizes (typical)
- **FK/FDBF**: 400 velocity points, 400-1000 frequency points
- **PS/SS**: 1200 velocity points, 400-1000 frequency points
- **Frequency range**: 0-100 Hz (configurable)
- **Velocity range**: 0-5000 m/s (configurable)

---

## Quick Reference

### Single Spectrum File
```python
data['frequencies']         # 1D array (M,)
data['velocities']          # 1D array (N,)
data['power']               # 2D array (N, M)
data['picked_velocities']   # 1D array (M,)
data['method']              # String
data['offset']              # String
```

### Combined Spectrum File
```python
data['offsets']                      # 1D array of offset tags
data['frequencies_{tag}']            # 1D array (M,)
data['velocities_{tag}']             # 1D array (N,)
data['power_{tag}']                  # 2D array (N, M)
data['picked_velocities_{tag}']      # 1D array (M,)
data['method']                       # String
```

Replace `{tag}` with actual offset tag (e.g., `p66`, `p0`, `m12`).
