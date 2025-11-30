# CMP Cross-Correlation (CMP-CC) Technical Reference

## Detailed Algorithm and Implementation Guide

---

## 1. Overview

The CMP Cross-Correlation technique enhances lateral resolution in 2D MASW by exploiting trace-pair correlations. Instead of using the raw shot gather directly, CMP-CC creates virtual source-receiver pairs at common midpoint locations.

**Key Benefits:**
- Improved lateral resolution (sub-receiver-spacing)
- Enhanced signal-to-noise through stacking
- More dispersion curves from same field data

---

## 2. Mathematical Foundation

### 2.1 Cross-Correlation Theory

For two time-series signals u(t) and v(t), the cross-correlation is:

```
R_uv(τ) = ∫ u(t) · v(t + τ) dt
```

In the frequency domain (via Wiener-Khinchin theorem):

```
R_uv(τ) = F⁻¹{ U*(f) · V(f) }
```

where U(f) and V(f) are Fourier transforms and * denotes complex conjugate.

### 2.2 Phase Information Preservation

For surface waves, the cross-correlation between two receivers separated by distance d contains:

```
R_ij(τ) peaks at τ = d / c(f)
```

where c(f) is the frequency-dependent phase velocity. The correlation preserves dispersion information while averaging out incoherent noise.

### 2.3 Virtual Source Concept

Cross-correlating traces from receivers i and j creates a virtual seismic record as if:
- Source at position (x_i + x_j)/2 (midpoint)
- Receiver at distance |x_j - x_i|/2 from virtual source

---

## 3. CMP-CC Workflow

### 3.1 Step 1: Input Data

**Input:** Shot gather with N channels
```
T[n_samples, n_channels]
t = time vector
x = receiver positions [x_0, x_1, ..., x_{N-1}]
dx = receiver spacing
```

### 3.2 Step 2: Compute All Pairwise Cross-Correlations

For each receiver pair (i, j) where j > i:

```python
for i in range(n_channels):
    for j in range(i+1, n_channels):
        # Cross-correlate traces
        cc_ij = correlate(T[:, i], T[:, j], mode='full')
        
        # Compute midpoint and spacing
        midpoint = (x[i] + x[j]) / 2.0
        spacing = x[j] - x[i]
        
        # Store with metadata
        correlations.append({
            'cc': cc_ij,
            'midpoint': midpoint,
            'spacing': spacing,
            'i': i, 'j': j
        })
```

**Number of pairs:** N(N-1)/2

### 3.3 Step 3: Sort by Common Midpoint

Group correlations sharing the same midpoint:

```python
from collections import defaultdict

midpoint_groups = defaultdict(list)
for corr in correlations:
    mid_key = round(corr['midpoint'] / dx) * dx  # quantize to grid
    midpoint_groups[mid_key].append(corr)
```

### 3.4 Step 4: Stack Equal-Spacing Correlations

Within each midpoint group, stack correlations with identical spacing:

```python
def create_cmpcc_gather(mid_group, dx, n_spacing_bins):
    """Create CMP-CC gather for one midpoint."""
    
    spacing_stacks = defaultdict(list)
    
    for corr in mid_group:
        spacing_key = round(corr['spacing'] / dx)  # in units of dx
        spacing_stacks[spacing_key].append(corr['cc'])
    
    # Stack traces with same spacing
    gather = []
    spacings = []
    for sp_key in sorted(spacing_stacks.keys()):
        if sp_key > 0:  # skip zero spacing
            stacked = np.mean(spacing_stacks[sp_key], axis=0)
            gather.append(stacked)
            spacings.append(sp_key * dx)
    
    return np.array(gather).T, np.array(spacings)  # [n_samples, n_spacings]
```

### 3.5 Step 5: Form CMP-CC Gathers

Each midpoint now has a gather with:
- Rows: time samples (from correlation lags)
- Columns: virtual receiver spacings

```
CMP-CC gather shape: [2*n_samples-1, n_unique_spacings]
```

### 3.6 Step 6: Apply MASW Transform

Apply standard dispersion extraction (FK, PS, FDBF, or SS) to each CMP-CC gather:

```python
for midpoint, gather in cmpcc_gathers.items():
    # Extract dispersion curve
    f, v, power = apply_transform(gather, dt, spacings, method='ps')
    dispersion_curves[midpoint] = (f, v, power)
```

---

## 4. Implementation Details

### 4.1 Complete Algorithm

```python
import numpy as np
from scipy.signal import correlate
from collections import defaultdict

def compute_cmpcc_gathers(T, t, dx, max_lag_samples=None):
    """
    Compute CMP Cross-Correlation gathers from shot gather.
    
    Parameters
    ----------
    T : ndarray, shape (n_samples, n_channels)
        Time-domain shot gather
    t : ndarray, shape (n_samples,)
        Time vector
    dx : float
        Receiver spacing (m)
    max_lag_samples : int, optional
        Maximum lag for correlation (defaults to n_samples)
    
    Returns
    -------
    cmpcc_gathers : dict
        {midpoint: (gather, spacings, lag_times)}
    """
    n_samples, n_channels = T.shape
    dt = t[1] - t[0]
    
    if max_lag_samples is None:
        max_lag_samples = n_samples
    
    # Receiver positions
    x = np.arange(n_channels) * dx
    
    # Step 1: Compute all pairwise correlations
    correlations = []
    
    for i in range(n_channels):
        for j in range(i + 1, n_channels):
            # Normalize traces
            trace_i = T[:, i] - np.mean(T[:, i])
            trace_j = T[:, j] - np.mean(T[:, j])
            
            # Compute cross-correlation
            cc = correlate(trace_i, trace_j, mode='full')
            
            # Extract symmetric part around zero lag
            center = len(cc) // 2
            cc_sym = cc[center - max_lag_samples:center + max_lag_samples + 1]
            
            correlations.append({
                'cc': cc_sym,
                'midpoint': (x[i] + x[j]) / 2.0,
                'spacing': x[j] - x[i],
                'i': i,
                'j': j
            })
    
    # Step 2: Group by midpoint
    midpoint_groups = defaultdict(list)
    unique_midpoints = np.unique([c['midpoint'] for c in correlations])
    
    for corr in correlations:
        # Find nearest grid midpoint
        mid_idx = np.argmin(np.abs(unique_midpoints - corr['midpoint']))
        mid_key = unique_midpoints[mid_idx]
        midpoint_groups[mid_key].append(corr)
    
    # Step 3: Create CMP-CC gathers
    cmpcc_gathers = {}
    lag_times = np.arange(-max_lag_samples, max_lag_samples + 1) * dt
    
    for midpoint, group in midpoint_groups.items():
        # Group by spacing within this midpoint
        spacing_traces = defaultdict(list)
        
        for corr in group:
            spacing_key = round(corr['spacing'] / dx) * dx
            spacing_traces[spacing_key].append(corr['cc'])
        
        # Stack and build gather
        spacings = []
        stacked_traces = []
        
        for spacing in sorted(spacing_traces.keys()):
            if spacing > 0:  # Positive spacing only
                # Stack traces with same spacing
                traces = np.array(spacing_traces[spacing])
                stacked = np.mean(traces, axis=0)
                
                stacked_traces.append(stacked)
                spacings.append(spacing)
        
        if stacked_traces:
            gather = np.column_stack(stacked_traces)
            cmpcc_gathers[midpoint] = {
                'gather': gather,
                'spacings': np.array(spacings),
                'lag_times': lag_times,
                'midpoint': midpoint
            }
    
    return cmpcc_gathers


def apply_ps_to_cmpcc(cmpcc_data, velocities, frequencies):
    """
    Apply phase-shift transform to CMP-CC gather.
    
    Parameters
    ----------
    cmpcc_data : dict
        Output from compute_cmpcc_gathers for one midpoint
    velocities : ndarray
        Trial phase velocities (m/s)
    frequencies : ndarray
        Frequencies to compute (Hz)
    
    Returns
    -------
    power : ndarray, shape (n_velocities, n_frequencies)
    """
    gather = cmpcc_data['gather']
    spacings = cmpcc_data['spacings']
    lag_times = cmpcc_data['lag_times']
    dt = lag_times[1] - lag_times[0]
    
    n_lags, n_spacings = gather.shape
    n_vel = len(velocities)
    n_freq = len(frequencies)
    
    # FFT of gather
    gather_fft = np.fft.rfft(gather, axis=0)
    freqs_fft = np.fft.rfftfreq(n_lags, dt)
    
    # Power spectrum
    power = np.zeros((n_vel, n_freq))
    
    for iv, v in enumerate(velocities):
        for ifr, f in enumerate(frequencies):
            # Find nearest FFT frequency
            idx_f = np.argmin(np.abs(freqs_fft - f))
            
            # Phase shifts for each spacing
            phase_shifts = np.exp(1j * 2 * np.pi * f * spacings / v)
            
            # Sum with phase shifts
            spec_sum = np.sum(gather_fft[idx_f, :] * phase_shifts)
            power[iv, ifr] = np.abs(spec_sum) ** 2
    
    return power
```

### 4.2 Memory Optimization

For large datasets, compute correlations in batches:

```python
def compute_cmpcc_batched(T, dx, batch_size=100):
    """Memory-efficient CMP-CC computation."""
    n_samples, n_channels = T.shape
    n_pairs = n_channels * (n_channels - 1) // 2
    
    # Process in batches
    for batch_start in range(0, n_pairs, batch_size):
        batch_correlations = []
        # ... compute batch
        yield batch_correlations
```

---

## 5. Resolution Analysis

### 5.1 Lateral Resolution

The lateral resolution of CMP-CC depends on:
- Receiver spacing dx
- Number of channels N
- Stacking redundancy

**Unique midpoints:** (N-1) for equally spaced array
**Midpoint spacing:** dx/2 (half the receiver spacing)

### 5.2 Depth Resolution

Limited by maximum receiver spacing in the gather:
- Maximum spacing: (N-1) × dx
- Approximate depth limit: L/2 where L = array length

---

## 6. Quality Control

### 6.1 Stacking Fold

Count number of correlations stacked at each (midpoint, spacing):

```python
fold_map = {}
for mid, group in midpoint_groups.items():
    fold_map[mid] = {}
    for corr in group:
        sp = corr['spacing']
        fold_map[mid][sp] = fold_map[mid].get(sp, 0) + 1
```

Higher fold = more robust stacking.

### 6.2 Signal-to-Noise Improvement

SNR improvement ≈ √(fold) for random noise.

---

## 7. References

1. Hayashi, K., & Suzuki, H. (2004). "CMP cross-correlation analysis of multi-channel surface-wave data." *Exploration Geophysics*, 35(1), 7-13.

2. Nakata, N., et al. (2011). "Body and surface wave extraction from ambient noise correlations." *Geophysical Research Letters*, 38(24).

3. Park, C.B., et al. (2007). "Multichannel analysis of surface waves (MASW) - active and passive methods." *The Leading Edge*, 26(1), 60-64.
