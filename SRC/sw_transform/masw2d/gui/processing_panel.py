"""Processing settings panel component.

Copied from masw2d_tab.py lines 242-278.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from sw_transform.masw2d.gui.defaults import MASW2D_DEFAULTS


class ProcessingPanel(ttk.LabelFrame):
    """Processing settings panel with method and frequency/velocity limits.
    
    Usage:
        panel = ProcessingPanel(
            parent,
            on_advanced_click=self._open_advanced_settings
        )
        panel.pack(fill="x", padx=4, pady=4)
        
        values = panel.get_values()
    """
    
    def __init__(self, parent: tk.Widget,
                 on_advanced_click: Optional[Callable[[], None]] = None,
                 **kwargs):
        """Initialize the processing panel.
        
        Args:
            parent: Parent widget
            on_advanced_click: Callback for Advanced Settings button
            **kwargs: Additional LabelFrame options
        """
        super().__init__(parent, text="Processing", padding=6, **kwargs)
        
        self.on_advanced_click = on_advanced_click
        
        self._create_variables()
        self._build_ui()
    
    def _create_variables(self):
        """Create tk variables."""
        self.method_var = tk.StringVar(value=MASW2D_DEFAULTS['method'])
        self.freq_min_var = tk.StringVar(value=MASW2D_DEFAULTS['freq_min'])
        self.freq_max_var = tk.StringVar(value=MASW2D_DEFAULTS['freq_max'])
        self.vel_min_var = tk.StringVar(value=MASW2D_DEFAULTS['vel_min'])
        self.vel_max_var = tk.StringVar(value=MASW2D_DEFAULTS['vel_max'])
    
    def _build_ui(self):
        """Build the panel UI.
        
        Copied from masw2d_tab.py lines 242-278.
        """
        # Method selector
        row_method = ttk.Frame(self)
        row_method.pack(fill="x", pady=2)
        ttk.Label(row_method, text="Method:").pack(side="left")
        method_combo = ttk.Combobox(row_method, textvariable=self.method_var,
                                    values=["fk", "ps", "fdbf", "ss"],
                                    width=8, state="readonly")
        method_combo.pack(side="left", padx=4)
        
        # Frequency range
        row_freq = ttk.Frame(self)
        row_freq.pack(fill="x", pady=2)
        ttk.Label(row_freq, text="Freq:").pack(side="left")
        ttk.Entry(row_freq, textvariable=self.freq_min_var, width=6).pack(side="left", padx=2)
        ttk.Label(row_freq, text="-").pack(side="left")
        ttk.Entry(row_freq, textvariable=self.freq_max_var, width=6).pack(side="left", padx=2)
        ttk.Label(row_freq, text="Hz").pack(side="left")
        
        # Velocity range
        row_vel = ttk.Frame(self)
        row_vel.pack(fill="x", pady=2)
        ttk.Label(row_vel, text="Velocity:").pack(side="left")
        ttk.Entry(row_vel, textvariable=self.vel_min_var, width=6).pack(side="left", padx=2)
        ttk.Label(row_vel, text="-").pack(side="left")
        ttk.Entry(row_vel, textvariable=self.vel_max_var, width=6).pack(side="left", padx=2)
        ttk.Label(row_vel, text="m/s").pack(side="left")
        
        # Advanced Settings button
        row_adv = ttk.Frame(self)
        row_adv.pack(fill="x", pady=4)
        ttk.Button(row_adv, text="⚙ Advanced Settings...",
                   command=self._on_advanced_clicked).pack(side="left")
    
    def _on_advanced_clicked(self):
        """Handle Advanced Settings button click."""
        if self.on_advanced_click:
            self.on_advanced_click()
    
    def get_values(self) -> dict:
        """Get current values as a dictionary.
        
        Returns:
            Dict with method, freq_min, freq_max, vel_min, vel_max
        """
        try:
            freq_min = float(self.freq_min_var.get())
            freq_max = float(self.freq_max_var.get())
            vel_min = float(self.vel_min_var.get())
            vel_max = float(self.vel_max_var.get())
        except ValueError:
            freq_min, freq_max = 5.0, 80.0
            vel_min, vel_max = 100.0, 1500.0
        
        return {
            'method': self.method_var.get(),
            'freq_min': freq_min,
            'freq_max': freq_max,
            'vel_min': vel_min,
            'vel_max': vel_max,
        }
    
    @property
    def method(self) -> str:
        """Get selected method."""
        return self.method_var.get()
