# Roll-Along Sub-Array Processing Technical Reference

## Implementation Guide for 2D MASW Data Management

---

## 1. Introduction

Roll-along (or walking) MASW acquisition generates multiple shot records along a survey line. To create 2D Vs cross-sections, these records must be processed to extract sub-arrays with consistent geometry. This document details the sub-array extraction algorithms.

---

## 2. Data Acquisition Geometry

### 2.1 Standard Roll-Along Setup

```
Survey Line
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━►
  0     dx    2dx   3dx   ...                            Distance (m)

Shot 1: S₁──X₁──[G₁ G₂ G₃ G₄ G₅ G₆ ... G_N]
Shot 2:      S₂──X₁──[G₁ G₂ G₃ G₄ G₅ G₆ ... G_N]
Shot 3:           S₃──X₁──[G₁ G₂ G₃ G₄ G₅ G₆ ... G_N]
  ...

S = Source position
X₁ = Source-to-first-receiver offset
G = Geophone (receiver)
N = Number of channels
dx = Receiver spacing
```

### 2.2 Key Parameters

| Parameter | Symbol | Typical Values | Description |
|-----------|--------|----------------|-------------|
| Receiver spacing | dx | 1-5 m | Distance between geophones |
| Number of channels | N | 24, 48 | Channels per shot record |
| Source offset | X₁ | 5-30 m | Distance from source to first geophone |
| Array length | L | L = (N-1)·dx | Total spread length |
| Roll increment | Δx | dx or multiples | Movement between shots |

### 2.3 Shoot-Through (Recompilation) Alternative

Instead of moving geophones, keep array fixed and move source:

```
Fixed Array: [G₁ G₂ G₃ G₄ G₅ G₆ ... G₂₄]
              ↑
Shot 1: S₁ at position -X₁ from G₁
Shot 2: S₂ at position -X₁ from G₂
Shot 3: S₃ at position -X₁ from G₃
...

Recompile by selecting sub-arrays from each shot that maintain X₁ and L.
```

---

## 3. Sub-Array Extraction Algorithm

### 3.1 Problem Statement

**Goal**: From a collection of full shot records, extract sub-arrays where:
1. Each sub-array has the same number of channels (n_sub)
2. Each sub-array has the same source offset (X₁)
3. Sub-arrays are centered at different midpoint positions

### 3.2 Algorithm for Roll-Along Data

```python
def extract_roll_along_subarrays(shot_records, geometry, target_subarray_length, 
                                  target_source_offset):
    """
    Extract sub-arrays from roll-along MASW data.
    
    Parameters
    ----------
    shot_records : list of dict
        Each dict contains:
            - 'data': ndarray [n_samples, n_channels]
            - 'shot_position': float (m)
            - 'first_receiver_position': float (m)
    geometry : dict
        - 'dx': receiver spacing (m)
        - 'n_channels': total channels per record
    target_subarray_length : int
        Number of channels in extracted sub-array
    target_source_offset : float
        Desired source-to-first-receiver offset (m)
    
    Returns
    -------
    subarrays : list of dict
        Each dict contains:
            - 'data': ndarray [n_samples, n_sub]
            - 'midpoint': float (m)
            - 'source_offset': float (m)
            - 'shot_index': int
    """
    
    dx = geometry['dx']
    n_channels = geometry['n_channels']
    n_sub = target_subarray_length
    
    subarrays = []
    
    for shot_idx, record in enumerate(shot_records):
        shot_pos = record['shot_position']
        first_recv_pos = record['first_receiver_position']
        data = record['data']
        
        # Current geometry
        current_offset = first_recv_pos - shot_pos
        
        # Find channel range that gives target_source_offset
        # Channel 0 is at first_recv_pos
        # Channel i is at first_recv_pos + i * dx
        
        # Required first channel for target offset:
        # shot_pos + target_source_offset = first_recv_pos + start_ch * dx
        start_ch = round((shot_pos + target_source_offset - first_recv_pos) / dx)
        end_ch = start_ch + n_sub
        
        # Check bounds
        if start_ch < 0 or end_ch > n_channels:
            continue  # Skip if target geometry not achievable
        
        # Extract sub-array
        sub_data = data[:, start_ch:end_ch]
        
        # Compute midpoint position
        # First channel of sub-array is at: first_recv_pos + start_ch * dx
        # Last channel is at: first_recv_pos + (end_ch - 1) * dx
        sub_first = first_recv_pos + start_ch * dx
        sub_last = first_recv_pos + (end_ch - 1) * dx
        midpoint = (sub_first + sub_last) / 2.0
        
        subarrays.append({
            'data': sub_data,
            'midpoint': midpoint,
            'source_offset': target_source_offset,
            'shot_index': shot_idx,
            'start_channel': start_ch,
            'n_channels': n_sub
        })
    
    return subarrays
```

### 3.3 Algorithm for Shoot-Through Data

```python
def recompile_shoot_through_subarrays(shot_records, geometry, 
                                       target_subarray_length):
    """
    Recompile shoot-through data into roll-along format.
    
    In shoot-through acquisition:
    - Geophone array is fixed
    - Source moves along the line
    
    For each shot, we select channels that maintain constant offset
    relative to the source.
    
    Parameters
    ----------
    shot_records : list of dict
        Each dict contains:
            - 'data': ndarray [n_samples, n_channels]
            - 'shot_position': float (m)
            - 'receiver_positions': ndarray of receiver positions (m)
    geometry : dict
        - 'dx': receiver spacing
        - 'n_channels': total channels
    target_subarray_length : int
        Channels per sub-array
    
    Returns
    -------
    subarrays : list of dict
    """
    
    dx = geometry['dx']
    n_full = geometry['n_channels']
    n_sub = target_subarray_length
    
    subarrays = []
    
    for shot_idx, record in enumerate(shot_records):
        shot_pos = record['shot_position']
        recv_pos = record['receiver_positions']
        data = record['data']
        
        # Find the channel closest to shot position
        # This defines the "center" of the spread relative to source
        center_ch = np.argmin(np.abs(recv_pos - shot_pos))
        
        # Select sub-array centered on the shot position
        # For consistent geometry, take n_sub channels starting
        # at a fixed offset from the nearest channel
        
        # Strategy: select channels such that source offset X₁ is constant
        # If shot is between channels i and i+1, use channels starting from i+1
        
        # Simple approach: channels where source is at specified offset
        first_channel_offset = 6 * dx  # e.g., 6 channels from source
        
        # Find first channel at desired offset from source
        target_first_pos = shot_pos + first_channel_offset
        start_ch = np.argmin(np.abs(recv_pos - target_first_pos))
        end_ch = start_ch + n_sub
        
        if end_ch <= n_full:
            sub_data = data[:, start_ch:end_ch]
            midpoint = (recv_pos[start_ch] + recv_pos[min(end_ch-1, n_full-1)]) / 2.0
            
            subarrays.append({
                'data': sub_data,
                'midpoint': midpoint,
                'source_offset': recv_pos[start_ch] - shot_pos,
                'shot_index': shot_idx,
                'start_channel': start_ch
            })
    
    return subarrays
```

---

## 4. Midpoint Calculation

### 4.1 Sub-Array Midpoint

For a sub-array with:
- First receiver at position x_first
- Last receiver at position x_last
- Array length L_sub = x_last - x_first

**Midpoint position:**
```
x_mid = (x_first + x_last) / 2 = x_first + L_sub / 2
```

### 4.2 Source-Receiver Midpoint (for CMP methods)

When source position matters:
```
x_mid = (x_source + x_array_center) / 2
```

### 4.3 Effective Investigation Point

The dispersion curve represents an average over the array footprint:
- Horizontal averaging: primarily beneath the array
- Depth sensitivity: varies with wavelength (λ/3 to λ/2 rule)

---

## 5. Sub-Array Configuration Examples

### 5.1 Example: 24-Channel Array → 12-Channel Sub-Arrays

**Full array:** 24 channels, dx = 2m, L = 46m
**Target sub-array:** 12 channels, L_sub = 22m
**Source offset:** X₁ = 10m

```
Full record channels: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, ... 23]
                       ↑                    ↑
                    Source               First sub-array
                    at -10m              (channels 5-16)
                    
Sub-array 1: channels 5-16  → midpoint at x_mid1
Sub-array 2: channels 6-17  → midpoint at x_mid2 = x_mid1 + dx
Sub-array 3: channels 7-18  → midpoint at x_mid3 = x_mid2 + dx
...
```

### 5.2 Optimizing Sub-Array Length

**Trade-off:**
- **Shorter sub-arrays** → Better lateral resolution, shallower depth penetration
- **Longer sub-arrays** → Deeper investigation, lower lateral resolution

**Rule of thumb:**
```
L_sub ≈ 2 × target_depth
```

---

## 6. File Management for Multi-Shot Processing

### 6.1 Survey Configuration File (JSON)

```json
{
    "survey_name": "Site_A_MASW_2D",
    "acquisition_type": "roll_along",
    "geometry": {
        "dx": 2.0,
        "n_channels": 24,
        "source_offset": 10.0,
        "roll_increment": 2.0
    },
    "shots": [
        {
            "filename": "shot_001.dat",
            "shot_position": 0.0,
            "first_receiver_position": 10.0
        },
        {
            "filename": "shot_002.dat", 
            "shot_position": 2.0,
            "first_receiver_position": 12.0
        }
    ],
    "subarray_config": {
        "n_channels": 12,
        "target_offset": 10.0
    }
}
```

### 6.2 Batch Processing Script

```python
import json
import os
from sw_transform.processing.seg2 import load_seg2_ar
from sw_transform.core.service import run_single

def process_2d_survey(config_path, output_dir, method='ps'):
    """
    Process 2D MASW survey.
    
    Parameters
    ----------
    config_path : str
        Path to survey configuration JSON
    output_dir : str
        Output directory for results
    method : str
        Processing method ('fk', 'fdbf', 'ps', 'ss')
    
    Returns
    -------
    results : list of dict
        Processing results for each sub-array
    """
    
    with open(config_path) as f:
        config = json.load(f)
    
    # Extract sub-arrays
    shot_records = []
    for shot_info in config['shots']:
        t, T, _, dx, dt, _ = load_seg2_ar(shot_info['filename'])
        shot_records.append({
            'data': T,
            'time': t,
            'dt': dt,
            'shot_position': shot_info['shot_position'],
            'first_receiver_position': shot_info['first_receiver_position']
        })
    
    geometry = config['geometry']
    sub_config = config['subarray_config']
    
    subarrays = extract_roll_along_subarrays(
        shot_records, 
        geometry,
        sub_config['n_channels'],
        sub_config['target_offset']
    )
    
    # Process each sub-array
    results = []
    os.makedirs(output_dir, exist_ok=True)
    
    for i, sub in enumerate(subarrays):
        # Create params dict for run_single
        params = {
            'data': sub['data'],  # Would need service modification
            'midpoint': sub['midpoint'],
            'base': f"subarray_{i:03d}",
            'key': method,
            'offset': f"+{sub['source_offset']:.0f}m",
            'outdir': output_dir,
            # ... other standard params
        }
        
        # Process
        # Note: run_single currently expects file path, 
        # would need modification to accept data directly
        result = run_single_from_data(params)
        result['midpoint'] = sub['midpoint']
        results.append(result)
    
    return results
```

---

## 7. Quality Control

### 7.1 Geometry Validation

```python
def validate_subarray_geometry(subarrays, tolerance=0.1):
    """Check that all sub-arrays have consistent geometry."""
    
    offsets = [s['source_offset'] for s in subarrays]
    n_channels = [s['n_channels'] for s in subarrays]
    
    # Check offset consistency
    offset_std = np.std(offsets)
    if offset_std > tolerance:
        print(f"Warning: Source offset varies by {offset_std:.2f} m")
    
    # Check channel count
    if len(set(n_channels)) > 1:
        print(f"Warning: Inconsistent sub-array lengths: {set(n_channels)}")
    
    # Check midpoint spacing
    midpoints = sorted([s['midpoint'] for s in subarrays])
    spacings = np.diff(midpoints)
    spacing_std = np.std(spacings)
    if spacing_std > tolerance:
        print(f"Warning: Irregular midpoint spacing: mean={np.mean(spacings):.2f}, std={spacing_std:.2f}")
    
    return True
```

### 7.2 Coverage Map

```python
def plot_coverage(subarrays, dx):
    """Plot sub-array coverage along survey line."""
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(12, 4))
    
    for i, sub in enumerate(subarrays):
        mid = sub['midpoint']
        n = sub['n_channels']
        L = (n - 1) * dx
        x0 = mid - L/2
        x1 = mid + L/2
        ax.hlines(i, x0, x1, colors='blue', linewidth=2)
        ax.plot(mid, i, 'ro', markersize=4)
    
    ax.set_xlabel('Position along line (m)')
    ax.set_ylabel('Sub-array index')
    ax.set_title('Sub-array Coverage')
    plt.tight_layout()
    return fig
```

---

## 8. Integration with SW_Transform

### 8.1 Required Modifications to service.py

```python
def run_single_from_array(params):
    """
    Run processing on pre-extracted array data.
    
    New params keys:
        - 'data': ndarray [n_samples, n_channels]
        - 'dt': sampling interval
        - 'dx': receiver spacing
        - 'midpoint': position along line (for metadata)
    """
    # Similar to run_single but skips file loading
    pass
```

### 8.2 New CLI Command

```bash
python -m sw_transform.cli.batch2d \
    --config survey_config.json \
    --output output_dir \
    --method ps \
    --subarray-length 12
```

---

## 9. References

1. Park, C.B., & Miller, R.D. (2008). "Roadside Passive MASW." *JEEG*, 13(1).

2. masw.com/RollAlongACQ.html - SurfSeis documentation

3. Park Seismic LLC. "Optimum Offset and Dispersion Image."
