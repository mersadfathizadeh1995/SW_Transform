<style>
</style>

# SW_Transform Repository Context

## Overview

SW_Transform is a seismic‐data processing
package that converts multichannel geophone recordings into **dispersion
curves** using several different transform methods. It is written in Python
and is organized under the SRC/sw_transform package. The software offers both command‑line and graphical user
interfaces for loading SEG‑2 files, preprocessing the data, applying one or
more dispersion‑curve extraction methods and exporting the results to CSV/NPZ
files. The primary goal is to simplify **Multichannel Analysis of Surface
Waves (MASW)** workflow by automating preprocessing, transform computation,
plotting and result export.

The
high‑level entry points are:

·         **run.py** – Adds the SRC directory to sys.path and launches the GUI. If the new GUI import fails it falls back to a
legacy version[[1]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/run.py#L1-L30).

·         **sw_transform** **package initializer** – Documents the package
submodules and notes that the codebase is transitioning legacy scripts into an
organized package structure[[2]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/__init__.py#L1-L17).

The
main functionality lives inside the SRC/sw_transform package, which is divided into subpackages: core, processing, gui, io, workers and cli. Each subpackage plays a specific role
in reading data, processing it with different transforms, orchestrating
workflows, or providing user interfaces. The sections below describe each part
in detail.

## Package

Structure

### sw_transform/core

The core package contains
services for caching and orchestrating the processing workflows.

- **core/cache.py** implements a unified
   preprocessing cache so that repeated transforms on the same data with the
   same parameters do not recompute the input matrix. It defines functions to
   generate cache keys, load or save preprocessed arrays and clear the cache[[3]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/core/cache.py#L14-L71).
- **core/service.py** is the heart of
   the package. Functions include:

·         _preprocess_with_cache – loads SEG‑2 files, calls preprocess_data from processing.preprocess,
and caches the result. Preprocessing can slice a time window, flip channels for
reverse shots and downsample.

·         _write_per_shot_csv – writes per‑shot dispersion picks (frequency, phase velocity,
wavelength) to a CSV file.

·         _save_spectrum_npz – exports the full power spectrum to an .npz file containing
arrays (frequencies, velocities, power spectrum, picked velocities) together
with metadata such as method name, offset and export date[[4]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/core/service.py#L104-L185).

·         create_combined_spectrum – combines several per‑offset spectra into a single .npz file, storing each
offset’s spectrum and metadata in a dictionary[[4]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/core/service.py#L104-L185).

·         **run_single** – orchestrates a single processing method. It pre‑processes the raw
data (possibly using the cache), dynamically loads the selected transform from processing.registry,
executes its **step 3** (transform) and **step 4** (analysis)
functions, saves spectra if requested, writes per‑shot CSVs, and returns a
plot. The function tailors interpolation and plotting parameters depending on
the chosen method (frequency–wavenumber, FDBF, phase shift or slant stack)[[5]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/core/service.py#L195-L306).

·         **run_compare** – runs all four methods on the same input file, producing a 2×2 grid
plot, saving individual spectra and CSVs and generating a combined CSV. It
returns a success indicator and the figure path[[6]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/core/service.py#L344-L430).

### sw_transform/processing

This package contains
implementations of the dispersion‑curve extraction algorithms. A **registry** module records each method’s functions for steps 3/4 and default plotting
parameters, allowing dynamic lookup.

#### Registry

processing/registry.py defines a dictionary
that maps method names (fk, fdbf, ps, ss) to a label, the **step 3** transform function, the **step 4** analysis function, the plotting
function and default plotting options[[7]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/registry.py#L12-L40). The
registry also includes a helper compute_reverse_flag to handle reversing
geometry based on user input.

#### FK method –

frequency–wavenumber transform

In processing/fk.py the **FK transform** uses a 2D FFT to convert the time–space data matrix to the frequency–wavenumber
domain. The fk_transform function returns frequency and
wavenumber vectors and a complex spectrum[[8]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/fk.py#L20-L31). The analysis function analyze_fk_spectrum can normalize the
spectrum by each frequency column or by the overall maximum and then picks
phase velocities by locating peaks in the normalized spectrum[[9]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/fk.py#L34-L61). The plotting function plot_freq_velocity_uniform converts the
wavenumber dimension to velocity, interpolates the spectrum onto a regular
velocity grid and creates a contour plot with the picked curve[[10]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/fk.py#L64-L94).

#### FDBF – frequency‑domain

beamforming

processing/fdbf.py implements the **frequency‑domain
beamforming** method. The first step computes cross‑spectral matrices between
channels using scipy.signal.csd, with optional amplitude
weighting to compensate for vibrosis or hammer sources[[11]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/fdbf.py#L20-L45). The second step performs a 1D f‑k analysis (fk_analysis_1d) that loops over velocities,
computing power by weighted beamforming and normalizing it; it also identifies
phase‑velocity peaks and wavelengths[[12]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/fdbf.py#L59-L94). The plotting function plot_freq_velocity_spectrum interpolates
the resulting power spectrum onto a velocity grid and draws contours and picks[[13]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/fdbf.py#L97-L127).

#### PS – phase shift method

processing/ps.py provides a **phase‑shift
stacking** approach. phase_shift_transform performs FFTs on each
channel and stacks the spectra with complex phase shifts corresponding to a
velocity grid to construct power as a function of frequency and velocity[[14]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/ps.py#L20-L41). analyze_phase_shift normalizes the spectrum either by each frequency or by the global
maximum and extracts velocity picks by finding maxima along the velocity axis
with an optional tolerance to avoid closely spaced picks[[15]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/ps.py#L45-L73). The plotter draws the velocity–frequency spectrum and overlays the
picks.

#### SS – slant stack (tau–p)

processing/ss.py implements the **slant‑stack** or tau–p transform. It shifts each trace by time delays corresponding to a set
of trial velocities and sums them to produce a tau–p section[[16]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/ss.py#L20-L33). The result is then transformed to the frequency domain to get power
versus frequency and velocity. Like the PS method, analyze_slant_stack normalizes and picks
velocities, and plot_slant_stack_dispersion generates a
contour plot.

#### Preprocessing and SEG‑2 I/O

·         **processing/preprocess.py** defines preprocess_data used by the core service.
It slices the time window, reverses the channel order for reverse shots,
downsamples, and optionally zero‑pads or trims the data length. It outputs the
processed time matrix and updated time vectors for subsequent transforms.

·         **processing/seg2.py** is a SEG‑2 file reader. It reads binary headers and trace pointers,
extracts trace data and metadata such as sampling rate, channel spacing and
delays, and returns the time vector and a 2‑D array of channel recordings. The
functions support reading multiple data files within the same shot.

### sw_transform/io

The io/file_assignment.py module assists the GUI and CLI in determining shot offsets and whether the
sensor array should be reversed. It parses .dat filenames, extracts
the shot index, infers offsets based on a repeating ten‑shot pattern (for
example, positions 1–10 correspond to offsets 1–10 m) and returns
assignments for each file[[17]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/io/file_assignment.py#L44-L74). A legacy assignment module
can be used if available, but the native implementation handles the logic in
pure Python.

### sw_transform/cli

This package exposes
command‑line interfaces for batch processing. The CLI entry points defined in cli/__init__.py are single and compare[[18]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/cli/__init__.py#L1-L4).

·         **cli/single.py** parses arguments such as the input file, output directory, offset,
processing method (fk, fdbf, ps, ss), reverse flag,
source type (hammer or vibrosis), and extra parameters (JSON). It calls run_single from core.service and prints
the JSON results[[19]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/cli/single.py#L10-L48).

·         **cli/compare.py** accepts similar arguments but runs all four methods using run_compare, saving
multiple outputs and printing the results[[20]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/cli/compare.py#L23-L45).

### sw_transform/gui

The GUI provides an
interactive environment for non‑technical users. The top‑level GUI function gui.main re‑exports from gui/app[[21]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/gui/__init__.py#L1-L5). A thin wrapper gui/app.py imports a
legacy GUI if the new GUI fails[[22]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/gui/app.py#L2-L24). The primary interface lives in gui/simple_app.py (not
reproduced here due to length), which builds a **Tkinter** window with
controls for selecting data files, specifying offsets, choosing processing
methods, adjusting preprocessing parameters, previewing raw and processed data,
running single or compare modes, exporting spectra, and generating combined
outputs. The GUI interacts with the core.service functions
and the method registry to ensure consistent parameter passing. It supports
vibrosis source compensation, saving plots, exporting .npz spectra for
advanced analysis, building combined CSVs across shots and offsets, and
optionally assembling a PowerPoint report. Various helper functions handle file
assignment, preview of arrays and waterfall plots, creation of combined
spectra, and management of figure galleries.

### sw_transform/workers

The workers modules
(e.g., workers/single.py, workers/compare.py) are thin wrappers that delegate to legacy asynchronous workers in the Previous/4_wave_cursor directory. They exist for backward compatibility and do not contain
significant logic.

## Documentation

Highlights

Several Markdown files accompany the source code to guide users and
developers:

1. **IMPROVEMENTS_ROADMAP.md** – A detailed roadmap of planned enhancements for the package. It
   covers metadata, documentation, testing, vibrosis improvements, GUI
   usability, error handling, performance features (such as power spectrum
   export and multi‑mode extraction), code quality, platform compatibility,
   advanced features (e.g., machine learning integration), distribution,
   community engagement and security. It provides a vision for future
   versions and success metrics.
2. **VIBROSIS_IMPLEMENTATION.md** – Describes how vibrosis source compensation is incorporated into
   the FDBF method. It explains that vibrosis applies amplitude‐dependent
   weighting in the cross‑spectral matrix computation to enhance high
   frequencies, shows code changes in fdbf.py, demonstrates using the
   feature in the GUI/CLI, and outlines tests and future improvements.
3. **SPECTRUM_EXPORT_FEATURE.md** – Documents the ability to export full power spectra to .npz files. It details the data fields
   stored for each method (frequencies, velocities, power values, picks),
   file naming conventions, approximate file sizes, and enumerates many
   potential uses: custom picking, higher‑mode extraction, QC metrics,
   high‑quality figures, machine‑learning datasets, advanced visualizations,
   and integration with inversion software. Examples show how to load these
   files in Python for analysis and plotting.
4. **SPECTRUM_NPZ_FILE_FORMAT.md** – Provides a reference for the .npz format of single and combined
   spectrum files. It explains naming conventions, metadata keys,
   organization of per‑offset data within combined files, and offers guidance
   on when to use single vs combined exports.
5. **IMPLEMENTATION_PLAN_SPECTRUM_EXPORT.md** – Outlines the design and development plan for implementing
   spectrum export. It breaks tasks into phases covering core changes,
   GUI/CLI integration, unit tests, documentation updates and risk
   management.

These documents help users understand the design philosophy behind the
package and how to extend or utilize advanced features.

## Typical

Workflow

1.      **Data
Collection**: Acquire surface‐wave recordings using an
array of geophones. Export the data in SEG‑2 format (.dat files).

2.      **File
Assignment**: Use the GUI or CLI to assign offsets and
reverse flags to each shot. file_assignment.assign_files reads file names, extracts shot indices and infers offsets based on a
ten‑shot pattern[[17]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/io/file_assignment.py#L44-L74).

3.      **Preprocessing**: Choose a time window, optionally reverse the channel order,
downsample and zero‑pad using preprocess_data. The results can be cached by core/cache to speed up repeated runs[[3]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/core/cache.py#L14-L71).

4.      **Transform
Selection**: Select a transform method (FK, FDBF, PS or
SS). The registry provides each method’s step‑3 transform, step‑4 analysis and
plotting functions[[7]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/registry.py#L12-L40).

5.      **Processing**: run_single (for one method) or run_compare (for all methods) orchestrates preprocessing, method execution and
result export[[5]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/core/service.py#L195-L306)[[6]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/core/service.py#L344-L430).

6.      **Result
Interpretation**: View contour plots of power vs
frequency and velocity. The analysis functions pick phase velocities by
locating spectral maxima[[9]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/fk.py#L34-L61)[[12]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/fdbf.py#L59-L94)[[15]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/ps.py#L45-L73).

7.      **Export**: Save per‑shot CSV files for numerical values, export full spectra to .npz for advanced analysis, or use combined CSV/NPZ for multi‑offset
studies.

## Strengths

and Extensibility

The design of SW_Transform emphasizes modularity. The **registry** allows new transform
methods to be added simply by writing a new module with step‑3/4 functions and
updating the registry. The **caching** mechanism accelerates iterative
analysis. Both command‑line and GUI interfaces cater to different user bases.
Extensive documentation anticipates advanced uses like vibrosis source
compensation, machine‑learning processing of spectra and integration with
inversion algorithms. The separate processing, core and io subpackages make it clear where to
implement improvements or contribute new functionality.

## Visual

Representation

The image above provides an abstract artistic representation of
geophone waves and dispersion curves. While not drawn from the code itself, it
evokes the frequency–velocity plots produced by the software.

---

[[1]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/run.py#L1-L30) run.py

https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/run.py

[[2]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/__init__.py#L1-L17) __init__.py

https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/__init__.py

[[3]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/core/cache.py#L14-L71) cache.py

https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/core/cache.py

[[4]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/core/service.py#L104-L185) [[5]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/core/service.py#L195-L306) [[6]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/core/service.py#L344-L430) service.py

https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/core/service.py

[[7]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/registry.py#L12-L40) registry.py

https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/registry.py

[[8]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/fk.py#L20-L31) [[9]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/fk.py#L34-L61) [[10]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/fk.py#L64-L94) fk.py

https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/fk.py

[[11]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/fdbf.py#L20-L45) [[12]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/fdbf.py#L59-L94) [[13]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/fdbf.py#L97-L127) fdbf.py

https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/fdbf.py

[[14]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/ps.py#L20-L41) [[15]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/ps.py#L45-L73) ps.py

https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/ps.py

[[16]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/ss.py#L20-L33) ss.py

https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/processing/ss.py

[[17]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/io/file_assignment.py#L44-L74) file_assignment.py

https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/io/file_assignment.py

[[18]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/cli/__init__.py#L1-L4) __init__.py

https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/cli/__init__.py

[[19]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/cli/single.py#L10-L48) single.py

https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/cli/single.py

[[20]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/cli/compare.py#L23-L45) compare.py

https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/cli/compare.py

[[21]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/gui/__init__.py#L1-L5) __init__.py

https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/gui/__init__.py

[[22]](https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/gui/app.py#L2-L24) app.py

https://github.com/mersadfathizadeh1995/SW_Transform/blob/HEAD/SRC/sw_transform/gui/app.py
