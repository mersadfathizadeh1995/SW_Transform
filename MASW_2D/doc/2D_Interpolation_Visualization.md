# 2D Interpolation and Cross-Section Visualization

## Building Pseudo-2D Vs Cross-Sections

---

## 1. Introduction

After inverting dispersion curves from multiple sub-arrays along a survey line, the next step is to combine the individual 1D Vs profiles into a pseudo-2D cross-section. This document covers interpolation methods and visualization techniques.

---

## 2. Data Organization

### 2.1 Input: Collection of 1D Vs Profiles

```python
# Each inverted profile contains:
profile = {
    'midpoint': 25.0,         # Position along line (m)
    'depths': [0, 2, 5, 10, 20],  # Layer boundaries (m)
    'Vs': [150, 200, 300, 450]    # Layer Vs values (m/s)
}

# Collection for 2D section
profiles = [
    {'midpoint': 0.0, 'depths': [...], 'Vs': [...]},
    {'midpoint': 2.0, 'depths': [...], 'Vs': [...]},
    {'midpoint': 4.0, 'depths': [...], 'Vs': [...]},
    # ... more profiles
]
```

### 2.2 Convert Layer Model to Depth Grid

```python
def layer_to_grid(depths, Vs, z_grid):
    """
    Convert layer model to values at discrete depth points.
    
    Parameters
    ----------
    depths : list
        Layer boundaries [0, z1, z2, ..., zn]
    Vs : list
        Layer velocities [Vs1, Vs2, ..., Vsn]
    z_grid : ndarray
        Depth grid points
    
    Returns
    -------
    Vs_grid : ndarray
        Vs values at grid depths
    """
    Vs_grid = np.zeros(len(z_grid))
    
    for i, z in enumerate(z_grid):
        # Find which layer contains this depth
        for layer_idx in range(len(Vs)):
            if layer_idx < len(depths) - 1:
                top = depths[layer_idx]
                bottom = depths[layer_idx + 1]
            else:
                top = depths[layer_idx] if layer_idx < len(depths) else depths[-1]
                bottom = np.inf  # Half-space
            
            if top <= z < bottom:
                Vs_grid[i] = Vs[layer_idx]
                break
        else:
            Vs_grid[i] = Vs[-1]  # Use deepest layer (half-space)
    
    return Vs_grid
```

---

## 3. 2D Interpolation Methods

### 3.1 Linear Interpolation

Simple and fast, but may show artificial discontinuities.

```python
from scipy.interpolate import griddata
import numpy as np

def interpolate_2d_linear(profiles, x_grid, z_grid):
    """
    Linear interpolation of Vs profiles to 2D grid.
    
    Parameters
    ----------
    profiles : list of dict
        Each with 'midpoint', 'depths', 'Vs'
    x_grid : ndarray
        Horizontal grid points (m)
    z_grid : ndarray
        Depth grid points (m)
    
    Returns
    -------
    Vs_2d : ndarray, shape (len(z_grid), len(x_grid))
        Interpolated Vs grid
    """
    
    # Build scattered points
    points = []
    values = []
    
    for prof in profiles:
        x = prof['midpoint']
        Vs_at_depths = layer_to_grid(prof['depths'], prof['Vs'], z_grid)
        
        for i, z in enumerate(z_grid):
            points.append([x, z])
            values.append(Vs_at_depths[i])
    
    points = np.array(points)
    values = np.array(values)
    
    # Create meshgrid
    X, Z = np.meshgrid(x_grid, z_grid)
    
    # Interpolate
    Vs_2d = griddata(points, values, (X, Z), method='linear')
    
    return Vs_2d
```

### 3.2 Natural Neighbor Interpolation

Smoother transitions, respects data distribution.

```python
def interpolate_2d_natural(profiles, x_grid, z_grid):
    """Natural neighbor interpolation."""
    
    # Same point collection as linear
    points = []
    values = []
    
    for prof in profiles:
        x = prof['midpoint']
        Vs_at_depths = layer_to_grid(prof['depths'], prof['Vs'], z_grid)
        
        for i, z in enumerate(z_grid):
            points.append([x, z])
            values.append(Vs_at_depths[i])
    
    points = np.array(points)
    values = np.array(values)
    
    X, Z = np.meshgrid(x_grid, z_grid)
    
    # Natural neighbor via cubic interpolation (approximation)
    Vs_2d = griddata(points, values, (X, Z), method='cubic')
    
    # Handle NaN at edges with nearest neighbor
    mask = np.isnan(Vs_2d)
    if np.any(mask):
        Vs_nearest = griddata(points, values, (X, Z), method='nearest')
        Vs_2d[mask] = Vs_nearest[mask]
    
    return Vs_2d
```

### 3.3 Kriging Interpolation

Geostatistical method that provides uncertainty estimates.

```python
from scipy.spatial.distance import cdist

def simple_kriging(profiles, x_grid, z_grid, range_param=20.0, sill=10000):
    """
    Simple Kriging interpolation.
    
    Uses exponential variogram model.
    
    Parameters
    ----------
    range_param : float
        Variogram range (distance at which correlation drops)
    sill : float
        Variogram sill (variance at large distances)
    """
    
    # Collect points and values
    points = []
    values = []
    
    for prof in profiles:
        x = prof['midpoint']
        Vs_at_depths = layer_to_grid(prof['depths'], prof['Vs'], z_grid)
        
        for i, z in enumerate(z_grid):
            points.append([x, z])
            values.append(Vs_at_depths[i])
    
    points = np.array(points)
    values = np.array(values)
    n_points = len(values)
    
    # Variogram model (exponential)
    def variogram(h):
        return sill * (1 - np.exp(-h / range_param))
    
    # Build covariance matrix
    distances = cdist(points, points)
    C = sill - variogram(distances)
    
    # Add regularization
    C += 1e-6 * np.eye(n_points)
    
    # Grid points
    X, Z = np.meshgrid(x_grid, z_grid)
    grid_points = np.column_stack([X.ravel(), Z.ravel()])
    
    # Solve kriging system
    C_inv = np.linalg.inv(C)
    
    Vs_flat = np.zeros(len(grid_points))
    
    for i, gp in enumerate(grid_points):
        dist_to_data = cdist([gp], points)[0]
        c0 = sill - variogram(dist_to_data)
        
        weights = C_inv @ c0
        Vs_flat[i] = np.dot(weights, values)
    
    Vs_2d = Vs_flat.reshape(X.shape)
    
    return Vs_2d
```

### 3.4 RBF (Radial Basis Function) Interpolation

```python
from scipy.interpolate import RBFInterpolator

def interpolate_2d_rbf(profiles, x_grid, z_grid, kernel='thin_plate_spline'):
    """
    RBF interpolation.
    
    Parameters
    ----------
    kernel : str
        RBF kernel type: 'thin_plate_spline', 'multiquadric', 'gaussian', etc.
    """
    
    points = []
    values = []
    
    for prof in profiles:
        x = prof['midpoint']
        Vs_at_depths = layer_to_grid(prof['depths'], prof['Vs'], z_grid)
        
        for i, z in enumerate(z_grid):
            points.append([x, z])
            values.append(Vs_at_depths[i])
    
    points = np.array(points)
    values = np.array(values)
    
    # Create interpolator
    rbf = RBFInterpolator(points, values, kernel=kernel, smoothing=0.0)
    
    # Evaluate on grid
    X, Z = np.meshgrid(x_grid, z_grid)
    grid_points = np.column_stack([X.ravel(), Z.ravel()])
    
    Vs_flat = rbf(grid_points)
    Vs_2d = Vs_flat.reshape(X.shape)
    
    return Vs_2d
```

---

## 4. Visualization

### 4.1 Basic Cross-Section Plot

```python
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.ticker import MultipleLocator

def plot_vs_cross_section(x_grid, z_grid, Vs_2d, 
                          profiles=None,
                          vmin=None, vmax=None,
                          cmap='jet_r',
                          title='Pseudo-2D Vs Cross-Section'):
    """
    Plot 2D Vs cross-section.
    
    Parameters
    ----------
    x_grid : ndarray
        Horizontal positions (m)
    z_grid : ndarray
        Depths (m)
    Vs_2d : ndarray
        Interpolated Vs grid
    profiles : list, optional
        Original profile data (for overlay)
    vmin, vmax : float
        Colorbar limits
    cmap : str
        Colormap name
    title : str
        Plot title
    """
    
    if vmin is None:
        vmin = np.nanmin(Vs_2d)
    if vmax is None:
        vmax = np.nanmax(Vs_2d)
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Plot filled contours
    X, Z = np.meshgrid(x_grid, z_grid)
    levels = np.linspace(vmin, vmax, 50)
    
    cf = ax.contourf(X, Z, Vs_2d, levels=levels, cmap=cmap, extend='both')
    
    # Add contour lines
    cs = ax.contour(X, Z, Vs_2d, levels=np.linspace(vmin, vmax, 10),
                    colors='k', linewidths=0.5, alpha=0.5)
    ax.clabel(cs, inline=True, fontsize=8, fmt='%.0f')
    
    # Overlay profile positions
    if profiles:
        for prof in profiles:
            ax.axvline(prof['midpoint'], color='white', linewidth=0.5, 
                      linestyle='--', alpha=0.5)
    
    # Formatting
    ax.set_xlabel('Distance along line (m)', fontsize=12)
    ax.set_ylabel('Depth (m)', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.invert_yaxis()  # Depth increases downward
    
    # Colorbar
    cbar = fig.colorbar(cf, ax=ax, label='Vs (m/s)', pad=0.02)
    
    # Grid
    ax.xaxis.set_major_locator(MultipleLocator(10))
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig, ax


def plot_vs_cross_section_advanced(x_grid, z_grid, Vs_2d, 
                                    profiles=None,
                                    surface_elevation=None,
                                    vs30_line=True):
    """
    Advanced cross-section with topography and Vs30 indicator.
    """
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    X, Z = np.meshgrid(x_grid, z_grid)
    
    # If surface elevation provided, convert depth to elevation
    if surface_elevation is not None:
        elev_interp = np.interp(x_grid, 
                                 surface_elevation['x'],
                                 surface_elevation['z'])
        Z_elev = elev_interp[np.newaxis, :] - Z
    else:
        Z_elev = -Z  # Just negative depth
    
    # Plot
    cf = ax.contourf(X, Z_elev, Vs_2d, 50, cmap='jet_r')
    
    # Vs30 reference line (30m depth)
    if vs30_line and surface_elevation is not None:
        z30 = elev_interp - 30
        ax.plot(x_grid, z30, 'w--', linewidth=2, label='30m depth')
    elif vs30_line:
        ax.axhline(-30, color='w', linestyle='--', linewidth=2, label='30m depth')
    
    # Surface line
    if surface_elevation is not None:
        ax.plot(x_grid, elev_interp, 'k-', linewidth=2)
        ax.fill_between(x_grid, elev_interp, elev_interp.max() + 10, 
                        color='lightgray', alpha=0.5)
        ax.set_ylabel('Elevation (m)', fontsize=12)
    else:
        ax.invert_yaxis()
        ax.set_ylabel('Depth (m)', fontsize=12)
    
    ax.set_xlabel('Distance (m)', fontsize=12)
    fig.colorbar(cf, ax=ax, label='Vs (m/s)')
    ax.legend()
    
    plt.tight_layout()
    return fig, ax
```

### 4.2 Side-by-Side 1D Profiles

```python
def plot_1d_profiles_sidebyside(profiles, spacing_factor=50):
    """
    Plot 1D Vs profiles side by side.
    
    Parameters
    ----------
    profiles : list of dict
    spacing_factor : float
        Scale factor for horizontal offset
    """
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Sort by midpoint
    profiles = sorted(profiles, key=lambda p: p['midpoint'])
    
    for prof in profiles:
        x_offset = prof['midpoint']
        
        # Build stair-step plot
        Vs = prof['Vs']
        depths = prof['depths']
        
        x_plot = []
        z_plot = []
        
        for i, vs in enumerate(Vs):
            z_top = depths[i] if i < len(depths) else depths[-1]
            z_bottom = depths[i+1] if i+1 < len(depths) else z_top + 10
            
            x_plot.extend([x_offset + vs/spacing_factor, x_offset + vs/spacing_factor])
            z_plot.extend([z_top, z_bottom])
        
        ax.plot(x_plot, z_plot, 'b-', linewidth=1)
    
    ax.set_xlabel('Distance (m) + scaled Vs', fontsize=12)
    ax.set_ylabel('Depth (m)', fontsize=12)
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig, ax
```

---

## 5. Export Formats

### 5.1 Save as NPZ

```python
def save_cross_section_npz(filepath, x_grid, z_grid, Vs_2d, metadata=None):
    """Save interpolated cross-section to NPZ file."""
    
    data = {
        'x_grid': x_grid,
        'z_grid': z_grid,
        'Vs_2d': Vs_2d
    }
    
    if metadata:
        for key, val in metadata.items():
            data[key] = val
    
    np.savez_compressed(filepath, **data)
```

### 5.2 Save as GeoTIFF (for GIS)

```python
def save_as_geotiff(filepath, x_grid, z_grid, Vs_2d, 
                    crs='EPSG:32632', transform_params=None):
    """Save as GeoTIFF for GIS applications."""
    
    try:
        import rasterio
        from rasterio.transform import from_bounds
    except ImportError:
        raise ImportError("rasterio required for GeoTIFF export")
    
    # Define transform
    if transform_params:
        transform = from_bounds(*transform_params)
    else:
        # Default: use x_grid as x-coordinates, z_grid as y-coordinates
        transform = from_bounds(
            x_grid[0], z_grid[-1],  # left, bottom
            x_grid[-1], z_grid[0],  # right, top
            len(x_grid), len(z_grid)
        )
    
    with rasterio.open(
        filepath, 'w',
        driver='GTiff',
        height=Vs_2d.shape[0],
        width=Vs_2d.shape[1],
        count=1,
        dtype=Vs_2d.dtype,
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(Vs_2d, 1)
```

### 5.3 Export to CSV

```python
def save_cross_section_csv(filepath, x_grid, z_grid, Vs_2d):
    """Save cross-section as CSV (long format)."""
    
    import csv
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['x_m', 'depth_m', 'Vs_m_s'])
        
        for i, z in enumerate(z_grid):
            for j, x in enumerate(x_grid):
                writer.writerow([x, z, Vs_2d[i, j]])
```

---

## 6. Complete Pipeline Example

```python
def build_2d_vs_section(profiles, output_dir, 
                        x_resolution=1.0,
                        z_max=30, z_resolution=0.5,
                        interp_method='rbf'):
    """
    Complete pipeline from profiles to cross-section.
    
    Parameters
    ----------
    profiles : list of dict
        Inverted Vs profiles with midpoints
    output_dir : str
        Output directory
    x_resolution : float
        Horizontal grid spacing (m)
    z_max : float
        Maximum depth (m)
    z_resolution : float
        Depth grid spacing (m)
    interp_method : str
        Interpolation method ('linear', 'cubic', 'rbf')
    
    Returns
    -------
    result : dict
        Contains grids and figures
    """
    import os
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Define grids
    x_min = min(p['midpoint'] for p in profiles)
    x_max = max(p['midpoint'] for p in profiles)
    x_grid = np.arange(x_min, x_max + x_resolution, x_resolution)
    z_grid = np.arange(0, z_max + z_resolution, z_resolution)
    
    # Interpolate
    if interp_method == 'linear':
        Vs_2d = interpolate_2d_linear(profiles, x_grid, z_grid)
    elif interp_method == 'cubic':
        Vs_2d = interpolate_2d_natural(profiles, x_grid, z_grid)
    elif interp_method == 'rbf':
        Vs_2d = interpolate_2d_rbf(profiles, x_grid, z_grid)
    else:
        raise ValueError(f"Unknown method: {interp_method}")
    
    # Save data
    save_cross_section_npz(
        os.path.join(output_dir, 'vs_2d_section.npz'),
        x_grid, z_grid, Vs_2d,
        metadata={'interp_method': interp_method}
    )
    
    # Create figure
    fig, ax = plot_vs_cross_section(
        x_grid, z_grid, Vs_2d, profiles=profiles
    )
    fig.savefig(os.path.join(output_dir, 'vs_2d_section.png'), dpi=200)
    plt.close(fig)
    
    return {
        'x_grid': x_grid,
        'z_grid': z_grid,
        'Vs_2d': Vs_2d,
        'figure_path': os.path.join(output_dir, 'vs_2d_section.png')
    }
```

---

## 7. References

1. DAS for 2D MASW Imaging (2022). ResearchGate.

2. Oliver, M.A., & Webster, R. (2014). "A tutorial guide to geostatistics." *Catena*, 113, 56-69.

3. Scipy Documentation - Interpolation routines.
