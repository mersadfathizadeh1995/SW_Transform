"""Interactive geometry preview with real geophone data display.

Two modes:
- **Overview**: Array schematic + waterfall of first/selected shot file +
  sub-array rectangles overlay (matches Input tab design).
- **Detail**: Highlighted sub-array channels + selected source position +
  actual waveform data for that sub-array region.
"""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from sw_transform.masw2d.geometry.subarray import SubArrayDef

import matplotlib as mpl
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle


_CLR_GEO_ACTIVE = "#2ca02c"
_CLR_GEO_INACTIVE = "#c0c0c0"
_CLR_SOURCE = "tab:red"
_CLR_FWD = "#4a86c8"
_CLR_REV = "#d4812a"
_CLR_SEL = "#2ca02c"
_CLR_LINE = "#888888"
_CLR_MID = "#b03060"
_CLR_TRACE_ACTIVE = "blue"
_CLR_TRACE_INACTIVE = "lightgray"


class GeometryPreviewPanel(ttk.Frame):
    """Two-mode preview: overview (all geophones + waterfall) and detail
    (single sub-array highlighted with source position).

    The design mirrors the Input tab's preview: top panel shows array
    schematic with green triangles for geophones and red diamond for
    source, bottom panel shows per-trace normalised waterfall.
    """

    def __init__(self, parent: tk.Widget, **kwargs: Any):
        super().__init__(parent, **kwargs)
        self._canvas: Optional[FigureCanvasTkAgg] = None
        self._figure: Optional[Figure] = None

        # Top bar with source selector (detail mode) and overview button
        self._top = ttk.Frame(self)
        self._top.pack(fill="x", padx=4, pady=(2, 0))
        ttk.Label(self._top, text="Source offset:").pack(side="left")
        self._src_var = tk.StringVar()
        self._src_combo = ttk.Combobox(
            self._top, textvariable=self._src_var, state="readonly", width=30
        )
        self._src_combo.pack(side="left", padx=4)
        self._src_combo.bind("<<ComboboxSelected>>", self._on_source_selected)
        self._overview_btn = ttk.Button(
            self._top, text="Show Overview", command=self._request_overview
        )
        self._overview_btn.pack(side="right")
        self._top.pack_forget()

        self._container = ttk.Frame(self)
        self._container.pack(fill="both", expand=True, padx=4, pady=4)

        # State
        self._detail_sa: Optional[SubArrayDef] = None
        self._detail_shots: List[Dict[str, Any]] = []
        self._detail_n_channels = 24
        self._detail_dx = 2.0
        self._selected_shot_idx: Optional[int] = None
        self._on_overview_request: Optional[Callable[[], None]] = None

        # Cached shot data {filepath: (time, data_matrix, dx, dt)}
        self._data_cache: Dict[str, Tuple] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_overview_callback(self, cb: Callable[[], None]) -> None:
        self._on_overview_request = cb

    def clear(self) -> None:
        for w in self._container.winfo_children():
            w.destroy()
        self._canvas = None
        self._figure = None

    # ------------------------------------------------------------------
    # OVERVIEW MODE  (with real data)
    # ------------------------------------------------------------------
    def show_overview(
        self,
        n_channels: int,
        dx: float,
        shot_positions: List[float],
        subarrays: List[SubArrayDef],
        plan: Any = None,
        shot_file: Optional[str] = None,
        shot_source_pos: Optional[float] = None,
    ) -> None:
        """Show overview with array schematic + waterfall of real data.

        If *shot_file* is provided, loads the SEG-2 data and shows a
        waterfall beneath the array schematic (matching Input tab design).
        Falls back to a plan-view layout when no data file is available.
        """
        self._top.pack_forget()
        self._detail_sa = None

        all_positions = np.arange(n_channels, dtype=float) * dx

        # Try loading real data
        time_data, trace_data, file_dx, file_dt = None, None, None, None
        if shot_file and os.path.isfile(shot_file):
            time_data, trace_data, file_dx, file_dt = self._load_shot_data(shot_file)

        if trace_data is not None:
            self._show_data_overview(
                all_positions, n_channels, dx, shot_positions,
                subarrays, plan, time_data, trace_data,
                shot_source_pos, shot_file,
            )
        else:
            self._show_plan_overview(
                all_positions, n_channels, dx, shot_positions,
                subarrays, plan,
            )

    # ------------------------------------------------------------------
    # DETAIL MODE  (sub-array highlighted with real data)
    # ------------------------------------------------------------------
    def show_detail(
        self,
        subarray: SubArrayDef,
        assigned_shots: List[Dict[str, Any]],
        n_channels: int,
        dx: float,
        shot_file: Optional[str] = None,
    ) -> None:
        """Show a single sub-array in detail with highlighted channels."""
        self._detail_sa = subarray
        self._detail_shots = assigned_shots
        self._detail_n_channels = n_channels
        self._detail_dx = dx

        # Top bar with source selector
        self._top.pack(fill="x", padx=4, pady=(2, 0), before=self._container)
        combo_vals = []
        for i, sh in enumerate(assigned_shots):
            pos = sh.get("source_position", 0.0)
            d = sh.get("direction", "?")
            off = sh.get("source_offset", 0.0)
            combo_vals.append(f"#{i}: pos={pos:.1f} m  off={off:.1f} m  ({d})")
        self._src_combo["values"] = combo_vals
        if combo_vals:
            if self._selected_shot_idx is None or self._selected_shot_idx >= len(combo_vals):
                self._selected_shot_idx = 0
            self._src_combo.current(self._selected_shot_idx)
        else:
            self._selected_shot_idx = None

        sa = subarray
        all_positions = np.arange(n_channels, dtype=float) * dx
        sa_channels = set(range(sa.start_channel, sa.end_channel))

        # Determine source position
        sel_idx = self._selected_shot_idx
        src_pos = None
        if sel_idx is not None and sel_idx < len(assigned_shots):
            src_pos = assigned_shots[sel_idx].get("source_position", 0.0)

        # Try to get data file
        data_file = shot_file
        if data_file is None and sel_idx is not None and sel_idx < len(assigned_shots):
            data_file = assigned_shots[sel_idx].get("file")

        time_data, trace_data, _, _ = None, None, None, None
        if data_file and os.path.isfile(data_file):
            time_data, trace_data, _, _ = self._load_shot_data(data_file)

        if trace_data is not None:
            self._show_data_detail(
                all_positions, n_channels, sa, sa_channels,
                assigned_shots, sel_idx, src_pos,
                time_data, trace_data, data_file,
            )
        else:
            self._show_plan_detail(
                all_positions, n_channels, dx, sa, sa_channels,
                assigned_shots, sel_idx, src_pos,
            )

    # ------------------------------------------------------------------
    # Internal: Data loading
    # ------------------------------------------------------------------
    def _load_shot_data(self, filepath: str) -> Tuple:
        """Load SEG-2 or .mat file, returning (time, data, dx, dt) or (None,)*4."""
        if filepath in self._data_cache:
            return self._data_cache[filepath]

        try:
            if filepath.lower().endswith('.mat'):
                from sw_transform.processing.vibrosis import load_vibrosis_mat
                data = load_vibrosis_mat(filepath)
                # For vibrosis, create a pseudo-time-domain representation
                tf_mag = np.abs(data.transfer_functions)  # (nfreq, nchannels)
                result = (data.frequencies, tf_mag, 2.0, None)
            else:
                from sw_transform.processing.seg2 import load_seg2_ar
                time, T, _sp, spacing, dt, _ = load_seg2_ar(filepath)
                result = (time, T, float(spacing), dt)
            self._data_cache[filepath] = result
            return result
        except Exception:
            return (None, None, None, None)

    # ------------------------------------------------------------------
    # Internal: Figure mounting
    # ------------------------------------------------------------------
    def _mount_figure(self, fig: Figure) -> None:
        self.clear()
        self._figure = fig
        self._canvas = FigureCanvasTkAgg(fig, master=self._container)
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Internal: Data-based overview (like Input tab)
    # ------------------------------------------------------------------
    def _show_data_overview(
        self,
        all_positions: np.ndarray,
        n_channels: int,
        dx: float,
        shot_positions: List[float],
        subarrays: List[SubArrayDef],
        plan: Any,
        time_data: np.ndarray,
        trace_data: np.ndarray,
        shot_source_pos: Optional[float],
        shot_file: str,
    ) -> None:
        """Overview with real data waterfall (matches Input tab design)."""
        fig = Figure(figsize=(7.5, 6.5), dpi=100)
        gs = fig.add_gridspec(2, 1, height_ratios=[1, 3], hspace=0.42)
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])

        # --- Top: Array schematic ---
        self._draw_array_schematic(
            ax1, all_positions, n_channels,
            selected_indices=None,
            source_positions=shot_positions,
            subarrays=subarrays,
            plan=plan,
            title=f"Survey Line — {os.path.basename(shot_file)}",
        )

        # --- Bottom: Waterfall of actual traces ---
        self._draw_waterfall(
            ax2, all_positions, time_data, trace_data,
            selected_indices=None,
            is_vibrosis=shot_file.lower().endswith('.mat'),
        )

        fig.tight_layout(rect=[0, 0, 0.88, 1])
        self._mount_figure(fig)

    # ------------------------------------------------------------------
    # Internal: Data-based detail (sub-array highlighted)
    # ------------------------------------------------------------------
    def _show_data_detail(
        self,
        all_positions: np.ndarray,
        n_channels: int,
        sa: SubArrayDef,
        sa_channels: set,
        assigned_shots: List[Dict[str, Any]],
        sel_idx: Optional[int],
        src_pos: Optional[float],
        time_data: np.ndarray,
        trace_data: np.ndarray,
        data_file: str,
    ) -> None:
        """Detail with highlighted sub-array channels + waterfall."""
        fig = Figure(figsize=(7.5, 6.5), dpi=100)
        gs = fig.add_gridspec(2, 1, height_ratios=[1, 3], hspace=0.42)
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])

        selected_indices = sorted(sa_channels)
        shot_positions = [sh.get("source_position", 0.0) for sh in assigned_shots]

        # --- Top: Array schematic with highlighted sub-array ---
        self._draw_array_schematic(
            ax1, all_positions, n_channels,
            selected_indices=selected_indices,
            source_positions=shot_positions,
            highlight_source_idx=sel_idx,
            title=f"Sub-array: {sa.config_name}  (ch {sa.start_channel}–{sa.end_channel - 1})  mid={sa.midpoint:.1f}m",
        )

        # --- Bottom: Waterfall with highlighted channels ---
        self._draw_waterfall(
            ax2, all_positions, time_data, trace_data,
            selected_indices=selected_indices,
            is_vibrosis=data_file.lower().endswith('.mat'),
        )

        fig.tight_layout(rect=[0, 0, 0.88, 1])
        self._mount_figure(fig)

    # ------------------------------------------------------------------
    # Internal: Plan-view overview (no data, geometry only)
    # ------------------------------------------------------------------
    def _show_plan_overview(
        self,
        all_positions: np.ndarray,
        n_channels: int,
        dx: float,
        shot_positions: List[float],
        subarrays: List[SubArrayDef],
        plan: Any,
    ) -> None:
        """Fallback overview when no shot data files are available."""
        fig = Figure(figsize=(7, 5), dpi=100, layout="constrained")
        ax = fig.add_subplot(111)

        self._draw_array_schematic(
            ax, all_positions, n_channels,
            selected_indices=None,
            source_positions=shot_positions,
            subarrays=subarrays,
            plan=plan,
            title="Survey Line (plan view)",
        )

        # Status text below
        n_sa = len(subarrays) if subarrays else 0
        n_sh = len(shot_positions) if shot_positions else 0
        status = f"{n_sa} sub-arrays  |  {n_sh} shot positions"
        if plan and hasattr(plan, 'assignments'):
            status += f"  |  {len(plan.assignments)} assignments"
        ax.text(
            0.5, -0.08, status, transform=ax.transAxes,
            ha="center", fontsize=8.5, color="0.4",
        )

        if not shot_positions and not subarrays:
            ax.text(
                0.5, 0.5, "Add shot files and configure sub-arrays\nto see preview",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=11, color="0.5",
            )

        self._mount_figure(fig)

    # ------------------------------------------------------------------
    # Internal: Plan-view detail (no data, geometry only)
    # ------------------------------------------------------------------
    def _show_plan_detail(
        self,
        all_positions: np.ndarray,
        n_channels: int,
        dx: float,
        sa: SubArrayDef,
        sa_channels: set,
        assigned_shots: List[Dict[str, Any]],
        sel_idx: Optional[int],
        src_pos: Optional[float],
    ) -> None:
        """Fallback detail when no shot data file is available."""
        fig = Figure(figsize=(7, 5), dpi=100, layout="constrained")
        ax = fig.add_subplot(111)

        selected_indices = sorted(sa_channels)
        shot_positions = [sh.get("source_position", 0.0) for sh in assigned_shots]

        self._draw_array_schematic(
            ax, all_positions, n_channels,
            selected_indices=selected_indices,
            source_positions=shot_positions,
            highlight_source_idx=sel_idx,
            title=f"Sub-array: {sa.config_name}  (ch {sa.start_channel}–{sa.end_channel - 1})  mid={sa.midpoint:.1f}m",
        )

        # Info text
        info_parts = [f"Channels: {sa.n_channels}", f"Length: {sa.length:.1f}m"]
        if sel_idx is not None and sel_idx < len(assigned_shots):
            sh = assigned_shots[sel_idx]
            info_parts.append(f"Offset: {sh.get('source_offset', 0.0):.1f}m ({sh.get('direction', '?')})")
        ax.text(
            0.5, -0.08, "  |  ".join(info_parts),
            transform=ax.transAxes, ha="center", fontsize=8.5, color="0.4",
        )

        self._mount_figure(fig)

    # ------------------------------------------------------------------
    # Shared drawing: Array schematic (ported from simple_app.py)
    # ------------------------------------------------------------------
    def _draw_array_schematic(
        self,
        ax,
        all_positions: np.ndarray,
        n_channels: int,
        selected_indices: Optional[List[int]] = None,
        source_positions: Optional[List[float]] = None,
        subarrays: Optional[List[SubArrayDef]] = None,
        plan: Any = None,
        highlight_source_idx: Optional[int] = None,
        title: str = "Array schematic",
    ) -> None:
        """Draw array schematic on given axes.

        - Green triangles for active geophones, gray for inactive
        - Red diamonds for source positions
        - Coloured rectangles for sub-arrays
        """
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.set_xlabel("Distance (m)")
        ax.set_yticks([])

        # Geophones
        if selected_indices is not None and len(selected_indices) > 0:
            sel_set = set(selected_indices)
            inactive_idx = [i for i in range(n_channels) if i not in sel_set]
            if inactive_idx:
                ax.plot(
                    all_positions[inactive_idx],
                    np.zeros(len(inactive_idx)),
                    "^", color=_CLR_GEO_INACTIVE, markersize=6, label="Inactive",
                )
            ax.plot(
                all_positions[list(selected_indices)],
                np.zeros(len(selected_indices)),
                "^", color=_CLR_GEO_ACTIVE, markersize=8, label="Selected",
            )
        else:
            ax.plot(
                all_positions, np.zeros(n_channels),
                "^", color=_CLR_GEO_ACTIVE, markersize=8, label="Sensor",
            )

        # Source positions
        if source_positions:
            for i, sx in enumerate(source_positions):
                if highlight_source_idx is not None and i == highlight_source_idx:
                    ax.plot([sx], [0.0], "D", color=_CLR_SEL, markersize=11, zorder=6)
                else:
                    ax.plot([sx], [0.0], "D", color=_CLR_SOURCE, markersize=10, zorder=5)
                ax.annotate(
                    f"{sx:.1f}m", (sx, 0), xytext=(0, 10),
                    textcoords="offset points", ha="center", fontsize=6.5, color="0.3",
                )
            # Label first source only in legend
            ax.plot([], [], "D", color=_CLR_SOURCE, markersize=8, label="Source")

        # Sub-array rectangles
        if subarrays:
            names: List[str] = []
            for sa in subarrays:
                if sa.config_name not in names:
                    names.append(sa.config_name)
            cycle = mpl.rcParams['axes.prop_cycle']
            colors = [c["color"] for c in list(cycle) * 4]
            y_base = -0.3
            dy = 0.15
            for ni, name in enumerate(names):
                y0 = y_base - ni * dy
                for sa in (s for s in subarrays if s.config_name == name):
                    col = colors[ni % len(colors)]
                    w = sa.end_position - sa.start_position
                    ax.add_patch(Rectangle(
                        (sa.start_position, y0 - 0.04), w, 0.08,
                        fc=col, alpha=0.25, ec=col, lw=0.6,
                    ))
                    ax.plot([sa.midpoint] * 2, [y0 - 0.04, y0 + 0.04], color=col, lw=0.8)

        # Assignment rays
        if plan and hasattr(plan, 'assignments') and plan.assignments:
            y_src = 0.15
            for a in plan.assignments:
                clr = _CLR_FWD if a.direction == "forward" else _CLR_REV
                ax.plot(
                    [a.shot_position, a.midpoint], [y_src, 0],
                    color=clr, lw=0.5, alpha=0.6, ls="--",
                )

        # Axis limits
        x_vals = list(all_positions)
        if source_positions:
            x_vals.extend(source_positions)
        x_lo = min(x_vals) - max(2, abs(min(x_vals)) * 0.05) if x_vals else -1
        x_hi = max(x_vals) + max(2, abs(max(x_vals)) * 0.05) if x_vals else 1
        ax.set_xlim(x_lo, x_hi)
        y_lo = -0.5
        if subarrays:
            n_names = len(set(sa.config_name for sa in subarrays))
            y_lo = min(y_lo, -0.3 - n_names * 0.15 - 0.1)
        ax.set_ylim(y_lo, 0.35)
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, fontsize=7.5)

    # ------------------------------------------------------------------
    # Shared drawing: Waterfall (ported from simple_app.py)
    # ------------------------------------------------------------------
    def _draw_waterfall(
        self,
        ax,
        all_positions: np.ndarray,
        time_data: np.ndarray,
        trace_data: np.ndarray,
        selected_indices: Optional[List[int]] = None,
        is_vibrosis: bool = False,
    ) -> None:
        """Draw per-trace normalised waterfall (matches Input tab design)."""
        n_channels = trace_data.shape[1] if trace_data.ndim == 2 else trace_data.shape[0]

        # Transpose if needed: we want (n_samples, n_channels)
        if trace_data.ndim == 2 and trace_data.shape[0] == n_channels:
            trace_data = trace_data.T

        traces = trace_data.copy().T  # (n_channels, n_samples)
        denom = np.max(np.abs(traces), axis=1, keepdims=True)
        denom[denom == 0] = 1.0
        traces = traces / denom

        spacing = float(np.mean(np.diff(all_positions))) if len(all_positions) > 1 else 1.0
        scale = 0.5 * spacing
        sel_set = set(selected_indices) if selected_indices else None

        n_plot = min(len(all_positions), traces.shape[0])
        for i in range(n_plot):
            x0 = all_positions[i]
            if sel_set is not None:
                color = _CLR_TRACE_ACTIVE if i in sel_set else _CLR_TRACE_INACTIVE
                lw = 0.6 if i in sel_set else 0.3
            else:
                color = _CLR_TRACE_ACTIVE
                lw = 0.5
            ax.plot(traces[i] * scale + x0, time_data, color=color, linewidth=lw)

        ax.invert_yaxis()
        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("Frequency (Hz)" if is_vibrosis else "Time (s)")
        ax.set_title(
            "Transfer Function Magnitude (normalised)" if is_vibrosis
            else "Waterfall (normalised)"
        )

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------
    def _request_overview(self) -> None:
        if self._on_overview_request:
            self._on_overview_request()

    def _on_source_selected(self, _e: Any = None) -> None:
        txt = self._src_var.get()
        try:
            idx = int(txt.split(":")[0].strip().lstrip("#"))
            self._selected_shot_idx = idx
        except (ValueError, IndexError):
            self._selected_shot_idx = None
        if self._detail_sa is not None:
            self.show_detail(
                self._detail_sa,
                self._detail_shots,
                self._detail_n_channels,
                self._detail_dx,
            )

    def invalidate_cache(self, filepath: Optional[str] = None) -> None:
        """Clear cached data. If *filepath* given, only that entry."""
        if filepath:
            self._data_cache.pop(filepath, None)
        else:
            self._data_cache.clear()
