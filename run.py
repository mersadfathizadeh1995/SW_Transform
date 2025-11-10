import os
import sys


def _pkg_src_dir() -> str:
    # Respect capitalized SRC per user preference
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "SRC"))


def main() -> None:
    # Prefer the new package GUI wrapper when available
    src = _pkg_src_dir()
    if src not in sys.path:
        sys.path.insert(0, src)
    try:
        # Prefer new simple GUI inside package
        from sw_transform.gui.simple_app import main as gui_main  # type: ignore
        gui_main()
        return
    except Exception:
        # Fallback to legacy path if import fails (first run)
        legacy = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Previous", "4_wave_cursor"))
        if legacy not in sys.path:
            sys.path.insert(0, legacy)
        from gui_app import main as legacy_main  # type: ignore
        legacy_main()


if __name__ == "__main__":
    main()


