"""MASW 2D Tab for the GUI.

Provides a complete interface for 2D MASW processing with:
- Array setup (channels, spacing, file selection)
- Sub-array configuration with visual layout preview
- Processing settings
- Workflow execution

This module has been refactored to use components from sw_transform.masw2d.gui.
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Any, Dict, List, Optional, Callable
import threading

# Import GUI components
from sw_transform.masw2d.gui import (
    MASW2D_DEFAULTS,
    ArraySetupPanel,
    FileManagerPanel,
    SubarrayConfigPanel,
    ProcessingPanel,
    OutputPanel,
    MASW2DRunPanel,
    LayoutPreviewPanel,
    MASW2DAdvancedSettings,
)


class MASW2DTab:
    """MASW 2D processing tab widget."""
    
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
        
        # State variables
        self.shot_files: List[str] = []
        self.shot_data: List[Dict[str, Any]] = []  # file, offset, reverse, source_position
        self.config: Dict[str, Any] = {}
        self.canvas_widget = None
        self.current_layout = None
        
        # Tkinter variables
        self.n_channels_var = tk.StringVar(value="24")
        self.dx_var = tk.StringVar(value="2.0")
        self.subarray_var = tk.StringVar(value="12")  # Currently selected for preview
        self.slide_step_var = tk.StringVar(value="1")
        self.source_type_var = tk.StringVar(value="hammer")  # Source type for depth estimation
        self.method_var = tk.StringVar(value="ps")
        self.freq_min_var = tk.StringVar(value="5")
        self.freq_max_var = tk.StringVar(value="80")
        self.vel_min_var = tk.StringVar(value="100")
        self.vel_max_var = tk.StringVar(value="1500")
        self.output_dir_var = tk.StringVar(value="")
        self.parallel_var = tk.BooleanVar(value=True)
        self.worker_var = tk.StringVar(value="auto")
        self.include_images_var = tk.BooleanVar(value=True)  # Enable images by default
        
        # === Advanced Settings Variables ===
        # Use defaults from masw2d.gui.defaults
        self._DEFAULTS = MASW2D_DEFAULTS
        
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
        
        # Selected sub-array sizes (checkboxes)
        self.subarray_checks: Dict[int, tk.BooleanVar] = {}
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the tab interface."""
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
    
    def _build_left_panel(self, parent):
        """Build the left settings panel."""
        # Scrollable canvas for settings
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # ===== Array Setup =====
        arr_frame = ttk.LabelFrame(scrollable, text="Array Setup", padding=6)
        arr_frame.pack(fill="x", padx=4, pady=4)
        
        row1 = ttk.Frame(arr_frame)
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="Total Channels:").pack(side="left")
        ttk.Entry(row1, textvariable=self.n_channels_var, width=6).pack(side="left", padx=4)
        ttk.Label(row1, text="Spacing (dx):").pack(side="left", padx=(10, 0))
        ttk.Entry(row1, textvariable=self.dx_var, width=6).pack(side="left", padx=4)
        ttk.Label(row1, text="m").pack(side="left")
        
        row2 = ttk.Frame(arr_frame)
        row2.pack(fill="x", pady=4)
        ttk.Button(row2, text="Update Array", command=self._update_array).pack(side="left")
        self.array_info_label = ttk.Label(row2, text="Length: -- m")
        self.array_info_label.pack(side="left", padx=10)
        
        # Source type for depth estimation
        row3 = ttk.Frame(arr_frame)
        row3.pack(fill="x", pady=2)
        ttk.Label(row3, text="Source Type:").pack(side="left")
        from sw_transform.masw2d.config.templates import SOURCE_LABELS
        source_values = list(SOURCE_LABELS.keys())
        source_combo = ttk.Combobox(row3, textvariable=self.source_type_var,
                                    values=source_values, width=15, state="readonly")
        source_combo.pack(side="left", padx=4)
        source_combo.bind("<<ComboboxSelected>>", lambda e: self._update_preview())
        # Show label for selected source
        self.source_label = ttk.Label(row3, text="(Sledgehammer 5-8 kg)", foreground="gray")
        self.source_label.pack(side="left", padx=4)
        
        # ===== Shot Files =====
        shot_frame = ttk.LabelFrame(scrollable, text="Shot Files", padding=6)
        shot_frame.pack(fill="x", padx=4, pady=4)
        
        btn_row = ttk.Frame(shot_frame)
        btn_row.pack(fill="x", pady=2)
        ttk.Button(btn_row, text="Import from Project", command=self._import_from_project).pack(side="left")
        ttk.Button(btn_row, text="Add Files...", command=self._add_shot_files).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Clear", command=self._clear_shot_files).pack(side="left", padx=4)
        
        # Treeview with columns for file, offset, reverse, source position
        columns = ("File", "Offset", "Rev", "Source Pos")
        self.shot_tree = ttk.Treeview(shot_frame, columns=columns, show="headings", height=5)
        self.shot_tree.heading("File", text="File")
        self.shot_tree.heading("Offset", text="Offset")
        self.shot_tree.heading("Rev", text="Rev")
        self.shot_tree.heading("Source Pos", text="Source Pos")
        self.shot_tree.column("File", width=120)
        self.shot_tree.column("Offset", width=60)
        self.shot_tree.column("Rev", width=40)
        self.shot_tree.column("Source Pos", width=80)
        self.shot_tree.pack(fill="x", pady=4)
        
        # ===== Sub-Array Configs =====
        sa_frame = ttk.LabelFrame(scrollable, text="Sub-Array Configurations", padding=6)
        sa_frame.pack(fill="x", padx=4, pady=4)
        
        # Quick select buttons
        btn_row = ttk.Frame(sa_frame)
        btn_row.pack(fill="x", pady=2)
        ttk.Button(btn_row, text="All", width=5, command=self._select_all_subarrays).pack(side="left", padx=2)
        ttk.Button(btn_row, text="None", width=5, command=self._select_no_subarrays).pack(side="left", padx=2)
        ttk.Button(btn_row, text="Even", width=5, command=self._select_even_subarrays).pack(side="left", padx=2)
        
        # Checkboxes container
        self.sa_check_frame = ttk.Frame(sa_frame)
        self.sa_check_frame.pack(fill="x", pady=2)
        
        row_ss = ttk.Frame(sa_frame)
        row_ss.pack(fill="x", pady=4)
        ttk.Label(row_ss, text="Slide Step:").pack(side="left")
        ttk.Entry(row_ss, textvariable=self.slide_step_var, width=4).pack(side="left", padx=4)
        ttk.Label(row_ss, text="channels").pack(side="left")
        
        # Preview selector
        row_prev = ttk.Frame(sa_frame)
        row_prev.pack(fill="x", pady=4)
        ttk.Label(row_prev, text="Preview:").pack(side="left")
        self.preview_combo = ttk.Combobox(row_prev, textvariable=self.subarray_var, 
                                          width=8, state="readonly")
        self.preview_combo.pack(side="left", padx=4)
        self.preview_combo.bind("<<ComboboxSelected>>", lambda e: self._update_preview())
        
        # Initialize checkboxes (first time - use even numbers as default)
        self._first_update = True
        self._update_subarray_checkboxes()
        
        # ===== Processing Settings =====
        proc_frame = ttk.LabelFrame(scrollable, text="Processing", padding=6)
        proc_frame.pack(fill="x", padx=4, pady=4)
        
        row_method = ttk.Frame(proc_frame)
        row_method.pack(fill="x", pady=2)
        ttk.Label(row_method, text="Method:").pack(side="left")
        method_combo = ttk.Combobox(row_method, textvariable=self.method_var,
                                    values=["fk", "ps", "fdbf", "ss"],
                                    width=8, state="readonly")
        method_combo.pack(side="left", padx=4)
        
        row_freq = ttk.Frame(proc_frame)
        row_freq.pack(fill="x", pady=2)
        ttk.Label(row_freq, text="Freq:").pack(side="left")
        ttk.Entry(row_freq, textvariable=self.freq_min_var, width=6).pack(side="left", padx=2)
        ttk.Label(row_freq, text="-").pack(side="left")
        ttk.Entry(row_freq, textvariable=self.freq_max_var, width=6).pack(side="left", padx=2)
        ttk.Label(row_freq, text="Hz").pack(side="left")
        
        row_vel = ttk.Frame(proc_frame)
        row_vel.pack(fill="x", pady=2)
        ttk.Label(row_vel, text="Velocity:").pack(side="left")
        ttk.Entry(row_vel, textvariable=self.vel_min_var, width=6).pack(side="left", padx=2)
        ttk.Label(row_vel, text="-").pack(side="left")
        ttk.Entry(row_vel, textvariable=self.vel_max_var, width=6).pack(side="left", padx=2)
        ttk.Label(row_vel, text="m/s").pack(side="left")
        
        # Advanced Settings button
        row_adv = ttk.Frame(proc_frame)
        row_adv.pack(fill="x", pady=4)
        ttk.Button(row_adv, text="⚙ Advanced Settings...", 
                   command=self._open_advanced_settings).pack(side="left")
        
        # ===== Output Settings =====
        out_frame = ttk.LabelFrame(scrollable, text="Output", padding=6)
        out_frame.pack(fill="x", padx=4, pady=4)
        
        row_dir = ttk.Frame(out_frame)
        row_dir.pack(fill="x", pady=2)
        ttk.Entry(row_dir, textvariable=self.output_dir_var, width=30).pack(side="left", fill="x", expand=True)
        ttk.Button(row_dir, text="Browse...", command=self._select_output_dir).pack(side="left", padx=4)
        
        row_par = ttk.Frame(out_frame)
        row_par.pack(fill="x", pady=4)
        ttk.Checkbutton(row_par, text="Parallel", variable=self.parallel_var).pack(side="left")
        ttk.Label(row_par, text="Workers:").pack(side="left", padx=(10, 2))
        import multiprocessing
        max_cpu = multiprocessing.cpu_count()
        worker_combo = ttk.Combobox(row_par, textvariable=self.worker_var,
                                     values=["auto"] + [str(i) for i in range(1, max_cpu + 1)],
                                     width=5, state="readonly")
        worker_combo.pack(side="left")
        
        # Image export option
        row_img = ttk.Frame(out_frame)
        row_img.pack(fill="x", pady=2)
        ttk.Checkbutton(row_img, text="Export Dispersion Images", variable=self.include_images_var).pack(side="left")
        
        # ===== Run Button =====
        run_frame = ttk.Frame(scrollable)
        run_frame.pack(fill="x", padx=4, pady=8)
        
        ttk.Button(run_frame, text="Run 2D MASW Workflow", 
                   command=self._run_workflow).pack(fill="x", pady=4)
        
        # Progress
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(run_frame, variable=self.progress_var,
                                             mode="determinate")
        self.progress_bar.pack(fill="x", pady=2)
        self.status_label = ttk.Label(run_frame, text="Ready")
        self.status_label.pack(fill="x")
    
    def _build_right_panel(self, parent):
        """Build the right preview panel."""
        # Info panel at top
        info_frame = ttk.LabelFrame(parent, text="Configuration Info", padding=6)
        info_frame.pack(fill="x", padx=4, pady=4)
        
        self.info_text = tk.Text(info_frame, height=6, wrap="word", state="disabled",
                                  font=("Consolas", 9))
        self.info_text.pack(fill="x")
        
        # Layout preview
        preview_frame = ttk.LabelFrame(parent, text="Layout Preview", padding=6)
        preview_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        self.preview_container = ttk.Frame(preview_frame)
        self.preview_container.pack(fill="both", expand=True)
        
        # Initial update
        self._update_array()
    
    def _select_all_subarrays(self):
        """Select all sub-array sizes."""
        for var in self.subarray_checks.values():
            var.set(True)
    
    def _select_no_subarrays(self):
        """Deselect all sub-array sizes."""
        for var in self.subarray_checks.values():
            var.set(False)
    
    def _select_even_subarrays(self):
        """Select only even sub-array sizes."""
        for size, var in self.subarray_checks.items():
            var.set(size % 2 == 0)
    
    def _update_subarray_checkboxes(self):
        """Update the sub-array configuration checkboxes."""
        # Preserve previously selected sizes
        previously_selected = {size for size, var in self.subarray_checks.items() if var.get()}
        
        # Clear existing widgets
        for widget in self.sa_check_frame.winfo_children():
            widget.destroy()
        self.subarray_checks.clear()
        
        try:
            n_channels = int(self.n_channels_var.get())
        except ValueError:
            n_channels = 24
        
        # Create checkboxes for each valid size
        from sw_transform.masw2d.config.templates import get_available_subarray_sizes
        sizes = get_available_subarray_sizes(n_channels, min_channels=6)
        
        # Determine which to select:
        # - On first update, use even numbers as default
        # - Keep previously selected if still valid
        # - Otherwise default to even numbers
        if getattr(self, '_first_update', False):
            # First time: select even numbers
            valid_previous = {s for s in sizes if s % 2 == 0}
            self._first_update = False
        else:
            valid_previous = previously_selected.intersection(set(sizes))
            if not valid_previous:
                # Fallback: select even numbers
                valid_previous = {s for s in sizes if s % 2 == 0}
        
        # Create grid of checkboxes (4 per row)
        cols = 4
        row_frame = None
        for i, size in enumerate(sizes):
            col_idx = i % cols
            
            # Create row frame if needed
            if col_idx == 0:
                row_frame = ttk.Frame(self.sa_check_frame)
                row_frame.pack(fill="x", pady=1)
            
            var = tk.BooleanVar(value=(size in valid_previous))
            self.subarray_checks[size] = var
            
            cb = ttk.Checkbutton(row_frame, text=f"{size}ch", variable=var,
                                 command=self._on_subarray_check_changed)
            cb.pack(side="left", padx=4)
        
        # Update preview combo
        self._update_preview_combo()
    
    def _update_preview_combo(self):
        """Update the preview size combobox."""
        try:
            n_channels = int(self.n_channels_var.get())
        except ValueError:
            n_channels = 24
        
        from sw_transform.masw2d.config.templates import get_available_subarray_sizes
        sizes = get_available_subarray_sizes(n_channels, min_channels=6)
        
        self.preview_combo['values'] = [str(s) for s in sizes]
        
        # Set to middle value if current not valid
        current = self.subarray_var.get()
        if current not in [str(s) for s in sizes]:
            mid = sizes[len(sizes) // 2]
            self.subarray_var.set(str(mid))
    
    def _on_subarray_check_changed(self):
        """Handle checkbox state change."""
        # Could update summary or enable/disable run button
        pass
    
    def _update_array(self):
        """Update array info and refresh previews."""
        try:
            n_channels = int(self.n_channels_var.get())
            dx = float(self.dx_var.get())
        except ValueError:
            self.array_info_label.config(text="Invalid values")
            return
        
        length = (n_channels - 1) * dx
        self.array_info_label.config(text=f"Length: {length:.1f} m")
        
        # Update checkboxes
        self._update_subarray_checkboxes()
        
        # Update preview
        self._update_preview()
    
    def _update_preview(self):
        """Update the layout preview."""
        try:
            n_channels = int(self.n_channels_var.get())
            dx = float(self.dx_var.get())
            subarray_size = int(self.subarray_var.get())
        except ValueError:
            return
        
        if subarray_size > n_channels:
            return
        
        source_type = self.source_type_var.get()
        
        # Update source label
        from sw_transform.masw2d.config.templates import get_source_label
        self.source_label.config(text=f"({get_source_label(source_type)})")
        
        # Calculate layout info
        from sw_transform.masw2d.geometry.layout import (
            calculate_layout, format_layout_summary, plot_layout
        )
        
        layout = calculate_layout(n_channels, dx, subarray_size, source_type=source_type)
        self.current_layout = layout
        
        # Update info text
        summary = format_layout_summary(layout)
        self.info_text.config(state="normal")
        self.info_text.delete("1.0", "end")
        self.info_text.insert("1.0", summary)
        self.info_text.config(state="disabled")
        
        # Update matplotlib preview
        self._update_matplotlib_preview(layout)
    
    def _update_matplotlib_preview(self, layout):
        """Update the matplotlib canvas preview."""
        # Clear existing
        for widget in self.preview_container.winfo_children():
            widget.destroy()
        
        try:
            import matplotlib
            matplotlib.use('TkAgg')
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
            from sw_transform.masw2d.geometry.layout import plot_layout
            
            # Create figure
            fig = Figure(figsize=(8, 5), dpi=100)
            
            # Create axes for layout plot
            ax_layout = fig.add_subplot(211)
            ax_depth = fig.add_subplot(212)
            
            # Plot layout on provided axes (simplified version)
            self._plot_layout_on_axes(layout, ax_layout, ax_depth)
            
            fig.tight_layout()
            
            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, self.preview_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            self.canvas_widget = canvas
            
        except ImportError as e:
            ttk.Label(self.preview_container, 
                     text=f"Matplotlib not available: {e}").pack()
        except Exception as e:
            ttk.Label(self.preview_container,
                     text=f"Preview error: {e}").pack()
    
    def _plot_layout_on_axes(self, layout, ax_layout, ax_depth):
        """Plot layout on provided axes."""
        import numpy as np
        
        # Colors
        c_geophone = "#2196F3"
        c_subarray = "#4CAF50"
        c_highlight = "#FF5722"
        c_depth = "#795548"
        
        # Draw geophone positions
        geophone_y = 0.5
        positions = np.arange(layout.total_channels) * layout.dx
        
        ax_layout.scatter(positions, [geophone_y] * layout.total_channels,
                         s=60, c="#BBDEFB", edgecolors=c_geophone,
                         linewidths=1.5, zorder=10, marker='v')
        ax_layout.hlines(geophone_y, 0, layout.total_length,
                        colors=c_geophone, linewidth=2, zorder=5)
        
        # Draw all sub-array positions faintly
        for i in range(layout.n_subarrays):
            mid = layout.midpoints[i]
            half = layout.subarray_length / 2
            ax_layout.axvspan(mid - half, mid + half, alpha=0.1, 
                             color=c_subarray, zorder=1)
        
        # Highlight middle sub-array
        mid_idx = layout.n_subarrays // 2
        mid = layout.midpoints[mid_idx]
        half = layout.subarray_length / 2
        ax_layout.axvspan(mid - half, mid + half, alpha=0.4,
                         color=c_highlight, zorder=2)
        ax_layout.axvline(mid, color=c_highlight, linewidth=2, zorder=3)
        
        ax_layout.set_xlim(-layout.dx, layout.total_length + layout.dx)
        ax_layout.set_ylim(0, 1)
        ax_layout.set_xlabel("Position (m)")
        ax_layout.set_yticks([])
        ax_layout.set_title(f"Sub-Array: {layout.n_channels}ch, {layout.n_subarrays} positions")
        ax_layout.spines['top'].set_visible(False)
        ax_layout.spines['right'].set_visible(False)
        ax_layout.spines['left'].set_visible(False)
        
        # Depth panel - with depth range
        from sw_transform.masw2d.config.templates import get_source_label
        
        x_range = np.linspace(layout.first_midpoint, layout.last_midpoint, 100)
        z_range = np.linspace(0, layout.depth_max * 1.2, 50)
        X, Z = np.meshgrid(x_range, z_range)
        
        # Confidence zones based on depth range
        confidence = np.ones_like(Z)
        confidence = np.where(Z > layout.depth_min, 
                             1 - (Z - layout.depth_min) / (layout.depth_max - layout.depth_min + 0.01),
                             confidence)
        confidence = np.where(Z > layout.depth_max, 0.1, confidence)
        confidence = np.clip(confidence, 0, 1)
        
        ax_depth.contourf(X, Z, confidence, levels=20, cmap='YlOrBr_r', alpha=0.7)
        
        # Depth range lines
        ax_depth.axhline(layout.depth_min, color='#4CAF50', linestyle='-',
                        linewidth=2, label=f"Min: {layout.depth_min:.1f}m")
        ax_depth.axhline(layout.depth_max, color=c_depth, linestyle='--',
                        linewidth=2, label=f"Max: {layout.depth_max:.1f}m")
        
        # Fill realistic depth zone
        ax_depth.axhspan(layout.depth_min, layout.depth_max, alpha=0.15, 
                        color='#4CAF50', zorder=1)
        
        ax_depth.axvline(layout.first_midpoint, color=c_subarray, linestyle=':', alpha=0.7)
        ax_depth.axvline(layout.last_midpoint, color=c_subarray, linestyle=':', alpha=0.7)
        
        ax_depth.set_xlim(0, layout.total_length)
        ax_depth.set_ylim(layout.depth_max * 1.2, 0)
        ax_depth.set_xlabel("Position (m)")
        ax_depth.set_ylabel("Depth (m)")
        source_label = get_source_label(layout.source_type)
        ax_depth.set_title(f"Depth ({source_label})", fontsize=10)
        ax_depth.legend(loc='lower right', fontsize=8)
        ax_depth.grid(True, alpha=0.3)
    
    def _import_from_project(self):
        """Import files from main project panel with offsets."""
        if not self.main_app or not hasattr(self.main_app, 'file_list'):
            messagebox.showwarning("Import", "No project files available")
            return
        
        if not self.main_app.file_list:
            messagebox.showinfo("Import", "No files loaded in project")
            return
        
        # Get array configuration for calculating source position
        try:
            n_channels = int(self.n_channels_var.get())
            dx = float(self.dx_var.get())
            array_length = (n_channels - 1) * dx
        except ValueError:
            array_length = 46.0  # Default
        
        count = 0
        for filepath in self.main_app.file_list:
            base = os.path.splitext(os.path.basename(filepath))[0]
            
            # Get offset and reverse from main app
            # NOTE: The offset stored in main_app is the ABSOLUTE SOURCE POSITION
            # (from file_assignment.py's BASE_OFFSETS), displayed as "+66" or "-2"
            offset_str = self.main_app.offsets.get(base, "+0")
            is_reverse = self.main_app.reverse_flags.get(base, False)
            
            # Parse offset as absolute source position
            try:
                source_pos = float(offset_str)
            except ValueError:
                source_pos = array_length  # Default: at array end
            
            # Check if already added
            existing = [s for s in self.shot_data if s["file"] == filepath]
            if not existing:
                shot_info = {
                    "file": filepath,
                    "offset": offset_str,
                    "reverse": is_reverse,
                    "source_position": source_pos
                }
                self.shot_data.append(shot_info)
                self.shot_files.append(filepath)
                rev_mark = "Yes" if is_reverse else "No"
                self.shot_tree.insert("", "end", values=(
                    base, offset_str, rev_mark, f"{source_pos:.1f}m"
                ))
                count += 1
        
        if count > 0:
            self.log(f"Imported {count} files from project")
        else:
            messagebox.showinfo("Import", "All project files already added.")
    
    def _add_shot_files(self):
        """Add shot files via dialog with auto-detection of offsets."""
        files = filedialog.askopenfilenames(
            title="Select Shot Files",
            filetypes=[("SEG-2 files", "*.dat *.sg2"), ("All files", "*.*")]
        )
        if files:
            # Get array configuration for calculating source position
            try:
                n_channels = int(self.n_channels_var.get())
                dx = float(self.dx_var.get())
                array_length = (n_channels - 1) * dx
            except ValueError:
                array_length = 46.0  # Default
            
            # Try to auto-detect offsets from filenames
            from sw_transform.io.file_assignment import assign_files
            try:
                rows = assign_files(files, recursive=False, include_unknown=True)
                file_info = {str(r.file_path): r for r in rows}
            except Exception:
                file_info = {}
            
            for f in files:
                if f not in self.shot_files:
                    self.shot_files.append(f)
                    base = os.path.basename(f)
                    
                    # Try to get auto-detected offset
                    row = file_info.get(f)
                    if row and row.offset_m is not None:
                        # offset_m from file_assignment is the ABSOLUTE SOURCE POSITION
                        # e.g., 66 means source at 66m, -2 means source at -2m
                        source_pos = float(row.offset_m)
                        is_reverse = bool(row.reverse)
                        # Display string shows distance to array edge
                        if source_pos >= 0:
                            offset_to_end = source_pos - array_length
                            offset_str = f"+{int(offset_to_end)}"
                        else:
                            offset_str = f"{int(source_pos)}"
                    else:
                        offset_str = "+0"
                        is_reverse = False
                        source_pos = array_length  # Default: at array end
                    
                    shot_info = {"file": f, "offset": offset_str, "reverse": is_reverse, "source_position": source_pos}
                    self.shot_data.append(shot_info)
                    rev_mark = "Yes" if is_reverse else "No"
                    self.shot_tree.insert("", "end", values=(base, offset_str, rev_mark, f"{source_pos:.1f}m"))
    
    def _clear_shot_files(self):
        """Clear all shot files."""
        self.shot_files.clear()
        self.shot_data.clear()
        for item in self.shot_tree.get_children():
            self.shot_tree.delete(item)
    
    def _select_output_dir(self):
        """Select output directory."""
        dir_path = filedialog.askdirectory(title="Select Output Directory")
        if dir_path:
            self.output_dir_var.set(dir_path)
    
    def _get_selected_sizes(self) -> List[int]:
        """Get list of checked sub-array sizes."""
        return [size for size, var in self.subarray_checks.items() if var.get()]
    
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
    
    def _open_advanced_settings(self):
        """Open the advanced settings popup window."""
        # Create popup window
        popup = tk.Toplevel(self.parent)
        popup.title("Advanced Settings")
        popup.geometry("450x550")
        popup.resizable(True, True)
        popup.transient(self.parent)
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
        grid_n_combo = ttk.Combobox(row1, textvariable=self.grid_n_var,
                                     values=["500", "1000", "2000", "4000", "8000"],
                                     width=10, state="readonly")
        grid_n_combo.pack(side="left", padx=4)
        ttk.Label(row1, text="points", foreground="gray").pack(side="left")
        
        # Velocity spacing (vspace)
        row2 = ttk.Frame(transform_frame)
        row2.pack(fill="x", pady=3)
        ttk.Label(row2, text="Velocity Spacing:", width=18).pack(side="left")
        vspace_combo = ttk.Combobox(row2, textvariable=self.vspace_var,
                                     values=["log", "linear"],
                                     width=10, state="readonly")
        vspace_combo.pack(side="left", padx=4)
        
        # Vibrosis mode (for FDBF method)
        row_vib = ttk.Frame(transform_frame)
        row_vib.pack(fill="x", pady=3)
        ttk.Checkbutton(row_vib, text="Vibrosis mode (FDBF weighting)", 
                        variable=self.vibrosis_var).pack(side="left")
        
        # Cylindrical steering (for FDBF method)
        row_cyl = ttk.Frame(transform_frame)
        row_cyl.pack(fill="x", pady=3)
        ttk.Checkbutton(row_cyl, text="Cylindrical steering (FDBF near-field)", 
                        variable=self.cylindrical_var).pack(side="left")
        
        # ===== Peak Picking Settings =====
        peak_frame = ttk.LabelFrame(scrollable, text="Peak Picking", padding=8)
        peak_frame.pack(fill="x", padx=8, pady=6)
        
        # Tolerance (tol)
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
        down_combo = ttk.Combobox(row7, textvariable=self.down_factor_var,
                                   values=["1", "2", "4", "8", "16", "32"],
                                   width=10, state="readonly")
        down_combo.pack(side="left", padx=4)
        
        # FFT size (numf)
        row8 = ttk.Frame(preproc_frame)
        row8.pack(fill="x", pady=3)
        ttk.Label(row8, text="FFT Size:", width=18).pack(side="left")
        numf_combo = ttk.Combobox(row8, textvariable=self.numf_var,
                                   values=["1000", "2000", "4000", "8000"],
                                   width=10, state="readonly")
        numf_combo.pack(side="left", padx=4)
        ttk.Label(row8, text="points", foreground="gray").pack(side="left")
        
        # ===== Image Export Settings =====
        image_frame = ttk.LabelFrame(scrollable, text="Image Export Options", padding=8)
        image_frame.pack(fill="x", padx=8, pady=6)
        
        # Max velocity for plots
        row9 = ttk.Frame(image_frame)
        row9.pack(fill="x", pady=3)
        ttk.Label(row9, text="Max Velocity (plot):", width=18).pack(side="left")
        vel_plot_combo = ttk.Combobox(row9, textvariable=self.plot_max_vel_var,
                                       values=["auto", "500", "1000", "1500", "2000", "3000", "5000"],
                                       width=10)
        vel_plot_combo.pack(side="left", padx=4)
        ttk.Label(row9, text="m/s", foreground="gray").pack(side="left")
        
        # Max frequency for plots
        row10 = ttk.Frame(image_frame)
        row10.pack(fill="x", pady=3)
        ttk.Label(row10, text="Max Frequency (plot):", width=18).pack(side="left")
        freq_plot_combo = ttk.Combobox(row10, textvariable=self.plot_max_freq_var,
                                        values=["auto", "50", "80", "100", "150", "200"],
                                        width=10)
        freq_plot_combo.pack(side="left", padx=4)
        ttk.Label(row10, text="Hz", foreground="gray").pack(side="left")
        
        # Colormap
        row11 = ttk.Frame(image_frame)
        row11.pack(fill="x", pady=3)
        ttk.Label(row11, text="Colormap:", width=18).pack(side="left")
        cmap_combo = ttk.Combobox(row11, textvariable=self.cmap_var,
                                   values=["jet", "viridis", "plasma", "turbo", "seismic", "hot"],
                                   width=10, state="readonly")
        cmap_combo.pack(side="left", padx=4)
        
        # DPI
        row12 = ttk.Frame(image_frame)
        row12.pack(fill="x", pady=3)
        ttk.Label(row12, text="DPI:", width=18).pack(side="left")
        dpi_combo = ttk.Combobox(row12, textvariable=self.dpi_var,
                                  values=["72", "100", "150", "200", "300"],
                                  width=10, state="readonly")
        dpi_combo.pack(side="left", padx=4)
        
        # ===== Buttons =====
        btn_frame = ttk.Frame(scrollable)
        btn_frame.pack(fill="x", padx=8, pady=12)
        
        ttk.Button(btn_frame, text="Reset to Defaults", 
                   command=self._reset_advanced_defaults).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Close", 
                   command=popup.destroy).pack(side="right", padx=4)
        
        # Center the window
        popup.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - popup.winfo_width()) // 2
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() - popup.winfo_height()) // 2
        popup.geometry(f"+{x}+{y}")
    
    def _on_vibrosis_changed(self, *args):
        """Auto-check cylindrical when vibrosis is enabled."""
        if self.vibrosis_var.get():
            self.cylindrical_var.set(True)
    
    def _build_config(self) -> Dict[str, Any]:
        """Build configuration dictionary from UI state."""
        try:
            n_channels = int(self.n_channels_var.get())
            dx = float(self.dx_var.get())
            slide_step = int(self.slide_step_var.get())
            freq_min = float(self.freq_min_var.get())
            freq_max = float(self.freq_max_var.get())
            vel_min = float(self.vel_min_var.get())
            vel_max = float(self.vel_max_var.get())
            
            # Advanced settings
            grid_n = int(self.grid_n_var.get())
            tol = float(self.tol_var.get())
            power_threshold = float(self.power_threshold_var.get())
            start_time = float(self.start_time_var.get())
            end_time = float(self.end_time_var.get())
            down_factor = int(self.down_factor_var.get())
            numf = int(self.numf_var.get())
            
            # Plot settings - handle 'auto' values
            plot_max_vel_str = self.plot_max_vel_var.get()
            plot_max_vel = float(vel_max) if plot_max_vel_str == 'auto' else float(plot_max_vel_str)
            
            plot_max_freq_str = self.plot_max_freq_var.get()
            plot_max_freq = float(freq_max) if plot_max_freq_str == 'auto' else float(plot_max_freq_str)
            
            dpi = int(self.dpi_var.get())
            
        except ValueError as e:
            raise ValueError(f"Invalid numeric value: {e}")
        
        selected_sizes = self._get_selected_sizes()
        if not selected_sizes:
            raise ValueError("No sub-array sizes selected")
        
        from sw_transform.masw2d.config.templates import (
            generate_standard_masw_template, generate_subarray_configs
        )
        
        # Generate subarray configs
        subarray_configs = generate_subarray_configs(selected_sizes, slide_step, naming="depth")
        
        # Build shots config from shot_data with source_position and force_reverse
        shots_config = []
        for shot in self.shot_data:
            shots_config.append({
                "file": shot["file"],
                "source_position": shot["source_position"],
                "force_reverse": shot.get("reverse", False)
            })
        
        config = {
            "survey_name": "GUI_MASW_2D",
            "version": "1.0",
            "array": {
                "n_channels": n_channels,
                "dx": dx,
                "first_channel_position": 0.0
            },
            "shots": shots_config,
            "subarray_configs": subarray_configs,
            "processing": {
                "method": self.method_var.get(),
                "freq_min": freq_min,
                "freq_max": freq_max,
                "velocity_min": vel_min,
                "velocity_max": vel_max,
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
                "directory": self.output_dir_var.get() or "./output_2d/",
                "organize_by": "midpoint",
                "export_formats": ["csv", "npz", "image"],
                "include_images": self.include_images_var.get(),
                "max_velocity": plot_max_vel,
                "max_frequency": plot_max_freq,
                "auto_velocity_limit": False,  # Use explicit max_velocity from user
                "cmap": self.cmap_var.get(),
                "image_dpi": dpi
            }
        }
        
        return config
    
    def _run_workflow(self):
        """Run the 2D MASW workflow."""
        try:
            config = self._build_config()
        except ValueError as e:
            messagebox.showerror("Configuration Error", str(e))
            return
        
        if not self.shot_files:
            messagebox.showwarning("No Files", "Please add shot files first.")
            return
        
        output_dir = self.output_dir_var.get()
        if not output_dir:
            messagebox.showwarning("No Output", "Please select an output directory.")
            return
        
        # Disable run button
        self.status_label.config(text="Running...")
        self.progress_var.set(0)
        
        # Run in thread
        def run_thread():
            try:
                from sw_transform.masw2d.workflows import StandardMASWWorkflow
                
                workflow = StandardMASWWorkflow(config)
                
                # Get parallel settings
                parallel = self.parallel_var.get()
                workers = self.worker_var.get()
                max_workers = None if workers == "auto" else int(workers)
                
                def progress_cb(current, total, msg):
                    pct = (current / total * 100) if total > 0 else 0
                    self.parent.after(0, lambda: self.progress_var.set(pct))
                    self.parent.after(0, lambda: self.status_label.config(text=msg))
                
                # Set progress callback before running
                workflow.set_progress_callback(progress_cb)
                
                results = workflow.run(
                    output_dir=output_dir,
                    parallel=parallel,
                    max_workers=max_workers
                )
                
                self.parent.after(0, lambda: self._on_workflow_complete(results))
                
            except Exception as e:
                self.parent.after(0, lambda: self._on_workflow_error(str(e)))
        
        thread = threading.Thread(target=run_thread, daemon=True)
        thread.start()
    
    def _on_workflow_complete(self, results):
        """Handle workflow completion."""
        self.progress_var.set(100)
        n_results = results.get("n_results", 0)
        n_midpoints = results.get("n_midpoints", 0)
        status = results.get("status", "unknown")
        
        if status == "success":
            self.status_label.config(text=f"Complete! {n_results} dispersion curves at {n_midpoints} midpoints.")
            self.log(f"MASW 2D workflow complete: {n_results} results at {n_midpoints} midpoints")
            messagebox.showinfo("Complete", f"Workflow finished.\n{n_results} dispersion curves extracted\nat {n_midpoints} midpoint locations.")
        else:
            error = results.get("error", "Unknown error")
            self.status_label.config(text=f"Error: {error}")
            self.log(f"MASW 2D error: {error}")
            messagebox.showerror("Workflow Error", error)
    
    def _on_workflow_error(self, error_msg):
        """Handle workflow error."""
        self.progress_var.set(0)
        self.status_label.config(text=f"Error: {error_msg}")
        self.log(f"MASW 2D error: {error_msg}")
        messagebox.showerror("Workflow Error", error_msg)


def create_masw2d_tab(notebook: ttk.Notebook, log_callback=None, main_app=None) -> MASW2DTab:
    """Factory function to create and add MASW 2D tab to a notebook.
    
    Parameters
    ----------
    notebook : ttk.Notebook
        The notebook widget to add the tab to
    log_callback : callable, optional
        Logging function
    main_app : optional
        Reference to main app for importing project files
    
    Returns
    -------
    MASW2DTab
        The created tab instance
    """
    frame = ttk.Frame(notebook)
    notebook.add(frame, text="MASW 2D")
    
    tab = MASW2DTab(frame, log_callback, main_app)
    return tab
