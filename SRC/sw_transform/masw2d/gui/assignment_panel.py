"""Shot-Subarray Assignment settings panel for the MASW 2D GUI.

Lets the user enable the intelligent assignment engine, choose a strategy,
and configure constraints.  When disabled the legacy exterior-only
behaviour is used.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, Optional


_STRATEGIES = [
    ("Exterior Only (legacy)", "exterior_only"),
    ("Balanced (equal fwd/rev)", "balanced"),
    ("Max Coverage (all valid)", "max_coverage"),
    ("Offset Optimized (best L/2)", "offset_optimized"),
    ("Both Sides Priority", "both_sides_priority"),
]


class AssignmentPanel(ttk.LabelFrame):
    """Panel for configuring the shot-subarray assignment engine."""

    def __init__(
        self,
        parent: tk.Widget,
        on_change: Optional[callable] = None,
        **kw,
    ):
        super().__init__(parent, text="Shot Assignment", padding=6, **kw)
        self._on_change = on_change
        self._create_variables()
        self._build_ui()

    # ------------------------------------------------------------------
    # variables
    # ------------------------------------------------------------------

    def _create_variables(self):
        self.enabled_var = tk.BooleanVar(value=False)
        self.strategy_var = tk.StringVar(value="balanced")

        self.max_offset_enabled_var = tk.BooleanVar(value=True)
        self.max_offset_var = tk.StringVar(value="30.0")

        self.min_offset_var = tk.StringVar(value="0.0")

        self.max_offset_ratio_var = tk.StringVar(value="2.0")
        self.min_offset_ratio_var = tk.StringVar(value="0.0")

        self.max_shots_enabled_var = tk.BooleanVar(value=True)
        self.max_shots_var = tk.StringVar(value="4")

        self.require_both_sides_var = tk.BooleanVar(value=True)
        self.min_shots_per_side_var = tk.StringVar(value="0")
        self.allow_interior_var = tk.BooleanVar(value=False)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Enable toggle
        row0 = ttk.Frame(self)
        row0.pack(fill="x", pady=2)
        ttk.Checkbutton(
            row0,
            text="Enable intelligent assignment",
            variable=self.enabled_var,
            command=self._toggle_state,
        ).pack(side="left")

        # Strategy
        row1 = ttk.Frame(self)
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="Strategy:", width=18).pack(side="left")
        self._strategy_combo = ttk.Combobox(
            row1,
            textvariable=self.strategy_var,
            values=[label for label, _ in _STRATEGIES],
            state="readonly",
            width=26,
        )
        self._strategy_combo.pack(side="left", padx=4)
        self._strategy_combo.current(1)
        self._strategy_combo.bind("<<ComboboxSelected>>", self._on_strategy_display)

        # --- Constraints frame ---
        self._cns_frame = ttk.LabelFrame(self, text="Constraints", padding=4)
        self._cns_frame.pack(fill="x", padx=2, pady=4)

        # Max offset
        r_mo = ttk.Frame(self._cns_frame)
        r_mo.pack(fill="x", pady=1)
        ttk.Checkbutton(r_mo, text="Max offset (m):", variable=self.max_offset_enabled_var).pack(side="left")
        self._max_offset_entry = ttk.Entry(r_mo, textvariable=self.max_offset_var, width=8)
        self._max_offset_entry.pack(side="left", padx=4)

        # Min offset
        r_mino = ttk.Frame(self._cns_frame)
        r_mino.pack(fill="x", pady=1)
        ttk.Label(r_mino, text="Min offset (m):", width=18).pack(side="left")
        ttk.Entry(r_mino, textvariable=self.min_offset_var, width=8).pack(side="left", padx=4)

        # Offset ratio
        r_ratio = ttk.Frame(self._cns_frame)
        r_ratio.pack(fill="x", pady=1)
        ttk.Label(r_ratio, text="Offset/L ratio:").pack(side="left")
        ttk.Entry(r_ratio, textvariable=self.min_offset_ratio_var, width=5).pack(side="left", padx=2)
        ttk.Label(r_ratio, text="–").pack(side="left")
        ttk.Entry(r_ratio, textvariable=self.max_offset_ratio_var, width=5).pack(side="left", padx=2)

        # Max shots per subarray
        r_ms = ttk.Frame(self._cns_frame)
        r_ms.pack(fill="x", pady=1)
        ttk.Checkbutton(r_ms, text="Max shots/subarray:", variable=self.max_shots_enabled_var).pack(side="left")
        self._max_shots_entry = ttk.Entry(r_ms, textvariable=self.max_shots_var, width=5)
        self._max_shots_entry.pack(side="left", padx=4)

        # Both sides + interior
        r_bs = ttk.Frame(self._cns_frame)
        r_bs.pack(fill="x", pady=1)
        ttk.Checkbutton(r_bs, text="Require both sides (fwd+rev)", variable=self.require_both_sides_var).pack(side="left")

        r_mps = ttk.Frame(self._cns_frame)
        r_mps.pack(fill="x", pady=1)
        ttk.Label(r_mps, text="Min shots/side:", width=18).pack(side="left")
        ttk.Entry(r_mps, textvariable=self.min_shots_per_side_var, width=5).pack(side="left", padx=4)

        r_int = ttk.Frame(self._cns_frame)
        r_int.pack(fill="x", pady=1)
        ttk.Checkbutton(r_int, text="Allow interior shots", variable=self.allow_interior_var).pack(side="left")

        self._toggle_state()

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _toggle_state(self):
        enabled = self.enabled_var.get()
        state = "normal" if enabled else "disabled"
        self._strategy_combo.configure(state="readonly" if enabled else "disabled")
        for child in self._cns_frame.winfo_children():
            for w in child.winfo_children():
                try:
                    w.configure(state=state)
                except tk.TclError:
                    pass
        if self._on_change:
            self._on_change()

    def _on_strategy_display(self, _event=None):
        display = self._strategy_combo.get()
        for label, value in _STRATEGIES:
            if label == display:
                self.strategy_var.set(value)
                break
        if self._on_change:
            self._on_change()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_config(self) -> Optional[Dict[str, Any]]:
        """Return the ``assignment`` config dict, or None if disabled."""
        if not self.enabled_var.get():
            return None

        strategy = self.strategy_var.get()

        max_offset = None
        if self.max_offset_enabled_var.get():
            try:
                max_offset = float(self.max_offset_var.get())
            except ValueError:
                max_offset = None

        max_shots = None
        if self.max_shots_enabled_var.get():
            try:
                max_shots = int(self.max_shots_var.get())
            except ValueError:
                max_shots = None

        try:
            min_offset = float(self.min_offset_var.get())
        except ValueError:
            min_offset = 0.0
        try:
            max_offset_ratio = float(self.max_offset_ratio_var.get())
        except ValueError:
            max_offset_ratio = 2.0
        try:
            min_offset_ratio = float(self.min_offset_ratio_var.get())
        except ValueError:
            min_offset_ratio = 0.0
        try:
            min_shots_per_side = int(self.min_shots_per_side_var.get())
        except ValueError:
            min_shots_per_side = 0

        return {
            "strategy": strategy,
            "constraints": {
                "max_offset": max_offset,
                "min_offset": min_offset,
                "max_offset_ratio": max_offset_ratio,
                "min_offset_ratio": min_offset_ratio,
                "max_shots_per_subarray": max_shots,
                "require_both_sides": self.require_both_sides_var.get(),
                "min_shots_per_side": min_shots_per_side,
                "allow_interior_shots": self.allow_interior_var.get(),
            },
        }
