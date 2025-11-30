# Approach B: Roll-Along Survey with Moving Array

## Detailed Concept and Examples

---

## 1. Core Concept

**Scenario:** The geophone array is physically MOVED along the survey line between shot acquisitions. Each position provides a new set of data centered at a different location.

**Combined with Approach A:** At each array position, we can ALSO extract multiple sub-arrays, multiplying the number of dispersion curves.

**Result:** Dense coverage along the entire survey line, extending far beyond a single array footprint.

---

## 2. Physical Setup

### 2.1 Roll-Along Configuration

```
Survey Line: 0m ─────────────────────────────────────────────► 200m

Setup 1: Array at 0-46m
         Source at -10m
         ◄── Array Position 1 ──►
         
Setup 2: Array at 10-56m (rolled 10m forward)
         Source at 0m
              ◄── Array Position 2 ──►

Setup 3: Array at 20-66m (rolled another 10m)
         Source at 10m
                   ◄── Array Position 3 ──►

... continue until survey line is covered
```

### 2.2 Visual Representation

```
Position (m):  -10   0    10   20   30   40   50   60   70   80   90   100
               │    │    │    │    │    │    │    │    │    │    │    │
Setup 1:       S────[====ARRAY-1====]
                    G1              G24
                    Midpoint: 23m

Setup 2:            S────[====ARRAY-2====]
                         G1              G24
                         Midpoint: 33m

Setup 3:                 S────[====ARRAY-3====]
                              G1              G24
                              Midpoint: 43m

Setup 4:                      S────[====ARRAY-4====]
                                   G1              G24
                                   Midpoint: 53m
```

---

## 3. Processing Options

### 3.1 Option B1: Full Array at Each Position (Simple)

Process all 24 channels at each setup position:

```
Setup 1: Full array → 1 DC at midpoint 23m
Setup 2: Full array → 1 DC at midpoint 33m
Setup 3: Full array → 1 DC at midpoint 43m
Setup 4: Full array → 1 DC at midpoint 53m

Result: 4 DCs with 10m spacing, maximum depth penetration
```

### 3.2 Option B2: Sub-Arrays at Each Position (Combining A + B)

Extract sub-arrays at EACH setup position:

```
Setup 1 (array at 0-46m):
├── SA-01 (G1-G12)  → DC at midpoint 11m
├── SA-02 (G2-G13)  → DC at midpoint 13m
├── ...
└── SA-13 (G13-G24) → DC at midpoint 35m
    (13 DCs from Setup 1)

Setup 2 (array at 10-56m):
├── SA-01 (G1-G12)  → DC at midpoint 21m
├── SA-02 (G2-G13)  → DC at midpoint 23m
├── ...
└── SA-13 (G13-G24) → DC at midpoint 45m
    (13 DCs from Setup 2)

Setup 3 (array at 20-66m):
├── SA-01 (G1-G12)  → DC at midpoint 31m
├── SA-02 (G2-G13)  → DC at midpoint 33m
├── ...
└── SA-13 (G13-G24) → DC at midpoint 55m
    (13 DCs from Setup 3)

Result: 39 DCs (13 × 3), some with overlapping midpoints!
```

### 3.3 Overlapping Coverage with Sub-Arrays

When sub-arrays are extracted from adjacent setups, some midpoints may have multiple DCs:

```
Midpoint 23m:
- Setup 1, SA-07 (G7-G18)  → DC from array at 0-46m
- Setup 2, SA-02 (G2-G13)  → DC from array at 10-56m (OVERLAP!)

Midpoint 33m:
- Setup 1, SA-12 (G12-G23) → DC from array at 0-46m
- Setup 2, SA-07 (G7-G18)  → DC from array at 10-56m (OVERLAP!)
- Setup 3, SA-02 (G2-G13)  → DC from array at 20-66m (OVERLAP!)
```

**This redundancy is GOOD for quality control and averaging!**

---

## 4. Roll Increment Selection

### 4.1 Definition

**Roll increment** = Distance the array moves between setups

### 4.2 Trade-offs

```
Small roll increment (e.g., 2m = dx):
├── ✓ Maximum overlap between setups
├── ✓ High redundancy at each midpoint
├── ✗ Many setups required
├── ✗ Time-consuming acquisition

Large roll increment (e.g., 46m = full array length):
├── ✓ Fast survey
├── ✓ Maximum coverage per setup
├── ✗ No overlap (gaps if using full array only)
├── ✗ No redundancy

Moderate roll increment (e.g., 10-20m):
├── ✓ Balance of coverage and efficiency
├── ✓ Some overlap for quality control
└── Most common in practice
```

### 4.3 Typical Recommendations

```
Roll increment ≈ sub-array length / 2

For 12-channel sub-arrays (L=22m):
  Roll increment ≈ 11m → Midpoints spaced by dx (2m) with some overlap

For full 24-channel array (L=46m):
  Roll increment ≈ 23m → Midpoints spaced by 23m, some overlap
```

---

## 5. Extended Survey Example

### 5.1 Survey Configuration

```
Goal: Cover 200m survey line
Array: 24 channels, dx=2m, L=46m
Roll increment: 20m
Sub-array size: 12 channels (L_sub=22m)
```

### 5.2 Number of Setups

```
n_setups = (survey_length - array_length) / roll_increment + 1
n_setups = (200 - 46) / 20 + 1 = 8.7 → 9 setups
```

### 5.3 Coverage

```
Setup 1: Array 0-46m    → Sub-arrays cover midpoints 11-35m
Setup 2: Array 20-66m   → Sub-arrays cover midpoints 31-55m
Setup 3: Array 40-86m   → Sub-arrays cover midpoints 51-75m
Setup 4: Array 60-106m  → Sub-arrays cover midpoints 71-95m
Setup 5: Array 80-126m  → Sub-arrays cover midpoints 91-115m
Setup 6: Array 100-146m → Sub-arrays cover midpoints 111-135m
Setup 7: Array 120-166m → Sub-arrays cover midpoints 131-155m
Setup 8: Array 140-186m → Sub-arrays cover midpoints 151-175m
Setup 9: Array 160-206m → Sub-arrays cover midpoints 171-195m

Total: 9 setups × 13 sub-arrays = 117 DCs
Midpoint range: 11m to 195m (with overlapping coverage)
```

---

## 6. Multiple Source Offsets at Each Setup

### 6.1 Adding Source Redundancy

At each array position, multiple shots can be acquired:

```
Setup 1 (array at 0-46m):
├── Shot at -5m
├── Shot at -10m
├── Shot at -20m
├── Shot at +51m (reverse)
└── Shot at +56m (reverse)

Each shot × 13 sub-arrays = 65 DCs from Setup 1 alone!
```

### 6.2 Total DC Count

```
Total DCs = n_setups × n_shots_per_setup × n_subarrays

Example:
= 9 setups × 5 shots × 13 sub-arrays
= 585 dispersion curves!
```

---

## 7. Acquisition Strategies

### 7.1 Land Streamer (Fast Roll-Along)

```
Equipment: Geophones mounted on wheeled platform
Method: 
1. Acquire shot
2. Move entire streamer by roll increment
3. Acquire next shot
4. Repeat

Advantage: Fast
Disadvantage: May have lower coupling quality
```

### 7.2 Traditional Cable Array (High Quality)

```
Equipment: Individual planted geophones
Method:
1. Plant full array
2. Acquire all shots at this position
3. Move array (pick up rear, plant at front)
4. Repeat

Advantage: Better coupling, higher SNR
Disadvantage: Slow, labor-intensive
```

### 7.3 Extended Array (Efficient)

```
Method: 
1. Plant extended array (e.g., 48 or 72 channels)
2. Acquire shots at multiple positions along the array
3. Extract sub-arrays from each shot based on source position

This is essentially Approach A with a longer array!
```

---

## 8. Data Management

### 8.1 File Naming Convention

```
shot_setup001_offset_m10.dat   (Setup 1, source at -10m)
shot_setup001_offset_p51.dat   (Setup 1, source at +51m)
shot_setup002_offset_m10.dat   (Setup 2, source at -10m)
...
```

### 8.2 Geometry Metadata

```json
{
  "setup_id": 1,
  "array_start_position": 0.0,
  "array_end_position": 46.0,
  "n_channels": 24,
  "dx": 2.0,
  "shots": [
    {"file": "shot_setup001_offset_m10.dat", "source_position": -10.0},
    {"file": "shot_setup001_offset_p51.dat", "source_position": 51.0}
  ]
}
```

---

## 9. Advantages of Approach B

1. **Extended coverage** - Survey lines longer than array length
2. **Flexibility** - Can combine with sub-array extraction
3. **Redundancy** - Overlapping coverage at roll boundaries
4. **Scalability** - Cover any survey length

---

## 10. Limitations of Approach B

1. **Acquisition effort** - Requires moving equipment
2. **Time-consuming** - Each setup takes time
3. **Positioning accuracy** - Must track array positions carefully
4. **Equipment** - May need specialized hardware (land streamer)

---

## 11. When to Use Approach B

**Use Approach B when:**
- Survey line is longer than single array length
- You need continuous lateral coverage
- High-quality 2D cross-section is required
- Time and resources allow for multiple setups

**Skip Approach B when:**
- Survey area fits within single array deployment
- Quick assessment is sufficient
- Limited field time available

---

## 12. Summary

Approach B extends the survey coverage by physically moving the array along the line. Combined with Approach A (sub-array extraction), it provides dense dispersion curve coverage over extended distances. The roll increment controls the trade-off between efficiency and redundancy.

**Key formula:**
```
n_setups = (survey_length - array_length) / roll_increment + 1
Total DCs = n_setups × n_shots_per_setup × n_subarrays
```
