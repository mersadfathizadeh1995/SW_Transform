"""
Thin wrapper to launch the legacy GUI from Previous/4_wave_cursor until
the code is fully migrated into the package.
"""

from __future__ import annotations

import os
import sys


def _legacy_gui_path() -> str:
    # Resolve path: SW_Transform/src/sw_transform/gui/ -> up to SW_Transform
    # then into ../Previous/4_wave_cursor
    here = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(here, "..", "..", "..", "..", "Previous", "4_wave_cursor"))


def main() -> None:
    legacy = _legacy_gui_path()
    if legacy not in sys.path:
        sys.path.insert(0, legacy)
    from gui_app import main as legacy_main  # type: ignore
    legacy_main()


if __name__ == "__main__":
    main()



