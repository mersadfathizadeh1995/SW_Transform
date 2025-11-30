# Flexible Configuration for Various Survey Types

## Handling Standard MASW, P-Wave Refraction, and Mixed Data

---

## 1. Design Philosophy

### 1.1 The Challenge

Different survey types have different geometries:

| Survey Type | Array Size | Shot Locations | Typical Use |
|-------------|------------|----------------|-------------|
| Standard MASW | 24 channels | Outside array (both ends) | Vs profiling |
| P-Wave Refraction | 48+ channels | Along and outside array | Vp profiling, depth to bedrock |
| Mixed Survey | Variable | Multiple configurations | Research |

### 1.2 Our Solution

A **flexible, configurable system** that:
- Accepts any shot-receiver geometry
- Determines valid sub-arrays for each shot
- Handles interior shots (source inside array)
- Optimizes extraction based on data quality criteria

---

## 2. Survey Configuration Schema

### 2.1 General Structure

```json
{
  "survey_name": "Site_A_Investigation",
  "survey_type": "flexible",
  
  "array": {
    "n_channels": 24,
    "dx": 2.0,
    "first_channel_position": 0.0
  },
  
  "shots": [
    {
      "file": "shot_001.dat",
      "source_position": -10.0,
      "type": "standard"
    },
    {
      "file": "shot_002.dat", 
      "source_position": 23.0,
      "type": "interior"
    }
  ],
  
  "processing": {
    "subarray_configs": [
      {"n_channels": 12, "min_offset": 5.0, "max_offset": 30.0},
      {"n_channels": 24, "min_offset": 10.0, "max_offset": 50.0}
    ],
    "interior_shot_handling": "split"
  }
}
```

---

## 3. Shot Classification

### 3.1 Shot Types Based on Position

```
Array: G1 ─────────────────────────────────────── G24
       0m                   23m                   46m
       
Shot Classifications:
─────────────────────────────────────────────────────────────────────
Position        Type        Description
─────────────────────────────────────────────────────────────────────
x < 0           exterior_left    Standard forward shot
x > 46          exterior_right   Standard reverse shot  
0 < x < 46      interior         Shot inside array (special handling)
x = 0 or 46     edge             Shot at array boundary
─────────────────────────────────────────────────────────────────────
```

### 3.2 Automatic Classification

```python
def classify_shot(source_pos, array_start, array_end):
    """Classify shot based on position relative to array."""
    if source_pos < array_start:
        return "exterior_left"
    elif source_pos > array_end:
        return "exterior_right"
    elif source_pos == array_start or source_pos == array_end:
        return "edge"
    else:
        return "interior"
```

---

## 4. Handling Exterior Shots (Standard Case)

### 4.1 Left-Side Exterior Shot (source_pos < 0)

```
Source at -10m:
S ────────────► Array [G1 ... G24]
-10m            0m              46m

All sub-arrays are valid!
Sub-array extraction proceeds normally.
Offset = distance from source to first channel of sub-array.
```

### 4.2 Right-Side Exterior Shot (source_pos > 46m)

```
Array [G1 ... G24] ◄──────────── Source at +56m
0m              46m              56m

All sub-arrays are valid (REVERSED propagation direction)
For processing: Either reverse channel order OR use "reverse" flag
Offset = distance from source to LAST channel of sub-array
```

---

## 5. Handling Interior Shots (Special Case)

### 5.1 The Challenge

When source is INSIDE the array:

```
Array: G1 ─── G8 ─── G12 ─── S ─── G14 ─── G20 ─── G24
       0m    14m    22m    26m    26m     38m     46m
                            ↑
                       Source at 26m
```

**Problem:** Sub-arrays that span the source position have:
- Waves traveling in both directions simultaneously
- Near-field contamination at channels close to source
- Standard processing assumptions violated

### 5.2 Solution 1: Split Processing

Split the array at the source position and process as two separate arrays:

```
Source at 26m:

Left sub-array:  G1 ─── G8 ─── G13    (channels 1-13, positions 0-24m)
                 └──────────────┴──── Source is at RIGHT end
                 Process as "reverse" shot

Right sub-array: G14 ─── G20 ─── G24  (channels 14-24, positions 26-46m)
                 └──────────────┴──── Source is at LEFT end
                 Process as "forward" shot
```

### 5.3 Solution 2: Exclusion Zone

Define an exclusion zone around the source:

```
Source at 26m, exclusion radius = 5m:

Exclusion zone: 21m ─────────── 31m
                      ████████
                      
Valid sub-arrays:
- Must be entirely LEFT of 21m, OR
- Must be entirely RIGHT of 31m
- Sub-arrays spanning 21-31m are SKIPPED
```

### 5.4 Solution 3: Channel Removal

Remove channels within a certain distance of the source:

```
Source at 26m, remove channels within 3m:

Original: G1, G2, G3, ... G12, G13, G14, G15, ... G24
                              ↑   ↑   ↑
                           Remove these (positions 24-28m)
                           
Remaining: G1-G12 (0-22m) and G15-G24 (28-46m)
Process each group as separate short arrays
```

---

## 6. P-Wave Refraction Data Configuration

### 6.1 Typical P-Wave Refraction Geometry

```
48-channel array, dx = 5m, total length = 235m

Shot positions:
- Exterior: -10m, -50m, +245m, +285m (standard refraction shots)
- Interior: Every 5th geophone position (0m, 25m, 50m, ... 235m)

Total shots: ~50+ shot records
```

### 6.2 Configuration for P-Wave Refraction

```json
{
  "survey_name": "Refraction_Line_01",
  "survey_type": "p_wave_refraction",
  
  "array": {
    "n_channels": 48,
    "dx": 5.0,
    "first_channel_position": 0.0
  },
  
  "shots": [
    {"file": "shot_ext_m10.dat", "source_position": -10.0, "type": "exterior"},
    {"file": "shot_ext_m50.dat", "source_position": -50.0, "type": "exterior"},
    {"file": "shot_int_000.dat", "source_position": 0.0, "type": "edge"},
    {"file": "shot_int_025.dat", "source_position": 25.0, "type": "interior"},
    {"file": "shot_int_050.dat", "source_position": 50.0, "type": "interior"}
  ],
  
  "processing": {
    "subarray_configs": [
      {"n_channels": 12, "name": "shallow"},
      {"n_channels": 24, "name": "medium"},
      {"n_channels": 36, "name": "deep"}
    ],
    "interior_shot_handling": "split",
    "exclusion_radius": 10.0,
    "min_subarray_channels": 8
  }
}
```

### 6.3 Processing Strategy for P-Wave Refraction Data

```
For each shot:
    Classify shot type (exterior/interior/edge)
    
    If exterior:
        Extract all sub-arrays normally
        
    If interior (split method):
        Split array at source position
        For left segment:
            Extract sub-arrays (reverse processing)
        For right segment:
            Extract sub-arrays (forward processing)
            
    If edge:
        Process as exterior with source at array end
```

---

## 7. Mixed Survey Handling

### 7.1 Scenario: Standard MASW + Mid-Array Shot

```
Array: 24 channels, 0-46m

Standard MASW shots:
- shot_m05.dat: source at -5m  (exterior)
- shot_m10.dat: source at -10m (exterior)
- shot_p51.dat: source at +51m (exterior)
- shot_p56.dat: source at +56m (exterior)

Additional mid-array shot (originally for refraction or other purpose):
- shot_mid.dat: source at +23m (interior)
```

### 7.2 Configuration

```json
{
  "survey_name": "Mixed_MASW_Refraction",
  
  "array": {
    "n_channels": 24,
    "dx": 2.0
  },
  
  "shot_groups": {
    "standard_masw": {
      "files": ["shot_m05.dat", "shot_m10.dat", "shot_p51.dat", "shot_p56.dat"],
      "processing": "full_subarray_extraction"
    },
    "mid_array": {
      "files": ["shot_mid.dat"],
      "processing": "split_at_source"
    }
  }
}
```

### 7.3 What We Get from Mid-Array Shot

```
Source at 23m:

Left segment: G1-G11 (0-20m), source on right
    Sub-arrays: SA(G1-G8) at midpoint 7m
                SA(G2-G9) at midpoint 9m
                SA(G3-G10) at midpoint 11m
                SA(G4-G11) at midpoint 13m
    Investigation depth: ~7m (limited by segment length)

Right segment: G13-G24 (24-46m), source on left
    Sub-arrays: SA(G13-G20) at midpoint 31m
                SA(G14-G21) at midpoint 33m
                SA(G15-G22) at midpoint 35m
                SA(G16-G23) at midpoint 37m
                SA(G17-G24) at midpoint 39m
    Investigation depth: ~7m

Contribution: Additional DCs at positions 7-13m and 31-39m
              (Complements standard shots which cover 11-35m well)
```

---

## 8. Implementation Design

### 8.1 Processing Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                  FLEXIBLE PROCESSING PIPELINE            │
└─────────────────────────────────────────────────────────┘

1. LOAD CONFIGURATION
   └── Parse survey config JSON
   └── Validate geometry

2. CLASSIFY ALL SHOTS
   └── For each shot file:
       └── Determine type (exterior/interior/edge)
       └── Store classification

3. DETERMINE VALID SUB-ARRAYS
   └── For each shot:
       └── Based on type and config:
           └── List all extractable sub-arrays
           └── Calculate midpoint and offset for each

4. PROCESS SUB-ARRAYS
   └── For each (shot, sub-array) combination:
       └── Extract channel data
       └── Apply preprocessing
       └── Run dispersion transform
       └── Store DC with metadata

5. ORGANIZE OUTPUT
   └── Group by midpoint
   └── Merge/average where appropriate
   └── Generate summary
```

### 8.2 Key Functions

```python
def get_valid_subarrays(shot_info, array_config, subarray_config):
    """
    Determine valid sub-arrays for a given shot.
    
    Returns list of:
    {
        'channels': (start_ch, end_ch),
        'midpoint': float,
        'offset': float,
        'direction': 'forward' or 'reverse'
    }
    """
    
def process_shot_subarrays(shot_data, valid_subarrays, transform_params):
    """
    Process all valid sub-arrays from a shot record.
    
    Returns list of dispersion curves with metadata.
    """
    
def merge_duplicate_midpoints(all_dcs, merge_strategy):
    """
    Combine DCs at same midpoint from different shots/configurations.
    """
```

---

## 9. Advantages of Flexible Configuration

1. **Universality** - Handle any survey geometry
2. **Backward compatible** - Standard MASW is a special case
3. **Data rescue** - Extract MASW from refraction surveys
4. **Research flexibility** - Support non-standard acquisitions
5. **Maximum utilization** - Use all available data

---

## 10. Summary

The flexible configuration system allows processing of:
- Standard MASW (exterior shots)
- Roll-along surveys (multiple array positions)
- P-wave refraction data (interior shots)
- Mixed/hybrid surveys

Key features:
- Automatic shot classification
- Interior shot handling (split, exclude, or remove)
- Variable sub-array configurations
- Configurable processing rules

This design ensures SW_Transform can handle virtually any surface wave data geometry.
