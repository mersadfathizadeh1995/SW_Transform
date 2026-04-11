"""Subarray explorer panel: smart placement modes + interactive table."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional

from sw_transform.masw2d.geometry.subarray import SubArrayDef
from sw_transform.masw2d.config.templates import (
    calculate_depth_range,
    generate_subarray_configs_smart,
    get_available_subarray_sizes,
)


class SubarrayExplorerPanel(ttk.LabelFrame):
    """Smart subarray configuration with interactive table.

    Three placement modes:
      * Target midpoint spacing (m)
      * Target midpoint count
      * Manual slide-step (legacy)

    Emits callbacks when the subarray set changes or a row is selected.
    """

    def __init__(
        self,
        parent: tk.Widget,
        n_channels_getter: Optional[Callable[[], int]] = None,
        dx_getter: Optional[Callable[[], float]] = None,
        on_change: Optional[Callable[[], None]] = None,
        on_row_selected: Optional[Callable[[Optional[SubArrayDef]], None]] = None,
        **kwargs: Any,
    ):
        super().__init__(parent, text="Sub-Array Configuration", padding=6, **kwargs)
        self._get_n_channels = n_channels_getter or (lambda: 24)
        self._get_dx = dx_getter or (lambda: 2.0)
        self._on_change = on_change
        self._on_row_selected = on_row_selected

        self._all_subarrays: List[SubArrayDef] = []
        self._configs: List[dict] = []

        self._build_ui()

    def _notify_change(self) -> None:
        if self._on_change:
            self._on_change()

    def _build_ui(self) -> None:
        # --- Size selector ---
        sz_frame = ttk.LabelFrame(self, text="Sizes", padding=4)
        sz_frame.pack(fill="x", pady=2)
        r1 = ttk.Frame(sz_frame)
        r1.pack(fill="x", pady=1)
        ttk.Label(r1, text="Min channels:").pack(side="left")
        self._min_ch_var = tk.StringVar(value="12")
        ttk.Spinbox(r1, from_=6, to=96, textvariable=self._min_ch_var, width=5).pack(
            side="left", padx=4
        )
        ttk.Label(r1, text="Max channels:").pack(side="left", padx=(8, 0))
        self._max_ch_var = tk.StringVar(value="24")
        ttk.Spinbox(r1, from_=6, to=96, textvariable=self._max_ch_var, width=5).pack(
            side="left", padx=4
        )
        r2 = ttk.Frame(sz_frame)
        r2.pack(fill="x", pady=1)
        ttk.Label(r2, text="Step:").pack(side="left")
        self._step_var = tk.StringVar(value="4")
        ttk.Spinbox(r2, from_=1, to=24, textvariable=self._step_var, width=5).pack(
            side="left", padx=4
        )
        ttk.Label(r2, text="ch").pack(side="left")

        # --- Placement mode ---
        mode_frame = ttk.LabelFrame(self, text="Midpoint Placement", padding=4)
        mode_frame.pack(fill="x", pady=4)
        self._mode_var = tk.StringVar(value="spacing")

        rm1 = ttk.Frame(mode_frame)
        rm1.pack(fill="x", pady=1)
        ttk.Radiobutton(
            rm1, text="Target spacing (m):", variable=self._mode_var, value="spacing"
        ).pack(side="left")
        self._spacing_var = tk.StringVar(value="10.0")
        ttk.Entry(rm1, textvariable=self._spacing_var, width=8).pack(side="left", padx=4)

        rm2 = ttk.Frame(mode_frame)
        rm2.pack(fill="x", pady=1)
        ttk.Radiobutton(
            rm2, text="Target count:", variable=self._mode_var, value="count"
        ).pack(side="left")
        self._count_var = tk.StringVar(value="5")
        ttk.Entry(rm2, textvariable=self._count_var, width=8).pack(side="left", padx=4)

        rm3 = ttk.Frame(mode_frame)
        rm3.pack(fill="x", pady=1)
        ttk.Radiobutton(
            rm3, text="Slide step (channels):", variable=self._mode_var, value="slide"
        ).pack(side="left")
        self._slide_var = tk.StringVar(value="1")
        ttk.Entry(rm3, textvariable=self._slide_var, width=8).pack(side="left", padx=4)

        ttk.Button(mode_frame, text="Generate", command=self.generate).pack(
            anchor="w", pady=4
        )

        # --- Subarray table ---
        cols = ("No", "Config", "Channels", "Midpoint_m", "Length_m", "Depth_m")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", height=10)
        self._tree.heading("No", text="#")
        self._tree.heading("Config", text="Config")
        self._tree.heading("Channels", text="Channels")
        self._tree.heading("Midpoint_m", text="Midpoint (m)")
        self._tree.heading("Length_m", text="Length (m)")
        self._tree.heading("Depth_m", text="Depth (m)")
        self._tree.column("No", width=32, stretch=False)
        self._tree.column("Config", width=64)
        self._tree.column("Channels", width=70)
        self._tree.column("Midpoint_m", width=80)
        self._tree.column("Length_m", width=70)
        self._tree.column("Depth_m", width=90)
        self._tree.pack(fill="both", expand=True, pady=4)
        self._tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        info = ttk.Frame(self)
        info.pack(fill="x")
        self._info_var = tk.StringVar(value="No subarrays generated.")
        ttk.Label(info, textvariable=self._info_var, foreground="gray").pack(
            side="left"
        )

    def _on_tree_select(self, _event: tk.Event) -> None:
        sel = self._tree.selection()
        sa = None
        if sel:
            iid = sel[0]
            try:
                idx = int(iid.split("_")[1])
                if 0 <= idx < len(self._all_subarrays):
                    sa = self._all_subarrays[idx]
            except (IndexError, ValueError):
                pass
        if self._on_row_selected:
            self._on_row_selected(sa)

    def generate(self) -> None:
        """(Re-)generate subarrays from current settings."""
        n_ch = self._get_n_channels()
        dx = self._get_dx()
        try:
            mn = int(self._min_ch_var.get())
            mx = int(self._max_ch_var.get())
            st = int(self._step_var.get())
        except ValueError:
            mn, mx, st = 12, n_ch, 4

        mn = max(6, min(mn, n_ch))
        mx = max(mn, min(mx, n_ch))
        st = max(1, st)
        sizes = list(range(mn, mx + 1, st))
        if mx not in sizes:
            sizes.append(mx)
        sizes = sorted(s for s in sizes if 6 <= s <= n_ch)
        if not sizes:
            sizes = [n_ch]

        mode = self._mode_var.get()
        try:
            if mode == "spacing":
                val = float(self._spacing_var.get())
            elif mode == "count":
                val = float(self._count_var.get())
            else:
                val = float(self._slide_var.get())
        except ValueError:
            val = 1.0

        self._configs = generate_subarray_configs_smart(
            sizes, mode, val, n_ch, dx, naming="depth"
        )

        self._all_subarrays = []
        for c in self._configs:
            self._all_subarrays.extend(c.get("_selected_subarrays", []))

        self._refresh_tree()
        self._notify_change()

    def _refresh_tree(self) -> None:
        for iid in self._tree.get_children():
            self._tree.delete(iid)
        for idx, sa in enumerate(self._all_subarrays):
            d_min, d_max = calculate_depth_range(sa.length, "hammer")
            self._tree.insert(
                "",
                "end",
                iid=f"sa_{idx}",
                values=(
                    str(idx + 1),
                    sa.config_name,
                    f"{sa.start_channel}-{sa.end_channel - 1}",
                    f"{sa.midpoint:.2f}",
                    f"{sa.length:.1f}",
                    f"{d_min:.1f}-{d_max:.1f}",
                ),
            )
        n = len(self._all_subarrays)
        n_cfg = len(self._configs)
        self._info_var.set(
            f"{n} subarray(s) across {n_cfg} config(s).  Click a row to preview."
        )

    def get_all_subarrays(self) -> List[SubArrayDef]:
        return list(self._all_subarrays)

    def get_selected_subarray(self) -> Optional[SubArrayDef]:
        sel = self._tree.selection()
        if not sel:
            return None
        try:
            idx = int(sel[0].split("_")[1])
            return self._all_subarrays[idx]
        except (IndexError, ValueError):
            return None

    def get_selected_sizes(self) -> List[int]:
        """Unique channel counts present in the generated set."""
        return sorted({sa.n_channels for sa in self._all_subarrays})

    def get_config_params(self) -> dict:
        """Return the raw GUI values for config building."""
        return {
            "mode": self._mode_var.get(),
            "spacing": self._spacing_var.get(),
            "count": self._count_var.get(),
            "slide": self._slide_var.get(),
            "min_ch": self._min_ch_var.get(),
            "max_ch": self._max_ch_var.get(),
            "step": self._step_var.get(),
        }

    @property
    def slide_step(self) -> int:
        try:
            return int(self._slide_var.get())
        except ValueError:
            return 1

    def get_subarray_configs(self) -> List[dict]:
        """Configs list compatible with the workflow engine."""
        out: List[dict] = []
        for c in self._configs:
            out.append({
                "n_channels": c["n_channels"],
                "slide_step": c["slide_step"],
                "name": c["name"],
            })
        return out

    def update_for_array(self) -> None:
        """Re-clamp max values when array changes."""
        n_ch = self._get_n_channels()
        try:
            mx = int(self._max_ch_var.get())
        except ValueError:
            mx = n_ch
        if mx > n_ch:
            self._max_ch_var.set(str(n_ch))
