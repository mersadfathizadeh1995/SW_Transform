"""Temporary forwarder to legacy worker implementation."""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, Tuple


def _legacy_base() -> str:
    here = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(here, "..", "..", "..", "Previous", "4_wave_cursor"))


def run_compare(params: Dict[str, Any]) -> Tuple[str, bool, str]:
    base = _legacy_base()
    if base not in sys.path:
        sys.path.insert(0, base)
    from workers.compare import run_compare as _run  # type: ignore
    return _run(params)



