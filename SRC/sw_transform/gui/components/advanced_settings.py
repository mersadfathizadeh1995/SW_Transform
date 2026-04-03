"""Advanced settings manager and dialog component.

Copied from simple_app.py:
- lines 133-144 (advanced settings tk variables)
- lines 417-420 (_on_vibrosis_changed)
- lines 422-453 (_reset_advanced_defaults)
- lines 455-462 (_toggle_vel_limits)
- lines 464-471 (_toggle_freq_limits)
- lines 473-638 (_open_advanced_settings dialog)
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from sw_transform.gui.utils.defaults import DEFAULTS


class AdvancedSettingsManager:
    """Manages all advanced settings tk variables.
    
    This class holds all the tk StringVar/BooleanVar objects for advanced
    settings, provides methods to get/set values, reset to defaults, and
    open the settings dialog.
    
    Usage:
        settings = AdvancedSettingsManager()
        
        # Get all values
        values = settings.get_all_values()
        
        # Open dialog
        settings.open_dialog(parent_window)
        
        # Reset to defaults
        settings.reset_to_defaults()
    """
    
    def __init__(self):
        """Initialize all advanced settings variables.
        
        Copied from simple_app.py lines 85-102 and 133-144.
        """
        # Transform settings - lines 89-93
        self.grid_fk_var = tk.StringVar(value=DEFAULTS['grid_fk'])
        self.tol_fk_var = tk.StringVar(value=DEFAULTS['tol_fk'])
        self.grid_ps_var = tk.StringVar(value=DEFAULTS['grid_ps'])
        self.vspace_ps_var = tk.StringVar(value=DEFAULTS['vspace_ps'])
        self.tol_ps_var = tk.StringVar(value=DEFAULTS['tol_ps'])
        
        # Mode flags - lines 71-73
        self.vibrosis_mode = tk.BooleanVar(value=DEFAULTS['vibrosis'])
        self.cylindrical_var = tk.BooleanVar(value=DEFAULTS['cylindrical'])
        
        # Vibrosis array config
        self.dx_var = tk.StringVar(value=DEFAULTS['dx'])
        
        # Preprocessing settings - lines 85-88
        self.downsample_var = tk.BooleanVar(value=DEFAULTS['downsample'])
        self.down_factor_var = tk.StringVar(value=DEFAULTS['down_factor'])
        self.numf_var = tk.StringVar(value=DEFAULTS['numf'])
        
        # Peak picking - line 133
        self.power_threshold_var = tk.StringVar(value=DEFAULTS['power_threshold'])
        
        # Plot/export settings - lines 134-144
        self.detailed_title_var = tk.BooleanVar(value=DEFAULTS['detailed_title'])
        self.auto_vel_limits_var = tk.BooleanVar(value=DEFAULTS['auto_vel_limits'])
        self.auto_freq_limits_var = tk.BooleanVar(value=DEFAULTS['auto_freq_limits'])
        self.plot_min_vel_var = tk.StringVar(value=DEFAULTS['plot_min_vel'])
        self.plot_max_vel_var = tk.StringVar(value=DEFAULTS['plot_max_vel'])
        self.plot_min_freq_var = tk.StringVar(value=DEFAULTS['plot_min_freq'])
        self.plot_max_freq_var = tk.StringVar(value=DEFAULTS['plot_max_freq'])
        self.freq_tick_spacing_var = tk.StringVar(value=DEFAULTS['freq_tick_spacing'])
        self.vel_tick_spacing_var = tk.StringVar(value=DEFAULTS['vel_tick_spacing'])
        self.cmap_var = tk.StringVar(value=DEFAULTS['cmap'])
        self.dpi_var = tk.StringVar(value=DEFAULTS['dpi'])
        self.export_spectra_var = tk.BooleanVar(value=DEFAULTS['export_spectra'])
        self.fig_width_var = tk.StringVar(value=DEFAULTS['fig_width'])
        self.fig_height_var = tk.StringVar(value=DEFAULTS['fig_height'])
        self.contour_levels_var = tk.StringVar(value=DEFAULTS['contour_levels'])
        self.plot_style_var = tk.StringVar(value=DEFAULTS['plot_style'])
        
        # Auto-link: when vibrosis is checked, auto-check cylindrical
        self.vibrosis_mode.trace_add('write', self._on_vibrosis_changed)
        
        # Entry widgets for toggle (set in dialog)
        self.plot_min_vel_entry = None
        self.plot_max_vel_entry = None
        self.plot_min_freq_entry = None
        self.plot_max_freq_entry = None
    
    def _on_vibrosis_changed(self, *args):
        """Auto-check cylindrical when vibrosis is enabled.
        
        Copied from simple_app.py lines 417-420.
        """
        if self.vibrosis_mode.get():
            self.cylindrical_var.set(True)
    
    def reset_to_defaults(self):
        """Reset all advanced settings to default values.
        
        Copied from simple_app.py lines 422-453.
        """
        self.grid_fk_var.set(DEFAULTS['grid_fk'])
        self.tol_fk_var.set(DEFAULTS['tol_fk'])
        self.grid_ps_var.set(DEFAULTS['grid_ps'])
        self.vspace_ps_var.set(DEFAULTS['vspace_ps'])
        self.tol_ps_var.set(DEFAULTS['tol_ps'])
        self.vibrosis_mode.set(DEFAULTS['vibrosis'])
        self.cylindrical_var.set(DEFAULTS['cylindrical'])
        self.downsample_var.set(DEFAULTS['downsample'])
        self.down_factor_var.set(DEFAULTS['down_factor'])
        self.numf_var.set(DEFAULTS['numf'])
        self.power_threshold_var.set(DEFAULTS['power_threshold'])
        self.detailed_title_var.set(DEFAULTS['detailed_title'])
        self.auto_vel_limits_var.set(DEFAULTS['auto_vel_limits'])
        self.auto_freq_limits_var.set(DEFAULTS['auto_freq_limits'])
        self.plot_min_vel_var.set(DEFAULTS['plot_min_vel'])
        self.plot_max_vel_var.set(DEFAULTS['plot_max_vel'])
        self.plot_min_freq_var.set(DEFAULTS['plot_min_freq'])
        self.plot_max_freq_var.set(DEFAULTS['plot_max_freq'])
        self.freq_tick_spacing_var.set(DEFAULTS['freq_tick_spacing'])
        self.vel_tick_spacing_var.set(DEFAULTS['vel_tick_spacing'])
        self.cmap_var.set(DEFAULTS['cmap'])
        self.dpi_var.set(DEFAULTS['dpi'])
        self.export_spectra_var.set(DEFAULTS['export_spectra'])
        self.dx_var.set(DEFAULTS['dx'])
        self.fig_width_var.set(DEFAULTS['fig_width'])
        self.fig_height_var.set(DEFAULTS['fig_height'])
        self.contour_levels_var.set(DEFAULTS['contour_levels'])
        self.plot_style_var.set(DEFAULTS['plot_style'])
        self._toggle_vel_limits()
        self._toggle_freq_limits()
    
    def _toggle_vel_limits(self):
        """Enable/disable velocity limit entries based on auto-limit checkbox.
        
        Copied from simple_app.py lines 455-462.
        """
        state = 'disabled' if self.auto_vel_limits_var.get() else 'normal'
        if self.plot_min_vel_entry is not None:
            self.plot_min_vel_entry.config(state=state)
            self.plot_max_vel_entry.config(state=state)
    
    def _toggle_freq_limits(self):
        """Enable/disable frequency limit entries based on auto-limit checkbox.
        
        Copied from simple_app.py lines 464-471.
        """
        state = 'disabled' if self.auto_freq_limits_var.get() else 'normal'
        if self.plot_min_freq_entry is not None:
            self.plot_min_freq_entry.config(state=state)
            self.plot_max_freq_entry.config(state=state)
    
    def get_all_values(self) -> dict:
        """Get all settings values as a dictionary.
        
        Returns:
            Dict with all setting values.
        """
        return {
            # Transform
            'grid_fk': self.grid_fk_var.get(),
            'tol_fk': self.tol_fk_var.get(),
            'grid_ps': self.grid_ps_var.get(),
            'vspace_ps': self.vspace_ps_var.get(),
            'tol_ps': self.tol_ps_var.get(),
            'vibrosis': self.vibrosis_mode.get(),
            'cylindrical': self.cylindrical_var.get(),
            'dx': self.dx_var.get(),
            # Preprocessing
            'downsample': self.downsample_var.get(),
            'down_factor': self.down_factor_var.get(),
            'numf': self.numf_var.get(),
            # Peak picking
            'power_threshold': self.power_threshold_var.get(),
            # Plot/export
            'auto_vel_limits': self.auto_vel_limits_var.get(),
            'auto_freq_limits': self.auto_freq_limits_var.get(),
            'plot_min_vel': self.plot_min_vel_var.get(),
            'plot_max_vel': self.plot_max_vel_var.get(),
            'plot_min_freq': self.plot_min_freq_var.get(),
            'plot_max_freq': self.plot_max_freq_var.get(),
            'freq_tick_spacing': self.freq_tick_spacing_var.get(),
            'vel_tick_spacing': self.vel_tick_spacing_var.get(),
            'cmap': self.cmap_var.get(),
            'dpi': self.dpi_var.get(),
            'export_spectra': self.export_spectra_var.get(),
            'fig_width': self.fig_width_var.get(),
            'fig_height': self.fig_height_var.get(),
            'contour_levels': self.contour_levels_var.get(),
            'plot_style': self.plot_style_var.get(),
        }
    
    # Comprehensive colormap list
    COLORMAPS = [
        # Perceptually uniform
        "viridis", "plasma", "inferno", "magma", "cividis",
        # Sequential
        "jet", "turbo", "hot", "coolwarm", "YlOrRd", "RdYlBu",
        "gnuplot", "gnuplot2", "CMRmap", "cubehelix", "nipy_spectral",
        # Diverging
        "seismic", "RdBu", "bwr", "PiYG", "PRGn",
        # Classic
        "rainbow", "hsv", "terrain", "ocean", "gist_earth", "gist_stern",
        # Reversed variants
        "jet_r", "viridis_r", "plasma_r", "inferno_r", "turbo_r",
        "hot_r", "seismic_r", "RdBu_r", "coolwarm_r",
    ]

    def open_dialog(self, parent: tk.Widget):
        """Open the advanced settings popup window with tabbed layout.
        
        Args:
            parent: Parent window for the dialog.
        """
        popup = tk.Toplevel(parent)
        popup.title("Advanced Settings")
        popup.geometry("500x540")
        popup.resizable(True, True)
        popup.transient(parent)
        popup.grab_set()

        # Notebook (tabs)
        notebook = ttk.Notebook(popup)
        notebook.pack(fill="both", expand=True, padx=6, pady=(6, 0))

        # ---------- Tab 1: Transform ----------
        t1 = tk.Frame(notebook, padx=10, pady=8)
        notebook.add(t1, text="Transform")

        # FK/FDBF
        fk_row = tk.Frame(t1); fk_row.pack(fill="x", pady=3)
        tk.Label(fk_row, text="FK/FDBF Grid Size:", width=18, anchor="w").pack(side="left")
        ttk.Combobox(fk_row, textvariable=self.grid_fk_var,
                     values=["500", "1000", "2000", "4000", "8000"],
                     width=8).pack(side="left", padx=4)
        tk.Label(fk_row, text="Tol:").pack(side="left", padx=(12, 0))
        tk.Entry(fk_row, textvariable=self.tol_fk_var, width=8).pack(side="left", padx=4)

        # PS/SS
        ps_row = tk.Frame(t1); ps_row.pack(fill="x", pady=3)
        tk.Label(ps_row, text="PS/SS Grid Size:", width=18, anchor="w").pack(side="left")
        ttk.Combobox(ps_row, textvariable=self.grid_ps_var,
                     values=["500", "1000", "1200", "2000", "4000", "8000"],
                     width=8).pack(side="left", padx=4)
        tk.Label(ps_row, text="Tol:").pack(side="left", padx=(12, 0))
        tk.Entry(ps_row, textvariable=self.tol_ps_var, width=8).pack(side="left", padx=4)

        sp_row = tk.Frame(t1); sp_row.pack(fill="x", pady=3)
        tk.Label(sp_row, text="PS/SS Spacing:", width=18, anchor="w").pack(side="left")
        ttk.Combobox(sp_row, textvariable=self.vspace_ps_var,
                     values=["log", "linear"], width=8, state="readonly").pack(side="left", padx=4)

        ttk.Separator(t1, orient="horizontal").pack(fill="x", pady=8)

        # Vibrosis / steering
        tk.Checkbutton(t1, text="Vibrosis mode (FDBF weighting)",
                       variable=self.vibrosis_mode).pack(anchor="w", pady=2)
        tk.Checkbutton(t1, text="Cylindrical steering (FDBF near-field)",
                       variable=self.cylindrical_var).pack(anchor="w", pady=2)

        dx_row = tk.Frame(t1); dx_row.pack(fill="x", pady=3)
        tk.Label(dx_row, text="Sensor Spacing (dx):", width=18, anchor="w").pack(side="left")
        tk.Entry(dx_row, textvariable=self.dx_var, width=10).pack(side="left", padx=4)
        tk.Label(dx_row, text="m", fg="gray").pack(side="left")
        tk.Label(t1, text="Channel count auto-detected from .mat files",
                 fg="gray", font=("TkDefaultFont", 8)).pack(anchor="w")

        # ---------- Tab 2: Preprocessing ----------
        t2 = tk.Frame(notebook, padx=10, pady=8)
        notebook.add(t2, text="Preprocessing")

        ds_row = tk.Frame(t2); ds_row.pack(fill="x", pady=3)
        tk.Checkbutton(ds_row, text="Downsample", variable=self.downsample_var).pack(side="left")
        tk.Label(ds_row, text="Factor:").pack(side="left", padx=(16, 0))
        ttk.Combobox(ds_row, textvariable=self.down_factor_var,
                     values=["1", "2", "4", "8", "16", "32"],
                     width=6, state="readonly").pack(side="left", padx=4)

        fft_row = tk.Frame(t2); fft_row.pack(fill="x", pady=3)
        tk.Label(fft_row, text="FFT Size (numf):", width=18, anchor="w").pack(side="left")
        ttk.Combobox(fft_row, textvariable=self.numf_var,
                     values=["1000", "2000", "4000", "8000"],
                     width=8).pack(side="left", padx=4)
        tk.Label(fft_row, text="points", fg="gray").pack(side="left")

        ttk.Separator(t2, orient="horizontal").pack(fill="x", pady=8)

        pt_row = tk.Frame(t2); pt_row.pack(fill="x", pady=3)
        tk.Label(pt_row, text="Power Threshold:", width=18, anchor="w").pack(side="left")
        tk.Entry(pt_row, textvariable=self.power_threshold_var, width=10).pack(side="left", padx=4)
        tk.Label(pt_row, text="(0.0–1.0)", fg="gray").pack(side="left")

        # ---------- Tab 3: Image Export ----------
        t3 = tk.Frame(notebook, padx=10, pady=8)
        notebook.add(t3, text="Image Export")

        # -- Figure Size --
        sz_lbl = tk.Label(t3, text="Figure Size", font=("TkDefaultFont", 9, "bold"))
        sz_lbl.pack(anchor="w", pady=(0, 2))

        sz_row = tk.Frame(t3); sz_row.pack(fill="x", pady=2)
        tk.Label(sz_row, text="Width:", width=8, anchor="w").pack(side="left")
        tk.Entry(sz_row, textvariable=self.fig_width_var, width=6).pack(side="left", padx=2)
        tk.Label(sz_row, text="Height:").pack(side="left", padx=(12, 0))
        tk.Entry(sz_row, textvariable=self.fig_height_var, width=6).pack(side="left", padx=2)
        tk.Label(sz_row, text="inches", fg="gray").pack(side="left", padx=4)

        # -- Plot Style & Contour --
        style_row = tk.Frame(t3); style_row.pack(fill="x", pady=3)
        tk.Label(style_row, text="Plot Style:", width=12, anchor="w").pack(side="left")
        ttk.Combobox(style_row, textvariable=self.plot_style_var,
                     values=["contourf", "pcolormesh"], width=12,
                     state="readonly").pack(side="left", padx=4)

        lvl_row = tk.Frame(t3); lvl_row.pack(fill="x", pady=3)
        tk.Label(lvl_row, text="Contour Levels:", width=12, anchor="w").pack(side="left")
        ttk.Combobox(lvl_row, textvariable=self.contour_levels_var,
                     values=["10", "15", "20", "30", "50", "100"],
                     width=8).pack(side="left", padx=4)

        # -- Colormap --
        cmap_row = tk.Frame(t3); cmap_row.pack(fill="x", pady=3)
        tk.Label(cmap_row, text="Colormap:", width=12, anchor="w").pack(side="left")
        ttk.Combobox(cmap_row, textvariable=self.cmap_var,
                     values=self.COLORMAPS,
                     width=16).pack(side="left", padx=4)

        ttk.Separator(t3, orient="horizontal").pack(fill="x", pady=6)

        # -- Axis Ranges --
        rng_lbl = tk.Label(t3, text="Axis Ranges", font=("TkDefaultFont", 9, "bold"))
        rng_lbl.pack(anchor="w", pady=(0, 2))

        vel_row = tk.Frame(t3); vel_row.pack(fill="x", pady=2)
        tk.Checkbutton(vel_row, text="Auto", variable=self.auto_vel_limits_var,
                       command=self._toggle_vel_limits).pack(side="left")
        tk.Label(vel_row, text="Velocity:", width=8, anchor="w").pack(side="left")
        self.plot_min_vel_entry = tk.Entry(vel_row, textvariable=self.plot_min_vel_var, width=7)
        self.plot_min_vel_entry.pack(side="left", padx=2)
        tk.Label(vel_row, text="to").pack(side="left", padx=2)
        self.plot_max_vel_entry = tk.Entry(vel_row, textvariable=self.plot_max_vel_var, width=7)
        self.plot_max_vel_entry.pack(side="left", padx=2)
        tk.Label(vel_row, text="m/s", fg="gray").pack(side="left", padx=2)

        freq_row = tk.Frame(t3); freq_row.pack(fill="x", pady=2)
        tk.Checkbutton(freq_row, text="Auto", variable=self.auto_freq_limits_var,
                       command=self._toggle_freq_limits).pack(side="left")
        tk.Label(freq_row, text="Frequency:", width=8, anchor="w").pack(side="left")
        self.plot_min_freq_entry = tk.Entry(freq_row, textvariable=self.plot_min_freq_var, width=7)
        self.plot_min_freq_entry.pack(side="left", padx=2)
        tk.Label(freq_row, text="to").pack(side="left", padx=2)
        self.plot_max_freq_entry = tk.Entry(freq_row, textvariable=self.plot_max_freq_var, width=7)
        self.plot_max_freq_entry.pack(side="left", padx=2)
        tk.Label(freq_row, text="Hz", fg="gray").pack(side="left", padx=2)

        self._toggle_vel_limits()
        self._toggle_freq_limits()

        # -- Tick Spacing --
        freq_tick_row = tk.Frame(t3); freq_tick_row.pack(fill="x", pady=2)
        tk.Label(freq_tick_row, text="Freq Ticks:", width=12, anchor="w").pack(side="left")
        ttk.Combobox(freq_tick_row, textvariable=self.freq_tick_spacing_var,
                     values=["auto", "1", "2", "5", "10", "20"],
                     width=8).pack(side="left", padx=2)
        tk.Label(freq_tick_row, text="Hz", fg="gray").pack(side="left", padx=2)

        vel_tick_row = tk.Frame(t3); vel_tick_row.pack(fill="x", pady=2)
        tk.Label(vel_tick_row, text="Vel Ticks:", width=12, anchor="w").pack(side="left")
        ttk.Combobox(vel_tick_row, textvariable=self.vel_tick_spacing_var,
                     values=["auto", "10", "25", "50", "100", "200"],
                     width=8).pack(side="left", padx=2)
        tk.Label(vel_tick_row, text="m/s", fg="gray").pack(side="left", padx=2)

        ttk.Separator(t3, orient="horizontal").pack(fill="x", pady=6)

        # -- Misc --
        misc_lbl = tk.Label(t3, text="Output Options", font=("TkDefaultFont", 9, "bold"))
        misc_lbl.pack(anchor="w", pady=(0, 2))

        dpi_row = tk.Frame(t3); dpi_row.pack(fill="x", pady=2)
        tk.Label(dpi_row, text="DPI:", width=12, anchor="w").pack(side="left")
        tk.Entry(dpi_row, textvariable=self.dpi_var, width=8).pack(side="left", padx=4)
        tk.Label(dpi_row, text="(72–600)", fg="gray").pack(side="left")

        tk.Checkbutton(t3, text="Detailed figure titles (source position + offset)",
                       variable=self.detailed_title_var).pack(anchor="w", pady=2)
        tk.Checkbutton(t3, text="Export power spectra (.npz)",
                       variable=self.export_spectra_var).pack(anchor="w", pady=2)

        # ===== Bottom buttons =====
        btn_frame = tk.Frame(popup)
        btn_frame.pack(fill="x", padx=10, pady=8)
        tk.Button(btn_frame, text="Reset to Defaults",
                  command=self.reset_to_defaults).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Close",
                  command=popup.destroy).pack(side="right", padx=4)

        # Center on parent
        popup.update_idletasks()
        try:
            x = parent.winfo_rootx() + (parent.winfo_width() - popup.winfo_width()) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - popup.winfo_height()) // 2
            popup.geometry(f"+{x}+{y}")
        except Exception:
            pass
