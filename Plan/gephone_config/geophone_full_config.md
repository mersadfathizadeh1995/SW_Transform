# Geophone Array Configuration - Full Implementation Plan

**Created:** January 7, 2026  
**Project:** SW_Transform MASW Processing Package  
**Status:** Planning Phase

---

## 1. Problem Statement

### Current Limitations

The current SW_Transform package has several limitations regarding geophone array configuration:

1. **Fixed Channel Count**: The software auto-detects the number of channels from the SEG-2 file and uses ALL channels. Users cannot select a subset (e.g., use only 24 of 48 channels).

2. **Uniform Spacing Only**: The software assumes uniform geophone spacing (dx). Non-uniform arrays (common in research and specialized surveys) are not supported.

3. **Exterior Shots Only**: The system only handles exterior shots (source outside the array). Interior shots (source within the array) cannot be properly processed.

4. **No Visual Confirmation**: Users cannot visualize the array configuration before processing to verify it matches their field setup.

### User Requirements

Based on user feedback, the following capabilities are needed:

- Process data from arrays with different numbers of geophones (24, 36, 48, etc.)
- Use only a subset of channels (e.g., first 24 of 48)
- Support non-uniform geophone spacing (like the MATLAB UofA_MASWMultiProcessVibroseisNonUniform.m)
- Handle interior shots by selecting left or right side of the array
- Visualize the array configuration to confirm setup before processing

---

## 2. Reference: MATLAB Non-Uniform Spacing Implementation

From `UofA_MASWMultiProcessVibroseisNonUniform (1).m`:

```matlab
% Line 41: Non-uniform positions array (not spacing!)
spacing=[0;2;4;6;8;10;14;18;22;26;30;35;40;45;50;55;60;65;70;75;80;85;90;95];

% Line 49: Number of channels
numchannels=24;

% Line 256: Position array used directly
position(:,1)=spacing;

% Line 264: Aliasing uses minimum spacing
kalias=pi./(min(abs(diff(position(:,1)/2))));

% Line 280: Beamforming uses actual positions
expterm=exp(1i * ktrial(j) * position(:,1));
```

**Key Insight**: The MATLAB code uses an array of actual positions instead of computing positions from uniform dx. This allows full flexibility for non-uniform arrays.

---

## 3. Current Codebase Analysis

### Transform Support Status

| Transform | File | Current Support | Required Change |
|-----------|------|-----------------|-----------------|
| **PS (Phase-Shift)** | `processing/ps.py:48-52` | ✅ Already supports position array | None |
| **FK** | `processing/fk.py:48` | ❌ Uniform dx only | Add array support |
| **FDBF** | `processing/fdbf.py:60,416` | ❌ Uniform dx only | Add array support |
| **SS (Slant-Stack)** | `processing/ss.py:50` | ❌ Uniform dx only | Add array support |

### PS Transform (Already Working)

```python
# processing/ps.py lines 48-52
# Receiver offsets
if np.isscalar(dx):
    offsets = np.arange(nchannels) * dx
else:
    offsets = np.asarray(dx)  # <-- Already accepts positions array!
```

### FK Transform (Needs Update)

```python
# processing/fk.py line 48
offsets = np.arange(nchannels) * dx  # <-- Only scalar dx
```

### FDBF Transform (Needs Update)

```python
# processing/fdbf.py line 60
offsets = np.arange(nchannels) * dx  # <-- Only scalar dx

# processing/fdbf.py line 416 (fdbf_transform_from_R)
offsets = np.arange(nchannels, dtype=float) * dx  # <-- Only scalar dx
```

### SS (Slant-Stack) Transform (Needs Update)

```python
# processing/ss.py line 50
offsets = np.arange(nchannels) * dx  # <-- Only scalar dx
```

### Data Flow

```
SEG-2 File
    ↓
load_seg2_ar() → returns (time, T, shotpoint, spacing, dt, delay)
    ↓                              ↑
    ↓                    scalar dx from file header
    ↓
preprocess_data() → returns (Tpre, time_pre, dt2)
    ↓
    ↓   Currently passes scalar dx
    ↓
transform_func(Tpre, dt2, dx, ...) → (frequencies, velocities, power)
    ↓
analyze_func() → (pnorm, vmax, wavelength, freq)
    ↓
plot_func() → saves PNG
```

**Required Change**: Pass positions array instead of scalar dx when array configuration specifies non-uniform spacing or channel selection.

---

## 4. Feature Specification

### 4.1 Channel Selection Modes

| Mode | Description | Example |
|------|-------------|---------|
| `all` | Use all channels from file | 48 channels → use all 48 |
| `first_n` | Use first N channels | 48 channels → use 1-24 |
| `last_n` | Use last N channels | 48 channels → use 25-48 |
| `range` | Use channel range [start, end] | 48 channels → use 10-34 |
| `custom` | Specify exact channel indices | Use [1, 3, 5, 7, 10, 15, 20] |

### 4.2 Spacing/Position Modes

| Mode | Description | Example |
|------|-------------|---------|
| `uniform` | Equal spacing between all geophones | dx = 2.0m |
| `custom` | Specify actual positions for each geophone | [0, 2, 4, 6, 10, 15, 20, 30] |
| `pattern` | Repeating pattern of spacings | [2, 2, 2, 4, 4, 4, 6, 6, 6] |

### 4.3 Shot Type Handling

| Shot Type | Description | Processing |
|-----------|-------------|------------|
| `exterior_left` | Source before first geophone | Normal forward processing |
| `exterior_right` | Source after last geophone | Reverse channel order |
| `edge_left` | Source at first geophone | Normal processing |
| `edge_right` | Source at last geophone | Reverse processing |
| `interior` | Source within array | Split into left/right virtual shots |

### 4.4 Interior Shot Options

When source is within the array:

- **Left side only**: Use geophones left of source (reversed for correct wave direction)
- **Right side only**: Use geophones right of source (normal direction)
- **Both sides**: Create two virtual shots and process separately

---

## 5. Implementation Design

### 5.1 New Data Structure: ArrayConfig

**File**: `sw_transform/core/array_config.py`

```python
from dataclasses import dataclass, field
from typing import List, Optional, Literal
import numpy as np


@dataclass
class ArrayConfig:
    """Flexible geophone array configuration.
    
    This class encapsulates all array configuration options including
    channel selection, positions, and source handling.
    """
    
    # === File Information (auto-detected) ===
    n_channels_file: int = 24  # Total channels in file
    dx_file: float = 2.0  # Spacing from file header
    
    # === Channel Selection ===
    channel_mode: Literal['all', 'first_n', 'last_n', 'range', 'custom'] = 'all'
    n_channels_use: int = 24  # For first_n, last_n modes
    channel_start: int = 0  # For range mode (0-indexed)
    channel_end: int = 24  # For range mode (exclusive)
    channel_indices: List[int] = field(default_factory=list)  # For custom mode
    
    # === Position Configuration ===
    spacing_mode: Literal['uniform', 'custom'] = 'uniform'
    dx: float = 2.0  # Uniform spacing
    custom_positions: List[float] = field(default_factory=list)  # Custom positions
    
    # === Source Configuration ===
    source_position: float = -10.0  # Source position in meters
    shot_type: Literal['exterior_left', 'exterior_right', 'edge_left', 
                       'edge_right', 'interior'] = 'exterior_left'
    interior_side: Literal['left', 'right', 'both'] = 'both'
    
    # === Computed Properties ===
    def get_selected_indices(self) -> np.ndarray:
        """Get indices of selected channels (0-indexed)."""
        if self.channel_mode == 'all':
            return np.arange(self.n_channels_file)
        elif self.channel_mode == 'first_n':
            return np.arange(min(self.n_channels_use, self.n_channels_file))
        elif self.channel_mode == 'last_n':
            start = max(0, self.n_channels_file - self.n_channels_use)
            return np.arange(start, self.n_channels_file)
        elif self.channel_mode == 'range':
            return np.arange(self.channel_start, min(self.channel_end, self.n_channels_file))
        elif self.channel_mode == 'custom':
            return np.array(self.channel_indices)
        return np.arange(self.n_channels_file)
    
    def get_positions(self) -> np.ndarray:
        """Get positions for selected channels."""
        indices = self.get_selected_indices()
        
        if self.spacing_mode == 'uniform':
            # Compute positions from uniform spacing
            all_positions = np.arange(self.n_channels_file) * self.dx
            return all_positions[indices]
        else:
            # Use custom positions
            positions = np.array(self.custom_positions)
            if len(positions) >= len(indices):
                return positions[:len(indices)]
            else:
                # Pad with uniform spacing if not enough custom positions
                extra = np.arange(len(positions), len(indices)) * self.dx
                return np.concatenate([positions, extra])
    
    def get_effective_data(self, full_data: np.ndarray) -> np.ndarray:
        """Extract selected channels from full data array.
        
        Parameters
        ----------
        full_data : ndarray
            Full data array (nsamples, nchannels)
            
        Returns
        -------
        ndarray
            Selected data (nsamples, n_selected_channels)
        """
        indices = self.get_selected_indices()
        return full_data[:, indices]
    
    def get_array_length(self) -> float:
        """Get total length of selected array."""
        positions = self.get_positions()
        return float(positions[-1] - positions[0]) if len(positions) > 1 else 0.0
    
    def classify_shot(self) -> str:
        """Classify shot type based on source position."""
        positions = self.get_positions()
        array_start = positions[0]
        array_end = positions[-1]
        tolerance = 0.01 * self.dx  # 1% of spacing
        
        if abs(self.source_position - array_start) < tolerance:
            return 'edge_left'
        elif abs(self.source_position - array_end) < tolerance:
            return 'edge_right'
        elif self.source_position < array_start:
            return 'exterior_left'
        elif self.source_position > array_end:
            return 'exterior_right'
        else:
            return 'interior'
    
    def needs_reverse(self) -> bool:
        """Check if data needs to be reversed for correct wave direction."""
        shot_type = self.classify_shot()
        return shot_type in ('exterior_right', 'edge_right')
    
    def split_interior_shot(self) -> List['ArrayConfig']:
        """Split interior shot into left and right virtual shots.
        
        Returns
        -------
        List[ArrayConfig]
            One or two configs for left/right sides
        """
        if self.classify_shot() != 'interior':
            return [self]
        
        positions = self.get_positions()
        indices = self.get_selected_indices()
        
        configs = []
        
        # Left side (geophones left of source)
        if self.interior_side in ('left', 'both'):
            left_mask = positions < self.source_position
            if np.sum(left_mask) >= 6:  # Minimum 6 geophones
                left_config = ArrayConfig(
                    n_channels_file=self.n_channels_file,
                    dx_file=self.dx_file,
                    channel_mode='custom',
                    channel_indices=indices[left_mask][::-1].tolist(),  # Reverse order
                    spacing_mode='custom',
                    custom_positions=positions[left_mask][::-1].tolist(),
                    source_position=self.source_position,
                    shot_type='exterior_right'  # Virtual exterior right
                )
                configs.append(left_config)
        
        # Right side (geophones right of source)
        if self.interior_side in ('right', 'both'):
            right_mask = positions > self.source_position
            if np.sum(right_mask) >= 6:  # Minimum 6 geophones
                right_config = ArrayConfig(
                    n_channels_file=self.n_channels_file,
                    dx_file=self.dx_file,
                    channel_mode='custom',
                    channel_indices=indices[right_mask].tolist(),
                    spacing_mode='custom',
                    custom_positions=positions[right_mask].tolist(),
                    source_position=self.source_position,
                    shot_type='exterior_left'  # Virtual exterior left
                )
                configs.append(right_config)
        
        return configs if configs else [self]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'n_channels_file': self.n_channels_file,
            'dx_file': self.dx_file,
            'channel_mode': self.channel_mode,
            'n_channels_use': self.n_channels_use,
            'channel_start': self.channel_start,
            'channel_end': self.channel_end,
            'channel_indices': self.channel_indices,
            'spacing_mode': self.spacing_mode,
            'dx': self.dx,
            'custom_positions': self.custom_positions,
            'source_position': self.source_position,
            'shot_type': self.shot_type,
            'interior_side': self.interior_side
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> 'ArrayConfig':
        """Create from dictionary."""
        return cls(**d)


def create_default_config(n_channels: int, dx: float) -> ArrayConfig:
    """Create default config from file info."""
    return ArrayConfig(
        n_channels_file=n_channels,
        dx_file=dx,
        dx=dx,
        n_channels_use=n_channels
    )
```

### 5.2 GUI Component: Array Configuration Panel

**File**: `sw_transform/gui/components/array_config_panel.py`

**UI Layout**:

```
┌─ Array Configuration ─────────────────────────────────────────────────┐
│                                                                       │
│  FILE INFO                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ Detected: 48 channels, dx = 2.0 m, Array length = 94 m          │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  CHANNEL SELECTION                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ ○ Use all channels (48)                                         │ │
│  │ ○ Use first [24    ] channels                                   │ │
│  │ ○ Use last  [24    ] channels                                   │ │
│  │ ○ Use channel range: from [1  ] to [24 ]                        │ │
│  │ ○ Custom channel list: [1,2,3,4,5,6,7,8,9,10,11,12]            │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  GEOPHONE SPACING                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ ○ Uniform spacing: dx = [2.0  ] meters                          │ │
│  │ ○ Custom positions (comma-separated, in meters):                │ │
│  │   [0, 2, 4, 6, 8, 10, 14, 18, 22, 26, 30, 35, 40, 45           ]│ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  SOURCE POSITION                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ Source offset: [-10   ] meters                                  │ │
│  │ Detected type: EXTERIOR LEFT (source before array)              │ │
│  │                                                                  │ │
│  │ (For Interior Shots)                                            │ │
│  │ Process: ○ Left side  ○ Right side  ○ Both sides               │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ [Update Preview]  [Apply to Selected]  [Apply to All Files]     │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 5.3 Enhanced Array Preview

**Update**: `sw_transform/gui/components/array_preview.py`

The preview should show:

1. **Array Schematic**:
   - Active geophones: Filled green triangles (▲)
   - Inactive geophones: Empty triangles (△)
   - Source position: Red diamond (◆)
   - Position labels on x-axis

2. **Configuration Summary**:
   - Number of channels used vs total
   - Array length
   - Source position and shot type
   - Non-uniform spacing warning if applicable

3. **Waterfall Plot**:
   - Show only selected channels
   - Correct x-axis positions (not just channel numbers)

**Example Display**:

```
ARRAY SCHEMATIC
                ◆                ▲ ▲ ▲ ▲ ▲ ▲ ▲ ▲ ▲ ▲ ▲ ▲ △ △ △ △ △ △ △ △ △ △ △ △
                |________________|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|
               -10               0   2   4   6   8  10  12  14  16  18  20  22  24  26  28  30

Configuration:
• Using 12 of 24 channels (first 12)
• Uniform spacing: dx = 2.0 m
• Array length: 22 m
• Source at -10 m: EXTERIOR LEFT
```

### 5.4 Transform Updates

#### FK Transform Update

**File**: `sw_transform/processing/fk.py`

```python
# Change line 48 from:
offsets = np.arange(nchannels) * dx

# To:
if np.isscalar(dx):
    offsets = np.arange(nchannels) * dx
else:
    offsets = np.asarray(dx)
```

#### FDBF Transform Update

**File**: `sw_transform/processing/fdbf.py`

```python
# Change line 60 (fdbf_transform) from:
offsets = np.arange(nchannels) * dx

# To:
if np.isscalar(dx):
    offsets = np.arange(nchannels) * dx
else:
    offsets = np.asarray(dx)

# Change line 416 (fdbf_transform_from_R) from:
offsets = np.arange(nchannels, dtype=float) * dx

# To:
if np.isscalar(dx):
    offsets = np.arange(nchannels, dtype=float) * dx
else:
    offsets = np.asarray(dx, dtype=float)
```

#### SS (Slant-Stack) Transform Update

**File**: `sw_transform/processing/ss.py`

```python
# Change line 50 from:
offsets = np.arange(nchannels) * dx

# To:
if np.isscalar(dx):
    offsets = np.arange(nchannels) * dx
else:
    offsets = np.asarray(dx)
```

#### PS Transform (No Change Needed)

**File**: `sw_transform/processing/ps.py`

Already supports position arrays - no changes required.

### 5.5 Service Layer Update

**File**: `sw_transform/core/service.py`

Add support for ArrayConfig in `run_single()`:

```python
def run_single(params: Dict[str, Any]) -> Tuple[str, bool, str]:
    # ... existing code ...
    
    # Get array configuration
    array_config = params.get('array_config', None)
    
    if array_config is not None:
        # Use ArrayConfig for channel selection and positions
        positions = array_config.get_positions()
        
        # Load and select data
        time, T, _, _, dt, _ = load_seg2_ar(path)
        T_selected = array_config.get_effective_data(T)
        
        # Handle interior shots
        if array_config.classify_shot() == 'interior':
            configs = array_config.split_interior_shot()
            # Process each virtual shot separately
            for cfg in configs:
                # ... process with cfg ...
        else:
            # Process normally with positions array
            # Pass positions instead of scalar dx to transforms
            f, vels, P = transform_func(Tpre, dt2, positions, **transform_kwargs)
```

---

## 6. Implementation Phases

### Phase 1: Core Data Structure (Priority: HIGH)
- [ ] Create `sw_transform/core/array_config.py`
- [ ] Implement `ArrayConfig` dataclass with all methods
- [ ] Add unit tests for ArrayConfig

**Estimated time**: 1 day

### Phase 2: Transform Updates (Priority: HIGH)
- [ ] Update FK transform to accept positions array (`processing/fk.py`)
- [ ] Update FDBF transform to accept positions array (`processing/fdbf.py`)
- [ ] Update SS (Slant-Stack) transform to accept positions array (`processing/ss.py`)
- [ ] Verify PS transform works correctly (already supports it)
- [ ] Add tests for non-uniform spacing with all 4 methods

**Estimated time**: 0.5 day

### Phase 3: GUI - Array Configuration Panel (Priority: HIGH)
- [ ] Create `sw_transform/gui/components/array_config_panel.py`
- [ ] Implement channel selection radio buttons
- [ ] Implement spacing configuration
- [ ] Implement source position handling
- [ ] Connect to file selection

**Estimated time**: 1.5 days

### Phase 4: Enhanced Array Preview (Priority: MEDIUM)
- [ ] Update `array_preview.py` to show active/inactive channels
- [ ] Add configuration summary display
- [ ] Show correct positions for non-uniform arrays
- [ ] Handle waterfall for selected channels only

**Estimated time**: 0.5 day

### Phase 5: Service Layer Integration (Priority: HIGH)
- [ ] Update `service.py` to accept ArrayConfig
- [ ] Implement interior shot splitting
- [ ] Pass positions array to transforms
- [ ] Update result naming for virtual shots

**Estimated time**: 1 day

### Phase 6: Testing and Documentation (Priority: HIGH)
- [ ] Test all channel selection modes
- [ ] Test non-uniform spacing
- [ ] Test interior shot handling
- [ ] Update user documentation

**Estimated time**: 1 day

**Total estimated time**: ~5.5 days

---

## 7. Test Cases

### 7.1 Channel Selection Tests

| Test | Input | Expected Output |
|------|-------|-----------------|
| Use all 24 channels | 24-ch file, mode='all' | Indices [0-23] |
| First 12 of 24 | 24-ch file, mode='first_n', n=12 | Indices [0-11] |
| Last 12 of 24 | 24-ch file, mode='last_n', n=12 | Indices [12-23] |
| Range 5-15 | 24-ch file, mode='range', start=5, end=15 | Indices [5-14] |
| Custom selection | mode='custom', indices=[0,2,4,6,8] | Indices [0,2,4,6,8] |

### 7.2 Non-Uniform Spacing Tests

| Test | Positions | Expected Aliasing |
|------|-----------|-------------------|
| Uniform 2m | [0,2,4,6,8,10] | k_alias = π/2 |
| Non-uniform | [0,2,4,8,14,22] | k_alias = π/1 (min diff = 2m) |
| Variable | [0,1,2,4,8,16] | k_alias = π/0.5 (min diff = 1m) |

### 7.3 Interior Shot Tests

| Test | Source Pos | Array | Expected Split |
|------|------------|-------|----------------|
| Source at 10m | 10 | [0-22m] | Left: 0-8m, Right: 12-22m |
| Source at 5m | 5 | [0-22m] | Left: 0-4m (few), Right: 6-22m |
| Near edge | 2m | [0-22m] | Right only: 4-22m |

---

## 8. Future Enhancements

### 8.1 Advanced Channel Selection
- Automatic quality-based channel rejection (noisy channels)
- Channel grouping for multi-source surveys

### 8.2 Advanced Spacing
- Import positions from file (CSV, TXT)
- GPS coordinate import and conversion
- Automatic spacing detection from headers

### 8.3 Survey Integration
- Multi-line surveys with automatic array rotation
- 2D array support (grid layouts)
- Automatic shot-to-array matching

---

## 9. References

1. **UofA_MASWMultiProcessVibroseisNonUniform.m** - MATLAB reference implementation for non-uniform arrays
2. **Park et al. (1998)** - Phase-shift method for MASW
3. **Vantassel (2021) swprocess** - Modern Python implementation reference
4. **Zywicki (1999)** - FDBF transform theory

---

## 10. Appendix: File Changes Summary

| File | Action | Changes |
|------|--------|---------|
| `core/array_config.py` | CREATE | ArrayConfig dataclass, helper functions |
| `gui/components/array_config_panel.py` | CREATE | New GUI panel for configuration |
| `gui/components/array_preview.py` | MODIFY | Enhanced preview with active/inactive display |
| `gui/components/advanced_settings.py` | MODIFY | Add link to array config |
| `gui/simple_app.py` | MODIFY | Integrate array config panel |
| `processing/fk.py` | MODIFY | Support positions array (line 48) |
| `processing/fdbf.py` | MODIFY | Support positions array (lines 60, 416) |
| `processing/ss.py` | MODIFY | Support positions array (line 50) |
| `processing/ps.py` | NONE | Already supports positions array |
| `core/service.py` | MODIFY | Accept ArrayConfig, pass positions to transforms |
| `processing/seg2.py` | OPTIONAL | Return additional file metadata |
