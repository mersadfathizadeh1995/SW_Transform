# Thomson-Haskell Matrix Method for Rayleigh Wave Dispersion

## Technical Reference Document

### 1. Introduction

The Thomson-Haskell matrix method (also known as the propagator matrix method or transfer matrix method) is the standard technique for computing theoretical Rayleigh wave dispersion curves in horizontally layered elastic media. This document provides the mathematical foundation needed for implementing surface wave inversion.

---

## 2. Problem Setup

### 2.1 Layered Earth Model

Consider an elastic half-space with N horizontal layers overlying a semi-infinite half-space:

```
Surface (z=0)
├── Layer 1: h₁, α₁, β₁, ρ₁
├── Layer 2: h₂, α₂, β₂, ρ₂
├── ...
├── Layer N: hₙ, αₙ, βₙ, ρₙ
└── Half-space: ∞, α_hs, β_hs, ρ_hs
```

**Parameters per layer:**
- h = thickness (m)
- α = P-wave velocity (m/s) or Vp
- β = S-wave velocity (m/s) or Vs
- ρ = density (kg/m³)

### 2.2 Wave Equation

Rayleigh waves are solutions to the elastic wave equation that decay exponentially with depth and satisfy stress-free boundary conditions at the surface.

**Plane wave assumption:**
```
u(x, z, t) = U(z) · exp(i(kx - ωt))
```

where:
- k = wavenumber (rad/m)
- ω = angular frequency = 2πf
- U(z) = depth-dependent amplitude

---

## 3. Layer Matrix Formulation

### 3.1 State Vector

Within each layer, the motion is described by a state vector:

```
y = [u, w, σ_zz, σ_xz]ᵀ
```

where:
- u = horizontal displacement
- w = vertical displacement  
- σ_zz = normal stress
- σ_xz = shear stress

### 3.2 Propagator Matrix

The state vector at the top of layer n relates to the state vector at the bottom through the propagator matrix:

```
y(z_top) = P_n · y(z_bottom)
```

### 3.3 Haskell Matrix Elements

For a layer with thickness h, the 4×4 propagator matrix P has elements:

```
r_α = sqrt(k² - ω²/α²)  [vertical P-wave slowness]
r_β = sqrt(k² - ω²/β²)  [vertical S-wave slowness]

C_α = cosh(r_α · h)     S_α = sinh(r_α · h)
C_β = cosh(r_β · h)     S_β = sinh(r_β · h)

μ = ρ · β²  [shear modulus]
γ = 2β²/c²  where c = ω/k [phase velocity]
```

**Matrix P (simplified notation):**

```python
P[0,0] = (2 - γ)·C_β - γ·(r_α·r_β)·C_α·S_β/(r_β·S_α)
P[0,1] = [complex expression involving sinh, cosh terms]
P[0,2] = [terms involving 1/μ]
P[0,3] = [terms involving 1/μ]
# ... (full matrix has 16 elements)
```

**Practical Implementation Note:** The explicit forms are lengthy. Most implementations use either:
1. Schwab & Knopoff (1972) formulation
2. Dunkin (1965) delta-matrix modification (for numerical stability)
3. Kennett (1983) reflection matrix approach

---

## 4. Boundary Conditions

### 4.1 Free Surface (z = 0)
```
σ_zz = 0
σ_xz = 0
```

### 4.2 Half-Space Condition (z → ∞)
Displacement decays exponentially (radiation condition):
```
u, w → 0 as z → ∞
```

This restricts the half-space solution to downgoing waves only.

### 4.3 Secular Equation

Combining boundary conditions through the total propagator matrix:

```
P_total = P_1 · P_2 · ... · P_N · P_hs
```

The secular equation is:

```
F(k, ω) = 0
```

where F is constructed from the boundary condition matrix. The roots k(ω) give the dispersion relation, and phase velocity is:

```
c(f) = ω/k = 2πf/k
```

---

## 5. Root Finding

### 5.1 Algorithm

For each frequency f:
1. Set ω = 2πf
2. Define velocity search range [c_min, c_max]
3. Convert to wavenumber: k = ω/c
4. Evaluate secular function F(k, ω) across k range
5. Find roots where F changes sign (bracket) then refine (bisection/Newton)

### 5.2 Mode Identification

- **Fundamental mode**: Lowest phase velocity root at each frequency
- **Higher modes**: Additional roots at higher velocities

### 5.3 Numerical Considerations

- **Overflow**: Large exponents in sinh/cosh; use delta-matrix or scaled formulations
- **Root crowding**: At high frequencies, modes become closely spaced
- **Starting values**: Use previous frequency's root as initial guess

---

## 6. Python Implementation Approach

### 6.1 Using `disba` Library

The `disba` library provides a fast implementation:

```python
from disba import PhaseDispersion

# Define model: thickness, Vp, Vs, density
thickness = [5, 10, 0]  # 0 = half-space
vp = [300, 600, 1000]
vs = [150, 300, 500]
density = [1800, 1900, 2000]

# Create dispersion object
pd = PhaseDispersion(*zip(thickness, vp, vs, density))

# Compute dispersion at frequencies
frequencies = np.linspace(5, 50, 100)
periods = 1.0 / frequencies

# Get fundamental mode (mode=0) Rayleigh wave (wave="rayleigh")
cpr = pd(periods, mode=0, wave="rayleigh")
phase_velocities = cpr.velocity
```

### 6.2 Using `pysurf96` (CPS wrapper)

```python
from pysurf96 import surf96

# Model arrays
h = np.array([5, 10, 0])
vp = np.array([300, 600, 1000])
vs = np.array([150, 300, 500])
rho = np.array([1800, 1900, 2000])

# Frequencies
freqs = np.linspace(5, 50, 100)
periods = 1.0 / freqs

# Compute
vel = surf96(h, vp, vs, rho, periods, wave='rayleigh', mode=0, velocity='phase')
```

### 6.3 Custom Implementation Skeleton

```python
import numpy as np
from scipy.optimize import brentq

def haskell_matrix(k, omega, h, vp, vs, rho):
    """Compute 4x4 layer propagator matrix."""
    c = omega / k  # phase velocity
    
    # Vertical slownesses
    if c < vp:
        r_alpha = np.sqrt(k**2 - (omega/vp)**2)
    else:
        r_alpha = 1j * np.sqrt((omega/vp)**2 - k**2)
    
    if c < vs:
        r_beta = np.sqrt(k**2 - (omega/vs)**2)
    else:
        r_beta = 1j * np.sqrt((omega/vs)**2 - k**2)
    
    # Build 4x4 matrix (Schwab & Knopoff formulation)
    # ... [detailed implementation]
    
    return P

def secular_function(k, omega, model):
    """Evaluate secular equation F(k,ω)."""
    # Total propagator
    P_total = np.eye(4)
    for layer in model.layers:
        P_layer = haskell_matrix(k, omega, layer.h, layer.vp, layer.vs, layer.rho)
        P_total = P_total @ P_layer
    
    # Apply boundary conditions
    # ... construct boundary matrix B from P_total and half-space
    
    return np.linalg.det(B)

def compute_dispersion(model, frequencies, mode=0):
    """Compute phase velocities for given frequencies."""
    velocities = []
    
    for f in frequencies:
        omega = 2 * np.pi * f
        
        # Search for roots
        c_min, c_max = 50, 5000  # velocity bounds
        k_min, k_max = omega/c_max, omega/c_min
        
        # Find all roots (modes)
        roots = find_all_roots(lambda k: secular_function(k, omega, model), 
                               k_min, k_max)
        
        # Sort by velocity (ascending)
        vels = sorted([omega/k for k in roots])
        
        if mode < len(vels):
            velocities.append(vels[mode])
        else:
            velocities.append(np.nan)
    
    return np.array(velocities)
```

---

## 7. Sensitivity Analysis

### 7.1 Jacobian Matrix

For inversion, we need partial derivatives:

```
J_ij = ∂c(f_i)/∂p_j
```

where p_j are model parameters (Vs, h for each layer).

### 7.2 Depth Sensitivity

- **Shallow layers**: Affect high frequencies
- **Deep layers**: Affect low frequencies
- **Approximate rule**: Sensitivity depth ≈ λ/3 to λ/2

---

## 8. References

1. Thomson, W.T. (1950). "Transmission of elastic waves through a stratified solid medium." *J. Appl. Phys.*, 21, 89-93.

2. Haskell, N.A. (1953). "The dispersion of surface waves on multilayered media." *Bull. Seism. Soc. Am.*, 43, 17-34.

3. Schwab, F., & Knopoff, L. (1972). "Fast surface wave and free mode computations." *Methods in Computational Physics*, 11, 87-180.

4. Dunkin, J.W. (1965). "Computation of modal solutions in layered, elastic media at high frequencies." *Bull. Seism. Soc. Am.*, 55, 335-358.

5. Kennett, B.L.N. (1983). *Seismic Wave Propagation in Stratified Media*. Cambridge University Press.

---

## 9. Recommended Libraries

| Library | Installation | Notes |
|---------|-------------|-------|
| `disba` | `pip install disba` | Fast, pure Python, recommended |
| `pysurf96` | `pip install pysurf96` | Wrapper for CPS surf96 |
| `evodcinv` | GitHub | Evolutionary DC inversion |
| `BayHunter` | GitHub | Bayesian inversion |
