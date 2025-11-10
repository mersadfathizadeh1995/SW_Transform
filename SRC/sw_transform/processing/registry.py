"""Central registry for methods (FK, FDBF, PS, SS) and reverse policy.

Now points to native implementations inside sw_transform.processing.
"""

from __future__ import annotations

import importlib
from typing import Any, Callable, Dict, Tuple


METHODS: Dict[str, Dict[str, Any]] = {
    "fk": {
        "label": "Frequency–Wavenumber (FK)",
        "step3": ("sw_transform.processing.fk", "fk_transform"),
        "step4": ("sw_transform.processing.fk", "analyze_fk_spectrum"),
        "plot":  ("sw_transform.processing.fk", "plot_freq_velocity_uniform"),
        "plot_kwargs": dict(cmap="jet", nv=400, vmax_plot=5000),
    },
    "fdbf": {
        "label": "Frequency‑Domain Beamformer (FDBF)",
        "step3": ("sw_transform.processing.fdbf", "compute_cross_spectra"),
        "step4": ("sw_transform.processing.fdbf", "fk_analysis_1d"),
        "plot":  ("sw_transform.processing.fdbf", "plot_freq_velocity_spectrum"),
        "plot_kwargs": dict(max_velocity=5000, max_frequency=100.0),
    },
    "ps": {
        "label": "Phase‑Shift (PS)",
        "step3": ("sw_transform.processing.ps", "phase_shift_transform"),
        "step4": ("sw_transform.processing.ps", "analyze_phase_shift"),
        "plot":  ("sw_transform.processing.ps", "plot_phase_shift_dispersion"),
        "plot_kwargs": dict(vmax_plot=5000),
    },
    "ss": {
        "label": "Slant‑Stack (τ–p)",
        "step3": ("sw_transform.processing.ss", "slant_stack_transform"),
        "step4": ("sw_transform.processing.ss", "analyze_slant_stack"),
        "plot":  ("sw_transform.processing.ss", "plot_slant_stack_dispersion"),
        "plot_kwargs": dict(vmax_plot=5000),
    },
}


def dyn(pair: Tuple[str, str]) -> Callable[..., Any]:
    mod, attr = pair
    return getattr(importlib.import_module(mod), attr)


def compute_reverse_flag(user_reverse: bool, method_key: str) -> bool:
    """Apply consistent reverse policy: flip for FK/PS, as in legacy GUI."""
    if method_key in ("fk", "ps"):
        return (not user_reverse)
    return user_reverse


