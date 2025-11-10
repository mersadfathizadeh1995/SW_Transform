# SW_Transform Package - Improvements Roadmap

**Version**: 1.0
**Date**: November 10, 2025
**Status**: Pre-Release Planning

---

## 🚀 Critical (Required Before Public Release)

### 1. Package Configuration & Metadata

**Priority**: CRITICAL
**Status**: ❌ Missing

- [ ] Create `setup.py` or `pyproject.toml` with package metadata
  - Package name: `sw-transform` or `masw-transform`
  - Version: `0.1.0` (semantic versioning)
  - Author information
  - License declaration
  - Entry points for CLI tools
  - Dependencies specification

- [ ] Create `requirements.txt` with exact dependencies:
  ```
  numpy>=1.20.0
  scipy>=1.7.0
  matplotlib>=3.3.0
  Pillow>=8.0.0
  # Additional dependencies as identified
  ```

- [ ] Add `__version__` variable to `SRC/sw_transform/__init__.py`

- [ ] Test package installation with:
  ```bash
  pip install -e .
  python -m sw_transform --version
  ```

---

### 2. Documentation

**Priority**: CRITICAL
**Status**: ❌ Missing

#### README.md
- [ ] Project overview and purpose (MASW analysis)
- [ ] Key features (4 methods: FK, FDBF, PS, SS)
- [ ] Installation instructions
- [ ] Quick start guide with example
- [ ] Screenshots of GUI
- [ ] System requirements (Python 3.8+, OS compatibility)
- [ ] Dependencies list
- [ ] Citation information (if academic)
- [ ] Contact/support information
- [ ] Link to full documentation

#### LICENSE
- [ ] Choose appropriate license (MIT, GPL-3.0, Apache 2.0, or proprietary)
- [ ] Add LICENSE file to repository root
- [ ] Update headers in source files if needed

#### CHANGELOG.md
- [ ] Document version history
- [ ] Format: Keep a Changelog standard
- [ ] Start with v0.1.0 initial release

#### User Guide (Optional but Recommended)
- [ ] Create `docs/` folder
- [ ] User manual for GUI operation
- [ ] CLI usage examples
- [ ] Theory behind each method (FK, FDBF, PS, SS)
- [ ] Interpretation guide for dispersion curves

---

### 3. Testing Infrastructure

**Priority**: HIGH
**Status**: ❌ Missing

- [ ] Create `tests/` directory structure
- [ ] Unit tests for core modules:
  - `test_seg2.py` - SEG-2 file reader
  - `test_preprocessing.py` - Data preprocessing
  - `test_fk.py`, `test_fdbf.py`, `test_ps.py`, `test_ss.py` - Transform methods
  - `test_cache.py` - Caching system
  - `test_file_assignment.py` - Offset detection

- [ ] Integration tests:
  - End-to-end processing pipeline
  - GUI workflow testing
  - CLI tool validation

- [ ] Test data:
  - Include sample SEG-2 files (small, sanitized)
  - Expected output files (PNG, CSV)

- [ ] CI/CD setup (optional):
  - GitHub Actions workflow
  - Automated testing on push/PR
  - Multi-platform testing (Windows, Linux, macOS)

---

## 🎯 High Priority (User Experience)

### 4. Vibrosis Source Support Enhancement

**Priority**: HIGH
**Status**: ✅ Partially Implemented → ⚠️ Needs Improvement

#### Current State:
- ✅ FDBF supports vibrosis weighting (`weight_mode='invamp'`)
- ✅ GUI has source type radio buttons (Hammer/Vibrosis)
- ✅ Parameter flows through processing pipeline

#### Needed Improvements:

- [x] **GUI Enhancement**:
  - [x] Replace radio buttons with prominent checkbox: "☑ Vibrosis Source (FDBF compensation)"
  - [x] Add tooltip explaining when to use vibrosis mode
  - [x] Add visual indicator: "(FDBF only)" label
  - [x] Consider adding icon/color highlight when enabled

- [ ] **Output Labeling**:
  - [ ] Append source type to FDBF filenames:
    - `shot01_fdbf_vibrosis.png` / `shot01_fdbf_hammer.png`
  - [ ] Add metadata header to CSV files:
    ```csv
    # Source Type: Vibrosis
    # Weight Mode: invamp
    # Processing Date: 2025-11-10
    Frequency(Hz), PhaseVelocity(m/s), Wavelength(m)
    ```

- [ ] **Plot Annotations**:
  - [ ] Add text to FDBF figures: "Vibrosis compensated" or "Hammer source"
  - [ ] Small annotation in top-right corner of plot
  - [ ] Include in compare mode FDBF subplot

- [ ] **CLI Support**:
  - [ ] Add `--source-type` flag to CLI tools:
    ```bash
    python -m sw_transform.cli.single data.dat --key fdbf --source-type vibrosis
    python -m sw_transform.cli.compare data.dat --source-type vibrosis
    ```
  - [ ] Update CLI help text and documentation

- [ ] **Persistent Settings**:
  - [ ] Save source type preference to config file
  - [ ] Remember last-used setting between sessions
  - [ ] Menu option: `File → Preferences → Default Source Type`

#### Advanced Features (Future):

- [ ] **Auto-Detection**:
  - [ ] Analyze signal characteristics to suggest source type
  - [ ] Hammer: Short duration (<100ms), high kurtosis
  - [ ] Vibrosis: Long duration (>1s), swept frequency
  - [ ] Show suggestion dialog with recommendation

- [ ] **Spectrum Viewer QC Tab**:
  - [ ] Display amplitude spectrum of loaded data
  - [ ] Show before/after weighting comparison
  - [ ] Help user validate source type selection

- [ ] **Extended Weighting Options**:
  - [ ] Custom weighting slider (0-100%)
  - [ ] Alternative weighting functions
  - [ ] Export weighting curves for documentation

---

### 5. GUI Usability Improvements

**Priority**: HIGH
**Status**: ⚠️ Needs Enhancement

#### Layout & Navigation:
- [ ] Add keyboard shortcuts:
  - `Ctrl+O`: Open files
  - `Ctrl+R`: Run processing
  - `F5`: Refresh file list
  - `F1`: Help documentation

- [ ] Reorganize Input tab for better flow:
  - Move source type selector higher (more prominent)
  - Group related settings with visual separators
  - Add collapsible sections for advanced settings

- [ ] Status bar enhancements:
  - Show current settings summary
  - Display memory usage for large datasets
  - Real-time processing speed (files/sec)

#### Visual Feedback:
- [ ] Progress indicators:
  - Per-file progress (current: 3/10 files)
  - Time remaining estimate
  - Animated icon during processing

- [ ] File list enhancements:
  - Color-code rows: processed (green), failed (red), pending (gray)
  - Add status column: ✓ Done, ✗ Failed, ⏳ Processing
  - Right-click context menu: View results, Re-process, Remove

- [ ] Interactive result previews:
  - Click on completed file → show thumbnail
  - Double-click → open full image in viewer
  - Zoom/pan controls in preview pane

#### Help System:
- [ ] Add Help menu:
  - `Help → User Guide` (open README or PDF)
  - `Help → Method Explanations` (FK, FDBF, PS, SS theory)
  - `Help → Source Types Explained` (Hammer vs Vibrosis)
  - `Help → About` (version, license, credits)

- [ ] Tooltips for all input fields:
  - Hover over label → explanation appears
  - Include typical value ranges
  - Link to documentation sections

- [ ] First-run wizard:
  - Welcome screen with quick tour
  - Load sample data for demonstration
  - Guided processing example

---

### 6. Error Handling & Validation

**Priority**: HIGH
**Status**: ⚠️ Basic implementation, needs enhancement

- [ ] Input validation:
  - Check file paths exist before processing
  - Validate numeric inputs (non-negative, reasonable ranges)
  - Warn if frequency range exceeds Nyquist limit
  - Detect corrupt SEG-2 files early

- [ ] Graceful error messages:
  - User-friendly language (avoid technical jargon)
  - Suggest solutions: "Try reducing downsample factor"
  - Log detailed error to file for debugging
  - Option to report bug (copy error to clipboard)

- [ ] Recovery mechanisms:
  - Save processing state periodically
  - Resume interrupted batch processing
  - Skip failed files, continue with others
  - Auto-save log file to output folder

- [ ] Warnings system:
  - Warn if offset assignments seem incorrect
  - Alert if spectrum looks unusual (DC offset, clipping)
  - Flag if dispersion picks are sparse/noisy

---

## 📊 Medium Priority (Features & Quality)

### 7. Data Export Enhancements

**Priority**: MEDIUM
**Status**: ⚠️ Basic CSV export works

- [ ] **Excel Export (.xlsx)**:
  - One sheet per method
  - Formatted tables with headers
  - Include plots as embedded images
  - Summary sheet with metadata

- [ ] **MATLAB Export (.mat)**:
  - Save dispersion data as structs
  - Include frequency, velocity, wavelength arrays
  - Processing parameters as metadata

- [ ] **JSON Export**:
  - Machine-readable format for automated workflows
  - Include all processing parameters
  - Versioned schema for compatibility

- [ ] **Combined Report (PDF)**:
  - Automated report generation
  - All plots in single document
  - Table of contents
  - Processing summary and parameters

- [ ] **PowerPoint Improvements**:
  - Current: Basic PPT generation exists
  - Needed: Better layout, custom templates
  - Separate slides for each method
  - Add text annotations with key findings

---

### 8. Processing Features

**Priority**: MEDIUM
**Status**: Core functionality complete

#### Batch Processing:
- [ ] **Multi-project support**:
  - Process multiple surveys in sequence
  - Each with different parameters
  - Generate comparison reports across projects

- [ ] **Parameter profiles**:
  - Save/load parameter sets as presets
  - "Urban survey", "Deep investigation", etc.
  - Share profiles as JSON files

- [ ] **Parallel processing**:
  - Multi-threading for file processing
  - Utilize multiple CPU cores
  - Configurable worker count

#### Analysis Tools:
- [ ] **Dispersion curve editing**:
  - Manual picking mode
  - Remove outlier points
  - Smooth/interpolate curves
  - Export edited curves

- [ ] **Comparison tools**:
  - Overlay multiple files on one plot
  - Statistical analysis (mean, std dev)
  - Identify anomalies/outliers

- [ ] **Inversion interface** (Advanced):
  - Link to external inversion software
  - Export to DINVER, Geopsy formats
  - Import shear wave velocity profiles

---

### 9. Code Quality & Maintenance

**Priority**: MEDIUM
**Status**: ⚠️ Needs attention

#### Code Organization:
- [ ] Remove legacy dependencies:
  - Audit all `_legacy_base()` references
  - Complete migration to native implementations
  - Remove `Previous/` folder references

- [ ] Type hints:
  - Add comprehensive type annotations
  - Use `mypy` for static type checking
  - Document return types clearly

- [ ] Docstrings:
  - Add docstrings to all public functions/classes
  - Use NumPy or Google style
  - Include parameter descriptions and examples

#### Refactoring:
- [ ] Break up large files:
  - `simple_app.py` (975 lines) → split into modules
  - Separate concerns: UI layout, event handlers, processing logic

- [ ] Configuration system:
  - Centralized config file (JSON/TOML)
  - User preferences (GUI geometry, defaults)
  - Processing defaults by survey type

- [ ] Logging:
  - Use Python `logging` module (not just GUI log)
  - Configurable log levels (DEBUG, INFO, WARNING)
  - Rotate log files, prevent unbounded growth

---

### 10. Platform Compatibility

**Priority**: MEDIUM
**Status**: ⚠️ Primary testing on Windows

- [ ] Cross-platform testing:
  - Windows 10/11 (primary target)
  - Ubuntu/Debian Linux
  - macOS (Intel and Apple Silicon)

- [ ] Path handling:
  - Use `pathlib.Path` throughout
  - Avoid hard-coded `\` or `/` separators
  - Test with spaces and special characters in paths

- [ ] File system:
  - Handle case-sensitive vs case-insensitive FS
  - Long path support (Windows >260 chars)
  - Network drive compatibility

- [ ] Packaging:
  - Create standalone executables (PyInstaller, cx_Freeze)
  - Windows installer (.msi or .exe)
  - Linux AppImage or snap package
  - macOS .app bundle with signing/notarization

---

## 🔮 Future Enhancements (Long-term)

### 11. Advanced Features

**Priority**: LOW
**Status**: 💡 Ideas for future versions

#### Real-time Processing:
- [ ] Live data acquisition support
- [ ] Process data as it's being recorded
- [ ] Real-time dispersion curve updates
- [ ] Field QC mode for data collection

#### Cloud Integration:
- [ ] Cloud storage support (AWS S3, Google Drive)
- [ ] Web-based interface (Flask/Django backend)
- [ ] Collaborative projects (multiple users)
- [ ] Remote processing on HPC clusters

#### Machine Learning:
- [ ] Auto-picking with trained ML models
- [ ] Noise/artifact detection
- [ ] Quality scoring for dispersion curves
- [ ] Source type classification

#### 3D Visualization:
- [ ] 3D surface plots (freq-velocity-amplitude)
- [ ] Interactive rotation/zoom
- [ ] Export to 3D formats (OBJ, STL)
- [ ] Virtual reality viewer (VR headset support)

#### Mobile Support:
- [ ] Android/iOS app for field QC
- [ ] Quick preview of dispersion curves
- [ ] Cloud sync with desktop version
- [ ] GPS tagging of survey locations

---

### 12. Integration & Interoperability

**Priority**: LOW
**Status**: 💡 Future consideration

- [ ] Plugin system:
  - Custom processing methods
  - Third-party integrations
  - User-contributed extensions

- [ ] API development:
  - REST API for remote processing
  - Python SDK for scripting
  - R package wrapper for statisticians

- [ ] Format support:
  - SEG-Y seismic format
  - MiniSEED (earthquake seismology)
  - Generic CSV/TXT import
  - SEGY export for other tools

- [ ] GIS integration:
  - Export results with coordinates
  - Import survey layouts from KML/SHP
  - Generate maps with dispersion data
  - QGIS plugin for visualization

---

## 📋 Documentation Gaps

### 13. Missing Documentation

**Priority**: HIGH (for public release)
**Status**: ❌ Minimal documentation

#### User Documentation:
- [ ] Installation guide (Windows, Linux, macOS)
- [ ] Beginner tutorial (step-by-step)
- [ ] Video tutorials (screen recordings)
- [ ] FAQ section
- [ ] Troubleshooting guide
- [ ] Best practices for field data

#### Developer Documentation:
- [ ] Architecture overview
- [ ] Module organization diagram
- [ ] API reference (auto-generated from docstrings)
- [ ] Contributing guidelines
- [ ] Code style guide (PEP 8 compliance)
- [ ] Development setup instructions

#### Scientific Documentation:
- [ ] Theory behind each method
- [ ] Algorithm descriptions
- [ ] Validation studies
- [ ] Benchmark comparisons with other software
- [ ] Citation guidelines for academic use
- [ ] Example case studies

---

## 🐛 Known Issues & Bugs

### 14. Issues to Resolve

**Priority**: Variable
**Status**: ⚠️ Documented in FIXES_APPLIED.md

#### From FIXES_APPLIED.md:
- ✅ Combined CSV generation (FIXED)
- ✅ Icon display problems (FIXED)

#### Potential Issues:
- [ ] Large file handling (memory optimization needed)
- [ ] Thread safety in parallel processing
- [ ] Cache invalidation edge cases
- [ ] Unicode filenames on Windows
- [ ] Matplotlib backend conflicts

---

## 📈 Performance Optimization

### 15. Speed & Efficiency

**Priority**: MEDIUM
**Status**: Acceptable for current use cases

- [ ] Profiling:
  - Identify bottlenecks with cProfile
  - Memory profiling with memory_profiler
  - Optimize hot paths

- [ ] Algorithm optimization:
  - Vectorize NumPy operations
  - Use FFT more efficiently (FFTW backend)
  - Reduce redundant calculations

- [ ] Caching improvements:
  - LRU cache for frequently accessed data
  - Smarter cache invalidation
  - Compressed cache storage

- [ ] UI responsiveness:
  - Move processing to background threads
  - Non-blocking GUI updates
  - Cancel operation support

---

## 🎨 Visual Polish

### 16. Aesthetic Improvements

**Priority**: LOW
**Status**: Functional but basic

- [ ] Modern UI theme:
  - Dark mode support
  - Custom color schemes
  - High-DPI display scaling

- [ ] Professional icons:
  - Consistent icon set throughout
  - Scalable vector icons (SVG)
  - Themed icons (light/dark variants)

- [ ] Plot styling:
  - Publication-quality default styles
  - Customizable color maps
  - Export with transparent backgrounds
  - Vector formats (SVG, PDF, EPS)

- [ ] Splash screen:
  - Show on startup
  - Display version and credits
  - Progress indicator for initialization

---

## 🔐 Security & Privacy

### 17. Security Considerations

**Priority**: MEDIUM (for public release)
**Status**: ⚠️ Not formally reviewed

- [ ] Input sanitization:
  - Validate file paths (prevent directory traversal)
  - Limit file sizes (prevent DoS)
  - Check SEG-2 file structure (prevent buffer overflows)

- [ ] Data privacy:
  - No telemetry or usage tracking (unless opt-in)
  - Clear privacy policy
  - Local processing only (no cloud by default)

- [ ] Code signing:
  - Sign executables (Windows, macOS)
  - Verify package integrity (checksums)
  - Secure distribution channels

- [ ] Dependency audit:
  - Regular security updates for dependencies
  - Use `pip-audit` or `safety` tools
  - Pin versions to avoid supply chain attacks

---

## 📦 Distribution & Deployment

### 18. Release Process

**Priority**: CRITICAL (for v1.0)
**Status**: ❌ Not established

- [ ] Version control:
  - Git branching strategy (main, develop, feature/*)
  - Semantic versioning (MAJOR.MINOR.PATCH)
  - Release tags and GitHub releases

- [ ] Distribution channels:
  - PyPI package publication
  - Conda-forge package (optional)
  - GitHub releases with binaries
  - Website/documentation hosting

- [ ] Update mechanism:
  - Check for updates on startup (optional)
  - In-app update notification
  - Changelog display for new versions

- [ ] Support infrastructure:
  - Issue tracker (GitHub Issues)
  - Discussion forum (GitHub Discussions)
  - Email support (if applicable)
  - User community (Slack, Discord?)

---

## 🎓 Community & Collaboration

### 19. Open Source Community

**Priority**: MEDIUM (if open source)
**Status**: 💡 Future planning

- [ ] Contributing guidelines:
  - CONTRIBUTING.md file
  - Code of conduct
  - Pull request template
  - Issue templates (bug, feature request)

- [ ] Developer onboarding:
  - README for developers
  - Development environment setup
  - Architecture walkthrough
  - First contribution guide

- [ ] Recognition:
  - Contributors list
  - Credit system for community contributions
  - Featured contributions showcase

---

## 📊 Success Metrics

### 20. Release Readiness Checklist

**For v0.1.0 (Minimum Viable Release)**:

- [ ] ✅ Core functionality works (FK, FDBF, PS, SS)
- [ ] ✅ GUI is stable and usable
- [ ] ✅ CLI tools functional
- [ ] ❌ setup.py / pyproject.toml configured
- [ ] ❌ README.md written
- [ ] ❌ LICENSE file added
- [ ] ❌ requirements.txt complete
- [ ] ❌ Basic tests pass
- [ ] ❌ Installation tested on 2+ platforms
- [ ] ✅ No critical bugs

**For v1.0.0 (Production Release)**:

- [ ] All v0.1.0 requirements met
- [ ] Comprehensive documentation
- [ ] Test coverage >70%
- [ ] User guide complete
- [ ] CI/CD pipeline established
- [ ] Security audit passed
- [ ] Performance benchmarks documented
- [ ] Community feedback incorporated

---

## 📝 Notes

- **Current package name**: `SW_Transform`
- **Suggested PyPI name**: `sw-transform` or `masw-transform` or `surface-wave-transform`
- **Current status**: Pre-release, functional but needs polish
- **Target users**: Geophysicists, seismologists, civil engineers
- **License recommendation**: MIT (permissive) or GPL-3.0 (copyleft)

---

**Document maintained by**: SW_Transform Development Team
**Last updated**: 2025-11-10
**Next review**: Before v0.1.0 release
