# Multiple Dispersion Curve Extraction for 2D MASW

## Introduction and Core Concepts

---

## 1. The Goal: From 1D to 2D MASW

### 1.1 Traditional 1D MASW

In standard 1D MASW, we:
1. Deploy a linear array of geophones (e.g., 24 channels)
2. Hit at one or more source offsets
3. Process ALL channels together
4. Obtain ONE dispersion curve representing the array midpoint
5. Invert to get ONE Vs profile

**Limitation:** The result represents an average over the entire array length (~46m for 24 channels at 2m spacing). No lateral variation is captured.

### 1.2 The 2D MASW Objective

**Goal:** Obtain MULTIPLE dispersion curves at DIFFERENT positions along the survey line.

Each dispersion curve, when inverted, gives a 1D Vs profile at that position. Multiple profiles can then be interpolated to create a 2D Vs cross-section showing lateral variations.

### 1.3 Key Insight

**The location of a dispersion curve is determined by which geophones are used in the analysis, NOT by where the source is located.**

The source location affects:
- Signal quality (near-field/far-field effects)
- Wave propagation direction
- Data redundancy for stacking

But the dispersion curve location = **midpoint of the selected geophone sub-array**.

---

## 2. Three Approaches Overview

We define three approaches for obtaining multiple dispersion curves:

| Approach | Array Movement | Source Movement | Complexity | Our Priority |
|----------|---------------|-----------------|------------|--------------|
| **A: Sub-Array Extraction** | Fixed | Multiple offsets | Simple | First |
| **B: Roll-Along Survey** | Moving | Moving with array | Moderate | Second |
| **C: CMP Cross-Correlation** | Fixed | Single or multiple | Complex | Advanced |

### Key Innovation in Our Implementation

**Variable sub-array lengths** - Unlike standard commercial software that uses fixed channel counts, we will support:
- Multiple sub-array sizes from the same data
- Shallow analysis with short sub-arrays (high lateral resolution)
- Deep analysis with long sub-arrays (fewer points but greater depth)
- Combining results for comprehensive subsurface characterization

---

## 3. Terminology

| Term | Definition |
|------|------------|
| **Sub-array** | A subset of channels selected from the full array |
| **Midpoint** | Center position of a sub-array; where the dispersion curve is assigned |
| **Source offset (X₁)** | Distance from source to first geophone of the sub-array |
| **Array length (L)** | Total length of the sub-array: L = (n_channels - 1) × dx |
| **Roll increment** | Distance the array moves between survey positions |
| **CMP** | Common Mid-Point - location shared by multiple trace pairs |
| **Dispersion curve (DC)** | Phase velocity vs. frequency relationship |
| **Investigation depth** | Maximum depth that can be resolved; approximately L/2 to L/3 |

---

## 4. Data Types We Can Process

### 4.1 Standard MASW Survey Data

```
Array: 24 geophones, dx = 2m
Shots: Multiple offsets (-2, -5, -10, -20, -30, +48, +51, +56, +66 m)
Purpose: Originally for 1D MASW with redundancy
```

**Can be used for:** Approach A (sub-arrays from each shot)

### 4.2 Roll-Along MASW Survey Data

```
Multiple setups with array at different positions
Each setup: Full array + shots at consistent offset
Purpose: Designed for 2D MASW
```

**Can be used for:** Approach A + B combined

### 4.3 P-Wave Refraction Survey Data

```
Array: Often 48 geophones
Shots: Many positions along and outside the array
Purpose: Originally for refraction analysis
```

**Can be used for:** Approach A with flexible configuration
- Shots outside array → Standard sub-array extraction
- Shots inside array → Special handling (split sub-arrays)
- 48 channels → More sub-array options

### 4.4 Mixed Survey Data

```
Combination of above
Example: Standard MASW shots + mid-array shot + extended offsets
```

**Can be used for:** Flexible configuration supporting all scenarios

---

## 5. What Makes Our Approach Different

### 5.1 Commercial Software Limitations

Standard tools (SurfSeis, ParkSEIS) typically:
- Require uniform sub-array length
- Process all shots with same geometry
- Don't support variable channel counts
- Limited flexibility for non-standard acquisitions

### 5.2 Our Flexible Approach

We will implement:

1. **Variable sub-array sizes** - User-defined or automatic
2. **Multiple passes** - Different sizes for different depth targets
3. **Configurable source handling** - Support any shot geometry
4. **P-wave refraction compatibility** - Use existing refraction data
5. **Mid-array shot support** - Extract usable sub-arrays even from interior shots

---

## 6. Document Organization

This concept documentation is organized as follows:

| Document | Content |
|----------|---------|
| `01_Introduction_Multi_DC_Extraction.md` | This file - overview and terminology |
| `02_Approach_A_SubArray_Extraction.md` | Fixed array, multiple shots, sub-array extraction |
| `03_Approach_B_RollAlong_Survey.md` | Moving array acquisition and processing |
| `04_Approach_C_CMP_CrossCorrelation.md` | Advanced correlation-based method |
| `05_Variable_Channel_Strategy.md` | Multi-resolution analysis with different sub-array sizes |
| `06_Flexible_Configuration_Design.md` | Handling various survey types including P-wave refraction |

---

## 7. Next Steps

After understanding these concepts, the implementation will provide:

1. **CLI commands** for each approach
2. **Configurable parameters** for sub-array definition
3. **Batch processing** of multiple shots and sub-arrays
4. **Output management** with midpoint metadata
5. **Integration** with existing dispersion curve refinement and inversion workflows
