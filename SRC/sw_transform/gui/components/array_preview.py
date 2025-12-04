"""Array preview panel component with waterfall display.

Copied from simple_app.py:
- lines 216-230 (Array preview panel UI)
- lines 687-768 (preview_array method)
"""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox


class ArrayPreviewPanel(tk.LabelFrame):
    """Array schematic and waterfall preview panel.
    
    Provides a preview display showing the sensor array layout
    and a waterfall plot of the seismic traces.
    
    Usage:
        panel = ArrayPreviewPanel(parent)
        panel.pack(fill="both", expand=True)
        
        panel.update_preview(
            path="/path/to/data.dat",
            offset="+6",
            settings={'time_start': 0.0, 'time_end': 1.0, ...}
        )
    """
    
    def __init__(self, parent: tk.Widget, **kwargs):
        """Initialize the array preview panel.
        
        Args:
            parent: Parent widget
            **kwargs: Additional LabelFrame options
        """
        super().__init__(parent, text="Array preview (embedded)", **kwargs)
        
        self.canvas_widget = None
        self.display_time_var = tk.StringVar(value="1")
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the preview panel UI.
        
        Copied from simple_app.py lines 216-230:
            arr_box = tk.LabelFrame(p, text="Array preview (embedded)")
            arr_box.pack(fill="both", expand=True, padx=6, pady=6)
            topbar = tk.Frame(arr_box); topbar.pack(fill="x", pady=(2,4))
            tk.Button(topbar, text="Preview Array / Waterfall", command=self.preview_array).pack(side="left")
            tk.Label(topbar, text="Display time (s):").pack(side="left", padx=(10,2))
            self.display_time_var = tk.StringVar(value="1")
            tk.Entry(topbar, width=6, textvariable=self.display_time_var).pack(side="left")
            self.prev_host = tk.Frame(arr_box, height=300, bg="#f7f7f7"); self.prev_host.pack(fill="both", expand=True)
            self.prev_canvas_widget = None
        """
        # Top bar with button and display time
        topbar = tk.Frame(self)
        topbar.pack(fill="x", pady=(2, 4))
        
        self.preview_button = tk.Button(topbar, text="Preview Array / Waterfall")
        self.preview_button.pack(side="left")
        
        tk.Label(topbar, text="Display time (s):").pack(side="left", padx=(10, 2))
        tk.Entry(topbar, width=6, textvariable=self.display_time_var).pack(side="left")
        
        # Preview host frame
        self.prev_host = tk.Frame(self, height=300, bg="#f7f7f7")
        self.prev_host.pack(fill="both", expand=True)
    
    def set_preview_command(self, command):
        """Set the command for the preview button.
        
        Args:
            command: Callback function for preview button
        """
        self.preview_button.config(command=command)
    
    def update_preview(self, path: str, offset: str, settings: dict):
        """Update the preview with data from a file.
        
        Copied from simple_app.py lines 687-768 (preview_array).
        
        Args:
            path: Path to the data file
            offset: Source offset string (e.g., "+6")
            settings: Dict with keys: time_start, time_end, downsample, 
                      down_factor, numf
        """
        if path is None:
            messagebox.showerror("Preview", "No file selected.")
            return
        
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from sw_transform.processing.seg2 import load_seg2_ar
            from sw_transform.processing.preprocess import preprocess_data
            import numpy as np
            
            # Load data
            time, T, Shotpoint, Spacing, dt, _ = load_seg2_ar(path)
            
            # Get preprocessing settings
            st = settings.get('time_start', 0.0)
            en = settings.get('time_end', 1.0)
            ds = settings.get('downsample', True)
            df = settings.get('down_factor', 16)
            nf = settings.get('numf', 4000)
            
            # Preprocess
            Tpre, time_pre, dt2 = preprocess_data(
                T, time, dt, 
                reverse_shot=False, 
                start_time=st, end_time=en, 
                do_downsample=ds, down_factor=df, numf=nf
            )
            
            # Optional display time trim
            disp_txt = (self.display_time_var.get() or "").strip()
            if disp_txt:
                try:
                    disp_time = float(disp_txt)
                    if disp_time > 0:
                        n_keep = int(np.clip(disp_time / dt2, 1, Tpre.shape[0]))
                        Tpre = Tpre[:n_keep, :]
                        time_pre = time_pre[:n_keep]
                except Exception:
                    pass
            
            positions = np.arange(Tpre.shape[1], dtype=float) * float(Spacing)
            
            # Create figure
            fig = Figure(figsize=(7.5, 6.0), dpi=100)
            gs = fig.add_gridspec(2, 1, height_ratios=[1, 3], hspace=0.42)
            ax1 = fig.add_subplot(gs[0])
            ax2 = fig.add_subplot(gs[1])
            
            # Array schematic
            ax1.plot(positions, np.zeros_like(positions), "^", color="green", label="Sensor")
            
            # Source position from offset
            try:
                off_txt = (offset or "+0").strip().replace("m", "")
                if off_txt.startswith("+"):
                    src_x = float(off_txt[1:])
                else:
                    src_x = float(off_txt)
            except Exception:
                src_x = float(Shotpoint)
            
            ax1.plot([src_x], [0.0], "D", color="tab:red", label="Source")
            ax1.set_yticks([])
            ax1.set_xlabel("Distance (m)")
            ax1.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)
            ax1.set_title("Array schematic")
            
            # Waterfall plot
            traces = Tpre.copy().T
            denom = np.max(np.abs(traces), axis=1, keepdims=True)
            denom[denom == 0] = 1.0
            traces = traces / denom
            
            spacing = float(np.mean(np.diff(positions))) if len(positions) > 1 else 1.0
            scale = 0.5 * spacing
            
            for tr, x0 in zip(traces, positions):
                ax2.plot(tr * scale + x0, time_pre, color="b", linewidth=0.5)
            
            ax2.invert_yaxis()
            ax2.set_xlabel("Distance (m)")
            ax2.set_ylabel("Time (s)")
            ax2.set_title("Waterfall (normalized)")
            
            fig.tight_layout(rect=[0, 0, 0.88, 1])  # Leave space for legend on right
            
            # Mount canvas
            if self.canvas_widget is not None:
                try:
                    self.canvas_widget.destroy()
                except Exception:
                    pass
            
            canvas = FigureCanvasTkAgg(fig, master=self.prev_host)
            self.canvas_widget = canvas.get_tk_widget()
            self.canvas_widget.pack(fill="both", expand=True)
            canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Preview", str(e))
    
    def clear(self):
        """Clear the preview display."""
        if self.canvas_widget is not None:
            try:
                self.canvas_widget.destroy()
            except Exception:
                pass
            self.canvas_widget = None
    
    def set_figure(self, fig):
        """Set and display a matplotlib Figure.
        
        Args:
            fig: A matplotlib Figure object to display
        """
        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            # Clear existing canvas
            if self.canvas_widget is not None:
                try:
                    self.canvas_widget.destroy()
                except Exception:
                    pass
            
            # Mount new canvas
            canvas = FigureCanvasTkAgg(fig, master=self.prev_host)
            self.canvas_widget = canvas.get_tk_widget()
            self.canvas_widget.pack(fill="both", expand=True)
            canvas.draw()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Preview", str(e))
