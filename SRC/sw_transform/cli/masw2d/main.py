"""Main CLI entry point for MASW 2D commands."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for MASW 2D CLI.
    
    Parameters
    ----------
    argv : list of str, optional
        Command line arguments (uses sys.argv if not provided)
    
    Returns
    -------
    int
        Exit code (0 for success)
    """
    parser = argparse.ArgumentParser(
        prog="masw2d",
        description="MASW 2D Processing Tools - Extract multiple dispersion curves",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate config template:
    masw2d config generate -o survey.json --channels 24 --dx 2.0
  
  Validate config:
    masw2d config validate survey.json
  
  Show survey info:
    masw2d info geometry survey.json
    masw2d info shots survey.json
  
  Run workflow:
    masw2d workflow run survey.json -o ./output
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # ===== CONFIG COMMANDS =====
    config_parser = subparsers.add_parser("config", help="Configuration tools")
    config_sub = config_parser.add_subparsers(dest="config_cmd")
    
    # config generate
    gen_parser = config_sub.add_parser("generate", help="Generate config template")
    gen_parser.add_argument("--output", "-o", required=True, help="Output JSON file")
    gen_parser.add_argument("--channels", "-n", type=int, default=24, help="Number of channels")
    gen_parser.add_argument("--dx", type=float, default=2.0, help="Geophone spacing (m)")
    gen_parser.add_argument("--name", default="MASW_Survey", help="Survey name")
    gen_parser.add_argument("--subarrays", nargs="+", type=int, help="Sub-array sizes (e.g., 12 24)")
    gen_parser.add_argument("--from-dir", help="Directory with .dat files to auto-populate")
    
    # config validate
    val_parser = config_sub.add_parser("validate", help="Validate config file")
    val_parser.add_argument("config", help="Config file to validate")
    val_parser.add_argument("--check-files", action="store_true", help="Check if shot files exist")
    
    # config show
    show_parser = config_sub.add_parser("show", help="Display config contents")
    show_parser.add_argument("config", help="Config file to display")
    
    # ===== INFO COMMANDS =====
    info_parser = subparsers.add_parser("info", help="Survey information")
    info_sub = info_parser.add_subparsers(dest="info_cmd")
    
    # info geometry
    geom_parser = info_sub.add_parser("geometry", help="Show array geometry")
    geom_parser.add_argument("config", help="Config file")
    
    # info shots
    shots_parser = info_sub.add_parser("shots", help="List shots and classifications")
    shots_parser.add_argument("config", help="Config file")
    
    # info subarrays
    sa_parser = info_sub.add_parser("subarrays", help="Show sub-array definitions")
    sa_parser.add_argument("config", help="Config file")
    sa_parser.add_argument("--config-name", help="Filter by sub-array config name")
    
    # info summary
    summ_parser = info_sub.add_parser("summary", help="Show workflow summary")
    summ_parser.add_argument("config", help="Config file")
    
    # ===== WORKFLOW COMMANDS =====
    wf_parser = subparsers.add_parser("workflow", help="Execute workflows")
    wf_sub = wf_parser.add_subparsers(dest="workflow_cmd")
    
    # workflow run
    run_parser = wf_sub.add_parser("run", help="Run processing workflow")
    run_parser.add_argument("config", help="Config file")
    run_parser.add_argument("--output", "-o", help="Output directory")
    run_parser.add_argument("--method", choices=["fk", "fdbf", "ps", "ss"], help="Override processing method")
    run_parser.add_argument("--images", action="store_true", help="Export dispersion spectrum images")
    run_parser.add_argument("--max-velocity", type=float, default=5000, help="Max velocity for plots (m/s)")
    run_parser.add_argument("--max-frequency", type=float, help="Max frequency for plots (Hz)")
    run_parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress output")
    
    # workflow list
    list_parser = wf_sub.add_parser("list", help="List available workflows")
    
    # Parse arguments
    args = parser.parse_args(argv)
    
    # Dispatch to appropriate handler
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
        return 0


if __name__ == "__main__":
    sys.exit(main())
