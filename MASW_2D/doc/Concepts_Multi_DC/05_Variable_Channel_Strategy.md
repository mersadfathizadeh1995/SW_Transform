# Variable Channel Strategy for Multi-Resolution Analysis

## Combining Different Sub-Array Sizes

---

## 1. The Innovation: Variable Channel Counts

### 1.1 Why This Matters

Commercial software (SurfSeis, ParkSEIS) typically enforces:
- **Fixed sub-array length** for all extractions
- **Uniform processing** across the survey

**Our innovation:** Allow **multiple sub-array sizes** from the same data, enabling:
- Shallow analysis (short sub-arrays, high lateral resolution)
- Deep analysis (long sub-arrays, lower lateral resolution)
- Combined interpretation for complete characterization

### 1.2 The Trade-Off Revisited

```
Sub-array      Investigation    Lateral        Number of
Length         Depth            Resolution     Sub-arrays
────────────────────────────────────────────────────────────
8 channels     ~7m              2m spacing     17 sub-arrays
12 channels    ~11m             2m spacing     13 sub-arrays
16 channels    ~15m             2m spacing     9 sub-arrays
20 channels    ~19m             2m spacing     5 sub-arrays
24 channels    ~23m             Single point   1 sub-array

(For 24-channel array, dx=2m)
```

---

## 2. Multi-Pass Processing Strategy

### 2.1 Concept

Process the same data multiple times with different sub-array configurations:

```
Pass 1 (Shallow/Dense):   8-channel sub-arrays → 17 DCs, depth ~7m
Pass 2 (Medium):          12-channel sub-arrays → 13 DCs, depth ~11m  
Pass 3 (Deep/Sparse):     24-channel full array → 1 DC, depth ~23m
```

### 2.2 Visual Representation

```
Position (m):  0   5   10   15   20   25   30   35   40   45
               │   │    │    │    │    │    │    │    │    │

Pass 1 (8ch):  ●   ●    ●    ●    ●    ●    ●    ●    ●    ●    ... (many DCs)
               └─7m depth────────────────────────────────────┘

Pass 2 (12ch):     ●         ●         ●         ●         ●  ... (fewer DCs)
                   └────────11m depth──────────────────────┘

Pass 3 (24ch):                    ●                            ... (one DC)
                                  └──────23m depth───────────┘

Combined:      Shallow detail + Deep information at center
```

---

## 3. Detailed Example

### 3.1 Configuration

```
Array: 24 geophones, dx = 2m, positions 0-46m
Shots: -2, -5, -10, -20, +48, +51, +56, +66m (8 shots)
```

### 3.2 Pass 1: 8-Channel Sub-Arrays (Shallow, Dense)

```
Sub-array length: 8 channels = 14m
Investigation depth: ~7m
Number of sub-arrays: 24 - 8 + 1 = 17

Sub-arrays:
SA-01: G1-G8   (0-14m)   → midpoint 7m
SA-02: G2-G9   (2-16m)   → midpoint 9m
SA-03: G3-G10  (4-18m)   → midpoint 11m
...
SA-17: G17-G24 (32-46m)  → midpoint 39m

Total DCs: 17 sub-arrays × 8 shots = 136 dispersion curves
Midpoint range: 7m to 39m (dense coverage)
```

### 3.3 Pass 2: 12-Channel Sub-Arrays (Medium)

```
Sub-array length: 12 channels = 22m
Investigation depth: ~11m
Number of sub-arrays: 24 - 12 + 1 = 13

Sub-arrays:
SA-01: G1-G12  (0-22m)   → midpoint 11m
SA-02: G2-G13  (2-24m)   → midpoint 13m
...
SA-13: G13-G24 (24-46m)  → midpoint 35m

Total DCs: 13 sub-arrays × 8 shots = 104 dispersion curves
Midpoint range: 11m to 35m
```

### 3.4 Pass 3: 16-Channel Sub-Arrays (Medium-Deep)

```
Sub-array length: 16 channels = 30m
Investigation depth: ~15m
Number of sub-arrays: 24 - 16 + 1 = 9

Sub-arrays:
SA-01: G1-G16  (0-30m)   → midpoint 15m
SA-02: G2-G17  (2-32m)   → midpoint 17m
...
SA-09: G9-G24  (16-46m)  → midpoint 31m

Total DCs: 9 sub-arrays × 8 shots = 72 dispersion curves
Midpoint range: 15m to 31m
```

### 3.5 Pass 4: Full 24-Channel Array (Maximum Depth)

```
Sub-array length: 24 channels = 46m
Investigation depth: ~23m
Number of sub-arrays: 1

Full array: G1-G24 (0-46m) → midpoint 23m

Total DCs: 1 sub-array × 8 shots = 8 dispersion curves
All at midpoint 23m (can be averaged for robust result)
```

### 3.6 Combined Results

```
Total dispersion curves: 136 + 104 + 72 + 8 = 320 DCs

Coverage by depth:
- Shallow (0-7m):   Dense lateral coverage from Pass 1
- Medium (7-11m):   Good coverage from Pass 1 + 2
- Deep (11-15m):    Coverage from Pass 2 + 3
- Deepest (15-23m): Coverage from Pass 3 + 4 (fewer points)
```

---

## 4. Combining Dispersion Curves

### 4.1 At Same Midpoint, Different Depths

For midpoint 23m, we have:
- Pass 1 (8ch):  DC covering ~0-7m depth
- Pass 2 (12ch): DC covering ~0-11m depth
- Pass 3 (16ch): DC covering ~0-15m depth
- Pass 4 (24ch): DC covering ~0-23m depth

**These curves have different frequency ranges:**

```
Frequency vs. Sub-array Length:
- Short sub-arrays → High frequencies only (shallow)
- Long sub-arrays → Low frequencies (deep) + high frequencies

Pass 4 (24ch):    ████████████████████████████  (5-80 Hz, full range)
Pass 3 (16ch):    ██████████████████            (8-80 Hz)
Pass 2 (12ch):    ████████████████              (10-80 Hz)
Pass 1 (8ch):     ████████████                  (15-80 Hz)
                  └─────────────────────────────►
                  Low freq              High freq
                  (Deep)                (Shallow)
```

### 4.2 Merging Strategy

```
For position X:
1. Start with deepest DC available (longest sub-array)
2. Extend frequency range with shorter sub-array DCs
3. In overlapping frequencies, average or select best quality

Example at midpoint 23m:
- Use Pass 4 DC for 5-15 Hz (only available from full array)
- Use Pass 4 or Pass 3 for 15-25 Hz (average if both available)
- Use any pass for high frequencies (all have this range)
```

---

## 5. Quality-Based Selection

### 5.1 Source Offset Considerations

Not all DCs are equal quality. Source offset relative to sub-array affects:
- Near-field contamination (offset too small)
- Signal strength (offset too large)
- Optimal: X₁ ≈ L/2 for the sub-array

```
For 8-channel sub-array (L=14m), optimal offset ≈ 7m
For 12-channel sub-array (L=22m), optimal offset ≈ 11m
For 24-channel full array (L=46m), optimal offset ≈ 23m
```

### 5.2 Selecting Best DCs

```
For each (midpoint, sub-array_size) combination:
├── Calculate effective source offset for each shot
├── Rank shots by |offset - L/2| (smaller is better)
├── Keep top 3-5 best shots
└── Average their DCs

Example for SA-01 (G1-G12, 0-22m, L=22m, optimal offset=11m):
- Shot at -10m: offset = 10m, error = |10-11| = 1m  ✓ BEST
- Shot at -5m:  offset = 5m,  error = |5-11| = 6m
- Shot at -20m: offset = 20m, error = |20-11| = 9m
- Shot at +48m: offset = 48m, error = |48-11| = 37m  (far, reverse)
```

---

## 6. Output Organization

### 6.1 Directory Structure

```
output/
├── pass1_8ch/
│   ├── midpoint_07m/
│   │   ├── DC_shot_m02.csv
│   │   ├── DC_shot_m05.csv
│   │   └── DC_averaged.csv
│   ├── midpoint_09m/
│   └── ...
├── pass2_12ch/
│   └── ...
├── pass3_16ch/
│   └── ...
├── pass4_24ch/
│   └── ...
└── combined/
    ├── merged_DC_position_07m.csv
    ├── merged_DC_position_11m.csv
    └── ...
```

### 6.2 Metadata for Each DC

```json
{
  "midpoint_m": 23.0,
  "subarray_channels": 12,
  "subarray_length_m": 22.0,
  "investigation_depth_m": 11.0,
  "frequency_range_hz": [10, 80],
  "shot_file": "shot_m10.dat",
  "source_offset_m": 10.0,
  "channels_used": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
  "quality_score": 0.85
}
```

---

## 7. Implementation Parameters

### 7.1 Configurable Options

```python
config = {
    "passes": [
        {"n_channels": 8,  "slide": 1, "name": "shallow"},
        {"n_channels": 12, "slide": 1, "name": "medium"},
        {"n_channels": 16, "slide": 1, "name": "medium_deep"},
        {"n_channels": 24, "slide": 1, "name": "deep"}
    ],
    "offset_tolerance": 0.5,  # Select shots with offset within 50% of optimal
    "min_shots_per_dc": 2,    # Require at least 2 shots for averaging
    "merge_strategy": "weighted_average"  # or "best_quality", "all"
}
```

### 7.2 Automatic Pass Generation

```python
def generate_passes(n_total_channels, min_channels=6, step=4):
    """Generate pass configurations automatically."""
    passes = []
    n = min_channels
    while n <= n_total_channels:
        passes.append({
            "n_channels": n,
            "name": f"{n}ch",
            "depth_approx": (n - 1) * dx / 2
        })
        n += step
    return passes

# For 24-channel array:
# Generates: 6ch, 10ch, 14ch, 18ch, 22ch, 24ch (if step=4, min=6)
```

---

## 8. Advantages of Variable Channel Strategy

1. **Complete depth coverage** - From shallow to deep in one survey
2. **Optimal resolution at each depth** - Short arrays for shallow, long for deep
3. **Redundancy** - Multiple DCs at overlapping midpoints/depths
4. **Quality control** - Compare results from different configurations
5. **Maximum use of data** - Extract all possible information

---

## 9. Considerations and Limitations

### 9.1 Increased Data Volume

```
With 4 passes and 8 shots:
Total DCs = (17 + 13 + 9 + 1) × 8 = 320 DCs

This is manageable but requires:
- Good file organization
- Automated processing pipeline
- Summary/visualization tools
```

### 9.2 Interpretation Complexity

Different sub-array sizes give different:
- Frequency ranges
- Lateral resolution
- Depth sensitivity

User must understand which DC applies to which depth zone.

### 9.3 Not All Combinations Are Useful

Very short sub-arrays (e.g., 4 channels):
- Limited frequency range
- May not produce reliable dispersion curves
- Generally not recommended

---

## 10. Summary

The variable channel strategy allows multi-resolution analysis from a single dataset:

1. **Multiple passes** with different sub-array sizes
2. **Shallow passes** (short arrays) → High lateral resolution, limited depth
3. **Deep passes** (long arrays) → Maximum depth, fewer midpoints
4. **Combined results** → Complete characterization

This approach is not standard in commercial software and represents a significant enhancement for research-grade analysis.
