# Phase 2: Roll-Along Sub-Array Processing

## Moving Array MASW Data Management

---

## 1. Phase 2 Scope

### 1.1 What We're Building

**Roll-Along MASW Scenario:**
- Array MOVES along the survey line between shots
- Each shot record has a different array position
- Need to recompile data to maintain consistent geometry
- Support for both:
  - True roll-along (array physically moves)
  - Shoot-through (fixed array, source moves through)

### 1.2 Prerequisites

- Phase 1 complete (sub-array extraction working)
- Configuration system extended for roll-along

### 1.3 Deliverables

1. Roll-along configuration schema extension
2. Roll-along extractor module
3. Shoot-through recompiler
4. Interior shot handling (split method)
5. Roll-along workflow
6. Extended CLI commands
7. Geometry validation tools

---

## 2. Key Concepts

### 2.1 Roll-Along Acquisition

```
Survey Line
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━►
  0     dx    2dx   3dx   ...                            Distance (m)

Shot 1: S₁──X₁──[G₁ G₂ G₃ G₄ G₅ G₆ ... G_N]
Shot 2:      S₂──X₁──[G₁ G₂ G₃ G₄ G₅ G₆ ... G_N]
Shot 3:           S₃──X₁──[G₁ G₂ G₃ G₄ G₅ G₆ ... G_N]
  ...

Roll increment = dx (or multiples)
```

### 2.2 Geometry Tracking

Each shot record must include:
- `shot_position`: Source location (m)
- `first_receiver_position`: Position of first geophone (m)
- `array_configuration`: Number of channels, spacing

### 2.3 Recompilation Strategy

To create consistent sub-arrays across all shots:
1. Define target geometry (n_channels, source_offset)
2. For each shot, find channel range matching target geometry
3. Extract and align sub-arrays
4. Result: Multiple sub-arrays at different midpoints with identical geometry

---

## 3. Implementation Tasks

### Task 1: Extend Configuration Schema

```python
# New fields for roll-along surveys
ROLL_ALONG_CONFIG = {
    "acquisition_type": "roll_along",  # or "shoot_through"
    "geometry": {
        "dx": 2.0,
        "n_channels": 24,
        "roll_increment": 2.0,  # meters between shots
        "source_offset_nominal": 10.0
    },
    "shots": [
        {
            "file": "shot_001.dat",
            "shot_position": 0.0,
            "first_receiver_position": 10.0  # NEW: array position
        }
    ],
    "recompilation": {
        "target_n_channels": 12,
        "target_source_offset": 10.0,
        "offset_tolerance": 0.5  # meters
    }
}
```

### Task 2: Roll-Along Extractor

```python
# extraction/rollover_extractor.py

def extract_roll_along_subarrays(
    shot_records: List[dict],
    geometry: dict,
    target_subarray_length: int,
    target_source_offset: float
) -> List[ExtractedSubArray]:
    """
    Extract sub-arrays from roll-along data maintaining consistent geometry.
    """
    pass

def recompile_shoot_through_subarrays(
    shot_records: List[dict],
    geometry: dict,
    target_subarray_length: int
) -> List[ExtractedSubArray]:
    """
    Recompile shoot-through data into roll-along format.
    """
    pass
```

### Task 3: Interior Shot Handling

For shots where source is INSIDE the array:
- Split into two sub-arrays (left and right of source)
- Each side processed independently
- Requires careful offset calculation

```python
def handle_interior_shot(
    shot_data: np.ndarray,
    source_channel: int,
    ...
) -> Tuple[ExtractedSubArray, ExtractedSubArray]:
    """Split interior shot into left and right sub-arrays."""
    pass
```

### Task 4: Roll-Along Workflow

```python
# workflows/roll_along.py

class RollAlongWorkflow:
    """Workflow for roll-along MASW surveys."""
    
    def run(self):
        # 1. Load all shot records with positions
        # 2. Validate geometry consistency
        # 3. Recompile to target geometry
        # 4. Process each recompiled sub-array
        # 5. Organize by midpoint
        pass
```

### Task 5: Geometry Validation

```python
def validate_roll_along_geometry(shot_records: List[dict]) -> ValidationResult:
    """
    Check for:
    - Consistent roll increment
    - No gaps in coverage
    - Uniform channel count
    - Source offset consistency
    """
    pass

def plot_roll_along_coverage(shot_records: List[dict]) -> Figure:
    """Visualize array positions and coverage."""
    pass
```

### Task 6: CLI Extensions

```bash
# New commands
masw2d config generate --type roll_along -o config.json
masw2d info coverage config.json  # Show coverage map
masw2d workflow run config.json --type roll_along
```

---

## 4. File Summary

| Path | Purpose |
|------|---------|
| `masw2d/config/schema.py` | Extend for roll-along fields |
| `masw2d/extraction/rollover_extractor.py` | NEW: Roll-along extraction |
| `masw2d/geometry/interior_shot.py` | NEW: Interior shot handling |
| `masw2d/workflows/roll_along.py` | NEW: Roll-along workflow |
| `masw2d/output/coverage.py` | NEW: Coverage visualization |
| `cli/masw2d/coverage_cmd.py` | NEW: Coverage commands |

---

## 5. Estimated Timeline

| Task | Effort |
|------|--------|
| Config extension | 2-3 hours |
| Roll-along extractor | 4-5 hours |
| Shoot-through recompiler | 3-4 hours |
| Interior shot handling | 4-5 hours |
| Roll-along workflow | 3-4 hours |
| Geometry validation | 2-3 hours |
| CLI extensions | 2-3 hours |
| Testing | 3-4 hours |

**Total: 23-31 hours**

---

## 6. Success Criteria

- [ ] Roll-along config loads and validates
- [ ] Recompilation produces consistent geometry
- [ ] Interior shots split correctly
- [ ] Coverage map visualizes survey
- [ ] Roll-along workflow runs end-to-end
- [ ] Results match expected midpoints
