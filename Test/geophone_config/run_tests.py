"""Run all geophone_config tests.

Usage:
    python run_tests.py           # Run all tests
    python run_tests.py -v        # Verbose output
    python run_tests.py --phase1  # Run only Phase 1 tests
"""

import sys
import os

# Add SRC to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'SRC'))

import pytest

if __name__ == '__main__':
    # Default args
    args = [os.path.dirname(__file__), '-v', '--tb=short']
    
    # Check for phase filter
    if '--phase1' in sys.argv:
        args = [os.path.join(os.path.dirname(__file__), 'test_phase1_array_config.py'), '-v', '--tb=short']
    
    # Pass any extra args
    for arg in sys.argv[1:]:
        if arg not in ['--phase1']:
            args.append(arg)
    
    exit_code = pytest.main(args)
    sys.exit(exit_code)
