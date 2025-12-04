"""Layout preview panel with matplotlib visualization.

Copied from masw2d_tab.py lines 327-365, 389-447.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Optional


class LayoutPreviewPanel(ttk.Frame):
    """Layout preview panel with info text and matplotlib canvas.
    
    Usage:
        panel = LayoutPreviewPanel(parent)
        panel.pack(fill="both", expand=True)
        
        panel.update_preview(layout)
        panel.set_info_text("Configuration summary...")
    """
    
    def __init__(self, parent: tk.Widget, **kwargs):
        """Initialize the layout preview panel.
        
        Args:
            parent: Parent widget
            **kwargs: Additional Frame options
        """
        super().__init__(parent, **kwargs)
        
        self.canvas_widget = None
        self.current_layout = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the panel UI.
        
        Copied from masw2d_tab.py lines 327-339.
        """
        # Info panel at top
        info_frame = ttk.LabelFrame(self, text="Configuration Info", padding=6)
        info_frame.pack(fill="x", padx=4, pady=4)
        
        self.info_text = tk.Text(info_frame, height=6, wrap="word", state="disabled",
                                  font=("Consolas", 9))
        self.info_text.pack(fill="x")
        
        # Layout preview
        preview_frame = ttk.LabelFrame(self, text="Layout Preview", padding=6)
        preview_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        self.preview_container = ttk.Frame(preview_frame)
        self.preview_container.pack(fill="both", expand=True)
    
    def set_info_text(self, text: str):
        """Set the info text content.
        
        Args:
            text: Text to display
        """
        self.info_text.config(state="normal")
        self.info_text.delete("1.0", "end")
        self.info_text.insert("1.0", text)
        self.info_text.config(state="disabled")
    
    def update_preview(self, layout: Any):
        """Update the matplotlib preview with a layout.
        
        Copied from masw2d_tab.py lines 389-420.
        
        Args:
            layout: Layout object with geometry information
        """
        self.current_layout = layout
        
        # Clear existing
        for widget in self.preview_container.winfo_children():
            widget.destroy()
        
        try:
            import matplotlib
            matplotlib.use('TkAgg')
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
            
            # Create figure
            fig = Figure(figsize=(8, 5), dpi=100)
            
            # Create axes for layout plot
            ax_layout = fig.add_subplot(211)
            ax_depth = fig.add_subplot(212)
            
            # Plot layout on provided axes
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
        """Plot layout on provided axes.
        
        Copied from masw2d_tab.py lines 422-447.
        
        Args:
            layout: Layout object
            ax_layout: Matplotlib axes for layout
            ax_depth: Matplotlib axes for depth
        """
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
        try:
            from sw_transform.masw2d.config.templates import get_source_label
            source_label = get_source_label(layout.source_type)
        except (ImportError, AttributeError):
            source_label = "Unknown"
        
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
        ax_depth.set_title(f"Depth ({source_label})", fontsize=10)
        ax_depth.legend(loc='lower right', fontsize=8)
        ax_depth.grid(True, alpha=0.3)
    
    def clear(self):
        """Clear the preview."""
        for widget in self.preview_container.winfo_children():
            widget.destroy()
        self.current_layout = None
        self.canvas_widget = None
