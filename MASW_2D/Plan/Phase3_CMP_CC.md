# Phase 3: CMP Cross-Correlation (CMP-CC)

## Advanced Virtual Source Method

---

## 1. Phase 3 Scope

### 1.1 What We're Building

**CMP Cross-Correlation Technique:**
- Create virtual source-receiver pairs via trace correlation
- Achieve lateral resolution of dx/2 (half receiver spacing!)
- Enhanced SNR through stacking
- More dispersion curves from same field data

### 1.2 Prerequisites

- Phase 1 complete (basic sub-array extraction)
- Phase 2 complete (roll-along concepts)

### 1.3 Deliverables

1. CMP-CC computation module
2. CMP gather formation
3. Modified transform for CMP gathers
4. CMP-CC workflow
5. Stacking fold visualization
6. Quality metrics for CMP-CC
7. CLI and GUI integration

---

## 2. Mathematical Foundation

### 2.1 Cross-Correlation Theory

For two time-series signals u(t) and v(t):

```
R_uv(τ) = ∫ u(t) · v(t + τ) dt
```

In frequency domain:
```
R_uv(τ) = F⁻¹{ U*(f) · V(f) }
```

### 2.2 Virtual Source Concept

Cross-correlating traces from receivers i and j creates a virtual record:
- **Virtual source position**: (x_i + x_j) / 2 (midpoint)
- **Virtual receiver distance**: |x_j - x_i| / 2

### 2.3 Resolution Enhancement

For N-channel array:
- **Number of correlation pairs**: N(N-1)/2
- **Unique midpoints**: N-1
- **Midpoint spacing**: dx/2 (half receiver spacing!)

Example: 24 channels → 276 pairs → 23 midpoints at 1m spacing (for dx=2m)

---

## 3. Algorithm Overview

### 3.1 Step-by-Step Process

```
Step 1: Input shot gather T[n_samples, n_channels]
        ↓
Step 2: Compute all pairwise correlations (N(N-1)/2 pairs)
        ↓
Step 3: Group correlations by Common MidPoint (CMP)
        ↓
Step 4: Stack equal-spacing correlations at each CMP
        ↓
Step 5: Form CMP-CC gathers [n_lags, n_spacings] for each midpoint
        ↓
Step 6: Apply MASW transform (FK, PS, FDBF, SS) to each gather
        ↓
Step 7: Extract dispersion curves at each midpoint
```

### 3.2 Key Data Structures

```python
@dataclass
class CorrelationPair:
    cc: np.ndarray          # Cross-correlation result
    midpoint: float         # (x_i + x_j) / 2
    spacing: float          # x_j - x_i
    channel_i: int
    channel_j: int

@dataclass  
class CMPGather:
    gather: np.ndarray      # [n_lags, n_spacings]
    spacings: np.ndarray    # Virtual receiver spacings
    lag_times: np.ndarray   # Correlation lag times
    midpoint: float
    fold: dict              # Stacking fold per spacing
```

---

## 4. Implementation Tasks

### Task 1: Core CMP-CC Computation

```python
# extraction/cmpcc_extractor.py

def compute_all_correlations(
    data: np.ndarray,
    dx: float,
    max_lag_samples: int = None,
    normalize: bool = True
) -> List[CorrelationPair]:
    """Compute all pairwise cross-correlations."""
    pass

def group_by_midpoint(
    correlations: List[CorrelationPair],
    dx: float
) -> Dict[float, List[CorrelationPair]]:
    """Group correlations by common midpoint."""
    pass

def create_cmp_gather(
    midpoint_group: List[CorrelationPair],
    dx: float
) -> CMPGather:
    """Stack equal-spacing correlations into gather."""
    pass

def compute_cmpcc_gathers(
    data: np.ndarray,
    time: np.ndarray,
    dx: float
) -> Dict[float, CMPGather]:
    """Complete CMP-CC pipeline."""
    pass
```

### Task 2: Transform Adaptation

CMP-CC gathers have different structure than shot gathers:
- Rows: correlation lags (symmetric around zero)
- Columns: virtual receiver spacings (not regular dx)

```python
# processing/cmpcc_transform.py

def apply_ps_to_cmpcc(
    cmpcc_gather: CMPGather,
    velocities: np.ndarray,
    frequencies: np.ndarray
) -> np.ndarray:
    """Phase-shift transform adapted for CMP-CC gather."""
    pass

def apply_fk_to_cmpcc(
    cmpcc_gather: CMPGather,
    ...
) -> np.ndarray:
    """FK transform adapted for CMP-CC gather."""
    pass
```

### Task 3: CMP-CC Workflow

```python
# workflows/cmpcc.py

class CMPCCWorkflow:
    """Workflow for CMP Cross-Correlation processing."""
    
    def run(self):
        # 1. Load shot data
        # 2. Compute CMP-CC gathers
        # 3. For each midpoint:
        #    a. Apply transform
        #    b. Pick dispersion curve
        # 4. Organize results
        pass
```

### Task 4: Quality Metrics

```python
def compute_stacking_fold(cmpcc_gathers: Dict) -> Dict:
    """Count number of correlations stacked at each (midpoint, spacing)."""
    pass

def plot_fold_map(fold_data: Dict) -> Figure:
    """Visualize stacking fold as heatmap."""
    pass

def estimate_snr_improvement(fold: int) -> float:
    """SNR improvement ≈ √(fold) for random noise."""
    return np.sqrt(fold)
```

### Task 5: Memory Optimization

For large datasets (many channels, long records):

```python
def compute_cmpcc_batched(
    data: np.ndarray,
    dx: float,
    batch_size: int = 100
) -> Generator[List[CorrelationPair], None, None]:
    """Memory-efficient batched CMP-CC computation."""
    pass

def compute_cmpcc_parallel(
    data: np.ndarray,
    dx: float,
    n_workers: int = 4
) -> Dict[float, CMPGather]:
    """Parallel CMP-CC computation."""
    pass
```

### Task 6: CLI and GUI Integration

```bash
# CLI commands
masw2d cmpcc compute shot.dat -o cmpcc_gathers.npz
masw2d cmpcc process cmpcc_gathers.npz --method ps -o results/
masw2d cmpcc fold cmpcc_gathers.npz  # Show fold map

# Combined workflow
masw2d workflow run config.json --type cmpcc
```

---

## 5. File Summary

| Path | Purpose |
|------|---------|
| `masw2d/extraction/cmpcc_extractor.py` | NEW: CMP-CC computation |
| `masw2d/processing/cmpcc_transform.py` | NEW: Adapted transforms |
| `masw2d/processing/cmpcc_quality.py` | NEW: Quality metrics |
| `masw2d/workflows/cmpcc.py` | NEW: CMP-CC workflow |
| `masw2d/output/fold_map.py` | NEW: Fold visualization |
| `cli/masw2d/cmpcc_cmd.py` | NEW: CMP-CC commands |

---

## 6. Performance Considerations

### 6.1 Computational Complexity

| Operation | Complexity | For 24ch, 2000 samples |
|-----------|------------|------------------------|
| All correlations | O(N² × M log M) | ~2M operations |
| Grouping | O(N²) | 276 pairs |
| Transform per gather | O(V × F × S) | ~400 × 100 × 23 |

### 6.2 Memory Requirements

```
Correlation storage: N(N-1)/2 × (2M-1) × 8 bytes
For 24ch, 2000 samples: ~21 MB
```

### 6.3 Optimization Strategies

1. **Compute correlations in frequency domain** (faster for long signals)
2. **Process midpoints independently** (parallel-friendly)
3. **Use sparse storage** if many spacings have zero fold
4. **Stream processing** for very large datasets

---

## 7. Estimated Timeline

| Task | Effort |
|------|--------|
| Core CMP-CC computation | 5-6 hours |
| Transform adaptation | 4-5 hours |
| CMP-CC workflow | 3-4 hours |
| Quality metrics | 2-3 hours |
| Memory optimization | 3-4 hours |
| CLI integration | 2-3 hours |
| GUI integration | 3-4 hours |
| Testing | 4-5 hours |

**Total: 26-34 hours**

---

## 8. Success Criteria

- [ ] All pairwise correlations computed correctly
- [ ] Midpoint grouping produces N-1 unique positions
- [ ] Stacking combines traces with same spacing
- [ ] Transforms work on CMP-CC gathers
- [ ] Dispersion curves extracted at each midpoint
- [ ] Fold map shows expected pattern
- [ ] Results comparable to standard MASW
- [ ] Performance acceptable for 24-48 channel data

---

## 9. References

1. Hayashi, K., & Suzuki, H. (2004). "CMP cross-correlation analysis of multi-channel surface-wave data." *Exploration Geophysics*, 35(1), 7-13.

2. Nakata, N., et al. (2011). "Body and surface wave extraction from ambient noise correlations." *Geophysical Research Letters*.

3. Park, C.B., et al. (2007). "Multichannel analysis of surface waves (MASW)." *The Leading Edge*.
