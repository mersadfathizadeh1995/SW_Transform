"""Output settings panel component."""
from __future__ import annotations

import multiprocessing
import tkinter as tk
from tkinter import ttk, filedialog


class ExportOptionsDialog(tk.Toplevel):
    """Popup dialog for configuring export options in detail."""

    def __init__(self, parent: tk.Widget, current_values: dict):
        super().__init__(parent)
        self.title("Export Options")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._result = None
        self._vars: dict = {}
        self._build_ui(current_values)

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_rootx() + parent.winfo_width() // 2
        ph = parent.winfo_rooty() + parent.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{pw - w // 2}+{ph - h // 2}")

    def _build_ui(self, vals: dict):
        pad = dict(padx=10, pady=2, anchor="w")

        # --- Per-midpoint group ---
        grp1 = ttk.LabelFrame(self, text="Per-Midpoint Exports", padding=6)
        grp1.pack(fill="x", padx=8, pady=(8, 4))

        self._vars['include_images'] = tk.BooleanVar(value=vals.get('include_images', True))
        ttk.Checkbutton(grp1, text="Dispersion Images (PNG)",
                        variable=self._vars['include_images']).pack(**pad)

        self._vars['export_individual_npz'] = tk.BooleanVar(
            value=vals.get('export_individual_npz', True))
        ttk.Checkbutton(grp1, text="Individual Spectrum (NPZ)",
                        variable=self._vars['export_individual_npz']).pack(**pad)

        self._vars['export_combined_csv_per_midpoint'] = tk.BooleanVar(
            value=vals.get('export_combined_csv_per_midpoint', True))
        ttk.Checkbutton(grp1, text="Combined CSV per midpoint (multi-offset)",
                        variable=self._vars['export_combined_csv_per_midpoint']).pack(**pad)

        self._vars['export_combined_npz_per_midpoint'] = tk.BooleanVar(
            value=vals.get('export_combined_npz_per_midpoint', True))
        ttk.Checkbutton(grp1, text="Combined NPZ per midpoint (multi-offset)",
                        variable=self._vars['export_combined_npz_per_midpoint']).pack(**pad)

        # --- Summary group ---
        grp2 = ttk.LabelFrame(self, text="Summary Exports", padding=6)
        grp2.pack(fill="x", padx=8, pady=4)

        self._vars['export_midpoint_summary'] = tk.BooleanVar(
            value=vals.get('export_midpoint_summary', True))
        ttk.Checkbutton(grp2, text="Midpoint Summary (CSV)",
                        variable=self._vars['export_midpoint_summary']).pack(**pad)

        self._vars['export_all_picks'] = tk.BooleanVar(
            value=vals.get('export_all_picks', True))
        ttk.Checkbutton(grp2, text="All Dispersion Curves (CSV)",
                        variable=self._vars['export_all_picks']).pack(**pad)

        self._vars['export_combined_npz'] = tk.BooleanVar(
            value=vals.get('export_combined_npz', False))
        ttk.Checkbutton(grp2, text="Combined Spectra (NPZ)",
                        variable=self._vars['export_combined_npz']).pack(**pad)

        # --- Buttons ---
        btn_row = ttk.Frame(self)
        btn_row.pack(fill="x", padx=8, pady=(4, 8))
        ttk.Button(btn_row, text="OK", command=self._on_ok).pack(side="right", padx=4)
        ttk.Button(btn_row, text="Cancel", command=self._on_cancel).pack(side="right")

    def _on_ok(self):
        self._result = {k: v.get() for k, v in self._vars.items()}
        self.destroy()

    def _on_cancel(self):
        self._result = None
        self.destroy()

    @property
    def result(self) -> dict | None:
        return self._result


class OutputPanel(ttk.LabelFrame):
    """Output settings panel with directory, parallel, and export options."""

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, text="Output", padding=6, **kwargs)
        self._create_variables()
        self._build_ui()

    def _create_variables(self):
        """Create tk variables."""
        self.output_dir_var = tk.StringVar(value="")
        self.parallel_var = tk.BooleanVar(value=True)
        self.worker_var = tk.StringVar(value="auto")
        # Export settings (stored internally, edited via dialog)
        self._export_opts = {
            'include_images': True,
            'export_individual_npz': True,
            'export_combined_csv_per_midpoint': True,
            'export_combined_npz_per_midpoint': True,
            'export_midpoint_summary': True,
            'export_all_picks': True,
            'export_combined_npz': False,
        }

    def _build_ui(self):
        """Build the panel UI."""
        # Directory row
        row_dir = ttk.Frame(self)
        row_dir.pack(fill="x", pady=2)
        ttk.Entry(row_dir, textvariable=self.output_dir_var, width=30).pack(
            side="left", fill="x", expand=True)
        ttk.Button(row_dir, text="Browse...",
                   command=self._select_output_dir).pack(side="left", padx=4)

        # Parallel row
        row_par = ttk.Frame(self)
        row_par.pack(fill="x", pady=4)
        ttk.Checkbutton(row_par, text="Parallel", variable=self.parallel_var).pack(side="left")
        ttk.Label(row_par, text="Workers:").pack(side="left", padx=(10, 2))

        max_cpu = multiprocessing.cpu_count()
        worker_combo = ttk.Combobox(row_par, textvariable=self.worker_var,
                                     values=["auto"] + [str(i) for i in range(1, max_cpu + 1)],
                                     width=5, state="readonly")
        worker_combo.pack(side="left")

        # Export options summary + configure button
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=4)
        row_exp = ttk.Frame(self)
        row_exp.pack(fill="x")
        ttk.Label(row_exp, text="Export Options:", font=("", 8, "bold")).pack(side="left")
        self._export_summary_lbl = ttk.Label(row_exp, text="", foreground="gray")
        self._export_summary_lbl.pack(side="left", padx=6)
        ttk.Button(row_exp, text="Configure...",
                   command=self._open_export_dialog).pack(side="right")
        self._update_export_summary()

    def _select_output_dir(self):
        """Select output directory."""
        dir_path = filedialog.askdirectory(title="Select Output Directory")
        if dir_path:
            self.output_dir_var.set(dir_path)

    def _open_export_dialog(self):
        """Open the export options dialog."""
        dlg = ExportOptionsDialog(self.winfo_toplevel(), self._export_opts)
        self.wait_window(dlg)
        if dlg.result is not None:
            self._export_opts.update(dlg.result)
            self._update_export_summary()

    def _update_export_summary(self):
        """Update the compact summary label."""
        active = []
        if self._export_opts.get('include_images'):
            active.append("PNG")
        if self._export_opts.get('export_individual_npz'):
            active.append("NPZ")
        n_summary = sum(1 for k in ('export_midpoint_summary', 'export_all_picks',
                                     'export_combined_npz')
                        if self._export_opts.get(k))
        if n_summary:
            active.append(f"Summary({n_summary})")
        n_combined = sum(1 for k in ('export_combined_csv_per_midpoint',
                                      'export_combined_npz_per_midpoint')
                         if self._export_opts.get(k))
        if n_combined:
            active.append(f"Combined({n_combined})")
        self._export_summary_lbl.configure(text=", ".join(active) if active else "None")

    def get_values(self) -> dict:
        """Get current values as a dictionary."""
        workers = self.worker_var.get()
        max_workers = None if workers == "auto" else int(workers)

        any_summary = (self._export_opts.get('export_midpoint_summary', False) or
                       self._export_opts.get('export_all_picks', False) or
                       self._export_opts.get('export_combined_npz', False))

        return {
            'output_dir': self.output_dir_var.get(),
            'parallel': self.parallel_var.get(),
            'max_workers': max_workers,
            'include_images': self._export_opts.get('include_images', True),
            'export_individual_npz': self._export_opts.get('export_individual_npz', True),
            'export_combined_csv_per_midpoint': self._export_opts.get(
                'export_combined_csv_per_midpoint', True),
            'export_combined_npz_per_midpoint': self._export_opts.get(
                'export_combined_npz_per_midpoint', True),
            'generate_summary': any_summary,
            'export_midpoint_summary': self._export_opts.get('export_midpoint_summary', True),
            'export_all_picks': self._export_opts.get('export_all_picks', True),
            'export_combined_npz': self._export_opts.get('export_combined_npz', False),
        }

    @property
    def output_dir(self) -> str:
        """Get output directory."""
        return self.output_dir_var.get()

    @property
    def parallel_enabled(self) -> bool:
        """Check if parallel processing is enabled."""
        return self.parallel_var.get()
