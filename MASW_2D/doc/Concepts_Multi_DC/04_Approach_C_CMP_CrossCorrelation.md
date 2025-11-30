# Approach C: CMP Cross-Correlation Method

## Detailed Concept and Examples

---

## 1. Core Concept

**Scenario:** Instead of using raw geophone traces directly, we compute cross-correlations between ALL pairs of geophones. These correlations are then sorted by their Common Mid-Point (CMP) and used to create "virtual gathers" that can be processed for dispersion curves.

**Key Insight:** Cross-correlation between two traces extracts the phase relationship, effectively creating a virtual source-receiver pair at the midpoint between the two geophones.

**Result:** Higher lateral resolution than sub-array extraction, with midpoints at half the geophone spacing (dx/2 instead of dx).

---

## 2. Why Cross-Correlation Works

### 2.1 Surface Wave Propagation

When a surface wave travels from source S past geophones G1 and G2:

```
Source S                G1              G2
   │                    │               │
   │    distance d1     │   distance d  │
   │◄──────────────────►│◄─────────────►│
   │                    │               │
   ▼                    ▼               ▼
Wave arrives         Wave arrives    Wave arrives
at t = 0             at t = t1       at t = t2

Time difference: Δt = t2 - t1 = d / c(f)
where c(f) is the phase velocity at frequency f
```

### 2.2 What Cross-Correlation Does

**Cross-correlation of G1 and G2 signals:**

```
R(τ) = ∫ G1(t) × G2(t + τ) dt
```

The correlation function R(τ) has a **peak at τ = Δt**, which corresponds to the travel time between G1 and G2.

**Key result:**
```
Phase velocity = distance / time = d / Δt
```

### 2.3 The "Virtual Source" Interpretation

Mathematically, cross-correlating G1 and G2 is equivalent to:
- Placing a **virtual source at the position of G1**
- Recording at **G2** (virtual receiver)
- The correlation function = seismogram for this virtual experiment

```
Original experiment:       Virtual experiment (from correlation):

    S → G1 → G2                 [G1] ─────→ [G2]
        ↓     ↓                 virtual     virtual
     record record              source      receiver
     
The correlation contains the same phase information!
```

---

## 3. Why Assign to Midpoint?

### 3.1 Sampling the Subsurface

The surface wave traveling from G1 to G2 **samples the subsurface between them**:

```
Surface:    G1 ◄────────────────────────► G2
            x1           sampled           x2
                        region
                           ↓
Subsurface:     ████████████████████████
                Properties in this zone
                affect the wave travel time
                
Representative location = midpoint = (x1 + x2) / 2
```

### 3.2 Not the Source Location

The original source position becomes irrelevant in the correlation. What matters is:
- The positions of the two geophones (x1, x2)
- The distance between them (d = x2 - x1)
- The midpoint: (x1 + x2) / 2

---

## 4. Complete Example: 6 Geophones

### 4.1 Setup

```
Array: 6 geophones, dx = 2m
Positions: G1=0m, G2=2m, G3=4m, G4=6m, G5=8m, G6=10m
Source: S at -5m
```

### 4.2 Step 1: Compute All Pairwise Correlations

```
Number of pairs = n(n-1)/2 = 6×5/2 = 15 correlations

Pair    | Positions  | Spacing | Midpoint
--------|------------|---------|----------
G1-G2   | 0m, 2m     | 2m      | 1m
G1-G3   | 0m, 4m     | 4m      | 2m
G1-G4   | 0m, 6m     | 6m      | 3m
G1-G5   | 0m, 8m     | 8m      | 4m
G1-G6   | 0m, 10m    | 10m     | 5m
G2-G3   | 2m, 4m     | 2m      | 3m
G2-G4   | 2m, 6m     | 4m      | 4m
G2-G5   | 2m, 8m     | 6m      | 5m
G2-G6   | 2m, 10m    | 8m      | 6m
G3-G4   | 4m, 6m     | 2m      | 5m
G3-G5   | 4m, 8m     | 4m      | 6m
G3-G6   | 4m, 10m    | 6m      | 7m
G4-G5   | 6m, 8m     | 2m      | 7m
G4-G6   | 6m, 10m    | 4m      | 8m
G5-G6   | 8m, 10m    | 2m      | 9m
```

### 4.3 Step 2: Group by Common Mid-Point (CMP)

```
Midpoint 1m: G1-G2 (spacing 2m)                    → 1 trace
Midpoint 2m: G1-G3 (spacing 4m)                    → 1 trace
Midpoint 3m: G1-G4 (6m), G2-G3 (2m)               → 2 traces
Midpoint 4m: G1-G5 (8m), G2-G4 (4m)               → 2 traces
Midpoint 5m: G1-G6 (10m), G2-G5 (6m), G3-G4 (2m) → 3 traces (RICHEST!)
Midpoint 6m: G2-G6 (8m), G3-G5 (4m)               → 2 traces
Midpoint 7m: G3-G6 (6m), G4-G5 (2m)               → 2 traces
Midpoint 8m: G4-G6 (4m)                            → 1 trace
Midpoint 9m: G5-G6 (2m)                            → 1 trace

Total: 9 unique midpoints (from 6 geophones!)
Midpoint spacing: 1m (= dx/2)
```

### 4.4 Step 3: Form CMP Gathers

Each midpoint now has a "virtual gather" with traces at different spacings:

```
CMP Gather at Midpoint 5m (center of array):
┌─────────────────────────────────────────────────┐
│  Spacing 2m:  Correlation G3-G4                 │
│  Spacing 6m:  Correlation G2-G5                 │
│  Spacing 10m: Correlation G1-G6                 │
│                                                 │
│  This looks like a shot gather with:            │
│  - Virtual source at 5m                         │
│  - Virtual receivers at 2m, 6m, 10m spacing     │
└─────────────────────────────────────────────────┘
```

### 4.5 Step 4: Apply Dispersion Transform

Apply phase-shift, FK, or other transform to each CMP gather:

```
CMP Gather at 5m → Transform → Dispersion Curve at position 5m
CMP Gather at 3m → Transform → Dispersion Curve at position 3m
CMP Gather at 7m → Transform → Dispersion Curve at position 7m
... etc.

Result: 9 dispersion curves from 6 geophones!
(Compare: Sub-array approach would give fewer curves)
```

---

## 5. Investigation Depth in CMP-CC

### 5.1 Depth Depends on Maximum Spacing

**The investigation depth at each midpoint is determined by the largest spacing available:**

```
Midpoint 5m (array center):
- Maximum spacing = 10m (G1-G6)
- Investigation depth ≈ 10m / 2 = ~5m

Midpoint 1m (near edge):
- Maximum spacing = 2m (G1-G2 only)
- Investigation depth ≈ 2m / 2 = ~1m

Midpoint 9m (near edge):
- Maximum spacing = 2m (G5-G6 only)
- Investigation depth ≈ 2m / 2 = ~1m
```

### 5.2 Depth Profile Across Array

```
Position (m):   0    1    2    3    4    5    6    7    8    9   10
                │    │    │    │    │    │    │    │    │    │    │
                G1             G2             G3             G4
                     ↓    ↓    ↓    ↓    ↓    ↓    ↓    ↓    ↓
Max depth (m):  -    1    2    3    4    5    4    3    2    1    -

Depth profile:       ╱╲
                    ╱  ╲
                   ╱    ╲
                  ╱      ╲
                 ╱        ╲
                ──         ──
               Edge       Edge
             (shallow)  (shallow)
               
              Center has maximum depth!
```

### 5.3 Comparison with Full Array

```
Full 6-geophone array:
- Length L = 10m
- Single DC at midpoint 5m
- Investigation depth ≈ 5m (everywhere)

CMP-CC from same array:
- 9 DCs at midpoints 1-9m
- Variable depth: max 5m at center, less at edges
- Higher lateral resolution
- Trade-off: edge positions are shallow
```

---

## 6. Mathematical Details

### 6.1 Cross-Correlation Formula

For time-series traces u(t) and v(t):

```
R_uv(τ) = ∫ u(t) × v(t + τ) dt

In discrete form:
R_uv[k] = Σ u[n] × v[n + k]
          n
```

### 6.2 Frequency Domain (Faster)

```
R_uv = IFFT( FFT(u)* × FFT(v) )

where * denotes complex conjugate
```

### 6.3 Normalization Options

```
1. Raw correlation: R_uv(τ) = ∫ u(t) × v(t + τ) dt

2. Normalized (0 to 1): R_norm = R_uv / (σ_u × σ_v × N)

3. Phase-only (coherency): R_phase = IFFT( exp(i × angle(FFT(u)* × FFT(v))) )
```

---

## 7. How Source Position Becomes Irrelevant

### 7.1 The Key Insight

When we correlate G1 and G2, we're essentially **removing the common path** from source to the closer geophone:

```
Original arrivals:
- G1 receives wave at time t1 = d(S,G1) / c
- G2 receives wave at time t2 = d(S,G2) / c

Correlation peak at:
τ = t2 - t1 = [d(S,G2) - d(S,G1)] / c

For inline geometry (S before G1 before G2):
τ = d(G1,G2) / c

The source distance cancels out!
```

### 7.2 Why This Works for Surface Waves

Surface waves have a dispersive relationship c(f). The correlation:
- Preserves this dispersion relationship
- Contains all frequency components
- Can be analyzed for c(f) just like a direct recording

---

## 8. Stacking for Signal Enhancement

### 8.1 Multiple Shots

If you have multiple shots, correlations from each shot can be stacked:

```
Shot 1: Correlate all pairs → 15 correlations
Shot 2: Correlate all pairs → 15 correlations
Shot 3: Correlate all pairs → 15 correlations

For each (midpoint, spacing) combination:
  Stack correlations from all shots
  → Enhanced SNR
```

### 8.2 Stacking Equal-Spacing Correlations

Within each midpoint, correlations with the same spacing can come from different shot positions (in roll-along) or symmetric pairs:

```
Stack traces with same (midpoint, spacing) → Better signal quality
```

---

## 9. Advantages of Approach C

1. **Higher lateral resolution** - Midpoints at dx/2 spacing
2. **More DCs from same data** - n(n-1)/2 correlations from n geophones
3. **Source-independent** - Works regardless of source position
4. **Noise suppression** - Correlation reduces incoherent noise
5. **No sub-array definition needed** - All pairs contribute

---

## 10. Limitations of Approach C

1. **Variable depth** - Shallower at array edges
2. **Fewer traces per gather** - CMP gathers have fewer traces than original
3. **Computational cost** - n² correlations to compute
4. **May not work well** - If data is very noisy or has strong body waves
5. **Complexity** - More difficult to implement and QC

---

## 11. When to Use Approach C

**Good candidates:**
- Dense arrays with many geophones
- Need for high lateral resolution
- Good quality data (high SNR)
- Research applications

**Poor candidates:**
- Sparse arrays (few geophones)
- Very noisy data
- Need for maximum depth everywhere
- Quick processing required

---

## 12. Practical Implementation Notes

### 12.1 Memory Considerations

```
24 geophones: 276 correlations
48 geophones: 1128 correlations
96 geophones: 4560 correlations

Each correlation has length 2N-1 where N = samples per trace
Memory = n_correlations × (2N-1) × 4 bytes (float32)
```

### 12.2 Computation Time

```
Correlation via FFT: O(N log N) per pair
Total: O(n² × N log N) for all pairs

For 24 geophones, 10000 samples:
≈ 276 × 10000 × 13 ≈ 36 million operations
→ < 1 second on modern hardware
```

### 12.3 Output Organization

```
For each midpoint:
├── List of contributing correlations
├── Spacing for each correlation
├── Stacked CMP gather
├── Dispersion spectrum
└── Picked dispersion curve

Metadata:
├── Midpoint position
├── Maximum spacing (→ max depth)
├── Number of traces in gather
└── Fold (stacking count)
```

---

## 13. Summary

CMP Cross-Correlation creates virtual source-receiver pairs at the midpoint between every geophone pair. This provides higher lateral resolution than sub-array extraction but with depth that varies across the array (maximum at center, minimum at edges).

**Key formulas:**
```
Number of correlations = n(n-1)/2
Number of unique midpoints = n - 1
Midpoint spacing = dx / 2
Max depth at midpoint m = (max spacing at m) / 2
```
