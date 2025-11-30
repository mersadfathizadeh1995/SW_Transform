# Phase 1: Standard MASW Implementation Plan

## Fixed Array with Multiple Source Offsets + Variable Sub-Arrays

---

## 1. Phase 1 Scope

### 1.1 What We're Building

**Standard MASW Scenario:**
- Array is deployed at a FIXED location
- Multiple shots at different source offsets (exterior shots)
- Extract multiple sub-arrays from each shot
- Support variable sub-array sizes (our innovation)
- Generate multiple dispersion curves at different midpoints

### 1.2 What's NOT in Phase 1

- Moving array (roll-along) - Phase 2
- Interior shot handling - Phase 2
- CMP cross-correlation - Phase 3
- Inversion - Future

### 1.3 Deliverables

1. Package structure (all folders created)
2. Configuration system (load, validate, templates)
3. Geometry module (shot classification, sub-array definition)
4. Sub-array extractor
5. Batch processor
6. Standard MASW workflow
7. CLI commands for Phase 1
8. Basic tests
9. Example demonstration

---

## 2. Implementation Tasks

### Task 1: Create Package Structure

**Create all directories:**

```
sw_transform/masw2d/
├── __init__.py
├── config/
│   ├── __init__.py
│   ├── schema.py
│   ├── loader.py
│   └── templates.py
├── geometry/
│   ├── __init__.py
│   ├── shot_classifier.py
│   ├── subarray.py
│   └── midpoint.py
├── extraction/
│   ├── __init__.py
│   └── subarray_extractor.py
├── processing/
│   ├── __init__.py
│   ├── batch_processor.py
│   ├── dc_manager.py
│   └── quality.py
├── workflows/
│   ├── __init__.py
│   ├── base.py
│   └── standard_masw.py
└── output/
    ├── __init__.py
    ├── organizer.py
    ├── merger.py
    └── export.py

sw_transform/cli/masw2d/
├── __init__.py
├── main.py
├── config_cmd.py
├── extract_cmd.py
├── process_cmd.py
├── workflow_cmd.py
└── info_cmd.py
```

**Estimated effort:** 1-2 hours (structure only, minimal code)

---

### Task 2: Configuration System

#### 2.1 schema.py

```python
"""Configuration schema definitions."""

SURVEY_CONFIG_SCHEMA = {
    "survey_name": str,
    "array": {
        "n_channels": int,
        "dx": float,
        "first_channel_position": float  # default: 0.0
    },
    "shots": [
        {
            "file": str,
            "source_position": float,
            "label": str  # optional
        }
    ],
    "subarray_configs": [
        {
            "n_channels": int,
            "slide_step": int,  # default: 1
            "name": str  # optional
        }
    ],
    "processing": {
        "method": str,  # "fk", "ps", "fdbf", "ss"
        "freq_min": float,
        "freq_max": float,
        "velocity_min": float,
        "velocity_max": float
        # ... other processing params
    },
    "output": {
        "directory": str,
        "organize_by": str,  # "midpoint", "shot", "flat"
        "export_formats": list  # ["csv", "npz"]
    }
}

def validate_config(config: dict) -> tuple[bool, list[str]]:
    """Validate configuration against schema."""
    errors = []
    # ... validation logic
    return len(errors) == 0, errors
```

#### 2.2 loader.py

```python
"""Configuration loading and saving."""

import json
from pathlib import Path
from .schema import validate_config

def load_config(path: str | Path) -> dict:
    """Load and validate survey configuration."""
    with open(path) as f:
        config = json.load(f)
    
    valid, errors = validate_config(config)
    if not valid:
        raise ValueError(f"Invalid config: {errors}")
    
    return apply_defaults(config)

def save_config(config: dict, path: str | Path) -> None:
    """Save configuration to file."""
    with open(path, 'w') as f:
        json.dump(config, f, indent=2)

def apply_defaults(config: dict) -> dict:
    """Apply default values for optional fields."""
    # ... set defaults
    return config
```

#### 2.3 templates.py

```python
"""Configuration templates for common scenarios."""

def generate_standard_masw_template(
    n_channels: int = 24,
    dx: float = 2.0,
    shot_files: list[str] = None,
    shot_positions: list[float] = None
) -> dict:
    """Generate template for standard MASW survey."""
    
    template = {
        "survey_name": "Standard_MASW_Survey",
        "version": "1.0",
        
        "array": {
            "n_channels": n_channels,
            "dx": dx,
            "first_channel_position": 0.0
        },
        
        "shots": [],
        
        "subarray_configs": [
            {"n_channels": 12, "slide_step": 1, "name": "shallow"},
            {"n_channels": n_channels, "slide_step": 1, "name": "deep"}
        ],
        
        "processing": {
            "method": "ps",
            "freq_min": 5.0,
            "freq_max": 80.0,
            "velocity_min": 100.0,
            "velocity_max": 1500.0,
            "grid_n": 4000
        },
        
        "output": {
            "directory": "./output_2d/",
            "organize_by": "midpoint",
            "export_formats": ["csv", "npz"]
        }
    }
    
    # Add shots if provided
    if shot_files and shot_positions:
        for f, pos in zip(shot_files, shot_positions):
            template["shots"].append({
                "file": f,
                "source_position": pos
            })
    
    return template
```

**Estimated effort:** 3-4 hours

---

### Task 3: Geometry Module

#### 3.1 shot_classifier.py

```python
"""Shot classification based on position relative to array."""

from enum import Enum
from dataclasses import dataclass

class ShotType(Enum):
    EXTERIOR_LEFT = "exterior_left"
    EXTERIOR_RIGHT = "exterior_right"
    EDGE_LEFT = "edge_left"
    EDGE_RIGHT = "edge_right"
    INTERIOR = "interior"

@dataclass
class ShotInfo:
    file: str
    source_position: float
    shot_type: ShotType
    label: str = ""

def classify_shot(
    source_position: float,
    array_start: float,
    array_end: float,
    tolerance: float = 0.01
) -> ShotType:
    """
    Classify shot based on position relative to array.
    
    Parameters
    ----------
    source_position : float
        Position of the source (m)
    array_start : float
        Position of first geophone (m)
    array_end : float
        Position of last geophone (m)
    tolerance : float
        Tolerance for edge detection (m)
    
    Returns
    -------
    ShotType
        Classification of the shot
    """
    if abs(source_position - array_start) < tolerance:
        return ShotType.EDGE_LEFT
    elif abs(source_position - array_end) < tolerance:
        return ShotType.EDGE_RIGHT
    elif source_position < array_start:
        return ShotType.EXTERIOR_LEFT
    elif source_position > array_end:
        return ShotType.EXTERIOR_RIGHT
    else:
        return ShotType.INTERIOR

def classify_all_shots(shots: list[dict], array_config: dict) -> list[ShotInfo]:
    """Classify all shots in a survey."""
    array_start = array_config["first_channel_position"]
    array_end = array_start + (array_config["n_channels"] - 1) * array_config["dx"]
    
    results = []
    for shot in shots:
        shot_type = classify_shot(
            shot["source_position"],
            array_start,
            array_end
        )
        results.append(ShotInfo(
            file=shot["file"],
            source_position=shot["source_position"],
            shot_type=shot_type,
            label=shot.get("label", "")
        ))
    
    return results
```

#### 3.2 subarray.py

```python
"""Sub-array definition and enumeration."""

from dataclasses import dataclass
from typing import Iterator

@dataclass
class SubArrayDef:
    """Definition of a sub-array."""
    start_channel: int      # 0-indexed
    end_channel: int        # exclusive
    n_channels: int
    start_position: float   # meters
    end_position: float     # meters
    midpoint: float         # meters
    config_name: str        # e.g., "shallow", "deep"

def enumerate_subarrays(
    total_channels: int,
    subarray_n_channels: int,
    dx: float,
    first_position: float = 0.0,
    slide_step: int = 1,
    config_name: str = ""
) -> list[SubArrayDef]:
    """
    Enumerate all possible sub-arrays for a given configuration.
    
    Parameters
    ----------
    total_channels : int
        Total channels in array
    subarray_n_channels : int
        Channels per sub-array
    dx : float
        Geophone spacing (m)
    first_position : float
        Position of first geophone (m)
    slide_step : int
        Step size for sliding (in channels)
    config_name : str
        Name for this configuration
    
    Returns
    -------
    list[SubArrayDef]
        All possible sub-arrays
    """
    subarrays = []
    
    n_possible = (total_channels - subarray_n_channels) // slide_step + 1
    
    for i in range(n_possible):
        start_ch = i * slide_step
        end_ch = start_ch + subarray_n_channels
        
        start_pos = first_position + start_ch * dx
        end_pos = first_position + (end_ch - 1) * dx
        midpoint = (start_pos + end_pos) / 2.0
        
        subarrays.append(SubArrayDef(
            start_channel=start_ch,
            end_channel=end_ch,
            n_channels=subarray_n_channels,
            start_position=start_pos,
            end_position=end_pos,
            midpoint=midpoint,
            config_name=config_name
        ))
    
    return subarrays

def get_all_subarrays_from_config(config: dict) -> dict[str, list[SubArrayDef]]:
    """
    Get all sub-arrays for all configurations in survey config.
    
    Returns dict mapping config_name to list of SubArrayDefs.
    """
    array = config["array"]
    result = {}
    
    for sa_config in config["subarray_configs"]:
        name = sa_config.get("name", f"{sa_config['n_channels']}ch")
        subarrays = enumerate_subarrays(
            total_channels=array["n_channels"],
            subarray_n_channels=sa_config["n_channels"],
            dx=array["dx"],
            first_position=array.get("first_channel_position", 0.0),
            slide_step=sa_config.get("slide_step", 1),
            config_name=name
        )
        result[name] = subarrays
    
    return result
```

#### 3.3 midpoint.py

```python
"""Midpoint and offset calculations."""

from .subarray import SubArrayDef
from .shot_classifier import ShotInfo, ShotType

def calculate_source_offset(
    shot: ShotInfo,
    subarray: SubArrayDef
) -> tuple[float, str]:
    """
    Calculate source offset for a sub-array.
    
    Returns (offset, direction) where direction is "forward" or "reverse".
    """
    if shot.shot_type in (ShotType.EXTERIOR_LEFT, ShotType.EDGE_LEFT):
        # Source is before the sub-array (forward shot)
        offset = subarray.start_position - shot.source_position
        direction = "forward"
    elif shot.shot_type in (ShotType.EXTERIOR_RIGHT, ShotType.EDGE_RIGHT):
        # Source is after the sub-array (reverse shot)
        offset = shot.source_position - subarray.end_position
        direction = "reverse"
    else:
        # Interior shot - needs special handling (Phase 2)
        raise ValueError("Interior shots not supported in Phase 1")
    
    return abs(offset), direction

def is_valid_offset(
    offset: float,
    subarray_length: float,
    min_ratio: float = 0.3,
    max_ratio: float = 2.0
) -> bool:
    """
    Check if source offset is within acceptable range.
    
    Recommended: offset ≈ L/2, acceptable range: 0.3L to 2L
    """
    ratio = offset / subarray_length
    return min_ratio <= ratio <= max_ratio
```

**Estimated effort:** 4-5 hours

---

### Task 4: Sub-Array Extractor

#### extraction/subarray_extractor.py

```python
"""Extract sub-array data from shot gathers."""

import numpy as np
from dataclasses import dataclass
from typing import Optional

from ..geometry.subarray import SubArrayDef
from ..geometry.shot_classifier import ShotInfo, ShotType
from ..geometry.midpoint import calculate_source_offset

@dataclass
class ExtractedSubArray:
    """Extracted sub-array data with metadata."""
    data: np.ndarray              # shape: (n_samples, n_channels)
    time: np.ndarray              # time vector
    dt: float                     # sampling interval
    dx: float                     # geophone spacing
    
    subarray_def: SubArrayDef     # sub-array definition
    shot_info: ShotInfo           # shot information
    source_offset: float          # calculated offset
    direction: str                # "forward" or "reverse"

def extract_subarray(
    shot_data: np.ndarray,
    time: np.ndarray,
    dt: float,
    dx: float,
    subarray_def: SubArrayDef,
    shot_info: ShotInfo,
    reverse_if_needed: bool = True
) -> ExtractedSubArray:
    """
    Extract sub-array from shot gather.
    
    Parameters
    ----------
    shot_data : np.ndarray
        Full shot gather, shape (n_samples, n_total_channels)
    time : np.ndarray
        Time vector
    dt : float
        Sampling interval
    dx : float
        Geophone spacing
    subarray_def : SubArrayDef
        Sub-array definition
    shot_info : ShotInfo
        Shot information
    reverse_if_needed : bool
        If True, flip channel order for reverse shots
    
    Returns
    -------
    ExtractedSubArray
        Extracted data with metadata
    """
    # Extract channels
    start_ch = subarray_def.start_channel
    end_ch = subarray_def.end_channel
    sub_data = shot_data[:, start_ch:end_ch].copy()
    
    # Calculate offset
    offset, direction = calculate_source_offset(shot_info, subarray_def)
    
    # Reverse channel order for reverse shots if requested
    if reverse_if_needed and direction == "reverse":
        sub_data = np.fliplr(sub_data)
    
    return ExtractedSubArray(
        data=sub_data,
        time=time,
        dt=dt,
        dx=dx,
        subarray_def=subarray_def,
        shot_info=shot_info,
        source_offset=offset,
        direction=direction
    )

def extract_all_subarrays_from_shot(
    shot_data: np.ndarray,
    time: np.ndarray,
    dt: float,
    dx: float,
    shot_info: ShotInfo,
    subarray_defs: list[SubArrayDef],
    min_offset_ratio: float = 0.3,
    max_offset_ratio: float = 2.0
) -> list[ExtractedSubArray]:
    """
    Extract all valid sub-arrays from a single shot.
    
    Filters by offset quality.
    """
    results = []
    
    for sa_def in subarray_defs:
        try:
            extracted = extract_subarray(
                shot_data, time, dt, dx, sa_def, shot_info
            )
            
            # Check offset quality
            sa_length = (sa_def.n_channels - 1) * dx
            ratio = extracted.source_offset / sa_length
            
            if min_offset_ratio <= ratio <= max_offset_ratio:
                results.append(extracted)
                
        except ValueError:
            # Skip interior shots for now
            continue
    
    return results
```

**Estimated effort:** 3-4 hours

---

### Task 5: Batch Processor

#### processing/batch_processor.py

```python
"""Batch processing of sub-arrays for dispersion curves."""

from dataclasses import dataclass
from typing import Callable, Optional
import numpy as np

from ..extraction.subarray_extractor import ExtractedSubArray
from sw_transform.processing.registry import get_method

@dataclass
class DispersionResult:
    """Result from dispersion analysis."""
    frequencies: np.ndarray
    velocities: np.ndarray
    power: np.ndarray
    
    # Metadata
    midpoint: float
    subarray_config: str
    shot_file: str
    source_offset: float
    direction: str
    
    # Quality metrics
    peak_values: Optional[np.ndarray] = None

def process_subarray(
    extracted: ExtractedSubArray,
    method: str = "ps",
    freq_min: float = 5.0,
    freq_max: float = 80.0,
    velocity_min: float = 100.0,
    velocity_max: float = 1500.0,
    grid_n: int = 4000,
    **kwargs
) -> DispersionResult:
    """
    Process a single extracted sub-array to get dispersion curve.
    
    Uses existing SW_Transform processing methods.
    """
    # Get the transform function
    transform_func = get_method(method)
    
    # Run transform
    # (Adapt to your existing interface)
    freqs, vels, power = transform_func(
        extracted.data,
        extracted.dt,
        extracted.dx,
        freq_min=freq_min,
        freq_max=freq_max,
        v_min=velocity_min,
        v_max=velocity_max,
        grid_n=grid_n,
        **kwargs
    )
    
    return DispersionResult(
        frequencies=freqs,
        velocities=vels,
        power=power,
        midpoint=extracted.subarray_def.midpoint,
        subarray_config=extracted.subarray_def.config_name,
        shot_file=extracted.shot_info.file,
        source_offset=extracted.source_offset,
        direction=extracted.direction
    )

def process_batch(
    extracted_list: list[ExtractedSubArray],
    method: str = "ps",
    processing_params: dict = None,
    progress_callback: Callable = None
) -> list[DispersionResult]:
    """
    Process multiple sub-arrays.
    
    Parameters
    ----------
    extracted_list : list[ExtractedSubArray]
        List of extracted sub-arrays
    method : str
        Processing method
    processing_params : dict
        Processing parameters
    progress_callback : callable
        Optional callback(current, total) for progress
    
    Returns
    -------
    list[DispersionResult]
        Results for each sub-array
    """
    params = processing_params or {}
    results = []
    total = len(extracted_list)
    
    for i, extracted in enumerate(extracted_list):
        result = process_subarray(extracted, method=method, **params)
        results.append(result)
        
        if progress_callback:
            progress_callback(i + 1, total)
    
    return results
```

**Estimated effort:** 3-4 hours

---

### Task 6: Standard MASW Workflow

#### workflows/standard_masw.py

```python
"""Standard MASW workflow: Fixed array with multiple source offsets."""

from pathlib import Path
from typing import Optional
import json

from .base import BaseWorkflow
from ..config.loader import load_config
from ..geometry.shot_classifier import classify_all_shots, ShotType
from ..geometry.subarray import get_all_subarrays_from_config
from ..extraction.subarray_extractor import extract_all_subarrays_from_shot
from ..processing.batch_processor import process_batch
from ..output.organizer import organize_results

# Import existing seg2 loader
from sw_transform.processing.seg2 import load_seg2_ar

class StandardMASWWorkflow:
    """
    Workflow for standard MASW with fixed array and multiple shots.
    
    Steps:
    1. Load configuration
    2. Classify all shots
    3. Define sub-arrays
    4. For each shot:
       a. Load data
       b. Extract all valid sub-arrays
       c. Process each sub-array
    5. Organize and save results
    """
    
    def __init__(self, config_path: str):
        self.config = load_config(config_path)
        self.config_path = config_path
        
    def run(
        self,
        output_dir: Optional[str] = None,
        progress_callback=None
    ) -> dict:
        """
        Execute the workflow.
        
        Returns summary dict with results.
        """
        output_dir = output_dir or self.config["output"]["directory"]
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Step 1: Classify shots
        shots = classify_all_shots(
            self.config["shots"],
            self.config["array"]
        )
        
        # Filter to exterior shots only (Phase 1)
        exterior_shots = [
            s for s in shots 
            if s.shot_type in (ShotType.EXTERIOR_LEFT, ShotType.EXTERIOR_RIGHT)
        ]
        
        if not exterior_shots:
            raise ValueError("No exterior shots found in configuration")
        
        # Step 2: Define sub-arrays
        subarray_configs = get_all_subarrays_from_config(self.config)
        
        # Flatten all sub-array definitions
        all_subarrays = []
        for config_name, sa_list in subarray_configs.items():
            all_subarrays.extend(sa_list)
        
        # Step 3: Process each shot
        all_results = []
        array_cfg = self.config["array"]
        proc_params = self.config.get("processing", {})
        
        total_shots = len(exterior_shots)
        
        for shot_idx, shot in enumerate(exterior_shots):
            # Load shot data
            time, data, _, dx, dt, _ = load_seg2_ar(shot.file)
            
            # Extract all valid sub-arrays
            extracted = extract_all_subarrays_from_shot(
                data, time, dt, array_cfg["dx"],
                shot, all_subarrays
            )
            
            # Process
            results = process_batch(
                extracted,
                method=proc_params.get("method", "ps"),
                processing_params=proc_params
            )
            
            all_results.extend(results)
            
            if progress_callback:
                progress_callback(shot_idx + 1, total_shots)
        
        # Step 4: Organize results
        summary = organize_results(
            all_results,
            output_dir,
            organize_by=self.config["output"].get("organize_by", "midpoint"),
            export_formats=self.config["output"].get("export_formats", ["csv"])
        )
        
        return summary
```

**Estimated effort:** 4-5 hours

---

### Task 7: CLI Commands

#### cli/masw2d/main.py

```python
"""Main entry point for MASW 2D CLI."""

import argparse
import sys

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="masw2d",
        description="MASW 2D Processing Tools"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Config commands
    config_parser = subparsers.add_parser("config", help="Configuration tools")
    config_sub = config_parser.add_subparsers(dest="config_cmd")
    
    gen_parser = config_sub.add_parser("generate", help="Generate config template")
    gen_parser.add_argument("--output", "-o", required=True, help="Output file")
    gen_parser.add_argument("--channels", "-n", type=int, default=24)
    gen_parser.add_argument("--dx", type=float, default=2.0)
    
    val_parser = config_sub.add_parser("validate", help="Validate config")
    val_parser.add_argument("config", help="Config file to validate")
    
    # Info commands
    info_parser = subparsers.add_parser("info", help="Survey information")
    info_sub = info_parser.add_subparsers(dest="info_cmd")
    
    geom_parser = info_sub.add_parser("geometry", help="Show geometry")
    geom_parser.add_argument("config", help="Config file")
    
    shots_parser = info_sub.add_parser("shots", help="List shots")
    shots_parser.add_argument("config", help="Config file")
    
    sa_parser = info_sub.add_parser("subarrays", help="Show sub-arrays")
    sa_parser.add_argument("config", help="Config file")
    
    # Workflow commands
    wf_parser = subparsers.add_parser("workflow", help="Execute workflows")
    wf_sub = wf_parser.add_subparsers(dest="workflow_cmd")
    
    run_parser = wf_sub.add_parser("run", help="Run workflow")
    run_parser.add_argument("config", help="Config file")
    run_parser.add_argument("--output", "-o", help="Output directory")
    run_parser.add_argument("--type", "-t", default="standard",
                           choices=["standard", "custom"])
    
    list_parser = wf_sub.add_parser("list", help="List workflows")
    
    # Parse and dispatch
    args = parser.parse_args(argv)
    
    if args.command == "config":
        from . import config_cmd
        return config_cmd.dispatch(args)
    elif args.command == "info":
        from . import info_cmd
        return info_cmd.dispatch(args)
    elif args.command == "workflow":
        from . import workflow_cmd
        return workflow_cmd.dispatch(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

**Estimated effort:** 4-5 hours (all CLI commands)

---

## 3. File Summary

### Files to Create (Phase 1)

| Path | Purpose | Priority |
|------|---------|----------|
| `masw2d/__init__.py` | Package init | High |
| `masw2d/config/__init__.py` | Config module init | High |
| `masw2d/config/schema.py` | Config validation | High |
| `masw2d/config/loader.py` | Config loading | High |
| `masw2d/config/templates.py` | Config templates | High |
| `masw2d/geometry/__init__.py` | Geometry init | High |
| `masw2d/geometry/shot_classifier.py` | Shot classification | High |
| `masw2d/geometry/subarray.py` | Sub-array definition | High |
| `masw2d/geometry/midpoint.py` | Midpoint calculations | High |
| `masw2d/extraction/__init__.py` | Extraction init | High |
| `masw2d/extraction/subarray_extractor.py` | Sub-array extraction | High |
| `masw2d/processing/__init__.py` | Processing init | High |
| `masw2d/processing/batch_processor.py` | Batch processing | High |
| `masw2d/processing/dc_manager.py` | DC management | Medium |
| `masw2d/processing/quality.py` | Quality metrics | Medium |
| `masw2d/workflows/__init__.py` | Workflows init | High |
| `masw2d/workflows/base.py` | Base workflow | High |
| `masw2d/workflows/standard_masw.py` | Standard workflow | High |
| `masw2d/output/__init__.py` | Output init | High |
| `masw2d/output/organizer.py` | Result organization | High |
| `masw2d/output/merger.py` | DC merging | Medium |
| `masw2d/output/export.py` | Export functions | High |
| `cli/masw2d/__init__.py` | CLI init | High |
| `cli/masw2d/main.py` | CLI entry point | High |
| `cli/masw2d/config_cmd.py` | Config commands | High |
| `cli/masw2d/info_cmd.py` | Info commands | High |
| `cli/masw2d/workflow_cmd.py` | Workflow commands | High |
| `cli/masw2d/extract_cmd.py` | Extract commands | Medium |
| `cli/masw2d/process_cmd.py` | Process commands | Medium |

### Total: 29 files

---

## 4. Estimated Timeline

| Task | Effort | Dependencies |
|------|--------|--------------|
| Task 1: Structure | 1-2 hours | None |
| Task 2: Config | 3-4 hours | Task 1 |
| Task 3: Geometry | 4-5 hours | Task 1 |
| Task 4: Extractor | 3-4 hours | Tasks 2, 3 |
| Task 5: Batch Processor | 3-4 hours | Task 4 |
| Task 6: Workflow | 4-5 hours | Tasks 4, 5 |
| Task 7: CLI | 4-5 hours | Tasks 2, 6 |
| Testing & Debug | 3-4 hours | All |

**Total estimated: 25-33 hours**

---

## 5. Testing Plan

### Unit Tests
- Config validation
- Shot classification
- Sub-array enumeration
- Midpoint calculations

### Integration Tests
- Full workflow with synthetic data
- CLI command execution

### Manual Tests
- Test with real MASW data
- Verify output organization

---

## 6. Success Criteria

Phase 1 is complete when:

- [ ] All package directories created
- [ ] Config system loads and validates
- [ ] Config templates generate correctly
- [ ] Shot classification works
- [ ] Sub-array enumeration produces correct midpoints
- [ ] Extraction pulls correct channels
- [ ] Batch processing produces dispersion curves
- [ ] Standard workflow runs end-to-end
- [ ] CLI commands work
- [ ] Results organized by midpoint
- [ ] Export to CSV/NPZ works
