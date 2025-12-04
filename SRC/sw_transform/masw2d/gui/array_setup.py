"""Array setup panel component.

Copied from masw2d_tab.py lines 144-176 (Array Setup section).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from sw_transform.masw2d.gui.defaults import MASW2D_DEFAULTS


class ArraySetupPanel(ttk.LabelFrame):
    """Array Setup panel with channels, spacing, and source type.
    
    Usage:
        panel = ArraySetupPanel(parent, on_update=self._update_preview)
        panel.pack(fill="x", padx=4, pady=4)
        
        values = panel.get_values()
        # {'n_channels': 24, 'dx': 2.0, 'source_type': 'hammer', 'array_length': 46.0}
    """
    
    def __init__(self, parent: tk.Widget,
                 on_update: Optional[Callable[[], None]] = None,
                 **kwargs):
        """Initialize the array setup panel.
        
        Args:
            parent: Parent widget
            on_update: Callback when array is updated
            **kwargs: Additional LabelFrame options
        """
        super().__init__(parent, text="Array Setup", padding=6, **kwargs)
        
        self.on_update = on_update
        
        self._create_variables()
        self._build_ui()
    
    def _create_variables(self):
        """Create tk variables."""
        self.n_channels_var = tk.StringVar(value=MASW2D_DEFAULTS['n_channels'])
        self.dx_var = tk.StringVar(value=MASW2D_DEFAULTS['dx'])
        self.source_type_var = tk.StringVar(value=MASW2D_DEFAULTS['source_type'])
    
    def _build_ui(self):
        """Build the panel UI.
        
        Copied from masw2d_tab.py lines 144-176.
        """
        # Row 1: Channels and spacing
        row1 = ttk.Frame(self)
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="Total Channels:").pack(side="left")
        ttk.Entry(row1, textvariable=self.n_channels_var, width=6).pack(side="left", padx=4)
        ttk.Label(row1, text="Spacing (dx):").pack(side="left", padx=(10, 0))
        ttk.Entry(row1, textvariable=self.dx_var, width=6).pack(side="left", padx=4)
        ttk.Label(row1, text="m").pack(side="left")
        
        # Row 2: Update button and info
        row2 = ttk.Frame(self)
        row2.pack(fill="x", pady=4)
        ttk.Button(row2, text="Update Array", command=self._on_update_clicked).pack(side="left")
        self.array_info_label = ttk.Label(row2, text="Length: -- m")
        self.array_info_label.pack(side="left", padx=10)
        
        # Row 3: Source type
        row3 = ttk.Frame(self)
        row3.pack(fill="x", pady=2)
        ttk.Label(row3, text="Source Type:").pack(side="left")
        
        try:
            from sw_transform.masw2d.config.templates import SOURCE_LABELS
            source_values = list(SOURCE_LABELS.keys())
        except ImportError:
            source_values = ["hammer", "vibrosis", "drop_weight"]
        
        source_combo = ttk.Combobox(row3, textvariable=self.source_type_var,
                                    values=source_values, width=15, state="readonly")
        source_combo.pack(side="left", padx=4)
        source_combo.bind("<<ComboboxSelected>>", lambda e: self._trigger_update())
        
        # Source label
        self.source_label = ttk.Label(row3, text="(Sledgehammer 5-8 kg)", foreground="gray")
        self.source_label.pack(side="left", padx=4)
        
        # Initial update
        self._update_info()
    
    def _on_update_clicked(self):
        """Handle Update Array button click."""
        self._update_info()
        self._trigger_update()
    
    def _update_info(self):
        """Update the array info label."""
        try:
            n_channels = int(self.n_channels_var.get())
            dx = float(self.dx_var.get())
            length = (n_channels - 1) * dx
            self.array_info_label.config(text=f"Length: {length:.1f} m")
        except ValueError:
            self.array_info_label.config(text="Invalid values")
        
        # Update source label
        try:
            from sw_transform.masw2d.config.templates import get_source_label
            label = get_source_label(self.source_type_var.get())
            self.source_label.config(text=f"({label})")
        except (ImportError, Exception):
            pass
    
    def _trigger_update(self):
        """Trigger the update callback."""
        if self.on_update:
            self.on_update()
    
    def get_values(self) -> dict:
        """Get current values as a dictionary.
        
        Returns:
            Dict with n_channels, dx, source_type, array_length
        """
        try:
            n_channels = int(self.n_channels_var.get())
            dx = float(self.dx_var.get())
            length = (n_channels - 1) * dx
        except ValueError:
            n_channels = 24
            dx = 2.0
            length = 46.0
        
        return {
            'n_channels': n_channels,
            'dx': dx,
            'source_type': self.source_type_var.get(),
            'array_length': length,
        }
    
    @property
    def n_channels(self) -> int:
        """Get number of channels."""
        try:
            return int(self.n_channels_var.get())
        except ValueError:
            return 24
    
    @property
    def dx(self) -> float:
        """Get channel spacing."""
        try:
            return float(self.dx_var.get())
        except ValueError:
            return 2.0
