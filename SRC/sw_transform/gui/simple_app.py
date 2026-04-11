"""SimpleMASW GUI - Component-Based Architecture.

Main application window using modular components:
- FileTreePanel: File management with editing support
- ProcessingLimitsPanel: Velocity/frequency/time limits
- RunPanel: Method selector and run/compare buttons
- ProgressPanel: Progress bar and status
- FigureGallery: Figure browser with zoom and PPT export
- ArrayPreviewPanel: Waterfall preview canvas
- AdvancedSettingsManager: Advanced settings dialog
"""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from sw_transform.core.service import run_single as svc_run_single, run_compare as svc_run_compare
from sw_transform.processing.registry import METHODS, compute_reverse_flag
from sw_transform.io.file_assignment import assign_files as assign_files_from_names

# Import GUI components
from sw_transform.gui.components import (
    FileTreePanel,
    ProcessingLimitsPanel,
    RunPanel,
    ProgressPanel,
    FigureGallery,
    ArrayPreviewPanel,
    AdvancedSettingsManager,
    ArrayConfigPanel,
    ReceiverConfigPanel,
    SourceConfigPanel,
)
from sw_transform.gui.utils.defaults import DEFAULTS
from sw_transform.gui.utils.icons import load_icon, load_app_icon


class SimpleMASWGUI:
    """Main MASW GUI application using component-based architecture."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("MASW – SW_Transform GUI")
        try:
            self.root.geometry("1000x680")
            self.root.minsize(900, 560)
        except Exception:
            pass

        # App icon
        self._app_icon = load_app_icon(root)
        self._icons: dict[str, tk.PhotoImage] = {}

        # State
        self.output_folder: str = ""
        self.out_var = tk.StringVar(value="(not set)")

        # Figure title variable
        self.figure_topic_var = tk.StringVar(value="3-D Dispersion (Freq vs. Velocity)")

        # Create advanced settings manager (manages all tk variables)
        self.advanced = AdvancedSettingsManager()

        # Logbox reference (set during build)
        self.logbox = None

        # Component references (set during build)
        self.file_tree: FileTreePanel | None = None
        self.limits_panel: ProcessingLimitsPanel | None = None
        self.run_panel: RunPanel | None = None
        self.progress_panel: ProgressPanel | None = None
        self.figure_gallery: FigureGallery | None = None
        self.array_preview: ArrayPreviewPanel | None = None
        self.array_config: ArrayConfigPanel | None = None  # Legacy, kept for compatibility
        self.receiver_config: ReceiverConfigPanel | None = None
        self.source_config: SourceConfigPanel | None = None

        self._build_menu()
        self._build_ui()

    def _build_menu(self):
        """Build the application menu bar."""
        m = tk.Menu(self.root)
        filem = tk.Menu(m, tearoff=0)
        filem.add_command(label="Open Data Files...", command=self.select_files)
        filem.add_command(label="Open Vibrosis .MAT...", command=self.select_mat_files)
        filem.add_command(label="Select Output Folder...", command=self.select_out)
        filem.add_separator()
        filem.add_command(label="Exit", command=self.root.quit)
        m.add_cascade(label="File", menu=filem)

        datam = tk.Menu(m, tearoff=0)
        datam.add_command(label="Auto Assign Offsets (from filenames)",
                          command=self._auto_assign_from_filenames)
        m.add_cascade(label="Data", menu=datam)

        self.root.config(menu=m)

    def _build_ui(self):
        """Build the main UI using components."""
        # Left column: collapsible file tree + thin toggle strip on the right edge
        self._left_panel_expanded = True
        self._LEFT_PANEL_WIDTH = 320
        self._left_outer = tk.Frame(self.root)
        self._left_outer.pack(side="left", fill="y")

        self._left_content = tk.Frame(self._left_outer, width=self._LEFT_PANEL_WIDTH)
        self._left_content.pack(side="left", fill="both", expand=True)

        # Button row for Open and Clear
        btn_row = tk.Frame(self._left_content)
        btn_row.pack(anchor="w", padx=8, pady=6)

        # Open button with icon
        btn_open = tk.Button(btn_row, text=" Open Data...", command=self.select_files,
                             compound="left", padx=6, pady=4)
        ico = self._load_icon("ic_open.png", 32)
        if ico is not None:
            btn_open.config(image=ico)
        btn_open.pack(side="left")

        # Clear button
        btn_clear = tk.Button(btn_row, text=" Clear All", command=self.clear_all_files,
                              compound="left", padx=6, pady=4)
        ico_clear = self._load_icon("ic_clear.png", 32)
        if ico_clear is not None:
            btn_clear.config(image=ico_clear)
        btn_clear.pack(side="left", padx=4)

        # File tree component
        self.file_tree = FileTreePanel(self._left_content, log_callback=self._log,
                                       on_offset_change=self._on_file_offset_change)
        self.file_tree.pack(fill="both", expand=True, padx=8, pady=4)

        # Toggle strip (always visible): collapse / expand left panel
        toggle_strip = tk.Frame(self._left_outer, width=22)
        toggle_strip.pack(side="right", fill="y")
        self._left_toggle_var = tk.StringVar(value="<<")
        self._left_toggle_btn = tk.Button(
            toggle_strip,
            textvariable=self._left_toggle_var,
            width=2,
            command=self._toggle_left_panel,
            relief="flat",
            cursor="hand2",
        )
        self._left_toggle_btn.pack(fill="y", expand=True, padx=0, pady=40)

        # Center panel - Notebook with tabs
        self._center_frame = tk.Frame(self.root)
        self._center_frame.pack(side="left", fill="both", expand=True)
        center = self._center_frame

        nb = ttk.Notebook(center)
        self.tab_inputs = tk.Frame(nb)
        self.tab_run = tk.Frame(nb)
        self.tab_fig = tk.Frame(nb)
        nb.add(self.tab_inputs, text="Inputs")
        nb.add(self.tab_run, text="Run")
        nb.add(self.tab_fig, text="Figures")

        # Add MASW 2D tab
        try:
            from sw_transform.gui.masw2d_tab import create_masw2d_tab
            self.masw2d_tab = create_masw2d_tab(nb, log_callback=self._log, main_app=self)
        except ImportError:
            pass

        nb.pack(fill="both", expand=True)

        self._build_inputs_tab()
        self._build_run_tab()
        self._build_figures_tab()

    def _toggle_left_panel(self) -> None:
        """Collapse or expand the main file-tree column; toggle strip stays visible."""
        if self._left_panel_expanded:
            self._left_content.pack_forget()
            self._left_toggle_var.set(">>")
            self._left_panel_expanded = False
        else:
            self._left_content.pack(side="left", fill="both", expand=True)
            self._left_toggle_var.set("<<")
            self._left_panel_expanded = True

    def _build_inputs_tab(self):
        """Build the Inputs tab using components."""
        p = self.tab_inputs

        # Output folder row
        row = tk.Frame(p)
        row.pack(fill="x", padx=6, pady=4)
        tk.Label(row, text="Output folder:").pack(side="left")
        tk.Label(row, textvariable=self.out_var, anchor="w").pack(side="left", fill="x", expand=True, padx=6)
        tk.Button(row, text="Select", command=self.select_out).pack(side="left")

        # Processing limits component
        self.limits_panel = ProcessingLimitsPanel(p, include_time=True)
        self.limits_panel.pack(fill="x", padx=6, pady=4)

        # Receiver configuration component (with callback to refresh preview)
        self.receiver_config = ReceiverConfigPanel(p, on_config_change=self._on_receiver_config_change)
        self.receiver_config.pack(fill="x", padx=6, pady=4)
        
        # Keep array_config as alias to receiver_config for backward compatibility
        self.array_config = self.receiver_config
        
        # Source configuration component
        self.source_config = SourceConfigPanel(p, on_config_change=self._on_source_config_change)
        self.source_config.pack(fill="x", padx=6, pady=4)

        # Figure title
        topic_box = tk.LabelFrame(p, text="Figure Title")
        topic_box.pack(fill="x", padx=6, pady=4)
        tk.Entry(topic_box, textvariable=self.figure_topic_var, width=50).pack(fill="x", padx=4, pady=4)

        # Advanced Settings button
        adv_row = tk.Frame(p)
        adv_row.pack(fill="x", padx=6, pady=4)
        tk.Button(adv_row, text="\u2699 Advanced Settings...",
                  command=lambda: self.advanced.open_dialog(self.root)).pack(side="left")

        # Array preview component
        self.array_preview = ArrayPreviewPanel(p)
        self.array_preview.pack(fill="both", expand=True, padx=6, pady=6)
        self.array_preview.set_preview_command(self.preview_array)

    def _build_run_tab(self):
        """Build the Run tab using components."""
        r = self.tab_run

        # Run panel component
        self.run_panel = RunPanel(
            r,
            on_run_single=self.run_single_processing,
            on_run_compare=self.run_compare_processing,
            icon_loader=self._load_icon
        )
        self.run_panel.pack(fill="x", pady=6)

        # Log box
        try:
            from tkinter import scrolledtext
            self.logbox = scrolledtext.ScrolledText(r, width=92, height=10)
            self.logbox.pack(fill="both", expand=True, padx=6, pady=6)
        except Exception:
            self.logbox = None

        # Progress panel component
        self.progress_panel = ProgressPanel(r)
        self.progress_panel.pack(fill="x", padx=6, pady=(0, 6))

    def _build_figures_tab(self):
        """Build the Figures tab using components."""
        # Figure gallery component
        self.figure_gallery = FigureGallery(
            self.tab_fig,
            output_dir_var=self.out_var,
            icon_loader=self._load_icon
        )
        self.figure_gallery.pack(fill="both", expand=True)

    # ==================== File Operations ====================

    def select_files(self):
        """Open file dialog for SEG-2 (.dat) and vibrosis (.mat) files."""
        files = filedialog.askopenfilenames(
            title="Select Data Files",
            filetypes=[
                ("All supported", "*.dat *.mat"),
                ("SEG-2 .dat", "*.dat"),
                ("Vibrosis .mat", "*.mat"),
                ("All files", "*.*")
            ]
        )
        if not files:
            return
        self._add_files(files)

    def select_mat_files(self):
        """Open file dialog specifically for vibrosis .mat files."""
        files = filedialog.askopenfilenames(
            title="Select Vibrosis .MAT Files",
            filetypes=[("Vibrosis .mat", "*.mat"), ("All files", "*.*")]
        )
        if not files:
            return
        self._add_files(files)

    def _add_files(self, files: tuple | list):
        """Add files to the file tree and auto-configure vibrosis mode."""
        self.file_tree.add_files(files)
        # Auto-enable vibrosis mode if .mat files loaded
        if self.file_tree.has_mat_files:
            self.advanced.vibrosis_mode.set(True)
        # Update source config with file info
        if self.source_config:
            self.source_config.update_files(self.file_tree.file_data)
        # Auto-detect receiver geometry from first file
        if self.file_tree.files:
            try:
                import numpy as np
                first_file = self.file_tree.files[0]
                if first_file.lower().endswith('.mat'):
                    # Vibrosis .mat file: detect channel count from file
                    from sw_transform.processing.vibrosis import get_vibrosis_file_info
                    info = get_vibrosis_file_info(first_file)
                    if info.get('valid'):
                        n_channels = info['n_channels']
                        dx = float(self.advanced.dx_var.get())
                        if self.array_config:
                            self.array_config.set_file_info(n_channels, dx)
                        if self.source_config:
                            positions = (np.arange(n_channels) * dx).tolist()
                            self.source_config.update_receiver_positions(positions)
                else:
                    # SEG-2 .dat file
                    from sw_transform.processing.seg2 import load_seg2_ar
                    _, T, _, Spacing, _, _ = load_seg2_ar(first_file)
                    n_channels = T.shape[1]
                    if self.array_config:
                        self.array_config.set_file_info(n_channels, float(Spacing))
                    if self.source_config:
                        positions = (np.arange(n_channels) * float(Spacing)).tolist()
                        self.source_config.update_receiver_positions(positions)
            except Exception:
                pass

    def select_out(self):
        """Select output folder."""
        folder = filedialog.askdirectory(title="Choose output folder")
        if folder:
            self.output_folder = folder
            self.out_var.set(folder)

    def clear_all_files(self):
        """Clear all loaded files."""
        if self.file_tree:
            self.file_tree.clear()
            self.advanced.vibrosis_mode.set(False)
            self._log("Cleared all files.")
        if self.source_config:
            self.source_config.clear()

    def _auto_assign_from_filenames(self):
        """Auto-assign offsets from filenames."""
        if not self.file_tree.files:
            messagebox.showerror("No files", "Select SEG-2 files first.")
            return
        try:
            rows = assign_files_from_names(self.file_tree.files, recursive=False, include_unknown=True)
            new_offsets = {}
            new_reverse = {}
            for r in rows:
                try:
                    fp = str(getattr(r, 'file_path', ''))
                    b = os.path.splitext(os.path.basename(fp))[0]
                    off = getattr(r, 'offset_m', None)
                    rev = bool(getattr(r, 'reverse', False))
                    if off is not None:
                        val = float(off)
                        sign = "+" if val >= 0 else ""
                        new_offsets[b] = f"{sign}{int(round(val))}"
                    new_reverse[b] = rev
                except Exception:
                    continue
            # Update file tree with new values
            self.file_tree.update_offsets(new_offsets)
            self.file_tree.update_reverse_flags(new_reverse)
            messagebox.showinfo("Assign", "Offsets/reverse assigned from filenames.")
        except Exception as e:
            messagebox.showerror("Assign", str(e))

    # ==================== Preview ====================

    def _on_receiver_config_change(self):
        """Callback when receiver configuration changes - refresh preview and sync source config."""
        # Update source config with new receiver positions
        if self.source_config and self.receiver_config:
            try:
                cfg = self.receiver_config.get_config()
                positions = cfg.get_positions().tolist()
                self.source_config.update_receiver_positions(positions)
                # Force custom source mode if receiver uses non-standard selection
                if self.receiver_config.is_custom_mode():
                    self.source_config.force_custom_mode()
            except Exception:
                pass
        
        # Refresh preview if file loaded
        if self.file_tree and self.file_tree.files:
            try:
                self.preview_array()
            except Exception:
                pass
    
    def _on_file_offset_change(self, base: str, new_offset: str):
        """Callback when user edits offset in file tree — sync to source config."""
        if self.source_config:
            self.source_config.update_files(self.file_tree.file_data)

    def _on_source_config_change(self):
        """Callback when source configuration changes - refresh preview if file loaded."""
        if self.file_tree and self.file_tree.files:
            try:
                self.preview_array()
            except Exception:
                pass
    
    def _on_array_config_change(self):
        """Legacy callback - calls _on_receiver_config_change for backward compatibility."""
        self._on_receiver_config_change()

    def preview_array(self):
        """Build embedded preview (array schematic + waterfall/spectrum)."""
        path = self._resolve_selected_path()
        if path is None:
            messagebox.showerror("Preview", "No file selected.")
            return
        try:
            from matplotlib.figure import Figure
            import numpy as np

            base = os.path.splitext(os.path.basename(path))[0]
            is_mat = path.lower().endswith('.mat')

            if is_mat:
                self._preview_vibrosis(path, base)
            else:
                self._preview_seg2(path, base)

        except Exception as e:
            messagebox.showerror("Preview", str(e))

    def _preview_seg2(self, path: str, base: str):
        """Preview for SEG-2 (.dat) files: array schematic + time-domain waterfall."""
        from matplotlib.figure import Figure
        from sw_transform.processing.seg2 import load_seg2_ar
        from sw_transform.processing.preprocess import preprocess_data
        import numpy as np

        time, T, Shotpoint, Spacing, dt, _ = load_seg2_ar(path)
        
        n_channels_file = T.shape[1]
        if self.array_config:
            self.array_config.set_file_info(n_channels_file, float(Spacing))

        limits = self.limits_panel.get_values()
        st = limits['time_start']
        en = limits['time_end']
        ds = self.advanced.downsample_var.get()
        df = int(self.advanced.down_factor_var.get())
        nf = int(self.advanced.numf_var.get())

        Tpre, time_pre, dt2 = preprocess_data(
            T, time, dt, reverse_shot=False,
            start_time=st, end_time=en,
            do_downsample=ds, down_factor=df, numf=nf,
            numchannels=n_channels_file
        )

        disp_txt = (self.array_preview.display_time_var.get() or "").strip()
        if disp_txt:
            try:
                disp_time = float(disp_txt)
                if disp_time > 0:
                    n_keep = int(np.clip(disp_time / dt2, 1, Tpre.shape[0]))
                    Tpre = Tpre[:n_keep, :]
                    time_pre = time_pre[:n_keep]
            except Exception:
                pass

        all_positions = np.arange(n_channels_file, dtype=float) * float(Spacing)
        
        selected_indices = None
        if self.array_config:
            try:
                arr_cfg = self.array_config.get_config()
                selected_indices = arr_cfg.get_selected_indices()
            except Exception:
                pass

        fig = Figure(figsize=(7.5, 6.0), dpi=100)
        gs = fig.add_gridspec(2, 1, height_ratios=[1, 3], hspace=0.42)
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])

        self._draw_array_schematic(ax1, all_positions, selected_indices, base, n_channels_file)

        # Waterfall - show all traces, highlight selected
        traces = Tpre.copy().T
        denom = np.max(np.abs(traces), axis=1, keepdims=True)
        denom[denom == 0] = 1.0
        traces = traces / denom
        spacing = float(np.mean(np.diff(all_positions))) if len(all_positions) > 1 else 1.0
        scale = 0.5 * spacing
        
        for i, (tr, x0) in enumerate(zip(traces, all_positions)):
            if selected_indices is not None and len(selected_indices) > 0:
                color = "blue" if i in set(selected_indices) else "lightgray"
                lw = 0.6 if i in set(selected_indices) else 0.3
            else:
                color = "blue"
                lw = 0.5
            ax2.plot(tr * scale + x0, time_pre, color=color, linewidth=lw)
        
        ax2.invert_yaxis()
        ax2.set_xlabel("Distance (m)")
        ax2.set_ylabel("Time (s)")
        ax2.set_title("Waterfall (normalized)")
        fig.tight_layout(rect=[0, 0, 0.88, 1])

        self.array_preview.set_figure(fig)

    def _preview_vibrosis(self, path: str, base: str):
        """Preview for vibrosis (.mat) files: array schematic + TF magnitude per channel."""
        from matplotlib.figure import Figure
        from sw_transform.processing.vibrosis import load_vibrosis_mat
        import numpy as np

        data = load_vibrosis_mat(path)
        n_channels = data.n_channels
        dx = float(self.advanced.dx_var.get())
        
        if self.array_config:
            self.array_config.set_file_info(n_channels, dx)

        all_positions = np.arange(n_channels, dtype=float) * dx

        fig = Figure(figsize=(7.5, 6.0), dpi=100)
        gs = fig.add_gridspec(2, 1, height_ratios=[1, 3], hspace=0.42)
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])

        self._draw_array_schematic(ax1, all_positions, None, base, n_channels)

        # Transfer function magnitude per channel (frequency-domain waterfall)
        tf_mag = np.abs(data.transfer_functions)  # (nfreq, nchannels)
        # Normalize each channel
        denom = np.max(tf_mag, axis=0, keepdims=True)
        denom[denom == 0] = 1.0
        tf_norm = tf_mag / denom
        
        spacing = dx
        scale = 0.5 * spacing
        
        for i in range(n_channels):
            x0 = all_positions[i]
            ax2.plot(tf_norm[:, i] * scale + x0, data.frequencies, color="blue", linewidth=0.5)
        
        ax2.invert_yaxis()
        ax2.set_xlabel("Distance (m)")
        ax2.set_ylabel("Frequency (Hz)")
        ax2.set_title("Transfer Function Magnitude (normalized)")
        fig.tight_layout(rect=[0, 0, 0.88, 1])

        self.array_preview.set_figure(fig)

    def _draw_array_schematic(self, ax, all_positions, selected_indices, base: str, n_channels: int):
        """Draw the array schematic on the given axes."""
        import numpy as np
        
        if selected_indices is not None and len(selected_indices) > 0:
            selected_set = set(selected_indices)
            inactive_idx = [i for i in range(n_channels) if i not in selected_set]
            active_idx = list(selected_indices)
            
            if inactive_idx:
                inactive_pos = all_positions[inactive_idx]
                ax.plot(inactive_pos, np.zeros_like(inactive_pos), "^", 
                        color="lightgray", markersize=6, label="Inactive")
            if active_idx:
                active_pos = all_positions[active_idx]
                ax.plot(active_pos, np.zeros_like(active_pos), "^", 
                        color="green", markersize=8, label="Selected")
        else:
            ax.plot(all_positions, np.zeros_like(all_positions), "^", 
                    color="green", markersize=8, label="Sensor")

        # Source position from source_config or file tree
        try:
            if self.source_config:
                positions = self.source_config.get_source_positions()
                src_x = positions.get(base, 0.0)
            else:
                off_txt = (self.file_tree.offsets.get(base, "+0") or "+0").strip().replace("m", "")
                if off_txt.startswith("+"):
                    src_x = float(off_txt[1:])
                else:
                    src_x = float(off_txt)
        except Exception:
            src_x = 0.0

        ax.plot([src_x], [0.0], "D", color="tab:red", markersize=10, label="Source")
        ax.set_yticks([])
        ax.set_xlabel("Distance (m)")
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)
        ax.set_title("Array schematic")

    def _resolve_selected_path(self) -> str | None:
        """Get path of selected file in tree, or first file if none selected."""
        if not self.file_tree.files:
            return None
        sel = self.file_tree.tree.selection()
        if sel:
            want = self.file_tree.tree.item(sel[0], "values")[0]
            for f in self.file_tree.files:
                if os.path.splitext(os.path.basename(f))[0] == want:
                    return f
        return self.file_tree.files[0]

    # ==================== Processing ====================

    def _collect_common(self):
        """Collect common processing parameters."""
        limits = self.limits_panel.get_values()
        try:
            pick_vmin = limits['vmin']
            pick_vmax = limits['vmax']
            pick_fmin = limits['fmin']
            pick_fmax = limits['fmax']
            st = limits['time_start']
            en = limits['time_end']
        except (KeyError, ValueError):
            raise ValueError("Invalid pick/plot limits")

        try:
            downsample = self.advanced.downsample_var.get()
            dfac = int(self.advanced.down_factor_var.get())
            numf = int(self.advanced.numf_var.get())
        except Exception as e:
            raise ValueError(f"Invalid sampling: {e}")

        try:
            fig_dpi = int(self.advanced.dpi_var.get())
            assert fig_dpi > 0
        except Exception:
            raise ValueError("Figure DPI must be a positive integer")

        return pick_vmin, pick_vmax, pick_fmin, pick_fmax, st, en, downsample, dfac, numf, fig_dpi

    def _get_worker_count(self, mode: str = 'single') -> int:
        """Get worker count based on user setting or auto mode."""
        from sw_transform.workers.parallel import get_optimal_workers
        val = self.run_panel.worker_count_var.get()
        if val == "auto":
            return get_optimal_workers(mode=mode)
        try:
            return max(1, int(val))
        except ValueError:
            return get_optimal_workers(mode=mode)

    def run_single_processing(self, selected_only: bool = False):
        """Run single-method processing on files."""
        if not self.file_tree.files:
            messagebox.showerror("No files", "Select data files first.")
            return
        if not self.output_folder:
            messagebox.showerror("No output", "Choose an output folder.")
            return

        key = self.run_panel.selected_method

        # Determine which files will be processed
        if selected_only:
            sel = self.file_tree.tree.selection()
            selected_bases = {self.file_tree.tree.item(i, "values")[0] for i in sel} if sel else set()
            selected_types = [self.file_tree.file_types.get(b, 'seg2') for b in selected_bases]
            has_mat_in_selection = any(t == 'mat' for t in selected_types)
            has_seg2_in_selection = any(t == 'seg2' for t in selected_types)
        else:
            # Run All: check all files
            has_mat_in_selection = self.file_tree.has_mat_files
            has_seg2_in_selection = any(t == 'seg2' for t in self.file_tree.file_types.values())

        # Check for method compatibility
        if has_mat_in_selection and key != 'fdbf':
            if selected_only:
                # Single selection: user selected a .mat file with non-FDBF method
                messagebox.showerror("Method Error",
                                     "Vibrosis .mat files only support FDBF method.\n"
                                     "Please select FDBF method or select a .dat file.")
            else:
                # Run All with mixed files
                if has_seg2_in_selection:
                    messagebox.showerror("Mixed Files",
                                         f"Cannot run {key.upper()} on all files.\n\n"
                                         "Your file list contains both .mat and .dat files.\n"
                                         ".mat files only support FDBF method.\n\n"
                                         "Options:\n"
                                         "• Use 'Clear All' to remove files, then load only .dat files\n"
                                         "• Or select FDBF method (works with both types)")
                else:
                    messagebox.showerror("Method Error",
                                         "Vibrosis .mat files only support FDBF method.\n"
                                         "Please select FDBF or clear .mat files.")
            return

        # Get method-specific grid settings
        if key in ("fk", "fdbf"):
            grid_n = int(self.advanced.grid_fk_var.get())
            tol = float(self.advanced.tol_fk_var.get())
            vspace = "linear"
        else:
            grid_n = int(self.advanced.grid_ps_var.get())
            tol = float(self.advanced.tol_ps_var.get())
            vspace = self.advanced.vspace_ps_var.get() or "linear"

        pick_vmin, pick_vmax, pick_fmin, pick_fmax, st, en, downsample, dfac, numf, fig_dpi = self._collect_common()

        # Get dx for vibrosis
        try:
            dx = float(self.advanced.dx_var.get())
        except ValueError:
            dx = 1.0

        try:
            import matplotlib as mpl
            old_dpi = mpl.rcParams.get('savefig.dpi', 'figure')
            mpl.rcParams['savefig.dpi'] = fig_dpi
        except Exception:
            old_dpi = None

        try:
            paths = list(self.file_tree.files)
            if selected_only:
                sel = self.file_tree.tree.selection()
                selected_bases = {self.file_tree.tree.item(i, "values")[0] for i in sel} if sel else set()
                paths = [p for p in self.file_tree.files
                         if os.path.splitext(os.path.basename(p))[0] in selected_bases]

            # Get array config positions and selected indices
            positions = None
            selected_indices = None
            if self.array_config:
                try:
                    arr_cfg = self.array_config.get_config()
                    if arr_cfg.spacing_mode == 'custom' or arr_cfg.channel_mode != 'all':
                        positions = arr_cfg.get_positions().tolist()
                        selected_indices = arr_cfg.get_selected_indices().tolist()
                except Exception:
                    pass

            # Get source positions from source_config
            source_positions = {}
            if self.source_config:
                source_positions = self.source_config.get_source_positions()
            
            # Get receiver config info
            n_geophones = 24
            geophone_spacing = 2.0
            array_start = 0.0
            array_end = 46.0
            if self.receiver_config:
                try:
                    rcfg = self.receiver_config.get_config()
                    n_geophones = rcfg.get_n_selected()
                    geophone_spacing = rcfg.dx
                    pos_arr = rcfg.get_positions()
                    if len(pos_arr) > 0:
                        array_start = float(pos_arr[0])
                        array_end = float(pos_arr[-1])
                except Exception:
                    pass

            # Build params list
            params_list = []
            self._log(f"=== Run Configuration ===")
            self._log(f"Method: {key.upper()}")
            self._log(f"Array: {n_geophones} geophones @ {geophone_spacing}m ({array_start:.1f}m -> {array_end:.1f}m)")
            self._log(f"")
            
            for path in paths:
                base = os.path.splitext(os.path.basename(path))[0]
                offset = self.file_tree.offsets.get(base, "+0")
                user_rev = self.file_tree.reverse_flags.get(base, False)
                rev = compute_reverse_flag(bool(user_rev), key)
                source_type = "vibrosis" if self.advanced.vibrosis_mode.get() else "hammer"
                cylindrical = self.advanced.cylindrical_var.get()
                file_type = self.file_tree.file_types.get(base, 'seg2')
                
                # Get source position for this file and compute relative offset
                src_pos = source_positions.get(base, 0.0)
                relative_offset = src_pos - array_start
                
                # Determine shot type
                if src_pos < array_start:
                    shot_type = "exterior_left"
                elif src_pos > array_end:
                    shot_type = "exterior_right"
                else:
                    shot_type = "interior"
                
                # Log file config with detailed info
                self._log(f"File: {base}")
                self._log(f"  Source: {src_pos:.1f}m (offset: {relative_offset:+.1f}m from array start)")
                self._log(f"  Shot type: {shot_type}, Reverse: {rev}")

                # Build offset label for figure title
                detailed_title = self.advanced.detailed_title_var.get()
                if detailed_title:
                    offset_label = f"Source: {src_pos:.1f}m (offset: {relative_offset:+.1f}m)"
                else:
                    offset_label = f"{relative_offset:+.0f}"
                
                params = dict(
                    path=path, base=base, key=key, offset=offset_label, outdir=self.output_folder,
                    pick_vmin=pick_vmin, pick_vmax=pick_vmax, pick_fmin=pick_fmin, pick_fmax=pick_fmax,
                    st=st, en=en, downsample=downsample, dfac=dfac, numf=numf,
                    grid_n=grid_n, tol=tol, vspace=vspace, dpi=fig_dpi, rev=rev,
                    topic=(self.figure_topic_var.get() or ""),
                    source_type=source_type,
                    cylindrical=cylindrical,
                    export_spectra=self.advanced.export_spectra_var.get(),
                    file_type=file_type,
                    dx=dx if file_type == 'mat' else None,
                    positions=positions,
                    selected_indices=selected_indices,
                    source_position=src_pos,
                    relative_offset=relative_offset,
                    detailed_title=detailed_title,
                    auto_vel_limits=self.advanced.auto_vel_limits_var.get(),
                    auto_freq_limits=self.advanced.auto_freq_limits_var.get(),
                    plot_min_vel=self.advanced.plot_min_vel_var.get(),
                    plot_max_vel=self.advanced.plot_max_vel_var.get(),
                    plot_min_freq=self.advanced.plot_min_freq_var.get(),
                    plot_max_freq=self.advanced.plot_max_freq_var.get(),
                    cmap=self.advanced.cmap_var.get(),
                    freq_tick_spacing=self.advanced.freq_tick_spacing_var.get(),
                    vel_tick_spacing=self.advanced.vel_tick_spacing_var.get(),
                    fig_width=self.advanced.fig_width_var.get(),
                    fig_height=self.advanced.fig_height_var.get(),
                    contour_levels=self.advanced.contour_levels_var.get(),
                    plot_style=self.advanced.plot_style_var.get()
                )
                params_list.append(params)

            total = max(1, len(params_list))
            self.progress_panel.set_maximum(total)
            self.progress_panel.set_progress(0)
            use_parallel = self.run_panel.parallel_enabled and len(params_list) > 1

            if use_parallel:
                from sw_transform.workers.parallel import run_batch_parallel
                n_workers = self._get_worker_count(mode='single')
                self.progress_panel.set_status(f"Processing {total} files ({n_workers} workers)...")
                self.root.update()
                self._log(f"Starting parallel processing: {total} files on {n_workers} workers")

                def progress_cb(completed, total_count, current_base):
                    self.progress_panel.set_progress(completed)
                    self.progress_panel.set_status(f"Completed {completed}/{total_count}: {current_base}")
                    self._log(f"Finished: {current_base}")
                    self.root.update()

                results = run_batch_parallel(params_list, mode='single', max_workers=n_workers,
                                             progress_callback=progress_cb)
                success = sum(1 for r in results if r.success)
                failures = sum(1 for r in results if not r.success)

                for r in results:
                    if not r.success:
                        self._log(f"Failed {r.base}: {r.error}")
            else:
                self.progress_panel.set_status("Processing…")
                self.root.update_idletasks()
                success = 0
                failures = 0
                for idx, params in enumerate(params_list):
                    base = params['base']
                    self.progress_panel.set_status(f"Processing {idx + 1}/{total}: {base}")
                    self.progress_panel.set_progress(idx)
                    self.root.update()
                    self._log(f"Running {base} [{key}]...")
                    _b, ok, out = svc_run_single(params)
                    if ok and isinstance(out, str) and out.lower().endswith('.png'):
                        success += 1
                        self._log(f"Saved: {out}")
                    else:
                        failures += 1
                        self._log(f"Failed {base}: {out}")
                    self.progress_panel.set_progress(idx + 1)
                    self.root.update()

            # Create combined outputs
            if success > 0:
                self._create_combined_csv_single_method(key, paths)
                if self.advanced.export_spectra_var.get() and success > 1:
                    self._create_combined_spectrum_single_method(key, paths)

            # Show result message
            if success > 0 and failures == 0:
                messagebox.showinfo("Run", f"Completed ({success} file(s))")
            elif success > 0:
                messagebox.showwarning("Run", f"Completed with errors: {success} success, {failures} failed.")
            else:
                messagebox.showerror("Run", "No outputs created. Check the log for errors.")

            # Optional PPT
            if success > 0 and self.run_panel.ppt_enabled:
                self.figure_gallery.build_ppt()

            # Combined CSV
            if success > 1:
                self._build_combined_csv_single(key, paths)

        except Exception as e:
            messagebox.showerror("Run", str(e))
        finally:
            try:
                import matplotlib as mpl
                if old_dpi is not None:
                    mpl.rcParams['savefig.dpi'] = old_dpi
            except Exception:
                pass
            self.progress_panel.reset()

    def run_compare_processing(self, selected_only: bool = False):
        """Run compare processing (all 4 methods) on files."""
        if not self.file_tree.files:
            messagebox.showerror("No files", "Select data files first.")
            return
        if not self.output_folder:
            messagebox.showerror("No output", "Choose an output folder.")
            return

        # Check for .mat files
        if self.file_tree.has_mat_files:
            messagebox.showerror("Compare Not Supported",
                                 "Compare mode is not supported for vibrosis .mat files.\n"
                                 "Use 'Run Selected/All' with FDBF method instead.")
            return

        pick_vmin, pick_vmax, pick_fmin, pick_fmax, st, en, downsample, dfac, numf, fig_dpi = self._collect_common()
        n_fk = int(self.advanced.grid_fk_var.get())
        tol_fk = float(self.advanced.tol_fk_var.get())
        n_ps = int(self.advanced.grid_ps_var.get())
        vspace_ps = self.advanced.vspace_ps_var.get() or "linear"

        paths = list(self.file_tree.files)
        if selected_only:
            sel = self.file_tree.tree.selection()
            selected_bases = {self.file_tree.tree.item(i, "values")[0] for i in sel} if sel else set()
            paths = [p for p in self.file_tree.files
                     if os.path.splitext(os.path.basename(p))[0] in selected_bases]

        # Get array config positions if custom spacing is used
        positions = None
        if self.array_config:
            try:
                arr_cfg = self.array_config.get_config()
                if arr_cfg.spacing_mode == 'custom' or arr_cfg.channel_mode != 'all':
                    positions = arr_cfg.get_positions().tolist()
            except Exception:
                pass

        # Build params list
        params_list = []
        for path in paths:
            base = os.path.splitext(os.path.basename(path))[0]
            offset = self.file_tree.offsets.get(base, "+0")
            user_rev = self.file_tree.reverse_flags.get(base, False)
            source_type = "vibrosis" if self.advanced.vibrosis_mode.get() else "hammer"
            cylindrical = self.advanced.cylindrical_var.get()

            params = dict(
                path=path, base=base, outdir=self.output_folder, offset=offset,
                pick_vmin=pick_vmin, pick_vmax=pick_vmax, pick_fmin=pick_fmin, pick_fmax=pick_fmax,
                st=st, en=en, downsample=downsample, dfac=dfac, numf=numf,
                n_fk=n_fk, tol_fk=tol_fk, n_ps=n_ps, vspace_ps=vspace_ps,
                rev_fk=user_rev, rev_ps=user_rev, rev_fdbf=user_rev, rev_ss=user_rev,
                topic=(self.figure_topic_var.get() or ""),
                source_type=source_type,
                cylindrical=cylindrical,
                export_spectra=self.advanced.export_spectra_var.get(),
                positions=positions
            )
            params_list.append(params)

        total = max(1, len(params_list))
        self.progress_panel.set_maximum(total)
        self.progress_panel.set_progress(0)
        use_parallel = self.run_panel.parallel_enabled and len(params_list) > 1

        if use_parallel:
            from sw_transform.workers.parallel import run_batch_parallel
            n_workers = self._get_worker_count(mode='compare')
            self.progress_panel.set_status(f"Comparing {total} files ({n_workers} workers)...")
            self.root.update()
            self._log(f"Starting parallel comparison: {total} files on {n_workers} workers")

            def progress_cb(completed, total_count, current_base):
                self.progress_panel.set_progress(completed)
                self.progress_panel.set_status(f"Completed {completed}/{total_count}: {current_base}")
                self._log(f"Finished: {current_base}")
                self.root.update()

            results = run_batch_parallel(params_list, mode='compare', max_workers=n_workers,
                                         progress_callback=progress_cb)
            success = sum(1 for r in results if r.success)
            failures = sum(1 for r in results if not r.success)

            for r in results:
                if not r.success:
                    self._log(f"Failed {r.base}: {r.error}")
        else:
            self.progress_panel.set_status("Comparing…")
            self.root.update_idletasks()
            success = 0
            failures = 0
            for idx, params in enumerate(params_list):
                base = params['base']
                self.progress_panel.set_status(f"Comparing {idx + 1}/{total}: {base}")
                self.progress_panel.set_progress(idx)
                self.root.update()
                self._log(f"Compare {base}...")
                _b, ok, out = svc_run_compare(params)
                if ok and isinstance(out, str) and out.lower().endswith('.png'):
                    success += 1
                    self._log(f"Saved: {out}")
                else:
                    failures += 1
                    self._log(f"Failed {base}: {out}")
                self.progress_panel.set_progress(idx + 1)
                self.root.update()

        # Create combined outputs
        if success > 0:
            self._create_combined_csv_compare_mode(paths)
            if self.advanced.export_spectra_var.get() and success > 1:
                for method in ['fk', 'fdbf', 'ps', 'ss']:
                    self._create_combined_spectrum_single_method(method, paths)

        # Show result message
        if success > 0 and failures == 0:
            messagebox.showinfo("Run", f"Comparison completed ({success} file(s))")
        elif success > 0:
            messagebox.showwarning("Run", f"Comparison completed with errors: {success} success, {failures} failed.")
        else:
            messagebox.showerror("Run", "No comparison outputs created. Check the log for errors.")

        # Optional PPT
        if success > 0 and self.run_panel.ppt_enabled:
            self.figure_gallery.build_ppt()

        # Combined CSV
        if success > 1:
            self._build_combined_csv_compare(paths)

        self.progress_panel.reset()

    # ==================== CSV/Spectrum Helpers ====================

    def _create_combined_csv_single_method(self, key: str, paths: list):
        """Aggregate all per-shot CSVs into combined_<method>.csv."""
        import csv
        import glob

        pattern = os.path.join(self.output_folder, f"*_{key}_*.csv")
        csv_files = glob.glob(pattern)
        csv_files = [f for f in csv_files if not ('_compare' in f or 'combined_' in os.path.basename(f))]

        if not csv_files:
            return

        data_map = {}
        for csv_path in csv_files:
            try:
                with open(csv_path, 'r', newline='') as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    if not header or len(header) < 2:
                        continue
                    freq_list, vel_list, wav_list = [], [], []
                    for row in reader:
                        if len(row) >= 2:
                            freq_list.append(row[0])
                            vel_list.append(row[1])
                            wav_list.append(row[2] if len(row) > 2 else "")

                    fname = os.path.basename(csv_path)
                    parts = fname.replace(".csv", "").split("_")
                    if len(parts) >= 3:
                        method_idx = -1
                        for idx, part in enumerate(parts):
                            if part == key:
                                method_idx = idx
                                break
                        if method_idx >= 0 and method_idx < len(parts) - 1:
                            base = "_".join(parts[:method_idx])
                            offset_tag = parts[method_idx + 1]
                            if offset_tag.startswith('p'):
                                offset = "+" + offset_tag[1:] + "m"
                            elif offset_tag.startswith('m'):
                                offset = "-" + offset_tag[1:] + "m"
                            else:
                                offset = offset_tag
                            data_map[(base, offset)] = (freq_list, vel_list, wav_list)
            except Exception as e:
                self._log(f"Warning: Failed to read {csv_path}: {e}")
                continue

        if not data_map:
            return

        combined_path = os.path.join(self.output_folder, f"combined_{key}.csv")
        with open(combined_path, 'w', newline='') as f:
            writer = csv.writer(f)
            header = []
            sorted_keys = sorted(data_map.keys())
            for base, offset in sorted_keys:
                header.extend([f"freq({key}_{offset})", f"vel({key}_{offset})", f"wav({key}_{offset})"])
            writer.writerow(header)
            max_len = max(len(data_map[k][0]) for k in sorted_keys) if sorted_keys else 0
            for i in range(max_len):
                row = []
                for base, offset in sorted_keys:
                    freq_list, vel_list, wav_list = data_map[(base, offset)]
                    row.append(freq_list[i] if i < len(freq_list) else "")
                    row.append(vel_list[i] if i < len(vel_list) else "")
                    row.append(wav_list[i] if i < len(wav_list) else "")
                writer.writerow(row)
        self._log(f"Created combined_{key}.csv")

    def _create_combined_csv_compare_mode(self, paths: list):
        """Aggregate all per-file compare CSVs into combined_compare_all.csv."""
        import csv
        import glob

        pattern = os.path.join(self.output_folder, "*_compare.csv")
        csv_files = glob.glob(pattern)
        if not csv_files:
            return

        data_map = {}
        headers_map = {}
        for csv_path in csv_files:
            try:
                with open(csv_path, 'r', newline='') as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    if not header:
                        continue
                    rows = list(reader)
                    base = os.path.basename(csv_path).replace("_compare.csv", "")
                    data_map[base] = rows
                    headers_map[base] = header
            except Exception:
                continue

        if not data_map:
            return

        combined_path = os.path.join(self.output_folder, "combined_compare_all.csv")
        with open(combined_path, 'w', newline='') as f:
            writer = csv.writer(f)
            sorted_bases = sorted(data_map.keys())
            combined_header = []
            for base in sorted_bases:
                combined_header.extend(headers_map.get(base, []))
            writer.writerow(combined_header)
            max_len = max(len(data_map[b]) for b in sorted_bases) if sorted_bases else 0
            for i in range(max_len):
                row = []
                for base in sorted_bases:
                    file_rows = data_map[base]
                    if i < len(file_rows):
                        row.extend(file_rows[i])
                    else:
                        row.extend([""] * len(headers_map.get(base, [])))
                writer.writerow(row)
        self._log("Created combined_compare_all.csv")

    def _create_combined_spectrum_single_method(self, key: str, paths: list):
        """Create combined spectrum .npz file."""
        import glob
        from sw_transform.core.service import create_combined_spectrum

        pattern = os.path.join(self.output_folder, f"*_{key}_*_spectrum.npz")
        spectrum_files = glob.glob(pattern)
        spectrum_files = [f for f in spectrum_files if not os.path.basename(f).startswith('combined_')]

        if not spectrum_files:
            return

        create_combined_spectrum(self.output_folder, key, spectrum_files)
        self._log(f"Created combined_{key}_spectrum.npz")

    def _build_combined_csv_single(self, key: str, paths: list[str]):
        """Aggregate per-shot CSVs into combined_<method>.csv across all offsets."""
        try:
            import csv
            
            # Get source positions from source_config (same as run_single_processing)
            source_positions = {}
            if self.source_config:
                source_positions = self.source_config.get_source_positions()
            
            # Get array start for relative_offset computation
            array_start = 0.0
            if self.receiver_config:
                try:
                    rcfg = self.receiver_config.get_config()
                    pos_arr = rcfg.get_positions()
                    if len(pos_arr) > 0:
                        array_start = float(pos_arr[0])
                except Exception:
                    pass
            
            combined_rows = []
            for path in paths:
                base = os.path.splitext(os.path.basename(path))[0]
                
                # Compute relative_offset the same way as run_single_processing
                src_pos = source_positions.get(base, 0.0)
                relative_offset = src_pos - array_start
                offset_for_csv = f"{relative_offset:+.0f}"
                
                # Build offset tag matching service.py naming
                _off = offset_for_csv.strip().replace(" ", "").replace("m", "")
                if _off.startswith("+"):
                    _off_tag = "p" + _off[1:]
                elif _off.startswith("-"):
                    _off_tag = "m" + _off[1:]
                else:
                    _off_tag = _off
                per_csv = os.path.join(self.output_folder, f"{base}_{key}_{_off_tag}.csv")
                if not os.path.isfile(per_csv):
                    continue
                frq, vel, wl = [], [], []
                try:
                    with open(per_csv, "r", newline="") as fcsv:
                        rdr = csv.reader(fcsv)
                        next(rdr, None)
                        for row in rdr:
                            if len(row) >= 3:
                                try:
                                    frq.append(float(row[0]))
                                    vel.append(float(row[1]))
                                    wl.append(float(row[2]))
                                except Exception:
                                    continue
                except Exception:
                    continue
                if frq:
                    combined_rows.append((offset_for_csv, frq, vel, wl))

            if combined_rows and len(combined_rows) > 1:
                min_len = min(len(r[1]) for r in combined_rows)
                comb_csv = os.path.join(self.output_folder, f"combined_{key}.csv")
                with open(comb_csv, "w", newline="") as fcsv:
                    w = csv.writer(fcsv)
                    header = []
                    for off, _, _, _ in combined_rows:
                        header += [f"freq({key}_{off})", f"vel({key}_{off})", f"wav({key}_{off})"]
                    w.writerow(header)
                    for i in range(min_len):
                        row = []
                        for _, frq, vel, wl in combined_rows:
                            row += [frq[i], vel[i], wl[i] if i < len(wl) else ""]
                        w.writerow(row)
                self._log(f"Combined CSV → {comb_csv}")
        except Exception:
            pass

    def _build_combined_csv_compare(self, paths: list[str]):
        """Aggregate per-file compare CSVs into combined_compare_all.csv."""
        try:
            import csv
            rows_by_file = []
            headers = []
            for pth in paths:
                b = os.path.splitext(os.path.basename(pth))[0]
                comb_path = os.path.join(self.output_folder, f"{b}_compare.csv")
                if not os.path.isfile(comb_path):
                    continue
                with open(comb_path, "r", newline="") as fcsv:
                    rdr = list(csv.reader(fcsv))
                    if not rdr:
                        continue
                    hdr = rdr[0]
                    data = rdr[1:]
                    headers += [f"{h}[{b}]" for h in hdr]
                    rows_by_file.append(data)

            if rows_by_file and len(rows_by_file) > 1:
                min_len = min(len(r) for r in rows_by_file)
                out_all = os.path.join(self.output_folder, "combined_compare_all.csv")
                with open(out_all, "w", newline="") as fcsv:
                    w = csv.writer(fcsv)
                    w.writerow(headers)
                    for i in range(min_len):
                        row = []
                        for data in rows_by_file:
                            row += data[i]
                        w.writerow(row)
                self._log(f"Combined compare CSV → {out_all}")
        except Exception:
            pass

    # ==================== Helpers ====================

    def _log(self, msg: str):
        """Log a message to the logbox."""
        if self.logbox:
            self.logbox.insert(tk.END, msg + "\n")
            self.logbox.see(tk.END)

    def _load_icon(self, name: str, size: int) -> tk.PhotoImage | None:
        """Load and cache an icon using the utility function."""
        return load_icon(self._icons, name, size)

    # ==================== Proxy Properties for MASW 2D Sync ====================

    @property
    def file_list(self) -> list[str]:
        """Get list of file paths (proxy for MASW 2D sync)."""
        if self.file_tree:
            return self.file_tree.files
        return []

    @property
    def offsets(self) -> dict[str, str]:
        """Get offsets dict (proxy for MASW 2D sync)."""
        if self.file_tree:
            return self.file_tree.offsets
        return {}

    @property
    def reverse_flags(self) -> dict[str, bool]:
        """Get reverse flags dict (proxy for MASW 2D sync)."""
        if self.file_tree:
            return self.file_tree.reverse_flags
        return {}


def main() -> None:
    root = tk.Tk()
    SimpleMASWGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


