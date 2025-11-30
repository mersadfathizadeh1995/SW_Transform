"""Allow running as python -m sw_transform.cli.masw2d"""

from .main import main
import sys

if __name__ == "__main__":
    sys.exit(main())
