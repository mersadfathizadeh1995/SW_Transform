"""MASW 2D Tab -- Unified panel layout with collapsible sections + real-data preview."""
from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable, Dict, List, Optional

from sw_transform.masw2d.gui import (
    MASW2D_DEFAULTS,
    ArraySetupPanel,
    ProcessingPanel,
    OutputPanel,
    MASW2DRunPanel,
    AssignmentPanel,
    GeometryPreviewPanel,
    ShotInputPanel,
)
from sw_transform.masw2d.gui.subarray_explorer import SubarrayExplorerPanel
from sw_transform.masw2d.gui.collapsible import CollapsibleLabelFrame
from sw_transform.masw2d.geometry.subarray import SubArrayDef


class MASW2DTab:
    """MASW 2D processing tab: single scrollable left panel + real-data preview."""

    def __init__(
        self,
        parent: tk.Frame,
        log_callback: Optional[Callable[[str], None]] = None,
        main_app: Any = None,
    ):
        self.parent = parent
        self.log = log_callback or print
        self.main_app = main_app
        self._DEFAULTS = MASW2D_DEFAULTS
        self._create_advanced_variables()

        self.array_panel: Optional[ArraySetupPanel] = None
        self.shot_panel: Optional[ShotInputPanel] = None
        self.explorer_panel: Optional[SubarrayExplorerPanel] = None
        self.processing_panel: Optional[ProcessingPanel] = None
        self.output_panel: Optional[OutputPanel] = None
        self.run_panel: Optional[MASW2DRunPanel] = None
        self.preview: Optional[GeometryPreviewPanel] = None
        self.assignment_panel: Optional[AssignmentPanel] = None
        self._summary_text: Optional[tk.Text] = None

        self._preview_expanded = True
        self._selected_sa: Optional[SubArrayDef] = None

        self._build_ui()

    # ------------------------------------------------------------------
    # Advanced tk variables (unchanged)
    # ------------------------------------------------------------------
    def _create_advanced_variables(self) -> None:
        self.grid_n_var = tk.StringVar(value=self._DEFAULTS["grid_n"])
        self.vspace_var = tk.StringVar(value=self._DEFAULTS["vspace"])
        self.tol_var = tk.StringVar(value=self._DEFAULTS["tol"])
        self.power_threshold_var = tk.StringVar(value=self._DEFAULTS["power_threshold"])
        self.vibrosis_var = tk.BooleanVar(value=self._DEFAULTS["vibrosis"])
        self.cylindrical_var = tk.BooleanVar(value=self._DEFAULTS["cylindrical"])
        self.vibrosis_var.trace_add("write", self._on_vibrosis_changed)
        self.start_time_var = tk.StringVar(value=self._DEFAULTS["start_time"])
        self.end_time_var = tk.StringVar(value=self._DEFAULTS["end_time"])
        self.downsample_var = tk.BooleanVar(value=self._DEFAULTS["downsample"])
        self.down_factor_var = tk.StringVar(value=self._DEFAULTS["down_factor"])
        self.numf_var = tk.StringVar(value=self._DEFAULTS["numf"])
        self.plot_max_vel_var = tk.StringVar(value=self._DEFAULTS["plot_max_vel"])
        self.plot_max_freq_var = tk.StringVar(value=self._DEFAULTS["plot_max_freq"])
        self.cmap_var = tk.StringVar(value=self._DEFAULTS["cmap"])
        self.dpi_var = tk.StringVar(value=self._DEFAULTS["dpi"])
        self.fig_width_var = tk.StringVar(value=self._DEFAULTS.get("fig_width", "8"))
        self.fig_height_var = tk.StringVar(value=self._DEFAULTS.get("fig_height", "6"))
        self.contour_levels_var = tk.StringVar(value=self._DEFAULTS.get("contour_levels", "30"))
        self.plot_style_var = tk.StringVar(value=self._DEFAULTS.get("plot_style", "contourf"))

    def _on_vibrosis_changed(self, *_a: Any) -> None:
        if self.vibrosis_var.get():
            self.cylindrical_var.set(True)

    # ------------------------------------------------------------------
    # UI BUILD — single scrollable left panel + preview right panel
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        outer = ttk.Frame(self.parent)
        outer.pack(fill="both", expand=True, padx=4, pady=4)

        # Horizontal PanedWindow for drag-resizing
        self._paned = ttk.PanedWindow(outer, orient="horizontal")
        self._paned.pack(fill="both", expand=True)

        # LEFT: single scrollable panel with run at bottom
        left = ttk.Frame(self._paned)
        self._paned.add(left, weight=1)

        # Scrollable area for config sections
        canvas = tk.Canvas(left, highlightthickness=0)
        scroll = ttk.Scrollbar(left, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)

        def _mw(ev: tk.Event) -> str:
            canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units")
            return "break"
        canvas.bind("<MouseWheel>", _mw)

        # Run panel at the bottom (always visible, outside scroll)
        self.run_panel = MASW2DRunPanel(left, on_run=self._run_workflow)
        self.run_panel.pack(side="bottom", fill="x", padx=4, pady=4)

        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # --- Section 1: Array Setup (expanded) ---
        sec_array = CollapsibleLabelFrame(inner, title="Array Setup", collapsed=False)
        sec_array.pack(fill="x", padx=4, pady=2)
        self.array_panel = ArraySetupPanel(sec_array.content, on_update=self._on_array_updated)
        self.array_panel.pack(fill="x")

        # --- Section 2: Shot Files (expanded) ---
        sec_shots = CollapsibleLabelFrame(inner, title="Shot Files", collapsed=False)
        sec_shots.pack(fill="x", padx=4, pady=2)
        self.shot_panel = ShotInputPanel(
            sec_shots.content,
            main_app=self.main_app,
            log_callback=self.log,
            array_length_getter=self._get_array_length,
            on_change=self._on_shots_changed,
        )
        self.shot_panel.pack(fill="both", expand=True)

        # --- Section 3: Sub-Array Configuration (expanded) ---
        sec_sa = CollapsibleLabelFrame(inner, title="Sub-Array Configuration", collapsed=False)
        sec_sa.pack(fill="x", padx=4, pady=2)
        self.explorer_panel = SubarrayExplorerPanel(
            sec_sa.content,
            n_channels_getter=self._get_n_channels,
            dx_getter=self._get_dx,
            on_change=self._on_explorer_changed,
            on_row_selected=self._on_subarray_row_selected,
        )
        self.explorer_panel.pack(fill="x")

        # --- Section 4: Processing (collapsed) ---
        sec_proc = CollapsibleLabelFrame(inner, title="Processing", collapsed=True)
        sec_proc.pack(fill="x", padx=4, pady=2)
        self.processing_panel = ProcessingPanel(sec_proc.content, on_advanced_click=self._open_advanced_settings)
        self.processing_panel.pack(fill="x")

        # --- Section 5: Output (collapsed) ---
        sec_out = CollapsibleLabelFrame(inner, title="Output", collapsed=True)
        sec_out.pack(fill="x", padx=4, pady=2)
        self.output_panel = OutputPanel(sec_out.content)
        self.output_panel.pack(fill="x")

        # --- Section 6: Assignment Summary (collapsed) ---
        sec_summary = CollapsibleLabelFrame(inner, title="Assignment Summary", collapsed=True)
        sec_summary.pack(fill="x", padx=4, pady=2)

        # Assignment panel (strategy/constraints)
        self.assignment_panel = AssignmentPanel(sec_summary.content, on_change=self._update_preview)
        self.assignment_panel.pack(fill="x", pady=(0, 4))

        self._summary_text = tk.Text(sec_summary.content, height=5, wrap="word", state="disabled")
        self._summary_text.pack(fill="x")

        # RIGHT: toggle strip + preview
        self._right_outer = ttk.Frame(self._paned)
        self._paned.add(self._right_outer, weight=2)

        toggle_strip = ttk.Frame(self._right_outer, width=22)
        toggle_strip.pack(side="left", fill="y")
        self._toggle_var = tk.StringVar(value=">>")
        self._toggle_btn = tk.Button(
            toggle_strip,
            textvariable=self._toggle_var,
            width=2,
            command=self._toggle_preview,
            relief="flat",
            cursor="hand2",
        )
        self._toggle_btn.pack(fill="y", expand=True, pady=40)

        self._preview_content = ttk.Frame(self._right_outer)
        self._preview_content.pack(side="left", fill="both", expand=True)

        self.preview = GeometryPreviewPanel(self._preview_content)
        self.preview.pack(fill="both", expand=True)
        self.preview.set_overview_callback(self._show_overview)

        self._update_preview()

    def _toggle_preview(self) -> None:
        if self._preview_expanded:
            self._preview_content.pack_forget()
            self._toggle_var.set("<<")
            self._preview_expanded = False
        else:
            self._preview_content.pack(side="left", fill="both", expand=True)
            self._toggle_var.set(">>")
            self._preview_expanded = True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_n_channels(self) -> int:
        return self.array_panel.n_channels if self.array_panel else 24

    def _get_dx(self) -> float:
        if self.array_panel:
            return float(self.array_panel.get_values().get("dx", 2.0))
        return 2.0

    def _get_array_length(self) -> float:
        if self.array_panel:
            return float(self.array_panel.get_values().get("array_length", 46.0))
        return 46.0

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------
    def _on_array_updated(self) -> None:
        if self.explorer_panel:
            self.explorer_panel.update_for_array()
        self._update_preview()

    def _on_shots_changed(self) -> None:
        if self.shot_panel and self.shot_panel.has_mat_files():
            self.vibrosis_var.set(True)
            self.cylindrical_var.set(True)
            self.log("Vibrosis .mat files detected -- FDBF mode enabled")

        if self.shot_panel and self.array_panel:
            files = self.shot_panel.files
            if files:
                first = files[0]
                try:
                    n_ch = 0
                    dx_val = 0.0
                    if first.lower().endswith(".mat"):
                        from sw_transform.processing.vibrosis import get_vibrosis_file_info
                        info = get_vibrosis_file_info(first)
                        n_ch = int(info.get("n_channels", 0) or 0)
                        dx_val = float(info.get("dx", 0) or 0)
                    else:
                        from sw_transform.processing.seg2 import load_seg2_ar
                        _, data, _, dx_val, _, _ = load_seg2_ar(first)
                        n_ch = data.shape[1]
                    if n_ch > 0 or dx_val > 0:
                        self.array_panel.set_file_info(
                            n_ch if n_ch > 0 else self.array_panel.n_channels,
                            dx_val if dx_val > 0 else self.array_panel.dx,
                        )
                        self.log(f"Array auto-detected: {n_ch} ch, {dx_val:.2f} m spacing")
                except Exception as e:
                    self.log(f"Could not auto-detect array config: {e}")
        self._update_preview()

    def _on_explorer_changed(self) -> None:
        self._selected_sa = None
        self._update_preview()

    def _on_subarray_row_selected(self, sa: Optional[SubArrayDef]) -> None:
        self._selected_sa = sa
        self._update_preview()

    def _show_overview(self) -> None:
        self._selected_sa = None
        self._update_preview()

    # ------------------------------------------------------------------
    # Preview update (two paths)
    # ------------------------------------------------------------------
    def _update_preview(self) -> None:
        if not self.array_panel or not self.preview or not self.shot_panel:
            return

        n_channels = self._get_n_channels()
        dx = self._get_dx()
        shot_positions = self.shot_panel.get_shot_positions()
        shots = self.shot_panel.get_shots()

        subarrays = self.explorer_panel.get_all_subarrays() if self.explorer_panel else []

        # Get first valid shot file for preview data
        first_shot_file = None
        first_source_pos = None
        for sh in shots:
            fp = (sh.get("file") or "").strip()
            if fp and os.path.isfile(fp):
                first_shot_file = fp
                first_source_pos = float(sh.get("source_position", 0.0))
                break

        if self._selected_sa is not None:
            self._show_detail_for_sa(self._selected_sa, n_channels, dx, shots, first_shot_file)
        else:
            plan = self._try_build_plan(n_channels, dx, shots, subarrays)
            self.preview.show_overview(
                n_channels, dx, shot_positions, subarrays, plan,
                shot_file=first_shot_file,
                shot_source_pos=first_source_pos,
            )

        self._update_assignment_summary()

    def _show_detail_for_sa(
        self, sa: SubArrayDef, n_channels: int, dx: float,
        shots: List[Dict[str, Any]], shot_file: Optional[str] = None,
    ) -> None:
        """Build assigned-shot info for this subarray and show detail."""
        assigned: List[Dict[str, Any]] = []
        plan = self._try_build_plan(n_channels, dx, shots, [sa])
        if plan:
            for a in plan.assignments:
                if (
                    a.subarray_def.start_channel == sa.start_channel
                    and a.subarray_def.end_channel == sa.end_channel
                    and a.subarray_def.config_name == sa.config_name
                ):
                    assigned.append({
                        "source_position": a.shot_position,
                        "direction": a.direction,
                        "source_offset": a.source_offset,
                        "shot_index": a.shot_index,
                        "file": shots[a.shot_index].get("file") if a.shot_index < len(shots) else None,
                    })
        if not assigned:
            for i, sh in enumerate(shots):
                pos = float(sh.get("source_position", 0.0))
                if pos < sa.start_position:
                    d, off = "forward", sa.start_position - pos
                elif pos > sa.end_position:
                    d, off = "reverse", pos - sa.end_position
                else:
                    d, off = "interior", min(pos - sa.start_position, sa.end_position - pos)
                assigned.append({
                    "source_position": pos,
                    "direction": d,
                    "source_offset": off,
                    "shot_index": i,
                    "file": sh.get("file"),
                })
        self.preview.show_detail(sa, assigned, n_channels, dx, shot_file=shot_file)

    def _try_build_plan(
        self,
        n_channels: int,
        dx: float,
        shots: List[Dict[str, Any]],
        subarrays: List[SubArrayDef],
    ) -> Any:
        if not subarrays or not shots:
            return None
        names_set: set = set()
        sa_configs: List[dict] = []
        for sa in subarrays:
            if sa.config_name not in names_set:
                names_set.add(sa.config_name)
                sa_configs.append({
                    "n_channels": sa.n_channels,
                    "slide_step": 1,
                    "name": sa.config_name,
                })
        shots_cfg = []
        for i, sh in enumerate(shots):
            fp = (sh.get("file") or "").strip()
            shots_cfg.append({"file": fp or f"_shot{i}", "source_position": float(sh["source_position"])})
        cfg: Dict[str, Any] = {
            "array": {"n_channels": n_channels, "dx": dx, "first_channel_position": 0.0},
            "shots": shots_cfg,
            "subarray_configs": sa_configs,
        }
        if self.assignment_panel:
            ac = self.assignment_panel.get_config()
            if ac:
                cfg["assignment"] = ac
        try:
            from sw_transform.masw2d.geometry.shot_assigner import generate_plan_from_config
            return generate_plan_from_config(cfg)
        except Exception:
            return None

    def _update_assignment_summary(self) -> None:
        if not self._summary_text:
            return
        self._summary_text.config(state="normal")
        self._summary_text.delete("1.0", "end")
        try:
            subarrays = self.explorer_panel.get_all_subarrays() if self.explorer_panel else []
            shots = self.shot_panel.get_shots() if self.shot_panel else []
            n_ch = self._get_n_channels()
            dx = self._get_dx()
            plan = self._try_build_plan(n_ch, dx, shots, subarrays)
            if plan:
                self._summary_text.insert("1.0", plan.describe())
            else:
                self._summary_text.insert("1.0", "Generate subarrays and add shots to see assignment summary.")
        except Exception as e:
            self._summary_text.insert("1.0", f"Summary unavailable: {e}")
        self._summary_text.config(state="disabled")

    # ------------------------------------------------------------------
    # Advanced settings popup (unchanged from previous version)
    # ------------------------------------------------------------------
    def _reset_advanced_defaults(self) -> None:
        for key in (
            "grid_n", "vspace", "tol", "power_threshold",
            "start_time", "end_time", "downsample", "down_factor", "numf",
            "plot_max_vel", "plot_max_freq", "cmap", "dpi",
            "vibrosis", "cylindrical",
        ):
            var = getattr(self, f"{key}_var", None)
            if var is not None:
                var.set(self._DEFAULTS[key])
        for key in ("fig_width", "fig_height", "contour_levels", "plot_style"):
            var = getattr(self, f"{key}_var", None)
            if var is not None:
                var.set(self._DEFAULTS.get(key, ""))

    def _open_advanced_settings(self) -> None:
        popup = tk.Toplevel(self.parent)
        popup.title("Advanced Settings")
        popup.geometry("450x550")
        popup.resizable(True, True)
        popup.transient(self.parent)
        popup.grab_set()
        canvas = tk.Canvas(popup, highlightthickness=0)
        scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        def _row(parent: ttk.Frame, label: str, var: Any, values: list, **kw: Any) -> None:
            r = ttk.Frame(parent)
            r.pack(fill="x", pady=3)
            ttk.Label(r, text=label, width=18).pack(side="left")
            w_type = kw.pop("widget", "combo")
            if w_type == "entry":
                ttk.Entry(r, textvariable=var, width=12).pack(side="left", padx=4)
            elif w_type == "check":
                ttk.Checkbutton(r, text=kw.pop("check_text", ""), variable=var).pack(side="left")
            else:
                ttk.Combobox(r, textvariable=var, values=values, width=kw.pop("w", 10), state=kw.pop("st", "readonly")).pack(side="left", padx=4)

        tf = ttk.LabelFrame(scrollable, text="Transform Settings", padding=8)
        tf.pack(fill="x", padx=8, pady=6)
        _row(tf, "Velocity Grid Size:", self.grid_n_var, ["500","1000","2000","4000","8000"])
        _row(tf, "Velocity Spacing:", self.vspace_var, ["log","linear"])
        r_vib = ttk.Frame(tf); r_vib.pack(fill="x", pady=3)
        ttk.Checkbutton(r_vib, text="Vibrosis mode (FDBF weighting)", variable=self.vibrosis_var).pack(side="left")
        r_cyl = ttk.Frame(tf); r_cyl.pack(fill="x", pady=3)
        ttk.Checkbutton(r_cyl, text="Cylindrical steering (FDBF near-field)", variable=self.cylindrical_var).pack(side="left")

        pf = ttk.LabelFrame(scrollable, text="Peak Picking", padding=8)
        pf.pack(fill="x", padx=8, pady=6)
        _row(pf, "Tolerance:", self.tol_var, [], widget="entry")
        _row(pf, "Power Threshold:", self.power_threshold_var, [], widget="entry")

        ppf = ttk.LabelFrame(scrollable, text="Preprocessing", padding=8)
        ppf.pack(fill="x", padx=8, pady=6)
        r5 = ttk.Frame(ppf); r5.pack(fill="x", pady=3)
        ttk.Label(r5, text="Time Window:", width=18).pack(side="left")
        ttk.Entry(r5, textvariable=self.start_time_var, width=6).pack(side="left", padx=2)
        ttk.Label(r5, text="-").pack(side="left")
        ttk.Entry(r5, textvariable=self.end_time_var, width=6).pack(side="left", padx=2)
        ttk.Label(r5, text="sec", foreground="gray").pack(side="left", padx=4)
        r6 = ttk.Frame(ppf); r6.pack(fill="x", pady=3)
        ttk.Checkbutton(r6, text="Downsample", variable=self.downsample_var).pack(side="left")
        _row(ppf, "Downsample Factor:", self.down_factor_var, ["1","2","4","8","16","32"])
        _row(ppf, "FFT Size:", self.numf_var, ["1000","2000","4000","8000"])

        imf = ttk.LabelFrame(scrollable, text="Image Export Options", padding=8)
        imf.pack(fill="x", padx=8, pady=6)
        _row(imf, "Max Velocity (plot):", self.plot_max_vel_var, ["auto","500","1000","1500","2000","3000","5000"], st="normal")
        _row(imf, "Max Frequency (plot):", self.plot_max_freq_var, ["auto","50","80","100","150","200"], st="normal")
        from sw_transform.gui.components.advanced_settings import AdvancedSettingsManager
        _row(imf, "Colormap:", self.cmap_var, AdvancedSettingsManager.COLORMAPS, w=16, st="normal")
        _row(imf, "DPI:", self.dpi_var, ["72","100","150","200","300"])
        r13 = ttk.Frame(imf); r13.pack(fill="x", pady=3)
        ttk.Label(r13, text="Figure Width:", width=18).pack(side="left")
        ttk.Entry(r13, textvariable=self.fig_width_var, width=6).pack(side="left", padx=2)
        ttk.Label(r13, text="Height:").pack(side="left", padx=(8,0))
        ttk.Entry(r13, textvariable=self.fig_height_var, width=6).pack(side="left", padx=2)
        ttk.Label(r13, text="in", foreground="gray").pack(side="left", padx=2)
        _row(imf, "Plot Style:", self.plot_style_var, ["contourf","pcolormesh"])
        _row(imf, "Contour Levels:", self.contour_levels_var, ["10","15","20","30","50","100"], st="normal")

        bf = ttk.Frame(scrollable); bf.pack(fill="x", padx=8, pady=12)
        ttk.Button(bf, text="Reset to Defaults", command=self._reset_advanced_defaults).pack(side="left", padx=4)
        ttk.Button(bf, text="Close", command=popup.destroy).pack(side="right", padx=4)
        popup.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - popup.winfo_width()) // 2
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() - popup.winfo_height()) // 2
        popup.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # Config building
    # ------------------------------------------------------------------
    def _build_config(self) -> Dict[str, Any]:
        array_values = self.array_panel.get_values()
        proc_values = self.processing_panel.get_values()
        output_values = self.output_panel.get_values()

        sa_configs = self.explorer_panel.get_subarray_configs() if self.explorer_panel else []
        if not sa_configs:
            raise ValueError("No sub-arrays generated. Click Generate in the Config tab.")

        try:
            grid_n = int(self.grid_n_var.get())
            tol = float(self.tol_var.get())
            power_threshold = float(self.power_threshold_var.get())
            start_time = float(self.start_time_var.get())
            end_time = float(self.end_time_var.get())
            down_factor = int(self.down_factor_var.get())
            numf = int(self.numf_var.get())
            plot_max_vel_str = self.plot_max_vel_var.get()
            plot_max_vel = None if plot_max_vel_str == "auto" else float(plot_max_vel_str)
            auto_velocity_limit = plot_max_vel_str == "auto"
            plot_max_freq_str = self.plot_max_freq_var.get()
            plot_max_freq = None if plot_max_freq_str == "auto" else float(plot_max_freq_str)
            auto_frequency_limit = plot_max_freq_str == "auto"
            dpi = int(self.dpi_var.get())
        except ValueError as e:
            raise ValueError(f"Invalid numeric value in advanced settings: {e}") from e

        shots_config: List[Dict[str, Any]] = []
        for shot in self.shot_panel.get_shots():
            fp = (shot.get("file") or "").strip()
            if not fp or not os.path.isfile(fp):
                continue
            shots_config.append({"file": fp, "source_position": float(shot["source_position"])})
        if not shots_config:
            raise ValueError("No valid shot files -- assign files in the Data tab.")

        config: Dict[str, Any] = {
            "survey_name": "GUI_MASW_2D",
            "version": "1.0",
            "array": {"n_channels": array_values["n_channels"], "dx": array_values["dx"], "first_channel_position": 0.0},
            "shots": shots_config,
            "subarray_configs": sa_configs,
            "processing": {
                "method": proc_values["method"],
                "freq_min": proc_values["freq_min"],
                "freq_max": proc_values["freq_max"],
                "velocity_min": proc_values["vel_min"],
                "velocity_max": proc_values["vel_max"],
                "grid_n": grid_n, "tol": tol, "power_threshold": power_threshold,
                "vspace": self.vspace_var.get(),
                "source_type": "vibrosis" if self.vibrosis_var.get() else "hammer",
                "cylindrical": self.cylindrical_var.get(),
                "start_time": start_time, "end_time": end_time,
                "downsample": self.downsample_var.get(),
                "down_factor": down_factor, "numf": numf,
            },
            "output": {
                "directory": output_values["output_dir"] or "./output_2d/",
                "organize_by": "midpoint",
                "export_formats": ["csv", "npz", "image"],
                "include_images": output_values["include_images"],
                "export_individual_npz": output_values.get("export_individual_npz", True),
                "export_combined_csv_per_midpoint": output_values.get("export_combined_csv_per_midpoint", True),
                "export_combined_npz_per_midpoint": output_values.get("export_combined_npz_per_midpoint", True),
                "generate_summary": output_values.get("generate_summary", True),
                "export_midpoint_summary": output_values.get("export_midpoint_summary", True),
                "export_all_picks": output_values.get("export_all_picks", True),
                "export_combined_npz": output_values.get("export_combined_npz", False),
                "max_velocity": plot_max_vel, "max_frequency": plot_max_freq,
                "auto_velocity_limit": auto_velocity_limit, "auto_frequency_limit": auto_frequency_limit,
                "cmap": self.cmap_var.get(), "image_dpi": dpi,
                "fig_width": int(float(self.fig_width_var.get())),
                "fig_height": int(float(self.fig_height_var.get())),
                "contour_levels": int(float(self.contour_levels_var.get())),
                "plot_style": self.plot_style_var.get(),
            },
        }
        if self.assignment_panel:
            ac = self.assignment_panel.get_config()
            if ac:
                config["assignment"] = ac
        return config

    # ------------------------------------------------------------------
    # Workflow execution
    # ------------------------------------------------------------------
    def _run_workflow(self) -> None:
        try:
            config = self._build_config()
        except ValueError as e:
            messagebox.showerror("Configuration Error", str(e))
            return
        shot_files = self.shot_panel.files
        if not shot_files:
            messagebox.showwarning("No Files", "Please add shot files first.")
            return
        output_dir = self.output_panel.output_dir
        if not output_dir:
            messagebox.showwarning("No Output", "Please select an output directory.")
            return
        mat_files = [f for f in shot_files if f.lower().endswith(".mat")]
        seg2_files = [f for f in shot_files if not f.lower().endswith(".mat")]
        if mat_files and seg2_files:
            result = messagebox.askyesno(
                "Mixed File Types",
                f"Both .mat ({len(mat_files)}) and SEG-2 ({len(seg2_files)}) files detected.\n"
                "Process .mat files only?\n(No = SEG-2 only)",
            )
            if result:
                seg2_files = []
            else:
                mat_files = []
        use_vibrosis = len(mat_files) > 0
        if use_vibrosis and self.processing_panel.method != "fdbf":
            messagebox.showinfo("Vibrosis Mode", "Vibrosis .mat files require FDBF method.\nFDBF will be used.")
        self.run_panel.set_progress(0, "Running...")

        def run_thread() -> None:
            try:
                if use_vibrosis:
                    from sw_transform.masw2d.workflows import VibrosisMASWWorkflow
                    config["mat_files"] = mat_files
                    config["processing"]["cylindrical"] = True
                    wf = VibrosisMASWWorkflow(config)
                    def pcb(c: int, t: int, m: str) -> None:
                        self.parent.after(0, lambda: self.run_panel.set_progress((c/t*100) if t else 0, m))
                    wf.set_progress_callback(pcb)
                    results = wf.run(mat_files=mat_files, output_dir=output_dir)
                else:
                    use_assign = "assignment" in config
                    if use_assign:
                        from sw_transform.masw2d.workflows import AssignedMASWWorkflow
                        wf = AssignedMASWWorkflow(config)
                    else:
                        from sw_transform.masw2d.workflows import StandardMASWWorkflow
                        wf = StandardMASWWorkflow(config)
                    ov = self.output_panel.get_values()
                    def pcb(c: int, t: int, m: str) -> None:
                        self.parent.after(0, lambda: self.run_panel.set_progress((c/t*100) if t else 0, m))
                    wf.set_progress_callback(pcb)
                    results = wf.run(output_dir=output_dir, parallel=ov["parallel"], max_workers=ov["max_workers"])
                self.parent.after(0, lambda: self._on_workflow_complete(results))
            except Exception as e:
                import traceback
                msg = f"{e}\n\n{traceback.format_exc()}"
                self.parent.after(0, lambda: self._on_workflow_error(msg))

        threading.Thread(target=run_thread, daemon=True).start()

    def _on_workflow_complete(self, results: Dict[str, Any]) -> None:
        self.run_panel.set_progress(100, "Complete!")
        nr = results.get("n_results", 0)
        nm = results.get("n_midpoints", 0)
        if results.get("status") == "success":
            self.run_panel.set_status(f"Complete! {nr} curves at {nm} midpoints.")
            self.log(f"MASW 2D complete: {nr} results at {nm} midpoints")
            messagebox.showinfo("Complete", f"Workflow finished.\n{nr} dispersion curves\nat {nm} midpoint locations.")
        else:
            err = results.get("error", "Unknown error")
            self.run_panel.set_status(f"Error: {err}")
            self.log(f"MASW 2D error: {err}")
            messagebox.showerror("Workflow Error", err)

    def _on_workflow_error(self, msg: str) -> None:
        self.run_panel.set_progress(0, "Error")
        self.run_panel.set_status(f"Error: {msg[:50]}...")
        self.log(f"MASW 2D error: {msg}")
        messagebox.showerror("Workflow Error", msg)


def create_masw2d_tab(notebook: ttk.Notebook, log_callback: Any = None, main_app: Any = None) -> MASW2DTab:
    frame = ttk.Frame(notebook)
    notebook.add(frame, text="MASW 2D")
    tab = MASW2DTab(frame, log_callback, main_app)

    def on_tab_change(_ev: tk.Event) -> None:
        try:
            cur = notebook.select()
            if notebook.tab(cur, "text") == "MASW 2D" and tab.shot_panel and main_app:
                tab.shot_panel.sync_from_main_app()
        except Exception:
            pass

    notebook.bind("<<NotebookTabChanged>>", on_tab_change)
    return tab
