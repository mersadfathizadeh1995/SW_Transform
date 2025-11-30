# 2D MASW Literature Review and Background Research

## 1. Introduction to 2D MASW

### 1.1 What is 2D MASW?

Two-dimensional Multichannel Analysis of Surface Waves (2D MASW) extends the traditional 1D MASW method to provide a lateral cross-section of shear-wave velocity (Vs) along a survey line. While 1D MASW produces a single Vs profile representing the average subsurface beneath the entire receiver array, 2D MASW generates multiple Vs profiles at different locations, which are then interpolated to create a pseudo-2D Vs cross-section.

**Key Distinction:**
- **1D MASW**: One dispersion curve → One Vs profile (single midpoint)
- **2D MASW**: Multiple dispersion curves → Multiple Vs profiles → Interpolated 2D section

### 1.2 Applications

- Near-surface site characterization for seismic hazard assessment
- Detection of lateral variations in soil/rock properties
- Mapping bedrock depth and geometry
- Cavity and void detection
- Foundation investigation
- Landslide assessment
- Levee and embankment evaluation

---

## 2. Key Techniques for 2D MASW

### 2.1 Roll-Along (or Walking) MASW

**Reference**: Park et al. (1999), Park & Miller (2008), masw.com/RollAlongACQ

**Principle**: The geophone array is moved incrementally along the survey line, collecting separate shot records at each position. Each record is processed independently to extract a dispersion curve, which is then inverted to obtain a 1D Vs profile associated with the array midpoint.

**Acquisition Strategies:**

#### A. Land Streamer Method
- All geophones mounted on a wheeled/sliding platform
- After each shot, the entire assembly moves by one receiver spacing (dx)
- Maintains constant source-to-first-receiver offset (X₁) and array length (L)
- Fast acquisition but potentially lower signal-to-noise (receivers not spiked)

#### B. Shoot-Through (Recompilation) Method
- Conventional fixed 24-48 channel array
- Multiple shots fired at different positions along the line
- Post-processing extracts sub-arrays with constant X₁ and L from each shot record
- Higher SNR but requires more processing

**Geometry Parameters (Park Seismic Guidelines):**
- Array length L ≈ 2 × investigation depth (Zmax)
- Source offset X₁ ≈ 0.5 × L
- Receiver spacing dx controls lateral resolution
- Spatial aliasing: λmin ≥ 2·dx

### 2.2 Common Mid-Point Cross-Correlation (CMP-CC)

**References**: Hayashi & Suzuki (2004), Wadi Fatima case study (SCIRP 2018)

**Principle**: Instead of processing each shot record independently, CMP-CC exploits trace-pair cross-correlations to improve lateral resolution and enhance signal-to-noise. The method groups traces sharing the same midpoint position.

**Workflow:**
1. **Cross-correlate all trace pairs** within each shot record
2. **Sort by common midpoint** - compute midpoint index for each pair: mid = (i + j) / 2
3. **Sort by equal spacing** - group correlations with identical receiver separations
4. **Stack equal-spacing correlations** within each midpoint group
5. **Form CMP-CC gathers** - the stacked traces for each midpoint create a virtual gather
6. **Apply MASW transform** (FK, PS, FDBF, SS) to each CMP-CC gather
7. **Extract dispersion curves** at higher lateral resolution

**Advantages:**
- Improved lateral resolution compared to roll-along
- Better signal-to-noise through stacking
- More dispersion curves from same field data

### 2.3 Spatial Autocorrelation (SPAC) Method

**References**: Aki (1957), Okada (2003)

**Principle**: Uses ambient noise correlations between station pairs to estimate phase velocities. While originally developed for microtremor arrays, it can complement active-source MASW.

**Not typically used for active-source 2D MASW but relevant for passive surveys.**

### 2.4 Multi-Offset Processing

**Principle**: Process shot gathers acquired at multiple source offsets from the same receiver array, then combine or average the dispersion images. This approach can improve spectral resolution and help identify higher modes.

---

## 3. Dispersion Curve Extraction Methods

These methods (already implemented in SW_Transform) are applied to each sub-array or CMP-CC gather:

### 3.1 Frequency-Wavenumber (F-K) Transform
- 2D FFT of time-space data
- Maps to frequency-wavenumber domain
- Phase velocity: V = 2πf/k

### 3.2 Phase-Shift Method (Park et al., 1998)
- Direct slant-stack in frequency domain
- Produces power as function of frequency and velocity
- Robust and widely used

### 3.3 Frequency-Domain Beamforming (FDBF)
- Cross-spectral matrix approach
- Allows amplitude weighting (vibrosis compensation)
- Good noise rejection

### 3.4 Slant-Stack (τ-p) Transform
- Time-domain stacking with velocity-dependent delays
- Followed by FFT to frequency domain
- Intuitive physical interpretation

---

## 4. Dispersion Curve Inversion

### 4.1 Forward Modeling: Thomson-Haskell Matrix Method

**References**: Thomson (1950), Haskell (1953), Schwab & Knopoff (1972)

**Theory**: The Thomson-Haskell propagator matrix method calculates the theoretical Rayleigh-wave dispersion relation for a horizontally layered elastic medium. For each layer n:

```
[stress_velocity]_top = P_n · [stress_velocity]_bottom
```

where P_n is a 4×4 propagator matrix depending on:
- Layer thickness (h_n)
- P-wave velocity (α_n) 
- S-wave velocity (β_n)
- Density (ρ_n)
- Frequency (f) and wavenumber (k)

The secular equation det(F(k, ω)) = 0 yields phase velocities for the fundamental and higher modes.

### 4.2 Inversion Algorithms

#### A. Genetic Algorithm (GA)
**References**: Dal Moro et al., Wadi Fatima study

**Workflow:**
1. Generate initial population of random Vs models
2. Compute forward dispersion curves (Thomson-Haskell)
3. Calculate misfit (RMS error between observed and theoretical)
4. Selection: keep models with lower misfit
5. Crossover: combine parameters from parent models
6. Mutation: random perturbations
7. Iterate until convergence

**Advantages:**
- Global optimization (avoids local minima)
- Handles nonlinear, non-unique inverse problem
- Can incorporate constraints

#### B. Monte Carlo Sampling
- Random sampling of parameter space
- Retains models within acceptable misfit threshold
- Provides uncertainty estimates

#### C. Gradient-Based (Linearized) Inversion
- Faster but requires good starting model
- May converge to local minimum
- Jacobian/sensitivity matrix computed

#### D. Neighborhood Algorithm (NA)
- Adaptive sampling of parameter space
- Efficient for high-dimensional problems

### 4.3 Parameterization Choices

- **Number of layers**: Typically 3-10
- **Parameters per layer**: Vs, thickness (h); sometimes Vp, density
- **Constraints**: Vs monotonically increasing with depth (common assumption)
- **Half-space**: Bottom layer typically treated as semi-infinite

---

## 5. Building Pseudo-2D Vs Cross-Sections

### 5.1 Workflow Summary

1. **Data Acquisition**: Roll-along or shoot-through geometry
2. **Sub-array Formation**: Extract sub-arrays with consistent X₁, L, dx
3. **Dispersion Analysis**: Apply FK/PS/FDBF/SS to each sub-array
4. **Pick Dispersion Curves**: Manual or automatic peak detection
5. **Inversion**: Convert each dispersion curve to 1D Vs profile
6. **Assign Midpoint**: Each Vs profile located at sub-array midpoint
7. **Interpolation**: Grid Vs values in distance-depth space
8. **Visualization**: Contour or color-fill cross-section

### 5.2 Interpolation Methods

**References**: DAS 2D MASW study (ResearchGate 2022)

- **Linear interpolation**: Simple, fast, may show discontinuities
- **Natural neighbor interpolation**: Smoother, respects data distribution
- **Kriging**: Geostatistical, provides uncertainty estimates
- **Scipy functions**: `griddata`, `interp2d`, `RBFInterpolator`

### 5.3 Resolution Considerations

- **Lateral resolution**: Controlled by sub-array spacing (typically = dx)
- **Depth resolution**: Limited by array length L
- **Trade-off**: Shorter sub-arrays → better lateral resolution but shallower penetration

---

## 6. Open-Source Software and Libraries

### 6.1 Existing Tools

| Tool | Language | Capabilities | License |
|------|----------|--------------|---------|
| MASWaves | MATLAB/Python | Dispersion + inversion | Academic |
| GeoInverse | Python | Surface wave inversion | Open |
| OpenSWPC | Fortran | 3D wave propagation | Open |
| Geopsy | C++ | Microtremor processing | Academic |
| pyrocko | Python | Seismology toolkit | LGPL |
| disba | Python | Rayleigh/Love dispersion | MIT |

### 6.2 Python Libraries for Implementation

- **NumPy/SciPy**: Numerical computation, FFT, optimization
- **disba**: Fast dispersion curve computation
- **pysurf96**: Python wrapper for surf96 (Herrmann)
- **pyswarm**: Particle swarm optimization
- **DEAP**: Evolutionary algorithms (GA)
- **matplotlib**: Plotting and visualization

---

## 7. Key References

### Foundational Papers

1. Park, C.B., Miller, R.D., & Xia, J. (1999). "Multichannel analysis of surface waves." *Geophysics*, 64(3), 800-808.

2. Xia, J., Miller, R.D., & Park, C.B. (1999). "Estimation of near-surface shear-wave velocity by inversion of Rayleigh waves." *Geophysics*, 64(3), 691-700.

3. Park, C.B., Miller, R.D., & Xia, J. (1998). "Imaging dispersion curves of surface waves on multi-channel record." *SEG Technical Program Expanded Abstracts*, 1377-1380.

### CMP Cross-Correlation

4. Hayashi, K., & Suzuki, H. (2004). "CMP cross-correlation analysis of multi-channel surface-wave data." *Exploration Geophysics*, 35(1), 7-13.

5. Wadi Fatima Case Study (2018). "MASW Survey with Fixed Receiver Geometry and CMP Cross-Correlation Technique." *SCIRP*.

### 2D MASW Implementation

6. Park, C.B., & Miller, R.D. (2008). "Roadside Passive Multi-Channel Analysis of Surface Waves (MASW)." *Journal of Environmental & Engineering Geophysics*, 13(1), 1-11.

7. DAS for 2D MASW Imaging (2022). "A Case Study on the Benefits of Flexible Sub-Array Processing." *ResearchGate*.

### Inversion Methods

8. Dal Moro, G., Pipan, M., & Gabrielli, P. (2007). "Rayleigh wave dispersion curve inversion via genetic algorithms and marginal posterior probability density estimation." *Journal of Applied Geophysics*, 61(1), 39-55.

9. Sambridge, M. (1999). "Geophysical inversion with a neighbourhood algorithm." *Geophysical Journal International*, 138(3), 479-494.

### Theory

10. Thomson, W.T. (1950). "Transmission of elastic waves through a stratified solid medium." *Journal of Applied Physics*, 21(2), 89-93.

11. Haskell, N.A. (1953). "The dispersion of surface waves on multilayered media." *Bulletin of the Seismological Society of America*, 43(1), 17-34.

---

## 8. Summary of Key Algorithms

### Algorithm 1: Roll-Along Sub-Array Extraction
```
Input: N shot records, each with M channels
Parameters: sub_length (e.g., 12), source_offset_channels (e.g., 6)
Output: List of sub-arrays with midpoint positions

For each shot s in shots:
    start_ch = calculate_start_channel(s, source_offset_channels)
    end_ch = start_ch + sub_length
    sub_array = shot[s].channels[start_ch:end_ch]
    midpoint = compute_midpoint_position(s, start_ch, end_ch, dx)
    yield (sub_array, midpoint)
```

### Algorithm 2: CMP Cross-Correlation
```
Input: Shot gather T[n_samples, n_channels], dx
Output: CMP-CC gathers for each midpoint

For i in range(n_channels):
    For j in range(i+1, n_channels):
        cc = correlate(T[:, i], T[:, j])
        midpoint = (i + j) / 2.0 * dx
        spacing = (j - i) * dx
        store cc with (midpoint, spacing)

For each unique midpoint:
    For each unique spacing at midpoint:
        stack all cc traces with same (midpoint, spacing)
    Form CMP-CC gather from stacked traces
```

### Algorithm 3: Thomson-Haskell Forward Model
```
Input: Layer model [h, Vp, Vs, rho], frequency f, wavenumber k
Output: Secular function value F(k, omega)

omega = 2 * pi * f
Initialize P = Identity(4x4)
For each layer n:
    Compute propagator matrix P_n(h_n, Vp_n, Vs_n, rho_n, omega, k)
    P = P @ P_n
Apply half-space boundary conditions
Return det(boundary_matrix)
```

### Algorithm 4: GA Inversion
```
Input: Observed dispersion curve (f, V), bounds [Vs_min, Vs_max], n_layers
Output: Best-fit Vs profile

Initialize population of random models
For generation in range(max_generations):
    For each model:
        Compute theoretical dispersion (Thomson-Haskell)
        Compute misfit = RMS(observed - theoretical)
    Selection: keep top 50% by fitness
    Crossover: create offspring by combining parents
    Mutation: randomly perturb some parameters
    Replace population with offspring
Return model with minimum misfit
```

---

## 9. Conclusions for SW_Transform Implementation

Based on this literature review, the following components are needed for 2D MASW:

1. **Sub-array management module** - Extract and manage overlapping sub-arrays from multi-shot datasets

2. **CMP-CC processing module** - Cross-correlation and stacking for enhanced lateral resolution

3. **Batch processing** - Process multiple sub-arrays/CMP gathers efficiently

4. **Dispersion curve inversion** - Thomson-Haskell forward model + GA/Monte-Carlo inversion

5. **2D interpolation and visualization** - Build and display pseudo-2D Vs cross-sections

6. **CLI and GUI integration** - Expose all functionality through existing interfaces
