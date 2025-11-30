"""Workflow execution CLI commands."""

from __future__ import annotations

import sys
from pathlib import Path


def dispatch(args) -> int:
    """Dispatch workflow subcommand."""
    if args.workflow_cmd == "run":
        return cmd_run(args)
    elif args.workflow_cmd == "list":
        return cmd_list(args)
    else:
        print("Unknown workflow command. Use --help for available commands.")
        return 1


def cmd_run(args) -> int:
    """Run processing workflow."""
    from sw_transform.masw2d.config import load_config
    from sw_transform.masw2d.workflows import StandardMASWWorkflow
    
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        return 1
    
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"Error loading config: {e}")
        return 1
    
    # Override method if specified
    if args.method:
        config["processing"]["method"] = args.method
    
    # Override output settings from CLI
    if "output" not in config:
        config["output"] = {}
    
    if args.images:
        config["output"]["include_images"] = True
    if args.max_velocity:
        config["output"]["max_velocity"] = args.max_velocity
    if args.max_frequency:
        config["output"]["max_frequency"] = args.max_frequency
    
    # Create workflow
    workflow = StandardMASWWorkflow(config)
    
    # Progress callback
    if not args.quiet:
        def progress(current, total, msg):
            print(f"[{current}/{total}] {msg}")
        workflow.set_progress_callback(progress)
    
    # Get info first
    info = workflow.get_info()
    
    if not args.quiet:
        print(f"Starting workflow: {info['survey_name']}")
        print(f"  Shots: {info['n_exterior_shots']}")
        print(f"  Sub-arrays/shot: {info['n_subarrays_per_shot']}")
        print(f"  Expected DCs: {info['expected_results']}")
        print()
    
    # Run
    try:
        results = workflow.run(output_dir=args.output)
    except Exception as e:
        print(f"Error: Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Print results
    if results.get("status") == "success":
        print(f"\n✓ Workflow completed successfully!")
        print(f"  Dispersion curves: {results.get('n_results', 0)}")
        print(f"  Midpoints: {results.get('n_midpoints', 0)}")
        print(f"  Output files: {len(results.get('files', []))}")
        
        if results.get('summary'):
            if results['summary'].get('summary_csv'):
                print(f"  Summary: {results['summary']['summary_csv']}")
        
        return 0
    else:
        print(f"\n✗ Workflow failed")
        if results.get("error"):
            print(f"  Error: {results['error']}")
        return 1


def cmd_list(args) -> int:
    """List available workflows."""
    print("Available workflows:")
    print()
    print("  standard")
    print("    Standard MASW workflow for fixed array with multiple source offsets.")
    print("    - Processes exterior shots only")
    print("    - Extracts configurable sub-arrays")
    print("    - Supports variable sub-array sizes")
    print()
    print("  (Future)")
    print("    roll_along    - Moving array survey")
    print("    refraction    - P-wave refraction data reuse")
    print("    cmp_cc        - CMP cross-correlation method")
    
    return 0
