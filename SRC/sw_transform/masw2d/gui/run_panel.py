"""MASW 2D Run panel with button and progress bar.

Copied from masw2d_tab.py lines 310-325.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class MASW2DRunPanel(ttk.Frame):
    """Run panel with button and progress bar for MASW 2D workflow.
    
    Usage:
        panel = MASW2DRunPanel(parent, on_run=self._run_workflow)
        panel.pack(fill="x", padx=4, pady=8)
        
        panel.set_progress(50, "Processing...")
        panel.set_status("Complete!")
    """
    
    def __init__(self, parent: tk.Widget,
                 on_run: Optional[Callable[[], None]] = None,
                 **kwargs):
        """Initialize the run panel.
        
        Args:
            parent: Parent widget
            on_run: Callback for Run button
            **kwargs: Additional Frame options
        """
        super().__init__(parent, **kwargs)
        
        self.on_run = on_run
        
        self._create_variables()
        self._build_ui()
    
    def _create_variables(self):
        """Create tk variables."""
        self.progress_var = tk.DoubleVar(value=0)
    
    def _build_ui(self):
        """Build the panel UI.
        
        Copied from masw2d_tab.py lines 310-325.
        """
        ttk.Button(self, text="Run 2D MASW Workflow",
                   command=self._on_run_clicked).pack(fill="x", pady=4)
        
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var,
                                             mode="determinate")
        self.progress_bar.pack(fill="x", pady=2)
        
        self.status_label = ttk.Label(self, text="Ready")
        self.status_label.pack(fill="x")
    
    def _on_run_clicked(self):
        """Handle Run button click."""
        if self.on_run:
            self.on_run()
    
    def set_progress(self, value: float, status: Optional[str] = None):
        """Set progress bar value and optionally status text.
        
        Args:
            value: Progress value (0-100)
            status: Optional status text
        """
        self.progress_var.set(value)
        if status is not None:
            self.status_label.config(text=status)
    
    def set_status(self, text: str):
        """Set status label text.
        
        Args:
            text: Status text
        """
        self.status_label.config(text=text)
    
    def reset(self):
        """Reset progress and status."""
        self.progress_var.set(0)
        self.status_label.config(text="Ready")
