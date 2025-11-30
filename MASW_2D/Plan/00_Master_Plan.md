# MASW 2D Implementation - Master Plan

## General Outline

---

## 1. Project Overview

### 1.1 Goal
Add 2D MASW capabilities to SW_Transform package, enabling extraction of multiple dispersion curves from surface wave data for lateral subsurface characterization.

### 1.2 Three Core Methods

| Method | Description | Array Movement | Implementation Priority |
|--------|-------------|----------------|------------------------|
| **A: Sub-Array Extraction** | Extract multiple sub-arrays from fixed array with multiple shots | Fixed | Phase 1 (First) |
| **B: Roll-Along** | Process data from moving array positions | Moving | Phase 2 |
| **C: CMP Cross-Correlation** | Virtual source method using trace correlations | Fixed | Phase 3 (Advanced) |

### 1.3 Key Features (All Phases)

- Variable sub-array sizes (our innovation)
- Configurable processing parameters
- Support for different shot types (exterior, edge, interior)
- CLI interface for all functionality
- Predefined workflows for common scenarios

---

## 2. Package Structure

### 2.1 New Directory Layout

```
sw_transform/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── cache.py
│   └── service.py                    # Existing (may need minor additions)
│
├── processing/                        # Existing processing modules
│   ├── __init__.py
│   ├── fk.py
│   ├── fdbf.py
│   ├── ps.py
│   ├── ss.py
│   ├── preprocess.py
│   ├── seg2.py
│   └── registry.py
│
├── masw2d/                            # ◄── NEW: 2D MASW subpackage
│   ├── __init__.py                    # Public API exports
│   │
│   ├── config/                        # Configuration handling
│   │   ├── __init__.py
│   │   ├── schema.py                  # Configuration schemas/validation
│   │   ├── loader.py                  # Load/save survey configs
│   │   └── templates.py               # Config templates generator
│   │
│   ├── geometry/                      # Geometry calculations
│   │   ├── __init__.py
│   │   ├── shot_classifier.py         # Classify shots (exterior/edge/interior)
│   │   ├── subarray.py                # Sub-array definitions and extraction
│   │   └── midpoint.py                # Midpoint calculations
│   │
│   ├── extraction/                    # Data extraction methods
│   │   ├── __init__.py
│   │   ├── subarray_extractor.py      # Method A: Sub-array extraction
│   │   ├── rollover_extractor.py      # Method B: Roll-along (Phase 2)
│   │   └── cmpcc_extractor.py         # Method C: CMP-CC (Phase 3)
│   │
│   ├── processing/                    # Dispersion curve processing
│   │   ├── __init__.py
│   │   ├── batch_processor.py         # Process multiple sub-arrays
│   │   ├── dc_manager.py              # Dispersion curve storage/organization
│   │   └── quality.py                 # Quality metrics and filtering
│   │
│   ├── workflows/                     # Predefined workflows
│   │   ├── __init__.py
│   │   ├── base.py                    # Base workflow class
│   │   ├── standard_masw.py           # Workflow: Fixed array, multiple shots
│   │   ├── roll_along.py              # Workflow: Moving array (Phase 2)
│   │   ├── refraction_reuse.py        # Workflow: P-wave refraction data (Phase 2)
│   │   └── custom.py                  # Workflow: Fully custom configuration
│   │
│   └── output/                        # Output management
│       ├── __init__.py
│       ├── organizer.py               # File organization by midpoint
│       ├── merger.py                  # Merge DCs at same midpoint
│       └── export.py                  # Export formats (CSV, NPZ, etc.)
│
├── cli/                               # Existing CLI folder
│   ├── __init__.py
│   ├── single.py                      # Existing
│   ├── compare.py                     # Existing
│   │
│   └── masw2d/                        # ◄── NEW: 2D MASW CLI subpackage
│       ├── __init__.py
│       ├── main.py                    # Main entry point (subcommand router)
│       ├── config_cmd.py              # Config generation/validation commands
│       ├── extract_cmd.py             # Sub-array extraction commands
│       ├── process_cmd.py             # Batch processing commands
│       ├── workflow_cmd.py            # Workflow execution commands
│       └── info_cmd.py                # Survey info/preview commands
│
├── gui/                               # Existing (future integration)
│   └── ...
│
└── io/                                # Existing I/O modules
    ├── __init__.py
    └── file_assignment.py
```

### 2.2 Module Responsibilities

#### config/
| Module | Responsibility |
|--------|---------------|
| `schema.py` | Define configuration structure, validation rules |
| `loader.py` | Load JSON configs, validate, provide defaults |
| `templates.py` | Generate config templates for different survey types |

#### geometry/
| Module | Responsibility |
|--------|---------------|
| `shot_classifier.py` | Determine shot type (exterior_left, exterior_right, edge, interior) |
| `subarray.py` | Define sub-arrays, calculate channel ranges |
| `midpoint.py` | Calculate midpoint positions, offsets |

#### extraction/
| Module | Responsibility |
|--------|---------------|
| `subarray_extractor.py` | Extract sub-array data from shot gathers (Method A) |
| `rollover_extractor.py` | Handle roll-along data with multiple array positions (Method B) |
| `cmpcc_extractor.py` | CMP cross-correlation extraction (Method C) |

#### processing/
| Module | Responsibility |
|--------|---------------|
| `batch_processor.py` | Process multiple sub-arrays through dispersion transform |
| `dc_manager.py` | Store, retrieve, organize dispersion curves |
| `quality.py` | Quality metrics, offset filtering, ranking |

#### workflows/
| Module | Responsibility |
|--------|---------------|
| `base.py` | Abstract base class for workflows |
| `standard_masw.py` | Fixed array + multiple source offsets |
| `roll_along.py` | Moving array survey |
| `refraction_reuse.py` | Extract MASW from P-wave refraction data |
| `custom.py` | Fully configurable workflow |

#### output/
| Module | Responsibility |
|--------|---------------|
| `organizer.py` | Create directory structure, organize by midpoint |
| `merger.py` | Combine DCs at same position from different shots |
| `export.py` | Export to various formats |

#### cli/masw2d/
| Module | Responsibility |
|--------|---------------|
| `main.py` | Entry point, route to subcommands |
| `config_cmd.py` | `masw2d config generate`, `masw2d config validate` |
| `extract_cmd.py` | `masw2d extract` - extract sub-arrays |
| `process_cmd.py` | `masw2d process` - run dispersion analysis |
| `workflow_cmd.py` | `masw2d workflow run` - execute predefined workflow |
| `info_cmd.py` | `masw2d info` - show survey geometry info |

---

## 3. Implementation Phases

### Phase 1: Foundation + Standard MASW (Current Focus)
- Package structure creation
- Configuration system
- Geometry calculations
- Sub-array extraction (Method A)
- Basic batch processing
- Standard MASW workflow
- CLI for Phase 1 features

### Phase 2: Roll-Along + Refraction Reuse
- Roll-along extractor (Method B)
- Interior shot handling (split method)
- Roll-along workflow
- Refraction reuse workflow
- Extended CLI commands

### Phase 3: CMP Cross-Correlation (Advanced)
- CMP-CC extractor (Method C)
- CMP gather formation
- Transform adaptation for CMP gathers
- CMP workflow
- CLI for CMP-CC

### Phase 4: Integration + Polish
- GUI integration (if desired)
- Advanced quality metrics
- Automated DC merging strategies
- Documentation completion

---

## 4. CLI Command Structure

### 4.1 Main Entry Point
```bash
python -m sw_transform.cli.masw2d <command> [options]
```

### 4.2 Commands Overview

```
masw2d
├── config
│   ├── generate     Generate config template
│   ├── validate     Validate existing config
│   └── show         Display config contents
│
├── info
│   ├── geometry     Show array geometry from config
│   ├── shots        List shots and classifications
│   └── subarrays    Preview sub-array definitions
│
├── extract
│   └── subarrays    Extract sub-arrays (data preparation)
│
├── process
│   ├── single       Process single sub-array
│   └── batch        Process all sub-arrays
│
└── workflow
    ├── list         List available workflows
    ├── run          Execute a workflow
    └── describe     Show workflow details
```

---

## 5. Configuration Schema Overview

```json
{
  "survey_name": "string",
  "version": "1.0",
  
  "array": {
    "n_channels": 24,
    "dx": 2.0,
    "first_channel_position": 0.0
  },
  
  "shots": [
    {
      "file": "path/to/shot.dat",
      "source_position": -10.0,
      "label": "optional_name"
    }
  ],
  
  "subarray_configs": [
    {
      "n_channels": 12,
      "slide_step": 1,
      "name": "shallow"
    },
    {
      "n_channels": 24,
      "slide_step": 1,
      "name": "deep"
    }
  ],
  
  "processing": {
    "method": "ps",
    "freq_min": 5.0,
    "freq_max": 80.0,
    "velocity_min": 100.0,
    "velocity_max": 1500.0
  },
  
  "output": {
    "directory": "output/",
    "organize_by": "midpoint",
    "export_formats": ["csv", "npz"]
  }
}
```

---

## 6. Dependencies

### Required (New)
```
None for Phase 1 (uses existing numpy, scipy, matplotlib)
```

### Future Phases
```
disba>=1.0.0        # Phase 4: If adding inversion
```

---

## 7. Document Index

| Document | Location | Description |
|----------|----------|-------------|
| Master Plan | `Plan/00_Master_Plan.md` | This file |
| Phase 1 Plan | `Plan/Phase1_Standard_MASW.md` | Detailed Phase 1 implementation |
| Phase 2 Plan | `Plan/Phase2_RollAlong.md` | (Future) |
| Phase 3 Plan | `Plan/Phase3_CMP_CC.md` | (Future) |
| Concepts | `doc/Concepts_Multi_DC/` | Technical concept documentation |

---

## 8. Success Criteria

### Phase 1 Complete When:
- [ ] Package structure created
- [ ] Configuration system working
- [ ] Sub-array extraction functional
- [ ] Batch processing working
- [ ] Standard MASW workflow executable
- [ ] CLI commands operational
- [ ] Basic tests passing
- [ ] Example workflow demonstrated
