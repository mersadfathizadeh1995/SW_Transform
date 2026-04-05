"""MASW 2D Tab for the GUI - Component-Based Architecture.
Provides a complete interface for 2D MASW processing using modular components:
- ArraySetupPanel: Array configuration (channels, spacing, source type)
- FileManagerPanel: Shot file management (import, add, clear)
- SubarrayConfigPanel: Sub-array size selection and preview
- ProcessingPanel: Processing method and frequency/velocity limits
- OutputPanel: Output directory and parallel settings
- MASW2DRunPanel: Run button and progress
- LayoutPreviewPanel: Visual preview with matplotlib
"""
from __future__ import annotations
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional, Callable
# Import GUI components from masw2d.gui package
from sw_transform.masw2d.gui import (
    MASW2D_DEFAULTS,
    CollapsibleLabelFrame,
    ArraySetupPanel,
    FileManagerPanel,
    SubarrayConfigPanel,
    ProcessingPanel,
    OutputPanel,
    MASW2DRunPanel,
    LayoutPreviewPanel,
    MASW2DAdvancedSettings,
    AssignmentPanel,
)
class MASW2DTab:
    """MASW 2D processing tab widget using component-based architecture."""
    def __init__(self, parent: tk.Frame, log_callback: Optional[Callable[[str], None]] = None, 
                 main_app=None):
        """Initialize the MASW 2D tab.
        Parameters
        ----------
        parent : tk.Frame
            Parent frame to build the tab in
        log_callback : callable, optional
            Function to call for logging messages
        main_app : optional
            Reference to main app for importing project files
        """
        self.parent = parent
        self.log = log_callback or print
        self.main_app = main_app
        # Defaults
        self._DEFAULTS = MASW2D_DEFAULTS
        # === Advanced Settings Variables (shared with popup) ===
        self._create_advanced_variables()
        # Component references (set during build)
        self.array_panel: Optional[ArraySetupPanel] = None
        self.file_panel: Optional[FileManagerPanel] = None
        self.subarray_panel: Optional[SubarrayConfigPanel] = None
        self.processing_panel: Optional[ProcessingPanel] = None
        self.output_panel: Optional[OutputPanel] = None
        self.run_panel: Optional[MASW2DRunPanel] = None
        self.preview_panel: Optional[LayoutPreviewPanel] = None
        self.assignment_panel: Optional[AssignmentPanel] = None
        self._build_ui()
    def _create_advanced_variables(self):
        """Create tk variables for advanced settings."""
        # Transform settings
        self.grid_n_var = tk.StringVar(value=self._DEFAULTS['grid_n'])
        self.vspace_var = tk.StringVar(value=self._DEFAULTS['vspace'])
        self.tol_var = tk.StringVar(value=self._DEFAULTS['tol'])
        self.power_threshold_var = tk.StringVar(value=self._DEFAULTS['power_threshold'])
        self.vibrosis_var = tk.BooleanVar(value=self._DEFAULTS['vibrosis'])
        self.cylindrical_var = tk.BooleanVar(value=self._DEFAULTS['cylindrical'])
        # Auto-link: when vibrosis is checked, auto-check cylindrical
        self.vibrosis_var.trace_add('write', self._on_vibrosis_changed)
        # Preprocessing settings
        self.start_time_var = tk.StringVar(value=self._DEFAULTS['start_time'])
        self.end_time_var = tk.StringVar(value=self._DEFAULTS['end_time'])
        self.downsample_var = tk.BooleanVar(value=self._DEFAULTS['downsample'])
        self.down_factor_var = tk.StringVar(value=self._DEFAULTS['down_factor'])
        self.numf_var = tk.StringVar(value=self._DEFAULTS['numf'])
        # Image export settings
        self.plot_max_vel_var = tk.StringVar(value=self._DEFAULTS['plot_max_vel'])
        self.plot_max_freq_var = tk.StringVar(value=self._DEFAULTS['plot_max_freq'])
        self.cmap_var = tk.StringVar(value=self._DEFAULTS['cmap'])
        self.dpi_var = tk.StringVar(value=self._DEFAULTS['dpi'])
        self.fig_width_var = tk.StringVar(value=self._DEFAULTS.get('fig_width', '8'))
        self.fig_height_var = tk.StringVar(value=self._DEFAULTS.get('fig_height', '6'))
        self.contour_levels_var = tk.StringVar(value=self._DEFAULTS.get('contour_levels', '30'))
        self.plot_style_var = tk.StringVar(value=self._DEFAULTS.get('plot_style', 'contourf'))
    def _on_vibrosis_changed(self, *args):
        """Auto-check cylindrical when vibrosis is enabled."""
        if self.vibrosis_var.get():
            self.cylindrical_var.set(True)
    def _build_ui(self):
        """Build the tab interface using components."""
        # Main paned window: left (settings) | right (preview)
        paned = ttk.PanedWindow(self.parent, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=4, pady=4)
        # Left panel - Settings
        left = ttk.Frame(paned)
        paned.add(left, weight=1)
        # Right panel - Preview
        right = ttk.Frame(paned)
        paned.add(right, weight=2)
        self._build_left_panel(left)
        self._build_right_panel(right)
        # Initial update
        self._update_preview()
    def _build_left_panel(self, parent):
        """Build the left settings panel using components."""
        # Scrollable canvas for settings
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        # ===== 1. Array Setup Panel =====
        self._array_collapse = CollapsibleLabelFrame(scrollable, title="Array Setup")
        self._array_collapse.pack(fill="x", padx=4, pady=2)
        self.array_panel = ArraySetupPanel(
            self._array_collapse.content,
            on_update=self._on_array_updated
        )
        self.array_panel.pack(fill="x")
        # ===== 2. File Manager Panel =====
        self._file_collapse = CollapsibleLabelFrame(scrollable, title="Shot Files")
        self._file_collapse.pack(fill="x", padx=4, pady=2)
        self.file_panel = FileManagerPanel(
            self._file_collapse.content,
            main_app=self.main_app,
            log_callback=self.log,
            array_length_getter=self._get_array_length,
            on_files_changed=self._on_files_changed
        )
        self.file_panel.pack(fill="x")
        # ===== 3. Sub-Array Config Panel =====
        self._subarray_collapse = CollapsibleLabelFrame(scrollable, title="Sub-Array Configurations")
        self._subarray_collapse.pack(fill="x", padx=4, pady=2)
        self.subarray_panel = SubarrayConfigPanel(
            self._subarray_collapse.content,
            n_channels_getter=self._get_n_channels,
            on_preview_change=self._update_preview
        )
        self.subarray_panel.pack(fill="x")
        # ===== 4. Shot Assignment Panel =====
        self._assignment_collapse = CollapsibleLabelFrame(
            scrollable, title="Shot Assignment"
        )
        self._assignment_collapse.pack(fill="x", padx=4, pady=2)
        self.assignment_panel = AssignmentPanel(self._assignment_collapse.content)
        self.assignment_panel.pack(fill="x")
        # ===== 5. Processing Panel =====
        self._processing_collapse = CollapsibleLabelFrame(scrollable, title="Processing")
        self._processing_collapse.pack(fill="x", padx=4, pady=2)
        self.processing_panel = ProcessingPanel(
            self._processing_collapse.content,
            on_advanced_click=self._open_advanced_settings
        )
        self.processing_panel.pack(fill="x")
        # ===== 6. Output Panel =====
        self._output_collapse = CollapsibleLabelFrame(scrollable, title="Output")
        self._output_collapse.pack(fill="x", padx=4, pady=2)
        self.output_panel = OutputPanel(self._output_collapse.content)
        self.output_panel.pack(fill="x")
        # ===== 7. Run Panel =====
        self.run_panel = MASW2DRunPanel(
            scrollable,
            on_run=self._run_workflow
        )
        self.run_panel.pack(fill="x", padx=4, pady=8)
    def _build_right_panel(self, parent):
        """Build the right preview panel using component."""
        self.preview_panel = LayoutPreviewPanel(parent)
        self.preview_panel.pack(fill="both", expand=True)
    # ==================== Component Callbacks ====================
    def _get_n_channels(self) -> int:
        """Get current n_channels from array panel."""
        if self.array_panel:
            return self.array_panel.n_channels
        return 24
    def _get_array_length(self) -> float:
        """Get current array length from array panel."""
        if self.array_panel:
            values = self.array_panel.get_values()
            return values.get('array_length', 46.0)
        return 46.0
    def _on_array_updated(self):
        """Handle array configuration update."""
        # Update subarray checkboxes when array changes
        if self.subarray_panel:
            self.subarray_panel.update_checkboxes()
        # Update preview
        self._update_preview()
    def _on_files_changed(self):
        """Handle files added/removed — auto-detect array config from first file."""
        # Check if .mat files were added - auto-enable vibrosis mode
        if self.file_panel and self.file_panel.has_mat_files:
            self.vibrosis_var.set(True)
            self.cylindrical_var.set(True)
            self.log("Vibrosis .mat files detected - FDBF mode enabled")
        
        # Auto-detect receiver geometry from first file
        if not self.file_panel or not self.array_panel:
            return
        files = self.file_panel.files
        if not files:
            return
        first_file = files[0] if isinstance(files[0], str) else files[0].get('file', '')
        if not first_file:
            return
        try:
            n_ch = 0
            dx_val = 0.0
            if first_file.lower().endswith('.mat'):
                from sw_transform.processing.vibrosis import get_vibrosis_file_info
                info = get_vibrosis_file_info(first_file)
                n_ch = info.get('n_channels', 0)
                dx_val = info.get('dx', 0)
            else:
                from sw_transform.processing.seg2 import load_seg2_ar
                _, data, _, dx_val, _, _ = load_seg2_ar(first_file)
                n_ch = data.shape[1]
            # Update array panel — set whatever we detected
            if n_ch > 0 or dx_val > 0:
                self.array_panel.set_file_info(
                    n_ch if n_ch > 0 else self.array_panel.n_channels,
                    dx_val if dx_val > 0 else self.array_panel.dx,
                )
                self.log(f"Array auto-detected from file: {n_ch} channels, {dx_val:.2f} m spacing")
            else:
                self.log(f"Could not detect array info from file (channels={n_ch}, dx={dx_val})")
        except Exception as e:
            self.log(f"Could not auto-detect array config: {e}")
    def _update_preview(self):
        """Update the layout preview."""
        if not self.array_panel or not self.subarray_panel or not self.preview_panel:
            return
        array_values = self.array_panel.get_values()
        n_channels = array_values['n_channels']
        dx = array_values['dx']
        source_type = array_values['source_type']
        try:
            subarray_size = self.subarray_panel.preview_size
        except (ValueError, AttributeError):
            return
        if subarray_size > n_channels:
            return
        try:
            from sw_transform.masw2d.geometry.layout import (
                calculate_layout, format_layout_summary
            )
            layout = calculate_layout(n_channels, dx, subarray_size, source_type=source_type)
            # Update info text
            summary = format_layout_summary(layout)
            self.preview_panel.set_info_text(summary)
            # Update matplotlib preview
            self.preview_panel.update_preview(layout)
        except Exception as e:
            self.preview_panel.set_info_text(f"Preview error: {e}")
    # ==================== Advanced Settings ====================
    def _reset_advanced_defaults(self):
        """Reset all advanced settings to default values."""
        self.grid_n_var.set(self._DEFAULTS['grid_n'])
        self.vspace_var.set(self._DEFAULTS['vspace'])
        self.tol_var.set(self._DEFAULTS['tol'])
        self.power_threshold_var.set(self._DEFAULTS['power_threshold'])
        self.start_time_var.set(self._DEFAULTS['start_time'])
        self.end_time_var.set(self._DEFAULTS['end_time'])
        self.downsample_var.set(self._DEFAULTS['downsample'])
        self.down_factor_var.set(self._DEFAULTS['down_factor'])
        self.numf_var.set(self._DEFAULTS['numf'])
        self.plot_max_vel_var.set(self._DEFAULTS['plot_max_vel'])
        self.plot_max_freq_var.set(self._DEFAULTS['plot_max_freq'])
        self.cmap_var.set(self._DEFAULTS['cmap'])
        self.dpi_var.set(self._DEFAULTS['dpi'])
        self.vibrosis_var.set(self._DEFAULTS['vibrosis'])
        self.cylindrical_var.set(self._DEFAULTS['cylindrical'])
        self.fig_width_var.set(self._DEFAULTS.get('fig_width', '8'))
        self.fig_height_var.set(self._DEFAULTS.get('fig_height', '6'))
        self.contour_levels_var.set(self._DEFAULTS.get('contour_levels', '30'))
        self.plot_style_var.set(self._DEFAULTS.get('plot_style', 'contourf'))
    def _open_advanced_settings(self):
        """Open the advanced settings popup window."""
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
        # Transform Settings
        transform_frame = ttk.LabelFrame(scrollable, text="Transform Settings", padding=8)
        transform_frame.pack(fill="x", padx=8, pady=6)
        row1 = ttk.Frame(transform_frame)
        row1.pack(fill="x", pady=3)
        ttk.Label(row1, text="Velocity Grid Size:", width=18).pack(side="left")
        ttk.Combobox(row1, textvariable=self.grid_n_var,
                     values=["500", "1000", "2000", "4000", "8000"],
                     width=10, state="readonly").pack(side="left", padx=4)
        row2 = ttk.Frame(transform_frame)
        row2.pack(fill="x", pady=3)
        ttk.Label(row2, text="Velocity Spacing:", width=18).pack(side="left")
        ttk.Combobox(row2, textvariable=self.vspace_var,
                     values=["log", "linear"], width=10, state="readonly").pack(side="left", padx=4)
        row_vib = ttk.Frame(transform_frame)
        row_vib.pack(fill="x", pady=3)
        ttk.Checkbutton(row_vib, text="Vibrosis mode (FDBF weighting)", 
                        variable=self.vibrosis_var).pack(side="left")
        row_cyl = ttk.Frame(transform_frame)
        row_cyl.pack(fill="x", pady=3)
        ttk.Checkbutton(row_cyl, text="Cylindrical steering (FDBF near-field)", 
                        variable=self.cylindrical_var).pack(side="left")
        # Peak Picking
        peak_frame = ttk.LabelFrame(scrollable, text="Peak Picking", padding=8)
        peak_frame.pack(fill="x", padx=8, pady=6)
        row3 = ttk.Frame(peak_frame)
        row3.pack(fill="x", pady=3)
        ttk.Label(row3, text="Tolerance:", width=18).pack(side="left")
        ttk.Entry(row3, textvariable=self.tol_var, width=12).pack(side="left", padx=4)
        row4 = ttk.Frame(peak_frame)
        row4.pack(fill="x", pady=3)
        ttk.Label(row4, text="Power Threshold:", width=18).pack(side="left")
        ttk.Entry(row4, textvariable=self.power_threshold_var, width=12).pack(side="left", padx=4)
        # Preprocessing
        preproc_frame = ttk.LabelFrame(scrollable, text="Preprocessing", padding=8)
        preproc_frame.pack(fill="x", padx=8, pady=6)
        row5 = ttk.Frame(preproc_frame)
        row5.pack(fill="x", pady=3)
        ttk.Label(row5, text="Time Window:", width=18).pack(side="left")
        ttk.Entry(row5, textvariable=self.start_time_var, width=6).pack(side="left", padx=2)
        ttk.Label(row5, text="-").pack(side="left")
        ttk.Entry(row5, textvariable=self.end_time_var, width=6).pack(side="left", padx=2)
        ttk.Label(row5, text="sec", foreground="gray").pack(side="left", padx=4)
        row6 = ttk.Frame(preproc_frame)
        row6.pack(fill="x", pady=3)
        ttk.Checkbutton(row6, text="Downsample", variable=self.downsample_var).pack(side="left")
        row7 = ttk.Frame(preproc_frame)
        row7.pack(fill="x", pady=3)
        ttk.Label(row7, text="Downsample Factor:", width=18).pack(side="left")
        ttk.Combobox(row7, textvariable=self.down_factor_var,
                     values=["1", "2", "4", "8", "16", "32"],
                     width=10, state="readonly").pack(side="left", padx=4)
        row8 = ttk.Frame(preproc_frame)
        row8.pack(fill="x", pady=3)
        ttk.Label(row8, text="FFT Size:", width=18).pack(side="left")
        ttk.Combobox(row8, textvariable=self.numf_var,
                     values=["1000", "2000", "4000", "8000"],
                     width=10, state="readonly").pack(side="left", padx=4)
        # Image Export
        image_frame = ttk.LabelFrame(scrollable, text="Image Export Options", padding=8)
        image_frame.pack(fill="x", padx=8, pady=6)
        row9 = ttk.Frame(image_frame)
        row9.pack(fill="x", pady=3)
        ttk.Label(row9, text="Max Velocity (plot):", width=18).pack(side="left")
        ttk.Combobox(row9, textvariable=self.plot_max_vel_var,
                     values=["auto", "500", "1000", "1500", "2000", "3000", "5000"],
                     width=10).pack(side="left", padx=4)
        row10 = ttk.Frame(image_frame)
        row10.pack(fill="x", pady=3)
        ttk.Label(row10, text="Max Frequency (plot):", width=18).pack(side="left")
        ttk.Combobox(row10, textvariable=self.plot_max_freq_var,
                     values=["auto", "50", "80", "100", "150", "200"],
                     width=10).pack(side="left", padx=4)
        row11 = ttk.Frame(image_frame)
        row11.pack(fill="x", pady=3)
        ttk.Label(row11, text="Colormap:", width=18).pack(side="left")
        from sw_transform.gui.components.advanced_settings import AdvancedSettingsManager
        ttk.Combobox(row11, textvariable=self.cmap_var,
                     values=AdvancedSettingsManager.COLORMAPS,
                     width=16).pack(side="left", padx=4)
        row12 = ttk.Frame(image_frame)
        row12.pack(fill="x", pady=3)
        ttk.Label(row12, text="DPI:", width=18).pack(side="left")
        ttk.Combobox(row12, textvariable=self.dpi_var,
                     values=["72", "100", "150", "200", "300"],
                     width=10, state="readonly").pack(side="left", padx=4)
        # Figure size
        row13 = ttk.Frame(image_frame)
        row13.pack(fill="x", pady=3)
        ttk.Label(row13, text="Figure Width:", width=18).pack(side="left")
        ttk.Entry(row13, textvariable=self.fig_width_var, width=6).pack(side="left", padx=2)
        ttk.Label(row13, text="Height:").pack(side="left", padx=(8, 0))
        ttk.Entry(row13, textvariable=self.fig_height_var, width=6).pack(side="left", padx=2)
        ttk.Label(row13, text="in", foreground="gray").pack(side="left", padx=2)
        # Plot style and contour levels
        row14 = ttk.Frame(image_frame)
        row14.pack(fill="x", pady=3)
        ttk.Label(row14, text="Plot Style:", width=18).pack(side="left")
        ttk.Combobox(row14, textvariable=self.plot_style_var,
                     values=["contourf", "pcolormesh"],
                     width=12, state="readonly").pack(side="left", padx=4)
        row15 = ttk.Frame(image_frame)
        row15.pack(fill="x", pady=3)
        ttk.Label(row15, text="Contour Levels:", width=18).pack(side="left")
        ttk.Combobox(row15, textvariable=self.contour_levels_var,
                     values=["10", "15", "20", "30", "50", "100"],
                     width=10).pack(side="left", padx=4)
        # Buttons
        btn_frame = ttk.Frame(scrollable)
        btn_frame.pack(fill="x", padx=8, pady=12)
        ttk.Button(btn_frame, text="Reset to Defaults", 
                   command=self._reset_advanced_defaults).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Close", 
                   command=popup.destroy).pack(side="right", padx=4)
        popup.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - popup.winfo_width()) // 2
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() - popup.winfo_height()) // 2
        popup.geometry(f"+{x}+{y}")
    # ==================== Config Building ====================
    def _build_config(self) -> Dict[str, Any]:
        """Build configuration dictionary from component values."""
        array_values = self.array_panel.get_values()
        proc_values = self.processing_panel.get_values()
        output_values = self.output_panel.get_values()
        selected_sizes = self.subarray_panel.get_selected_sizes()
        slide_step = self.subarray_panel.slide_step
        if not selected_sizes:
            raise ValueError("No sub-array sizes selected")
        try:
            grid_n = int(self.grid_n_var.get())
            tol = float(self.tol_var.get())
            power_threshold = float(self.power_threshold_var.get())
            start_time = float(self.start_time_var.get())
            end_time = float(self.end_time_var.get())
            down_factor = int(self.down_factor_var.get())
            numf = int(self.numf_var.get())
            plot_max_vel_str = self.plot_max_vel_var.get()
            plot_max_vel = None if plot_max_vel_str == 'auto' else float(plot_max_vel_str)
            auto_velocity_limit = (plot_max_vel_str == 'auto')
            plot_max_freq_str = self.plot_max_freq_var.get()
            plot_max_freq = None if plot_max_freq_str == 'auto' else float(plot_max_freq_str)
            auto_frequency_limit = (plot_max_freq_str == 'auto')
            dpi = int(self.dpi_var.get())
        except ValueError as e:
            raise ValueError(f"Invalid numeric value in advanced settings: {e}")
        from sw_transform.masw2d.config.templates import generate_subarray_configs
        subarray_configs = generate_subarray_configs(selected_sizes, slide_step, naming="depth")
        shots_config = []
        for shot in self.file_panel.data:
            shots_config.append({
                "file": shot["file"],
                "source_position": shot["source_position"],
                "force_reverse": shot.get("reverse", False)
            })
        config = {
            "survey_name": "GUI_MASW_2D",
            "version": "1.0",
            "array": {
                "n_channels": array_values['n_channels'],
                "dx": array_values['dx'],
                "first_channel_position": 0.0
            },
            "shots": shots_config,
            "subarray_configs": subarray_configs,
            "processing": {
                "method": proc_values['method'],
                "freq_min": proc_values['freq_min'],
                "freq_max": proc_values['freq_max'],
                "velocity_min": proc_values['vel_min'],
                "velocity_max": proc_values['vel_max'],
                "grid_n": grid_n,
                "tol": tol,
                "power_threshold": power_threshold,
                "vspace": self.vspace_var.get(),
                "source_type": "vibrosis" if self.vibrosis_var.get() else "hammer",
                "cylindrical": self.cylindrical_var.get(),
                "start_time": start_time,
                "end_time": end_time,
                "downsample": self.downsample_var.get(),
                "down_factor": down_factor,
                "numf": numf
            },
            "output": {
                "directory": output_values['output_dir'] or "./output_2d/",
                "organize_by": "midpoint",
                "export_formats": ["csv", "npz", "image"],
                "include_images": output_values['include_images'],
                "export_individual_npz": output_values.get('export_individual_npz', True),
                "export_combined_csv_per_midpoint": output_values.get(
                    'export_combined_csv_per_midpoint', True),
                "export_combined_npz_per_midpoint": output_values.get(
                    'export_combined_npz_per_midpoint', True),
                "generate_summary": output_values.get('generate_summary', True),
                "export_midpoint_summary": output_values.get('export_midpoint_summary', True),
                "export_all_picks": output_values.get('export_all_picks', True),
                "export_combined_npz": output_values.get('export_combined_npz', False),
                "max_velocity": plot_max_vel,
                "max_frequency": plot_max_freq,
                "auto_velocity_limit": auto_velocity_limit,
                "auto_frequency_limit": auto_frequency_limit,
                "cmap": self.cmap_var.get(),
                "image_dpi": dpi,
                "fig_width": self.fig_width_var.get(),
                "fig_height": self.fig_height_var.get(),
                "contour_levels": self.contour_levels_var.get(),
                "plot_style": self.plot_style_var.get()
            }
        }
        # Assignment section (only when panel is enabled)
        if self.assignment_panel:
            assign_cfg = self.assignment_panel.get_config()
            if assign_cfg is not None:
                config["assignment"] = assign_cfg
        return config
    # ==================== Workflow Execution ====================
    def _run_workflow(self):
        """Run the 2D MASW workflow."""
        try:
            config = self._build_config()
        except ValueError as e:
            messagebox.showerror("Configuration Error", str(e))
            return
        shot_files = self.file_panel.files
        if not shot_files:
            messagebox.showwarning("No Files", "Please add shot files first.")
            return
        output_dir = self.output_panel.output_dir
        if not output_dir:
            messagebox.showwarning("No Output", "Please select an output directory.")
            return
        mat_files = [f for f in shot_files if f.lower().endswith('.mat')]
        seg2_files = [f for f in shot_files if not f.lower().endswith('.mat')]
        if mat_files and seg2_files:
            result = messagebox.askyesno(
                "Mixed File Types",
                f"You have both .mat ({len(mat_files)}) and SEG-2 ({len(seg2_files)}) files.\n\n"
                "It's recommended to process them separately.\n"
                "Do you want to continue with .mat files only?\n\n"
                "(Click No to process SEG-2 files only)"
            )
            if result:
                seg2_files = []
            else:
                mat_files = []
        use_vibrosis = len(mat_files) > 0
        if use_vibrosis and self.processing_panel.method != "fdbf":
            messagebox.showinfo(
                "Vibrosis Mode",
                "Vibrosis .mat files can only use FDBF method.\n"
                "Processing will use FDBF regardless of selection."
            )
        self.run_panel.set_progress(0, "Running...")
        def run_thread():
            try:
                if use_vibrosis:
                    from sw_transform.masw2d.workflows import VibrosisMASWWorkflow
                    config['mat_files'] = mat_files
                    config['processing']['cylindrical'] = True
                    workflow = VibrosisMASWWorkflow(config)
                    def progress_cb(current, total, msg):
                        pct = (current / total * 100) if total > 0 else 0
                        self.parent.after(0, lambda: self.run_panel.set_progress(pct, msg))
                    workflow.set_progress_callback(progress_cb)
                    results = workflow.run(mat_files=mat_files, output_dir=output_dir)
                else:
                    use_assignment = "assignment" in config
                    if use_assignment:
                        from sw_transform.masw2d.workflows import AssignedMASWWorkflow
                        workflow = AssignedMASWWorkflow(config)
                    else:
                        from sw_transform.masw2d.workflows import StandardMASWWorkflow
                        workflow = StandardMASWWorkflow(config)
                    output_values = self.output_panel.get_values()
                    def progress_cb(current, total, msg):
                        pct = (current / total * 100) if total > 0 else 0
                        self.parent.after(0, lambda: self.run_panel.set_progress(pct, msg))
                    workflow.set_progress_callback(progress_cb)
                    results = workflow.run(
                        output_dir=output_dir,
                        parallel=output_values['parallel'],
                        max_workers=output_values['max_workers']
                    )
                self.parent.after(0, lambda: self._on_workflow_complete(results))
            except Exception as e:
                import traceback
                error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
                self.parent.after(0, lambda: self._on_workflow_error(error_msg))
        threading.Thread(target=run_thread, daemon=True).start()
    def _on_workflow_complete(self, results):
        """Handle workflow completion."""
        self.run_panel.set_progress(100, "Complete!")
        n_results = results.get("n_results", 0)
        n_midpoints = results.get("n_midpoints", 0)
        status = results.get("status", "unknown")
        if status == "success":
            self.run_panel.set_status(f"Complete! {n_results} curves at {n_midpoints} midpoints.")
            self.log(f"MASW 2D complete: {n_results} results at {n_midpoints} midpoints")
            messagebox.showinfo("Complete", f"Workflow finished.\n{n_results} dispersion curves\nat {n_midpoints} midpoint locations.")
        else:
            error = results.get("error", "Unknown error")
            self.run_panel.set_status(f"Error: {error}")
            self.log(f"MASW 2D error: {error}")
            messagebox.showerror("Workflow Error", error)
    def _on_workflow_error(self, error_msg):
        """Handle workflow error."""
        self.run_panel.set_progress(0, "Error")
        self.run_panel.set_status(f"Error: {error_msg[:50]}...")
        self.log(f"MASW 2D error: {error_msg}")
        messagebox.showerror("Workflow Error", error_msg)
def create_masw2d_tab(notebook: ttk.Notebook, log_callback=None, main_app=None) -> MASW2DTab:
    """Factory function to create and add MASW 2D tab to a notebook."""
    frame = ttk.Frame(notebook)
    notebook.add(frame, text="MASW 2D")
    tab = MASW2DTab(frame, log_callback, main_app)
    
    # Auto-sync files when MASW 2D tab is activated
    def on_tab_change(event):
        try:
            current = notebook.select()
            tab_text = notebook.tab(current, "text")
            if tab_text == "MASW 2D" and tab.file_panel and main_app:
                tab.file_panel.sync_from_main_app()
        except Exception:
            pass
    
    notebook.bind("<<NotebookTabChanged>>", on_tab_change)
    return tab
