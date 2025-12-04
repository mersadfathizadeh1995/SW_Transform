"""Sub-array configuration panel component.

Copied from masw2d_tab.py lines 200-240, 296-373.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional

from sw_transform.masw2d.gui.defaults import MASW2D_DEFAULTS


class SubarrayConfigPanel(ttk.LabelFrame):
    """Sub-array configuration panel with checkboxes and preview selector.
    
    Usage:
        panel = SubarrayConfigPanel(
            parent,
            n_channels_getter=lambda: 24,
            on_preview_change=self._update_preview
        )
        panel.pack(fill="x", padx=4, pady=4)
        
        sizes = panel.get_selected_sizes()  # [12, 14, 16, ...]
        preview_size = panel.preview_size
    """
    
    def __init__(self, parent: tk.Widget,
                 n_channels_getter: Optional[Callable[[], int]] = None,
                 on_preview_change: Optional[Callable[[], None]] = None,
                 **kwargs):
        """Initialize the subarray config panel.
        
        Args:
            parent: Parent widget
            n_channels_getter: Function that returns current n_channels
            on_preview_change: Callback when preview selection changes
            **kwargs: Additional LabelFrame options
        """
        super().__init__(parent, text="Sub-Array Configurations", padding=6, **kwargs)
        
        self.get_n_channels = n_channels_getter or (lambda: 24)
        self.on_preview_change = on_preview_change
        
        # State
        self.subarray_checks: Dict[int, tk.BooleanVar] = {}
        self._first_update = True
        
        self._create_variables()
        self._build_ui()
        
        # Initial update
        self.update_checkboxes()
    
    def _create_variables(self):
        """Create tk variables."""
        self.slide_step_var = tk.StringVar(value=MASW2D_DEFAULTS['slide_step'])
        self.subarray_var = tk.StringVar(value="12")  # Preview selection
    
    def _build_ui(self):
        """Build the panel UI.
        
        Copied from masw2d_tab.py lines 200-240.
        """
        # Quick select buttons
        btn_row = ttk.Frame(self)
        btn_row.pack(fill="x", pady=2)
        ttk.Button(btn_row, text="All", width=5, 
                   command=self._select_all).pack(side="left", padx=2)
        ttk.Button(btn_row, text="None", width=5, 
                   command=self._select_none).pack(side="left", padx=2)
        ttk.Button(btn_row, text="Even", width=5, 
                   command=self._select_even).pack(side="left", padx=2)
        
        # Checkboxes container
        self.check_frame = ttk.Frame(self)
        self.check_frame.pack(fill="x", pady=2)
        
        # Slide step
        row_ss = ttk.Frame(self)
        row_ss.pack(fill="x", pady=4)
        ttk.Label(row_ss, text="Slide Step:").pack(side="left")
        ttk.Entry(row_ss, textvariable=self.slide_step_var, width=4).pack(side="left", padx=4)
        ttk.Label(row_ss, text="channels").pack(side="left")
        
        # Preview selector
        row_prev = ttk.Frame(self)
        row_prev.pack(fill="x", pady=4)
        ttk.Label(row_prev, text="Preview:").pack(side="left")
        self.preview_combo = ttk.Combobox(row_prev, textvariable=self.subarray_var,
                                          width=8, state="readonly")
        self.preview_combo.pack(side="left", padx=4)
        self.preview_combo.bind("<<ComboboxSelected>>", 
                                lambda e: self._trigger_preview_change())
    
    def _select_all(self):
        """Select all sub-array sizes.
        
        Copied from masw2d_tab.py lines 296-299.
        """
        for var in self.subarray_checks.values():
            var.set(True)
    
    def _select_none(self):
        """Deselect all sub-array sizes.
        
        Copied from masw2d_tab.py lines 301-304.
        """
        for var in self.subarray_checks.values():
            var.set(False)
    
    def _select_even(self):
        """Select only even sub-array sizes.
        
        Copied from masw2d_tab.py lines 306-309.
        """
        for size, var in self.subarray_checks.items():
            var.set(size % 2 == 0)
    
    def update_checkboxes(self):
        """Update the sub-array configuration checkboxes.
        
        Copied from masw2d_tab.py lines 311-351.
        """
        # Preserve previously selected sizes
        previously_selected = {size for size, var in self.subarray_checks.items() if var.get()}
        
        # Clear existing widgets
        for widget in self.check_frame.winfo_children():
            widget.destroy()
        self.subarray_checks.clear()
        
        n_channels = self.get_n_channels()
        
        # Get available sizes
        try:
            from sw_transform.masw2d.config.templates import get_available_subarray_sizes
            sizes = get_available_subarray_sizes(n_channels, min_channels=6)
        except ImportError:
            sizes = [s for s in range(6, n_channels + 1) if s <= n_channels]
        
        # Determine which to select
        if self._first_update:
            valid_previous = {s for s in sizes if s % 2 == 0}
            self._first_update = False
        else:
            valid_previous = previously_selected.intersection(set(sizes))
            if not valid_previous:
                valid_previous = {s for s in sizes if s % 2 == 0}
        
        # Create grid of checkboxes (4 per row)
        cols = 4
        row_frame = None
        for i, size in enumerate(sizes):
            col_idx = i % cols
            
            if col_idx == 0:
                row_frame = ttk.Frame(self.check_frame)
                row_frame.pack(fill="x", pady=1)
            
            var = tk.BooleanVar(value=(size in valid_previous))
            self.subarray_checks[size] = var
            
            cb = ttk.Checkbutton(row_frame, text=f"{size}ch", variable=var)
            cb.pack(side="left", padx=4)
        
        # Update preview combo
        self._update_preview_combo(sizes)
    
    def _update_preview_combo(self, sizes: List[int]):
        """Update the preview size combobox.
        
        Copied from masw2d_tab.py lines 353-363.
        """
        self.preview_combo['values'] = [str(s) for s in sizes]
        
        current = self.subarray_var.get()
        if current not in [str(s) for s in sizes]:
            mid = sizes[len(sizes) // 2] if sizes else 12
            self.subarray_var.set(str(mid))
    
    def _trigger_preview_change(self):
        """Trigger the preview change callback."""
        if self.on_preview_change:
            self.on_preview_change()
    
    def get_selected_sizes(self) -> List[int]:
        """Get list of checked sub-array sizes."""
        return [size for size, var in self.subarray_checks.items() if var.get()]
    
    @property
    def slide_step(self) -> int:
        """Get slide step value."""
        try:
            return int(self.slide_step_var.get())
        except ValueError:
            return 1
    
    @property
    def preview_size(self) -> int:
        """Get currently selected preview size."""
        try:
            return int(self.subarray_var.get())
        except ValueError:
            return 12
