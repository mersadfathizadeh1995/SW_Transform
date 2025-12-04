"""Progress panel component with progress bar and status label.

Copied from simple_app.py lines 307-320.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ProgressPanel(tk.Frame):
    """Progress bar with status label.
    
    Provides a horizontal progress bar and a status label for showing
    processing status during batch operations.
    
    Usage:
        panel = ProgressPanel(parent)
        panel.pack(fill="x", padx=6, pady=6)
        
        panel.set_progress(50, "Processing file 5/10...")
        panel.reset()
    """
    
    def __init__(self, parent: tk.Widget, **kwargs):
        """Initialize the progress panel.
        
        Args:
            parent: Parent widget
            **kwargs: Additional Frame options
        """
        super().__init__(parent, **kwargs)
        self._build_ui()
    
    def _build_ui(self):
        """Build the progress bar and label UI.
        
        Copied from simple_app.py lines 316-320:
            pb_row = tk.Frame(r); pb_row.pack(fill="x", padx=6, pady=(0,6))
            self.pb = ttk.Progressbar(pb_row, orient="horizontal", mode="determinate", length=220)
            self.pb.pack(side="right")
            self.pb_label = tk.Label(pb_row, text="Idle", anchor="e")
            self.pb_label.pack(side="right", padx=(0,8))
        """
        # Progress bar
        self.progressbar = ttk.Progressbar(
            self, 
            orient="horizontal", 
            mode="determinate", 
            length=220
        )
        self.progressbar.pack(side="right")
        
        # Status label
        self.label = tk.Label(self, text="Idle", anchor="e")
        self.label.pack(side="right", padx=(0, 8))
    
    def set_progress(self, value: float, status: str | None = None, maximum: float | None = None):
        """Set the progress bar value and optional status text.
        
        Args:
            value: Progress value (0 to maximum)
            status: Optional status text to display
            maximum: Optional maximum value for the progress bar
        """
        if maximum is not None:
            self.progressbar.config(maximum=maximum)
        self.progressbar['value'] = value
        if status is not None:
            self.label.config(text=status)
    
    def set_maximum(self, maximum: float):
        """Set the maximum value for the progress bar.
        
        Args:
            maximum: Maximum progress value
        """
        self.progressbar.config(maximum=maximum)
    
    def set_status(self, status: str):
        """Set the status label text.
        
        Args:
            status: Status text to display
        """
        self.label.config(text=status)
    
    def reset(self):
        """Reset progress bar and status to idle state."""
        self.progressbar.config(value=0)
        self.label.config(text="Idle")
    
    @property
    def value(self) -> float:
        """Get current progress value."""
        return float(self.progressbar['value'])
    
    @value.setter
    def value(self, val: float):
        """Set progress value."""
        self.progressbar['value'] = val
