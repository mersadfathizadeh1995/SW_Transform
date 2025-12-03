"""Central registry for methods (FK, FDBF, PS, SS) - swprocess-based.

All transforms now use unified interface:
- transform(data, dt, dx, ...) -> (frequencies, velocities, power)
- analyze(freq, vel, power, ...) -> (pnorm, vmax, wavelength, freq)
- plot(freq, vel, pnorm, vmax, ...) -> None
"""

from __future__ import annotations

import importlib
from typing import Any, Callable, Dict, Tuple


METHODS: Dict[str, Dict[str, Any]] = {
    "fk": {
        "label": "Frequency–Wavenumber (FK)",
        "transform": ("sw_transform.processing.fk", "fk_transform"),
        "analyze": ("sw_transform.processing.fk", "analyze_fk_spectrum"),
        "plot": ("sw_transform.processing.fk", "plot_freq_velocity_uniform"),
        "plot_kwargs": dict(cmap="jet", vmax_plot=5000),
        # Legacy aliases for backward compatibility
        "step3": ("sw_transform.processing.fk", "fk_transform"),
        "step4": ("sw_transform.processing.fk", "analyze_fk_spectrum"),
    },
    "fdbf": {
        "label": "Frequency‑Domain Beamformer (FDBF)",
        "transform": ("sw_transform.processing.fdbf", "fdbf_transform"),
        "analyze": ("sw_transform.processing.fdbf", "analyze_fdbf_spectrum"),
        "plot": ("sw_transform.processing.fdbf", "plot_fdbf_dispersion"),
        "plot_kwargs": dict(cmap="jet", vmax_plot=5000, max_frequency=100.0),
        # Legacy aliases
        "step3": ("sw_transform.processing.fdbf", "fdbf_transform"),
        "step4": ("sw_transform.processing.fdbf", "analyze_fdbf_spectrum"),
    },
    "ps": {
        "label": "Phase‑Shift (PS)",
        "transform": ("sw_transform.processing.ps", "phase_shift_transform"),
        "analyze": ("sw_transform.processing.ps", "analyze_phase_shift"),
        "plot": ("sw_transform.processing.ps", "plot_phase_shift_dispersion"),
        "plot_kwargs": dict(cmap="jet", vmax_plot=5000),
        # Legacy aliases
        "step3": ("sw_transform.processing.ps", "phase_shift_transform"),
        "step4": ("sw_transform.processing.ps", "analyze_phase_shift"),
    },
    "ss": {
        "label": "Slant‑Stack (τ–p)",
        "transform": ("sw_transform.processing.ss", "slant_stack_transform"),
        "analyze": ("sw_transform.processing.ss", "analyze_slant_stack"),
        "plot": ("sw_transform.processing.ss", "plot_slant_stack_dispersion"),
        "plot_kwargs": dict(cmap="jet", vmax_plot=5000),
        # Legacy aliases
        "step3": ("sw_transform.processing.ss", "slant_stack_transform"),
        "step4": ("sw_transform.processing.ss", "analyze_slant_stack"),
    },
}


def dyn(pair: Tuple[str, str]) -> Callable[..., Any]:
    """Dynamically import and return a function from module.attr tuple."""
    mod, attr = pair
    return getattr(importlib.import_module(mod), attr)


def compute_reverse_flag(user_reverse: bool, method_key: str) -> bool:
    """Apply consistent reverse policy for all methods.
    
    All methods now use the same convention: user's reverse flag is applied directly.
    The steering vectors are adjusted to match swprocess conventions.
    """
    # All methods use the same reversal - no special casing
    return user_reverse


