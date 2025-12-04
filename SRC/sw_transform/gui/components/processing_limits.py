"""Processing limits panel component.

Copied from simple_app.py lines 186-208 (Processing Limits LabelFrame).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from sw_transform.gui.utils.defaults import LIMITS_DEFAULTS


class ProcessingLimitsPanel(tk.LabelFrame):
    """Panel for velocity, frequency, and time window limits.
    
    Provides entry fields for processing parameter limits used in
    MASW transforms.
    
    Usage:
        panel = ProcessingLimitsPanel(parent)
        panel.pack(fill="x", padx=6, pady=4)
        
        values = panel.get_values()
        # values = {'vmin': 0, 'vmax': 5000, 'fmin': 0, 'fmax': 100, 
        #           'time_start': 0.0, 'time_end': 1.0}
    """
    
    def __init__(self, parent: tk.Widget, include_time: bool = True, **kwargs):
        """Initialize the processing limits panel.
        
        Args:
            parent: Parent widget
            include_time: Whether to include time window row (default True)
            **kwargs: Additional LabelFrame options
        """
        super().__init__(parent, text="Processing Limits", **kwargs)
        self.include_time = include_time
        self._create_variables()
        self._build_ui()
    
    def _create_variables(self):
        """Create tk variables for all limit entries.
        
        Copied from simple_app.py lines 82-84:
            self.vmin_var = tk.StringVar(value="0"); self.vmax_var = tk.StringVar(value="5000")
            self.fmin_var = tk.StringVar(value="0"); self.fmax_var = tk.StringVar(value="100")
            self.time_start_var = tk.StringVar(value="0.0"); self.time_end_var = tk.StringVar(value="1.0")
        """
        self.vmin_var = tk.StringVar(value=LIMITS_DEFAULTS['vmin'])
        self.vmax_var = tk.StringVar(value=LIMITS_DEFAULTS['vmax'])
        self.fmin_var = tk.StringVar(value=LIMITS_DEFAULTS['fmin'])
        self.fmax_var = tk.StringVar(value=LIMITS_DEFAULTS['fmax'])
        self.time_start_var = tk.StringVar(value=LIMITS_DEFAULTS['time_start'])
        self.time_end_var = tk.StringVar(value=LIMITS_DEFAULTS['time_end'])
    
    def _build_ui(self):
        """Build the limits panel UI.
        
        Copied from simple_app.py lines 186-208:
            # Processing Limits (simplified)
            limits_box = tk.LabelFrame(p, text="Processing Limits"); limits_box.pack(fill="x", padx=6, pady=4)
            lim_row1 = tk.Frame(limits_box); lim_row1.pack(fill="x", pady=2)
            tk.Label(lim_row1, text="Velocity:").pack(side="left")
            tk.Entry(lim_row1, width=6, textvariable=self.vmin_var).pack(side="left", padx=2)
            tk.Label(lim_row1, text="-").pack(side="left")
            tk.Entry(lim_row1, width=6, textvariable=self.vmax_var).pack(side="left", padx=2)
            tk.Label(lim_row1, text="m/s").pack(side="left", padx=(0, 12))
            tk.Label(lim_row1, text="Frequency:").pack(side="left")
            tk.Entry(lim_row1, width=6, textvariable=self.fmin_var).pack(side="left", padx=2)
            tk.Label(lim_row1, text="-").pack(side="left")
            tk.Entry(lim_row1, width=6, textvariable=self.fmax_var).pack(side="left", padx=2)
            tk.Label(lim_row1, text="Hz").pack(side="left")
            
            lim_row2 = tk.Frame(limits_box); lim_row2.pack(fill="x", pady=2)
            tk.Label(lim_row2, text="Time Window:").pack(side="left")
            tk.Entry(lim_row2, width=6, textvariable=self.time_start_var).pack(side="left", padx=2)
            tk.Label(lim_row2, text="-").pack(side="left")
            tk.Entry(lim_row2, width=6, textvariable=self.time_end_var).pack(side="left", padx=2)
            tk.Label(lim_row2, text="sec").pack(side="left")
        """
        # Row 1: Velocity and Frequency
        lim_row1 = tk.Frame(self)
        lim_row1.pack(fill="x", pady=2)
        
        tk.Label(lim_row1, text="Velocity:").pack(side="left")
        tk.Entry(lim_row1, width=6, textvariable=self.vmin_var).pack(side="left", padx=2)
        tk.Label(lim_row1, text="-").pack(side="left")
        tk.Entry(lim_row1, width=6, textvariable=self.vmax_var).pack(side="left", padx=2)
        tk.Label(lim_row1, text="m/s").pack(side="left", padx=(0, 12))
        
        tk.Label(lim_row1, text="Frequency:").pack(side="left")
        tk.Entry(lim_row1, width=6, textvariable=self.fmin_var).pack(side="left", padx=2)
        tk.Label(lim_row1, text="-").pack(side="left")
        tk.Entry(lim_row1, width=6, textvariable=self.fmax_var).pack(side="left", padx=2)
        tk.Label(lim_row1, text="Hz").pack(side="left")
        
        # Row 2: Time Window (optional)
        if self.include_time:
            lim_row2 = tk.Frame(self)
            lim_row2.pack(fill="x", pady=2)
            
            tk.Label(lim_row2, text="Time Window:").pack(side="left")
            tk.Entry(lim_row2, width=6, textvariable=self.time_start_var).pack(side="left", padx=2)
            tk.Label(lim_row2, text="-").pack(side="left")
            tk.Entry(lim_row2, width=6, textvariable=self.time_end_var).pack(side="left", padx=2)
            tk.Label(lim_row2, text="sec").pack(side="left")
    
    def get_values(self) -> dict:
        """Get current limit values as a dictionary.
        
        Returns:
            Dict with keys: vmin, vmax, fmin, fmax, time_start, time_end
            Values are floats.
        
        Raises:
            ValueError: If any value cannot be converted to float.
        """
        try:
            result = {
                'vmin': float(self.vmin_var.get()),
                'vmax': float(self.vmax_var.get()),
                'fmin': float(self.fmin_var.get()),
                'fmax': float(self.fmax_var.get()),
            }
            if self.include_time:
                result['time_start'] = float(self.time_start_var.get())
                result['time_end'] = float(self.time_end_var.get())
            return result
        except ValueError as e:
            raise ValueError(f"Invalid limit value: {e}")
    
    def set_values(self, 
                   vmin: str | None = None,
                   vmax: str | None = None,
                   fmin: str | None = None,
                   fmax: str | None = None,
                   time_start: str | None = None,
                   time_end: str | None = None):
        """Set limit values.
        
        Args:
            vmin: Minimum velocity
            vmax: Maximum velocity
            fmin: Minimum frequency
            fmax: Maximum frequency
            time_start: Time window start
            time_end: Time window end
        """
        if vmin is not None:
            self.vmin_var.set(str(vmin))
        if vmax is not None:
            self.vmax_var.set(str(vmax))
        if fmin is not None:
            self.fmin_var.set(str(fmin))
        if fmax is not None:
            self.fmax_var.set(str(fmax))
        if time_start is not None:
            self.time_start_var.set(str(time_start))
        if time_end is not None:
            self.time_end_var.set(str(time_end))
    
    def reset_to_defaults(self):
        """Reset all values to defaults."""
        self.vmin_var.set(LIMITS_DEFAULTS['vmin'])
        self.vmax_var.set(LIMITS_DEFAULTS['vmax'])
        self.fmin_var.set(LIMITS_DEFAULTS['fmin'])
        self.fmax_var.set(LIMITS_DEFAULTS['fmax'])
        self.time_start_var.set(LIMITS_DEFAULTS['time_start'])
        self.time_end_var.set(LIMITS_DEFAULTS['time_end'])
