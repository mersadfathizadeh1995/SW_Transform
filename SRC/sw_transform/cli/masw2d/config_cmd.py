"""Configuration CLI commands."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def dispatch(args) -> int:
    """Dispatch config subcommand."""
    if args.config_cmd == "generate":
        return cmd_generate(args)
    elif args.config_cmd == "validate":
        return cmd_validate(args)
    elif args.config_cmd == "show":
        return cmd_show(args)
    else:
        print("Unknown config command. Use --help for available commands.")
        return 1


def cmd_generate(args) -> int:
    """Generate configuration template."""
    from sw_transform.masw2d.config import generate_standard_masw_template, save_config
    
    # Determine sub-array sizes
    subarray_sizes = args.subarrays
    if subarray_sizes is None:
        subarray_sizes = [args.channels // 2, args.channels]
    
    # Check for --from-dir to auto-populate shots
    shot_files = None
    shot_positions = None
    
    if args.from_dir:
        from sw_transform.io.file_assignment import assign_files
        
        try:
            rows = assign_files([args.from_dir], recursive=False, include_unknown=False)
            if rows:
                shot_files = [str(r.file_path) for r in rows]
                shot_positions = [float(r.offset_m) for r in rows]
                print(f"Found {len(rows)} shot files in {args.from_dir}")
        except Exception as e:
            print(f"Warning: Could not auto-detect shots: {e}")
    
    # Generate template
    template = generate_standard_masw_template(
        n_channels=args.channels,
        dx=args.dx,
        shot_files=shot_files,
        shot_positions=shot_positions,
        subarray_sizes=subarray_sizes,
        survey_name=args.name
    )
    
    # Save
    output_path = Path(args.output)
    save_config(template, output_path, validate=False)
    
    print(f"Generated config: {output_path}")
    print(f"  Survey: {template['survey_name']}")
    print(f"  Array: {template['array']['n_channels']} channels, dx={template['array']['dx']}m")
    print(f"  Sub-arrays: {[c['n_channels'] for c in template['subarray_configs']]}")
    print(f"  Shots: {len(template['shots'])}")
    
    if not template['shots']:
        print("\n  NOTE: No shots defined. Edit the config to add shot files and positions.")
    
    return 0


def cmd_validate(args) -> int:
    """Validate configuration file."""
    from sw_transform.masw2d.config.schema import validate_config, validate_shot_files_exist
    from sw_transform.masw2d.config.loader import load_config
    
    config_path = Path(args.config)
    
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        return 1
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
        return 1
    
    # Validate schema
    valid, errors = validate_config(config)
    
    if valid:
        print(f"✓ Config is valid: {config_path}")
    else:
        print(f"✗ Config has errors:")
        for e in errors:
            print(f"  - {e}")
        return 1
    
    # Check files if requested
    if args.check_files:
        files_exist, missing = validate_shot_files_exist(config)
        if files_exist:
            print(f"✓ All {len(config['shots'])} shot files exist")
        else:
            print(f"✗ Missing shot files:")
            for f in missing:
                print(f"  - {f}")
            return 1
    
    return 0


def cmd_show(args) -> int:
    """Display configuration contents."""
    config_path = Path(args.config)
    
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        return 1
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
        return 1
    
    print(json.dumps(config, indent=2))
    return 0
