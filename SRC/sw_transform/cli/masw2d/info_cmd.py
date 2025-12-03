"""Information display CLI commands."""

from __future__ import annotations

from pathlib import Path


def dispatch(args) -> int:
    """Dispatch info subcommand."""
    if args.info_cmd == "geometry":
        return cmd_geometry(args)
    elif args.info_cmd == "shots":
        return cmd_shots(args)
    elif args.info_cmd == "subarrays":
        return cmd_subarrays(args)
    elif args.info_cmd == "summary":
        return cmd_summary(args)
    elif args.info_cmd == "layout":
        return cmd_layout(args)
    else:
        print("Unknown info command. Use --help for available commands.")
        return 1


def _load_config(config_path: str):
    """Load config with error handling."""
    from sw_transform.masw2d.config import load_config
    
    path = Path(config_path)
    if not path.exists():
        print(f"Error: Config file not found: {path}")
        return None
    
    try:
        return load_config(path)
    except Exception as e:
        print(f"Error loading config: {e}")
        return None


def cmd_geometry(args) -> int:
    """Show array geometry."""
    config = _load_config(args.config)
    if config is None:
        return 1
    
    from sw_transform.masw2d.geometry import get_array_bounds
    
    array = config["array"]
    start, end = get_array_bounds(array)
    length = end - start
    
    print(f"Array Geometry:")
    print(f"  Channels:     {array['n_channels']}")
    print(f"  Spacing (dx): {array['dx']} m")
    print(f"  Start:        {start} m")
    print(f"  End:          {end} m")
    print(f"  Length:       {length} m")
    print(f"  Midpoint:     {(start + end) / 2} m")
    
    return 0


def cmd_shots(args) -> int:
    """List shots and their classifications."""
    config = _load_config(args.config)
    if config is None:
        return 1
    
    from sw_transform.masw2d.geometry import classify_all_shots
    
    shots = classify_all_shots(config["shots"], config["array"])
    
    print(f"Shots ({len(shots)} total):")
    print(f"{'File':<30} {'Position':>10} {'Type':<15} {'Direction':<10}")
    print("-" * 70)
    
    for s in shots:
        fname = Path(s.file).name
        direction = "forward" if s.is_forward else "reverse" if s.is_reverse else "N/A"
        print(f"{fname:<30} {s.source_position:>+10.1f}m {s.shot_type.value:<15} {direction:<10}")
    
    # Summary
    exterior = sum(1 for s in shots if s.is_exterior)
    interior = sum(1 for s in shots if s.shot_type.value == "interior")
    edge = len(shots) - exterior - interior
    
    print(f"\nSummary:")
    print(f"  Exterior: {exterior}")
    print(f"  Edge:     {edge}")
    print(f"  Interior: {interior}")
    
    if interior > 0:
        print(f"\n  Note: Interior shots require Phase 2 support")
    
    return 0


def cmd_subarrays(args) -> int:
    """Show sub-array definitions."""
    config = _load_config(args.config)
    if config is None:
        return 1
    
    from sw_transform.masw2d.geometry import get_all_subarrays_from_config
    
    all_subarrays = get_all_subarrays_from_config(config)
    
    for config_name, subarrays in all_subarrays.items():
        if args.config_name and config_name != args.config_name:
            continue
        
        print(f"\nConfiguration: {config_name} ({len(subarrays)} sub-arrays)")
        print(f"{'#':<4} {'Channels':<12} {'Position':<16} {'Midpoint':>10} {'Length':>10}")
        print("-" * 55)
        
        for i, sa in enumerate(subarrays):
            ch_range = f"{sa.start_channel}-{sa.end_channel-1}"
            pos_range = f"{sa.start_position:.1f}-{sa.end_position:.1f}m"
            print(f"{i+1:<4} {ch_range:<12} {pos_range:<16} {sa.midpoint:>10.1f}m {sa.length:>10.1f}m")
    
    return 0


def cmd_summary(args) -> int:
    """Show workflow summary without running."""
    config = _load_config(args.config)
    if config is None:
        return 1
    
    from sw_transform.masw2d.workflows import StandardMASWWorkflow
    
    workflow = StandardMASWWorkflow(config)
    info = workflow.get_info()
    
    print(f"Workflow Summary: {info['survey_name']}")
    print("=" * 50)
    print(f"Array:          {info['array']['n_channels']} channels, dx={info['array']['dx']}m")
    print(f"Total shots:    {info['n_total_shots']}")
    print(f"Exterior shots: {info['n_exterior_shots']} (will be processed)")
    print(f"Sub-array configs: {info['n_subarray_configs']}")
    print(f"Sub-arrays/shot:   {info['n_subarrays_per_shot']}")
    print(f"Unique midpoints:  {info['n_unique_midpoints']}")
    print(f"Expected DCs:      {info['expected_results']}")
    print(f"Method:            {info['processing_method']}")
    
    print(f"\nMidpoint positions (m):")
    print(f"  {', '.join(f'{m:.1f}' for m in info['midpoints'])}")
    
    return 0


def cmd_layout(args) -> int:
    """Show layout information for sub-array configurations."""
    from sw_transform.masw2d.geometry.layout import (
        calculate_layout, format_layout_summary
    )
    from sw_transform.masw2d.config.templates import (
        get_available_subarray_sizes, get_all_subarray_info
    )
    
    # Get parameters - either from config or direct args
    if hasattr(args, 'config') and args.config:
        config = _load_config(args.config)
        if config is None:
            return 1
        total_channels = config["array"]["n_channels"]
        dx = config["array"]["dx"]
    else:
        total_channels = getattr(args, 'channels', 24)
        dx = getattr(args, 'dx', 2.0)
    
    subarray_size = getattr(args, 'subarray', None)
    
    # If specific subarray requested, show detailed info
    if subarray_size:
        if subarray_size > total_channels:
            print(f"Error: subarray size ({subarray_size}) > total channels ({total_channels})")
            return 1
        
        layout = calculate_layout(total_channels, dx, subarray_size)
        print(format_layout_summary(layout))
        return 0
    
    # Otherwise show all available configurations
    print(f"Available Sub-Array Configurations")
    print(f"Array: {total_channels} channels, dx={dx}m, total length={(total_channels-1)*dx}m")
    print(f"{'='*70}")
    print(f"{'Channels':>10} {'Length':>10} {'Max Depth':>12} {'# Positions':>12} {'Midpoint Range':>20}")
    print(f"{'-'*70}")
    
    infos = get_all_subarray_info(total_channels, dx, min_channels=6)
    for info in infos:
        mid_range = f"{info['first_midpoint']:.1f} - {info['last_midpoint']:.1f}m"
        print(f"{info['n_channels']:>10} {info['array_length']:>10.1f}m {info['max_depth']:>11.1f}m "
              f"{info['n_midpoints']:>12} {mid_range:>20}")
    
    print(f"\nUse --subarray N for detailed info on a specific configuration.")
    return 0
