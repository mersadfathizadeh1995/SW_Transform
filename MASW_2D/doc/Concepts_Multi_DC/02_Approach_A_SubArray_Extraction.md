# Approach A: Sub-Array Extraction from Fixed Array

## Detailed Concept and Examples

---

## 1. Core Concept

**Scenario:** The geophone array is deployed at a FIXED location. Multiple shots are acquired at different source offsets. Instead of processing all channels together, we extract MULTIPLE sub-arrays from each shot record.

**Result:** Many dispersion curves at different midpoint positions, with redundancy from multiple source offsets.

---

## 2. Physical Setup

### 2.1 Standard MASW Example

```
Array Configuration:
- 24 geophones (G1 to G24)
- Spacing: dx = 2m
- Positions: 0, 2, 4, 6, ... 44, 46m
- Array length: L = 46m
- Array midpoint: 23m

Shot Locations (typical):
- Negative side: -2, -5, -10, -20, -30m
- Positive side: +48, +51, +56, +66m
- Mid-array (if available): +23m

Total: 9-10 shot records
```

### 2.2 Visual Representation

```
         Source offsets (negative)              Array                    Source offsets (positive)
              ↓     ↓    ↓   ↓  ↓               ↓                              ↓   ↓    ↓     ↓
             -30  -20  -10  -5 -2              0m                            +48 +51  +56   +66
              S    S    S   S  S    G1  G2  G3  ...  G22 G23 G24              S   S    S     S
              │    │    │   │  │    │   │   │        │   │   │               │   │    │     │
              ▼    ▼    ▼   ▼  ▼    0   2   4   ...  42  44  46              ▼   ▼    ▼     ▼
                                   ◄────────────────────────►
                                        Fixed Array
```

---

## 3. Sub-Array Extraction Process

### 3.1 Defining Sub-Arrays

From the 24-channel array, we can define overlapping sub-arrays of various sizes:

**Example: 12-channel sub-arrays (sliding by 1 channel)**

```
Sub-array ID  | Channels Used | Position Range | Midpoint
--------------|---------------|----------------|----------
SA-01         | G1 - G12      | 0 - 22m        | 11m
SA-02         | G2 - G13      | 2 - 24m        | 13m
SA-03         | G3 - G14      | 4 - 26m        | 15m
SA-04         | G4 - G15      | 6 - 28m        | 17m
SA-05         | G5 - G16      | 8 - 30m        | 19m
SA-06         | G6 - G17      | 10 - 32m       | 21m
SA-07         | G7 - G18      | 12 - 34m       | 23m
SA-08         | G8 - G19      | 14 - 36m       | 25m
SA-09         | G9 - G20      | 16 - 38m       | 27m
SA-10         | G10 - G21     | 18 - 40m       | 29m
SA-11         | G11 - G22     | 20 - 42m       | 31m
SA-12         | G12 - G23     | 22 - 44m       | 33m
SA-13         | G13 - G24     | 24 - 46m       | 35m

Total: 13 sub-arrays from 24 geophones (with 12-channel sub-arrays)
```

### 3.2 Formula for Number of Sub-Arrays

```
n_subarrays = n_total_channels - n_subarray_channels + 1

For 24 channels with 12-channel sub-arrays:
n_subarrays = 24 - 12 + 1 = 13
```

---

## 4. Multiple Source Offsets → Multiple Dispersion Curves Per Midpoint

### 4.1 The Key Point

**Each shot record can produce ALL 13 sub-arrays (for 12-channel extraction).**

If you have 9 source offsets, you get:
```
Total dispersion curves = 9 shots × 13 sub-arrays = 117 dispersion curves!
```

But they are distributed across only 13 unique midpoints, with 9 curves per midpoint.

### 4.2 Detailed Example

```
Shot at -2m offset:
├── SA-01 (G1-G12)  → DC at midpoint 11m  (source offset to SA: -2 - 0 = -2m)
├── SA-02 (G2-G13)  → DC at midpoint 13m  (source offset to SA: -2 - 2 = -4m)
├── SA-03 (G3-G14)  → DC at midpoint 15m  (source offset to SA: -2 - 4 = -6m)
├── ...
└── SA-13 (G13-G24) → DC at midpoint 35m  (source offset to SA: -2 - 24 = -26m)

Shot at -10m offset:
├── SA-01 (G1-G12)  → DC at midpoint 11m  (source offset to SA: -10m)
├── SA-02 (G2-G13)  → DC at midpoint 13m  (source offset to SA: -12m)
├── ...
└── SA-13 (G13-G24) → DC at midpoint 35m  (source offset to SA: -34m)

Shot at +48m offset:
├── SA-01 (G1-G12)  → DC at midpoint 11m  (source offset to SA: 48 - 0 = 48m, REVERSE)
├── SA-02 (G2-G13)  → DC at midpoint 13m  (source offset to SA: 48 - 2 = 46m, REVERSE)
├── ...
└── SA-13 (G13-G24) → DC at midpoint 35m  (source offset to SA: 48 - 24 = 24m, REVERSE)
```

### 4.3 Result Summary

```
Midpoint 11m:  9 dispersion curves (one from each shot)
Midpoint 13m:  9 dispersion curves
Midpoint 15m:  9 dispersion curves
...
Midpoint 35m:  9 dispersion curves

→ Can stack/average DCs at each midpoint for robust results
→ Or analyze each independently to detect lateral variations
```

---

## 5. Why Multiple Source Offsets Help

### 5.1 Benefits

1. **Redundancy** - Multiple DCs at same location allow quality control
2. **Near-field mitigation** - Some offsets may have near-field contamination; averaging reduces this
3. **Frequency content** - Different offsets may emphasize different frequency ranges
4. **Direction averaging** - Forward and reverse shots reduce directional bias

### 5.2 Source Offset Considerations

**For each sub-array, the effective source offset varies:**

```
Sub-array SA-01 (starts at G1, position 0m):
- Shot at -2m:  offset = |-2 - 0| = 2m   (very close, near-field risk)
- Shot at -10m: offset = |-10 - 0| = 10m (good)
- Shot at -30m: offset = |-30 - 0| = 30m (far-field, may be weak)
- Shot at +48m: offset = |48 - 0| = 48m  (reverse shot, far)

Sub-array SA-13 (starts at G13, position 24m):
- Shot at -2m:  offset = |-2 - 24| = 26m (good)
- Shot at -10m: offset = |-10 - 24| = 34m (far)
- Shot at +48m: offset = |48 - 24| = 24m (reverse, good)
```

**Recommendation:** For each sub-array, select shots with appropriate offsets (typically X₁ ≈ L/2 for the sub-array).

---

## 6. Investigation Depth

### 6.1 Depth vs. Sub-Array Length

The investigation depth depends on the sub-array length:

```
Sub-array length L → Investigation depth ≈ L/2 to L/3

12 channels, dx=2m → L = 22m → Depth ≈ 7-11m
16 channels, dx=2m → L = 30m → Depth ≈ 10-15m
20 channels, dx=2m → L = 38m → Depth ≈ 13-19m
24 channels, dx=2m → L = 46m → Depth ≈ 15-23m
```

### 6.2 Trade-Off Visualization

```
More channels in sub-array:
├── ✓ Greater investigation depth
├── ✓ Better low-frequency resolution
├── ✗ Fewer sub-arrays (fewer midpoints)
└── ✗ Lower lateral resolution

Fewer channels in sub-array:
├── ✓ More sub-arrays (more midpoints)
├── ✓ Higher lateral resolution
├── ✗ Shallower investigation depth
└── ✗ Poorer low-frequency resolution
```

---

## 7. Practical Implementation

### 7.1 Input Requirements

```
Required:
- Shot gather data (time × channels matrix)
- Sampling interval (dt)
- Geophone spacing (dx)
- Sub-array configuration (n_channels, slide_increment)

Optional:
- Source offset for quality filtering
- Reverse flag for shots on positive side
```

### 7.2 Processing Loop

```
For each shot_file in survey:
    Load shot gather
    
    For each sub-array definition:
        Extract channels [start_ch : start_ch + n_subarray]
        Calculate midpoint position
        Calculate effective source offset
        
        Apply preprocessing (time window, etc.)
        Apply transform (PS/FK/FDBF/SS)
        Pick dispersion curve
        
        Store DC with metadata:
            - midpoint position
            - source offset
            - shot file reference
            - sub-array channels used
```

### 7.3 Output Structure

```
output/
├── midpoint_11m/
│   ├── DC_shot_m02_SA01.csv    (shot at -2m, sub-array 01)
│   ├── DC_shot_m05_SA01.csv    (shot at -5m, sub-array 01)
│   ├── DC_shot_m10_SA01.csv    (shot at -10m, sub-array 01)
│   └── ...
├── midpoint_13m/
│   ├── DC_shot_m02_SA02.csv
│   └── ...
├── midpoint_15m/
│   └── ...
└── summary/
    ├── all_dispersion_curves.csv
    └── midpoint_summary.json
```

---

## 8. Special Cases

### 8.1 Mid-Array Shot (Source at position 23m)

If a shot exists at the array center (e.g., for P-wave refraction):

```
Source at 23m:
├── SA-01 (G1-G12, 0-22m):   Source is BEYOND the sub-array (offset = 23 - 22 = 1m, TOO CLOSE)
├── SA-07 (G7-G18, 12-34m):  Source is INSIDE the sub-array (not standard, but usable)
├── SA-13 (G13-G24, 24-46m): Source is BEFORE the sub-array (offset = 24 - 23 = 1m, TOO CLOSE)

Options:
1. Skip sub-arrays where source is inside or too close
2. Use special processing for interior source
3. Split into two half-arrays (G1-G12 and G13-G24) with source at end
```

### 8.2 P-Wave Refraction Data (48 channels, many shots)

```
Array: 48 geophones, dx = 2m, positions 0-94m
Shots: Multiple along and outside the array

Processing strategy:
1. For shots OUTSIDE array: Standard sub-array extraction
2. For shots INSIDE array: 
   - Split array at shot location
   - Process left sub-array (source on right)
   - Process right sub-array (source on left)
3. Combine all dispersion curves with midpoint positions
```

---

## 9. Advantages of Approach A

1. **Uses existing data** - No special acquisition required
2. **Multiple DCs per midpoint** - Redundancy from different source offsets
3. **Simple implementation** - Just channel selection and standard processing
4. **Flexible** - Can use any sub-array configuration
5. **Quality control** - Compare DCs from different shots at same midpoint

---

## 10. Limitations of Approach A

1. **Lateral extent limited** - Only covers the array footprint
2. **Edge effects** - Sub-arrays near edges have unbalanced source offsets
3. **Fixed array length** - Cannot extend beyond the deployed array
4. **Trade-off** - Must choose between depth and lateral resolution

---

## 11. Summary

Approach A extracts multiple sub-arrays from each shot record, generating many dispersion curves at different midpoints along the array. With multiple source offsets, each midpoint has multiple DCs for averaging or quality control.

**Key formula:**
```
Total DCs = n_shots × n_subarrays
Unique midpoints = n_subarrays = n_total_channels - n_subarray_channels + 1
DCs per midpoint = n_shots
```
