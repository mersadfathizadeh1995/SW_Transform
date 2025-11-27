# Power Spectrum Export Feature

**Version**: 1.0
**Date**: November 10, 2025
**Format**: NumPy .npz (compressed binary)

---

## Overview

This feature exports the **full 2D power spectrum data** that creates the dispersion curve heatmaps. Instead of just saving the picked dispersion curve (frequency, velocity points), you also get the entire frequency-velocity power distribution.

**Simple Analogy**:
- Current output: The "line" drawn on top of a topographic map
- New output: The entire topographic map itself (elevation at every point)

---

## What Data is Exported?

### For Each Method and Each File

The exported `.npz` file contains:

#### **FK (Frequency-Wavenumber) Method**
```python
{
    'frequencies': 1D array [0, 1, 2, ..., 100] Hz
    'velocities': 1D array [0, 12.5, 25, ..., 5000] m/s
    'power': 2D array (nvel × nfreq) - normalized power values
    'picked_velocities': 1D array - the dispersion curve
    'method': 'fk'
    'offset': '+66m'
    'vibrosis_mode': False
}
```

#### **FDBF (Frequency-Domain Beamformer) Method**
```python
{
    'frequencies': 1D array - frequency points (may be non-uniform)
    'velocities': 1D array - velocity grid
    'power': 2D array - beamformer power spectrum
    'picked_velocities': 1D array - dispersion curve
    'method': 'fdbf'
    'offset': '+66m'
    'vibrosis_mode': True  # if vibrosis compensation was applied
}
```

#### **PS (Phase-Shift) Method**
```python
{
    'frequencies': 1D array
    'velocities': 1D array (usually log-spaced)
    'power': 2D array - phase-shift power
    'picked_velocities': 1D array
    'method': 'ps'
    'offset': '+66m'
    'vspace': 'log'  # velocity spacing type
}
```

#### **SS (Slant-Stack / τ-p) Method**
```python
{
    'frequencies': 1D array
    'velocities': 1D array
    'power': 2D array - slant-stack power
    'picked_velocities': 1D array
    'method': 'ss'
    'offset': '+66m'
}
```

---

## File Organization

### Naming Convention
```
output/
  shot01_fk.png              # Existing: plot
  shot01_fk.csv              # Existing: picked curve
  shot01_fk_spectrum.npz     # NEW: full power data

  shot01_fdbf.png
  shot01_fdbf.csv
  shot01_fdbf_spectrum.npz

  shot02_fk.png
  shot02_fk.csv
  shot02_fk_spectrum.npz
  ...
```

### File Sizes (Typical)
- FK spectrum: ~80-150 KB (compressed)
- FDBF spectrum: ~50-100 KB (subsampled frequencies)
- PS spectrum: ~100-200 KB (finer velocity grid)
- SS spectrum: ~100-200 KB

**Total overhead**: ~0.3-0.6 MB per file (all 4 methods)

---

## What Can You Do With This Data?

### 1. **Custom Dispersion Curve Picking**

**Problem**: The automatic peak-picking algorithm might not be optimal for your data.

**Solution**: Load the spectrum and apply your own algorithm.

**Examples**:
- **Manual picking**: Interactively click on peaks in Python/MATLAB
- **Threshold-based**: Pick only peaks above certain power threshold
- **Gradient-based**: Use 2D gradient to find steepest ascent
- **Weighted picking**: Weight by frequency content or SNR
- **Multi-mode**: Extract fundamental + higher modes simultaneously

**Python Example Workflow**:
```python
import numpy as np
import matplotlib.pyplot as plt

# Load spectrum
data = np.load('shot01_fk_spectrum.npz')
freq = data['frequencies']
vel = data['velocities']
power = data['power']

# Visualize with different threshold
plt.figure(figsize=(10, 6))
plt.contourf(freq, vel, power, levels=50, cmap='viridis')
plt.colorbar(label='Normalized Power')

# Apply custom picking
# Method 1: Pick maximum in each frequency bin
picked = []
for i in range(len(freq)):
    max_idx = np.argmax(power[:, i])
    picked.append(vel[max_idx])

# Method 2: Pick only where power > 0.8
threshold = 0.8
picked_high_confidence = []
for i in range(len(freq)):
    col = power[:, i]
    if np.max(col) > threshold:
        max_idx = np.argmax(col)
        picked_high_confidence.append((freq[i], vel[max_idx]))
```

---

### 2. **Higher Mode Detection and Extraction**

**What are modes?**
Surface wave dispersion can have multiple "modes":
- **Fundamental mode**: Dominant, lowest-velocity mode
- **Higher modes**: Additional energy bands at higher velocities
- Each mode represents different depth sensitivity

**Why detect higher modes?**
- Better constraint on shear wave velocity profile
- Improved inversion results (less ambiguity)
- Deeper investigation depth
- More complete site characterization

**Visual Example**:
```
Velocity
  ^
  |        ┌─── Higher mode (2nd)
5000|       /
  |      /
  |     /  ┌─── Fundamental mode (automatic pick)
2000|   /  /
  |  /  /
  | /  /
  └──────────> Frequency
```

**How to Extract Multiple Modes**:

**Method A: Peak Detection Algorithm**
```python
from scipy.signal import find_peaks

# For each frequency bin
modes = {0: [], 1: [], 2: []}  # fundamental, 1st higher, 2nd higher

for i, f in enumerate(freq):
    spectrum_slice = power[:, i]

    # Find all peaks above threshold
    peaks, properties = find_peaks(
        spectrum_slice,
        height=0.3,      # minimum peak height
        prominence=0.1,  # peak must stand out
        distance=20      # minimum separation between peaks
    )

    # Sort by power (highest first)
    sorted_peaks = peaks[np.argsort(properties['peak_heights'])[::-1]]

    # Assign to modes
    for mode_idx, peak_idx in enumerate(sorted_peaks[:3]):
        modes[mode_idx].append((f, vel[peak_idx]))
```

**Method B: Manual Interactive Picking**
```python
# Create interactive plot
fig, ax = plt.subplots(figsize=(12, 8))
ax.contourf(freq, vel, power, levels=50, cmap='jet')

# Store picks
fundamental = []
higher_mode = []

def onclick(event):
    if event.key == 'f':  # 'f' for fundamental
        fundamental.append((event.xdata, event.ydata))
    elif event.key == 'h':  # 'h' for higher mode
        higher_mode.append((event.xdata, event.ydata))
    # Redraw picks
    ax.plot(*zip(*fundamental), 'wo-', label='Fundamental')
    ax.plot(*zip(*higher_mode), 'rx-', label='Higher mode')
    fig.canvas.draw()

fig.canvas.mpl_connect('button_press_event', onclick)
plt.show()
```

**Figures You Can Create**:
- **Multi-mode dispersion curves**: Different colors for each mode
- **Mode separation plots**: Velocity difference between modes vs frequency
- **Effective depth plots**: Each mode's depth sensitivity
- **3D visualization**: Frequency × Velocity × Power surface plot

---

### 3. **Quality Control (QC) and Reliability Assessment**

#### **QC Use Case: "Are my dispersion picks reliable?"**

**Problem**: Automatic picks might be on noise, not signal. How do you verify?

**Solution**: Inspect the power spectrum characteristics.

#### **Metrics to Check**:

##### **A. Peak Sharpness (SNR proxy)**
```python
# Calculate peak sharpness at each frequency
sharpness = []
for i in range(len(freq)):
    col = power[:, i]
    peak_val = np.max(col)
    median_val = np.median(col)
    sharpness.append(peak_val / median_val)

# Plot sharpness vs frequency
plt.figure()
plt.plot(freq, sharpness)
plt.axhline(y=3.0, color='r', linestyle='--', label='Threshold')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Peak Sharpness Ratio')
plt.title('Dispersion Curve Quality Metric')
plt.legend()
```

**Interpretation**:
- Sharpness > 3.0: **Good** quality pick (clear peak)
- Sharpness 1.5-3.0: **Moderate** quality (acceptable)
- Sharpness < 1.5: **Poor** quality (noisy, unreliable)

##### **B. Peak Width (Uncertainty Estimate)**
```python
# Calculate velocity uncertainty from peak width
uncertainties = []
for i in range(len(freq)):
    col = power[:, i]
    peak_idx = np.argmax(col)
    peak_val = col[peak_idx]

    # Find half-maximum points
    half_max = peak_val / 2
    left_idx = np.where(col[:peak_idx] < half_max)[0]
    right_idx = np.where(col[peak_idx:] < half_max)[0]

    if len(left_idx) > 0 and len(right_idx) > 0:
        width = vel[peak_idx + right_idx[0]] - vel[left_idx[-1]]
        uncertainties.append(width)
    else:
        uncertainties.append(np.nan)

# Plot with error bars
plt.errorbar(freq, picked_vel, yerr=uncertainties,
             fmt='o', capsize=3, label='Picked ± uncertainty')
```

**Figures You Can Create**:
- **QC dashboard**: 2×2 grid showing spectrum, picks, sharpness, uncertainty
- **Confidence bands**: Dispersion curve with shaded uncertainty region
- **Frequency-dependent reliability**: Color-code picks by quality

##### **C. Multi-Mode Interference Check**
```python
# Check if multiple modes are interfering
for i in range(len(freq)):
    col = power[:, i]
    peaks, _ = find_peaks(col, height=0.5 * np.max(col))

    if len(peaks) > 1:
        print(f"Warning: {len(peaks)} modes at {freq[i]} Hz")
        print(f"  Velocities: {vel[peaks]} m/s")
```

---

### 4. **Publication-Quality Figure Generation**

#### **Publication Use Case: "Journal requires specific formatting"**

**Problem**: You've already run the analysis, but now the journal wants:
- Different colormap (not 'jet')
- Larger fonts
- Vector graphics (PDF/SVG, not PNG)
- Specific axis limits
- Custom annotations

**Solution**: Re-plot from saved spectrum data without re-processing.

#### **Example Workflows**:

##### **A. Change Colormap to Publication Standard**
```python
# Journal prefers perceptually uniform colormaps
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm

data = np.load('shot01_fk_spectrum.npz')
freq = data['frequencies']
vel = data['velocities']
power = data['power']
picked = data['picked_velocities']

fig, ax = plt.subplots(figsize=(6, 4), dpi=300)

# Use viridis (colorblind-friendly) instead of jet
cf = ax.contourf(freq, vel, power, levels=30,
                 cmap='viridis',  # or 'plasma', 'inferno', 'cividis'
                 norm=PowerNorm(gamma=0.5))  # enhance low-power features

# Add colorbar with proper label
cbar = plt.colorbar(cf, ax=ax)
cbar.set_label('Normalized Power', fontsize=12)

# Plot picks with better visibility
ax.plot(freq, picked, 'w-', linewidth=2, label='Dispersion curve')
ax.plot(freq, picked, 'k--', linewidth=1)

# Publication formatting
ax.set_xlabel('Frequency (Hz)', fontsize=14)
ax.set_ylabel('Phase Velocity (m/s)', fontsize=14)
ax.set_title('FK Dispersion Analysis\nSite: ABC, Offset: +66m', fontsize=14)
ax.tick_params(labelsize=12)
ax.grid(alpha=0.3, linestyle=':')
ax.legend(fontsize=11, loc='upper left')

# Save as vector PDF for publication
plt.tight_layout()
plt.savefig('figure_01_dispersion.pdf', dpi=300, bbox_inches='tight')
```

##### **B. Create Multi-Panel Comparison Figure**
```python
# Compare 4 offsets side-by-side
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

offsets = ['+66m', '+56m', '-5m', '-20m']
files = ['shot01_fk_spectrum.npz', 'shot02_fk_spectrum.npz',
         'shot03_fk_spectrum.npz', 'shot04_fk_spectrum.npz']

for ax, offset, file in zip(axes.flat, offsets, files):
    data = np.load(file)
    ax.contourf(data['frequencies'], data['velocities'],
                data['power'], levels=30, cmap='viridis')
    ax.plot(data['frequencies'], data['picked_velocities'],
            'w-', linewidth=2)
    ax.set_title(f'Offset: {offset}', fontsize=14)
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Phase Velocity (m/s)')

plt.tight_layout()
plt.savefig('figure_02_offset_comparison.pdf')
```

##### **C. Add Custom Annotations**
```python
# Highlight specific features for discussion
data = np.load('shot01_fk_spectrum.npz')

fig, ax = plt.subplots(figsize=(10, 6))
ax.contourf(data['frequencies'], data['velocities'],
            data['power'], levels=50, cmap='gray_r')
ax.plot(data['frequencies'], data['picked_velocities'], 'r-', linewidth=2)

# Annotate interesting features
ax.annotate('Higher mode?',
            xy=(25, 2500), xytext=(35, 3500),
            arrowprops=dict(arrowstyle='->', color='blue', lw=2),
            fontsize=12, color='blue')

ax.annotate('Low SNR region',
            xy=(80, 1000), xytext=(70, 500),
            arrowprops=dict(arrowstyle='->', color='red', lw=2),
            fontsize=12, color='red')

# Add velocity bounds from previous studies
ax.axhline(y=300, color='green', linestyle='--', alpha=0.7,
           label='Vs30 = 300 m/s (boundary)')
ax.legend()

plt.savefig('figure_03_annotated.pdf')
```

##### **D. Custom Color Scaling**
```python
# Emphasize low-power features (useful for weak higher modes)
from matplotlib.colors import LogNorm, PowerNorm

# Power normalization (gamma < 1 enhances weak features)
norm = PowerNorm(gamma=0.3)

# Or logarithmic scaling
# norm = LogNorm(vmin=0.01, vmax=1.0)

ax.contourf(freq, vel, power, levels=50,
            cmap='hot', norm=norm)
```

---

### 5. **Machine Learning and AI Applications**

#### **Why Use Spectrum Data for ML?**

Traditional approach:
- Input: Time-domain traces (1D per channel)
- Output: Dispersion curve

ML approach with spectra:
- Input: 2D power spectrum (frequency-velocity image)
- Output: Dispersion curve, mode labels, quality scores

**Advantages**:
- 2D patterns easier for neural networks to learn
- Transfer learning from computer vision models
- Can learn from noisy/poor quality data
- Multi-task learning (picks + quality + modes)

---

#### **A. Supervised Learning: Auto-Picking**

**Training Dataset Creation**:
```python
# Create training dataset from manually picked examples
import numpy as np

X_train = []  # Spectra (input)
y_train = []  # Manual picks (target)

# Load 100 files with manual picks
for i in range(100):
    data = np.load(f'training/shot{i:03d}_fk_spectrum.npz')
    spectrum = data['power']  # 2D array
    manual_picks = load_manual_picks(f'training/shot{i:03d}_manual.csv')

    X_train.append(spectrum)
    y_train.append(manual_picks)

X_train = np.array(X_train)  # Shape: (100, nvel, nfreq)
y_train = np.array(y_train)  # Shape: (100, nfreq)
```

**Model Architecture Options**:

**Option 1: Convolutional Neural Network (CNN)**
```python
import tensorflow as tf
from tensorflow.keras import layers

model = tf.keras.Sequential([
    # Treat spectrum as 2D image
    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(nvel, nfreq, 1)),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.Flatten(),
    layers.Dense(128, activation='relu'),
    layers.Dense(nfreq, activation='linear')  # Output: velocity at each freq
])

model.compile(optimizer='adam', loss='mse')
model.fit(X_train, y_train, epochs=50, batch_size=16)
```

**Option 2: U-Net for Segmentation**
```python
# Segment the spectrum into "dispersion region" vs "noise"
# Output: Binary mask highlighting the dispersion curve

# U-Net architecture
def unet_model(input_shape):
    inputs = layers.Input(shape=input_shape)

    # Encoder
    c1 = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(inputs)
    p1 = layers.MaxPooling2D((2, 2))(c1)

    c2 = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(p1)
    p2 = layers.MaxPooling2D((2, 2))(c2)

    # Bottleneck
    c3 = layers.Conv2D(256, (3, 3), activation='relu', padding='same')(p2)

    # Decoder
    u4 = layers.UpSampling2D((2, 2))(c3)
    c4 = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(u4)

    u5 = layers.UpSampling2D((2, 2))(c4)
    c5 = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(u5)

    # Output: probability map
    outputs = layers.Conv2D(1, (1, 1), activation='sigmoid')(c5)

    return tf.keras.Model(inputs, outputs)
```

**Benefits**:
- **Consistency**: Same picking criteria applied to all data
- **Speed**: Process thousands of files automatically
- **Handles noise**: Learns from noisy examples in training
- **Uncertainty**: Can output confidence scores

---

#### **B. Unsupervised Learning: Clustering Site Types**

**Goal**: Group sites by spectral similarity (e.g., soft soil vs bedrock)

```python
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Load 500 spectra from different sites
spectra = []
site_names = []

for i in range(500):
    data = np.load(f'sites/site{i:03d}_fk_spectrum.npz')
    # Flatten 2D spectrum to 1D vector
    spectra.append(data['power'].flatten())
    site_names.append(f'Site_{i:03d}')

spectra = np.array(spectra)  # Shape: (500, nvel*nfreq)

# Reduce dimensionality with PCA
pca = PCA(n_components=50)
spectra_reduced = pca.fit_transform(spectra)

# Cluster into 4 groups
kmeans = KMeans(n_clusters=4, random_state=42)
labels = kmeans.fit_predict(spectra_reduced)

# Visualize clusters
plt.figure(figsize=(10, 6))
for i in range(4):
    mask = labels == i
    plt.scatter(spectra_reduced[mask, 0], spectra_reduced[mask, 1],
                label=f'Cluster {i}', alpha=0.6)
plt.xlabel('PC1')
plt.ylabel('PC2')
plt.legend()
plt.title('Site Classification from Dispersion Spectra')
plt.show()

# Analyze each cluster's characteristics
for i in range(4):
    cluster_spectra = spectra[labels == i]
    mean_spectrum = cluster_spectra.mean(axis=0).reshape(nvel, nfreq)

    plt.figure()
    plt.contourf(freq, vel, mean_spectrum, levels=30, cmap='viridis')
    plt.title(f'Cluster {i}: Average Spectrum')
    plt.colorbar(label='Power')
    plt.show()
```

**Applications**:
- Site classification (NEHRP categories)
- Anomaly detection (unusual sites)
- Quality screening (identify bad data)

---

#### **C. Transfer Learning: Use Pre-trained Models**

**Idea**: Treat spectra as images, use ImageNet-pretrained models

```python
from tensorflow.keras.applications import ResNet50
from tensorflow.keras import layers, Model

# Load pre-trained ResNet (trained on millions of images)
base_model = ResNet50(weights='imagenet',
                      include_top=False,
                      input_shape=(224, 224, 3))

# Freeze base layers
base_model.trainable = False

# Add custom head for dispersion picking
inputs = layers.Input(shape=(nvel, nfreq, 1))

# Resize spectrum to 224×224 for ResNet
x = layers.Resizing(224, 224)(inputs)
x = layers.Concatenate()([x, x, x])  # Convert grayscale to RGB

x = base_model(x, training=False)
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dense(128, activation='relu')(x)
outputs = layers.Dense(nfreq, activation='linear')(x)  # Dispersion curve

model = Model(inputs, outputs)
model.compile(optimizer='adam', loss='mse')

# Train with small dataset (transfer learning needs less data)
model.fit(X_train, y_train, epochs=20, batch_size=8)
```

---

#### **D. Generative Models: Data Augmentation**

**Problem**: Limited labeled training data

**Solution**: Generate synthetic spectra with known dispersion curves

```python
from scipy.ndimage import gaussian_filter

def generate_synthetic_spectrum(freq, vel, true_dispersion):
    """
    Generate synthetic power spectrum given a dispersion curve
    """
    spectrum = np.zeros((len(vel), len(freq)))

    for i, f in enumerate(freq):
        v_peak = true_dispersion[i]

        # Create Gaussian peak centered at true velocity
        peak_width = 50  # m/s
        for j, v in enumerate(vel):
            spectrum[j, i] = np.exp(-((v - v_peak) ** 2) / (2 * peak_width ** 2))

    # Add noise
    noise = np.random.normal(0, 0.1, spectrum.shape)
    spectrum += noise

    # Smooth slightly
    spectrum = gaussian_filter(spectrum, sigma=1.5)

    # Normalize
    spectrum = spectrum / np.max(spectrum)

    return spectrum

# Generate 1000 synthetic spectra with known curves
for i in range(1000):
    # Random dispersion curve (Rayleigh wave model)
    true_curve = 200 + 500 * np.sqrt(freq / 50)  # Example model

    synthetic_spectrum = generate_synthetic_spectrum(freq, vel, true_curve)

    # Save as training example
    np.savez(f'synthetic/synth{i:04d}_spectrum.npz',
             frequencies=freq, velocities=vel,
             power=synthetic_spectrum,
             picked_velocities=true_curve)
```

---

### 6. **Advanced Visualizations**

#### **A. 3D Surface Plot**
```python
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# Create meshgrid
F, V = np.meshgrid(freq, vel)

# Plot surface
surf = ax.plot_surface(F, V, power, cmap='viridis',
                       linewidth=0, antialiased=True)

ax.set_xlabel('Frequency (Hz)')
ax.set_ylabel('Velocity (m/s)')
ax.set_zlabel('Normalized Power')
ax.set_title('3D Dispersion Spectrum')

fig.colorbar(surf, shrink=0.5, aspect=5)
plt.show()
```

#### **B. Animated Frequency Slices**
```python
import matplotlib.animation as animation

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

def update(frame):
    ax1.clear()
    ax2.clear()

    # Left: Full spectrum with current frequency highlighted
    ax1.contourf(freq, vel, power, levels=30, cmap='viridis')
    ax1.axvline(x=freq[frame], color='red', linewidth=2)
    ax1.set_title('Full Spectrum')

    # Right: Velocity distribution at current frequency
    ax2.plot(power[:, frame], vel, 'b-', linewidth=2)
    ax2.axhline(y=picked[frame], color='red', linestyle='--',
                label=f'Picked: {picked[frame]:.0f} m/s')
    ax2.set_xlabel('Power')
    ax2.set_ylabel('Velocity (m/s)')
    ax2.set_title(f'Frequency: {freq[frame]:.1f} Hz')
    ax2.legend()
    ax2.grid(True)

ani = animation.FuncAnimation(fig, update, frames=len(freq),
                             interval=100, repeat=True)
plt.show()

# Save as video
# ani.save('dispersion_animation.mp4', writer='ffmpeg', fps=10)
```

#### **C. Statistical Summary Plots**
```python
# Load all spectra from a survey
all_spectra = []
all_picks = []

for i in range(20):
    data = np.load(f'survey/shot{i:02d}_fk_spectrum.npz')
    all_spectra.append(data['power'])
    all_picks.append(data['picked_velocities'])

all_spectra = np.array(all_spectra)  # (20, nvel, nfreq)
all_picks = np.array(all_picks)      # (20, nfreq)

# Calculate statistics
mean_spectrum = np.mean(all_spectra, axis=0)
std_spectrum = np.std(all_spectra, axis=0)
mean_picks = np.mean(all_picks, axis=0)
std_picks = np.std(all_picks, axis=0)

# Plot with uncertainty bands
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Left: Average spectrum
cf = ax1.contourf(freq, vel, mean_spectrum, levels=30, cmap='viridis')
ax1.plot(freq, mean_picks, 'w-', linewidth=2, label='Mean')
ax1.fill_between(freq, mean_picks - std_picks, mean_picks + std_picks,
                 alpha=0.3, color='white', label='±1 std')
ax1.set_title('Average Spectrum (20 shots)')
plt.colorbar(cf, ax=ax1)
ax1.legend()

# Right: Variability map
cf2 = ax2.contourf(freq, vel, std_spectrum, levels=30, cmap='hot')
ax2.set_title('Standard Deviation Map')
plt.colorbar(cf2, ax=ax2, label='Std Dev of Power')

plt.tight_layout()
plt.show()
```

---

### 7. **Integration with Inversion Software**

Many shear wave velocity inversion codes can use **uncertainty estimates** from dispersion analysis.

#### **Export Uncertainty for Dinver/Geopsy**
```python
# Calculate dispersion curve with uncertainty bounds
for i in range(len(freq)):
    col = power[:, i]

    # Find points where power > 70% of maximum
    threshold = 0.7 * np.max(col)
    indices = np.where(col > threshold)[0]

    if len(indices) > 0:
        v_min = vel[indices[0]]
        v_max = vel[indices[-1]]
        v_pick = vel[np.argmax(col)]

        # Write to Dinver format
        print(f"{freq[i]:.2f} {v_pick:.1f} {v_min:.1f} {v_max:.1f}")
```

---

### 8. **Batch Processing and Automation**

```python
import glob

# Process entire survey automatically
spectrum_files = glob.glob('output/*_spectrum.npz')

results = []

for file in spectrum_files:
    data = np.load(file)

    # Extract metadata
    offset = data['offset']
    method = data['method']

    # Calculate quality metrics
    power = data['power']
    sharpness = []
    for i in range(power.shape[1]):
        col = power[:, i]
        sharpness.append(np.max(col) / np.median(col))

    avg_sharpness = np.mean(sharpness)

    # Store result
    results.append({
        'file': file,
        'offset': offset,
        'method': method,
        'quality': avg_sharpness
    })

# Create quality report
import pandas as pd
df = pd.DataFrame(results)
df.to_csv('quality_report.csv', index=False)

print(df.sort_values('quality'))
```

---

## Summary of Benefits

| Application | Benefit | Time Saved |
|-------------|---------|------------|
| Custom picking | Better accuracy | Hours per site |
| Multi-mode extraction | More complete analysis | Days per survey |
| QC assessment | Identify bad data early | Avoid bad inversions |
| Publication figures | Journal-ready plots | Hours per paper |
| ML training | Build auto-picker | Once trained, saves 90% time |
| Uncertainty quantification | Better inversion constraints | More reliable Vs profiles |
| Batch automation | Process 100s of files | Weeks → Hours |

---

## Loading Data Examples

### Python
```python
import numpy as np
data = np.load('shot01_fk_spectrum.npz')
print(data.files)  # List all arrays
freq = data['frequencies']
vel = data['velocities']
power = data['power']
```

### MATLAB
```matlab
data = load('shot01_fk_spectrum.npz', '-mat');
freq = data.frequencies;
vel = data.velocities;
power = data.power;
```

### Julia
```julia
using NPZ
data = npzread("shot01_fk_spectrum.npz")
freq = data["frequencies"]
```

---

**This feature unlocks advanced workflows that are impossible with just PNG plots and CSV picks!**
