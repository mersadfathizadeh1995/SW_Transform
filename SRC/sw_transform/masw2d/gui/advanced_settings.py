"""MASW 2D Advanced Settings manager and dialog.

Copied from masw2d_tab.py lines 537-680.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from sw_transform.masw2d.gui.defaults import MASW2D_DEFAULTS


class MASW2DAdvancedSettings:
    """Advanced settings manager for MASW 2D processing.
    
    Holds all tk variables for advanced settings and provides
    the dialog UI.
    
    Usage:
        settings = MASW2DAdvancedSettings()
        settings.open_dialog(parent_window)
        
        values = settings.get_all_values()
        settings.reset_to_defaults()
    """
    
    def __init__(self):
        """Initialize all advanced settings variables.
        
        Copied from masw2d_tab.py lines 87-112.
        """
        # Transform settings
        self.grid_n_var = tk.StringVar(value=MASW2D_DEFAULTS['grid_n'])
        self.vspace_var = tk.StringVar(value=MASW2D_DEFAULTS['vspace'])
        self.tol_var = tk.StringVar(value=MASW2D_DEFAULTS['tol'])
        self.power_threshold_var = tk.StringVar(value=MASW2D_DEFAULTS['power_threshold'])
        self.vibrosis_var = tk.BooleanVar(value=MASW2D_DEFAULTS['vibrosis'])
        self.cylindrical_var = tk.BooleanVar(value=MASW2D_DEFAULTS['cylindrical'])
        
        # Preprocessing settings
        self.start_time_var = tk.StringVar(value=MASW2D_DEFAULTS['start_time'])
        self.end_time_var = tk.StringVar(value=MASW2D_DEFAULTS['end_time'])
        self.downsample_var = tk.BooleanVar(value=MASW2D_DEFAULTS['downsample'])
        self.down_factor_var = tk.StringVar(value=MASW2D_DEFAULTS['down_factor'])
        self.numf_var = tk.StringVar(value=MASW2D_DEFAULTS['numf'])
        
        # Image export settings
        self.plot_max_vel_var = tk.StringVar(value=MASW2D_DEFAULTS['plot_max_vel'])
        self.plot_max_freq_var = tk.StringVar(value=MASW2D_DEFAULTS['plot_max_freq'])
        self.cmap_var = tk.StringVar(value=MASW2D_DEFAULTS['cmap'])
        self.dpi_var = tk.StringVar(value=MASW2D_DEFAULTS['dpi'])
        
        # Auto-link: when vibrosis is checked, auto-check cylindrical
        self.vibrosis_var.trace_add('write', self._on_vibrosis_changed)
    
    def _on_vibrosis_changed(self, *args):
        """Auto-check cylindrical when vibrosis is enabled.
        
        Copied from masw2d_tab.py lines 682-685.
        """
        if self.vibrosis_var.get():
            self.cylindrical_var.set(True)
    
    def reset_to_defaults(self):
        """Reset all advanced settings to default values.
        
        Copied from masw2d_tab.py lines 545-560.
        """
        self.grid_n_var.set(MASW2D_DEFAULTS['grid_n'])
        self.vspace_var.set(MASW2D_DEFAULTS['vspace'])
        self.tol_var.set(MASW2D_DEFAULTS['tol'])
        self.power_threshold_var.set(MASW2D_DEFAULTS['power_threshold'])
        self.start_time_var.set(MASW2D_DEFAULTS['start_time'])
        self.end_time_var.set(MASW2D_DEFAULTS['end_time'])
        self.downsample_var.set(MASW2D_DEFAULTS['downsample'])
        self.down_factor_var.set(MASW2D_DEFAULTS['down_factor'])
        self.numf_var.set(MASW2D_DEFAULTS['numf'])
        self.plot_max_vel_var.set(MASW2D_DEFAULTS['plot_max_vel'])
        self.plot_max_freq_var.set(MASW2D_DEFAULTS['plot_max_freq'])
        self.cmap_var.set(MASW2D_DEFAULTS['cmap'])
        self.dpi_var.set(MASW2D_DEFAULTS['dpi'])
        self.vibrosis_var.set(MASW2D_DEFAULTS['vibrosis'])
        self.cylindrical_var.set(MASW2D_DEFAULTS['cylindrical'])
    
    def get_all_values(self) -> dict:
        """Get all settings values as a dictionary.
        
        Returns:
            Dict with all setting values.
        """
        return {
            'grid_n': self.grid_n_var.get(),
            'vspace': self.vspace_var.get(),
            'tol': self.tol_var.get(),
            'power_threshold': self.power_threshold_var.get(),
            'vibrosis': self.vibrosis_var.get(),
            'cylindrical': self.cylindrical_var.get(),
            'start_time': self.start_time_var.get(),
            'end_time': self.end_time_var.get(),
            'downsample': self.downsample_var.get(),
            'down_factor': self.down_factor_var.get(),
            'numf': self.numf_var.get(),
            'plot_max_vel': self.plot_max_vel_var.get(),
            'plot_max_freq': self.plot_max_freq_var.get(),
            'cmap': self.cmap_var.get(),
            'dpi': self.dpi_var.get(),
        }
    
    def open_dialog(self, parent: tk.Widget):
        """Open the advanced settings popup window.
        
        Copied from masw2d_tab.py lines 562-680.
        
        Args:
            parent: Parent window for the dialog.
        """
        popup = tk.Toplevel(parent)
        popup.title("Advanced Settings")
        popup.geometry("450x550")
        popup.resizable(True, True)
        popup.transient(parent)  # type: ignore[arg-type]
        popup.grab_set()
        
        # Main scrollable frame
        canvas = tk.Canvas(popup, highlightthickness=0)
        scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # ===== Transform Settings =====
        transform_frame = ttk.LabelFrame(scrollable, text="Transform Settings", padding=8)
        transform_frame.pack(fill="x", padx=8, pady=6)
        
        # Grid size (grid_n)
        row1 = ttk.Frame(transform_frame)
        row1.pack(fill="x", pady=3)
        ttk.Label(row1, text="Velocity Grid Size:", width=18).pack(side="left")
        ttk.Combobox(row1, textvariable=self.grid_n_var,
                     values=["500", "1000", "2000", "4000", "8000"],
                     width=10, state="readonly").pack(side="left", padx=4)
        ttk.Label(row1, text="points", foreground="gray").pack(side="left")
        
        # Velocity spacing (vspace)
        row2 = ttk.Frame(transform_frame)
        row2.pack(fill="x", pady=3)
        ttk.Label(row2, text="Velocity Spacing:", width=18).pack(side="left")
        ttk.Combobox(row2, textvariable=self.vspace_var,
                     values=["log", "linear"],
                     width=10, state="readonly").pack(side="left", padx=4)
        
        # Vibrosis mode
        row_vib = ttk.Frame(transform_frame)
        row_vib.pack(fill="x", pady=3)
        ttk.Checkbutton(row_vib, text="Vibrosis mode (FDBF weighting)",
                        variable=self.vibrosis_var).pack(side="left")
        
        # Cylindrical steering
        row_cyl = ttk.Frame(transform_frame)
        row_cyl.pack(fill="x", pady=3)
        ttk.Checkbutton(row_cyl, text="Cylindrical steering (FDBF near-field)",
                        variable=self.cylindrical_var).pack(side="left")
        
        # ===== Peak Picking Settings =====
        peak_frame = ttk.LabelFrame(scrollable, text="Peak Picking", padding=8)
        peak_frame.pack(fill="x", padx=8, pady=6)
        
        # Tolerance
        row3 = ttk.Frame(peak_frame)
        row3.pack(fill="x", pady=3)
        ttk.Label(row3, text="Tolerance:", width=18).pack(side="left")
        ttk.Entry(row3, textvariable=self.tol_var, width=12).pack(side="left", padx=4)
        ttk.Label(row3, text="(filter closely-spaced picks)", foreground="gray").pack(side="left")
        
        # Power threshold
        row4 = ttk.Frame(peak_frame)
        row4.pack(fill="x", pady=3)
        ttk.Label(row4, text="Power Threshold:", width=18).pack(side="left")
        ttk.Entry(row4, textvariable=self.power_threshold_var, width=12).pack(side="left", padx=4)
        ttk.Label(row4, text="(0.0-1.0)", foreground="gray").pack(side="left")
        
        # ===== Preprocessing Settings =====
        preproc_frame = ttk.LabelFrame(scrollable, text="Preprocessing", padding=8)
        preproc_frame.pack(fill="x", padx=8, pady=6)
        
        # Time window
        row5 = ttk.Frame(preproc_frame)
        row5.pack(fill="x", pady=3)
        ttk.Label(row5, text="Time Window:", width=18).pack(side="left")
        ttk.Entry(row5, textvariable=self.start_time_var, width=6).pack(side="left", padx=2)
        ttk.Label(row5, text="-").pack(side="left")
        ttk.Entry(row5, textvariable=self.end_time_var, width=6).pack(side="left", padx=2)
        ttk.Label(row5, text="sec", foreground="gray").pack(side="left", padx=4)
        
        # Downsample checkbox
        row6 = ttk.Frame(preproc_frame)
        row6.pack(fill="x", pady=3)
        ttk.Checkbutton(row6, text="Downsample", variable=self.downsample_var).pack(side="left")
        
        # Downsample factor
        row7 = ttk.Frame(preproc_frame)
        row7.pack(fill="x", pady=3)
        ttk.Label(row7, text="Downsample Factor:", width=18).pack(side="left")
        ttk.Combobox(row7, textvariable=self.down_factor_var,
                     values=["1", "2", "4", "8", "16", "32"],
                     width=10, state="readonly").pack(side="left", padx=4)
        
        # FFT size
        row8 = ttk.Frame(preproc_frame)
        row8.pack(fill="x", pady=3)
        ttk.Label(row8, text="FFT Size:", width=18).pack(side="left")
        ttk.Combobox(row8, textvariable=self.numf_var,
                     values=["1000", "2000", "4000", "8000"],
                     width=10, state="readonly").pack(side="left", padx=4)
        ttk.Label(row8, text="points", foreground="gray").pack(side="left")
        
        # ===== Image Export Settings =====
        image_frame = ttk.LabelFrame(scrollable, text="Image Export Options", padding=8)
        image_frame.pack(fill="x", padx=8, pady=6)
        
        # Max velocity for plots
        row9 = ttk.Frame(image_frame)
        row9.pack(fill="x", pady=3)
        ttk.Label(row9, text="Max Velocity (plot):", width=18).pack(side="left")
        ttk.Combobox(row9, textvariable=self.plot_max_vel_var,
                     values=["auto", "500", "1000", "1500", "2000", "3000", "5000"],
                     width=10).pack(side="left", padx=4)
        ttk.Label(row9, text="m/s", foreground="gray").pack(side="left")
        
        # Max frequency for plots
        row10 = ttk.Frame(image_frame)
        row10.pack(fill="x", pady=3)
        ttk.Label(row10, text="Max Frequency (plot):", width=18).pack(side="left")
        ttk.Combobox(row10, textvariable=self.plot_max_freq_var,
                     values=["auto", "50", "80", "100", "150", "200"],
                     width=10).pack(side="left", padx=4)
        ttk.Label(row10, text="Hz", foreground="gray").pack(side="left")
        
        # Colormap
        row11 = ttk.Frame(image_frame)
        row11.pack(fill="x", pady=3)
        ttk.Label(row11, text="Colormap:", width=18).pack(side="left")
        ttk.Combobox(row11, textvariable=self.cmap_var,
                     values=["jet", "viridis", "plasma", "turbo", "seismic", "hot"],
                     width=10, state="readonly").pack(side="left", padx=4)
        
        # DPI
        row12 = ttk.Frame(image_frame)
        row12.pack(fill="x", pady=3)
        ttk.Label(row12, text="DPI:", width=18).pack(side="left")
        ttk.Combobox(row12, textvariable=self.dpi_var,
                     values=["72", "100", "150", "200", "300"],
                     width=10, state="readonly").pack(side="left", padx=4)
        
        # ===== Buttons =====
        btn_frame = ttk.Frame(scrollable)
        btn_frame.pack(fill="x", padx=8, pady=12)
        
        ttk.Button(btn_frame, text="Reset to Defaults",
                   command=self.reset_to_defaults).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Close",
                   command=popup.destroy).pack(side="right", padx=4)
        
        # Center the window
        popup.update_idletasks()
        try:
            x = parent.winfo_rootx() + (parent.winfo_width() - popup.winfo_width()) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - popup.winfo_height()) // 2
            popup.geometry(f"+{x}+{y}")
        except Exception:
            pass
