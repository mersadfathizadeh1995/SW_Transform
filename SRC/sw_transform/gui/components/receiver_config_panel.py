"""Receiver configuration panel component.

Provides GUI for configuring geophone/receiver array parameters:
- Channel selection (all, first_n, last_n, range, custom)
- Spacing mode (uniform, custom positions)

Features collapsible UI - click header to expand/collapse.
Note: Source position configuration is handled separately in SourceConfigPanel.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from sw_transform.core.array_config import ArrayConfig


class ReceiverConfigPanel(tk.Frame):
    """Collapsible panel for configuring receiver/geophone array parameters.
    
    Usage:
        panel = ReceiverConfigPanel(parent)
        panel.pack(fill="x", padx=6, pady=4)
        
        config = panel.get_config()
    """
    
    def __init__(self, parent: tk.Widget, on_config_change: Optional[Callable] = None, 
                 start_collapsed: bool = True, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_config_change = on_config_change
        self._collapsed = start_collapsed
        self._create_variables()
        self._build_ui()
    
    def _create_variables(self):
        """Create tk variables for all config entries."""
        self.n_channels_file_var = tk.StringVar(value="24")
        self.dx_file_var = tk.StringVar(value="2.0")
        
        self.channel_mode_var = tk.StringVar(value="all")
        self.n_channels_use_var = tk.StringVar(value="24")
        self.channel_start_var = tk.StringVar(value="0")
        self.channel_end_var = tk.StringVar(value="24")
        self.channel_indices_var = tk.StringVar(value="")
        
        self.spacing_mode_var = tk.StringVar(value="uniform")
        self.dx_var = tk.StringVar(value="2.0")
        self.custom_positions_var = tk.StringVar(value="")
        
        # Add trace callbacks to trigger config change on Entry edits
        for var in [self.n_channels_use_var, self.channel_start_var, self.channel_end_var,
                    self.channel_indices_var, self.dx_var, self.custom_positions_var]:
            var.trace_add("write", self._on_var_change)
    
    def _build_ui(self):
        """Build the collapsible receiver config panel UI."""
        self._build_header()
        self._build_content()
        self._update_collapse_state()
    
    def _build_header(self):
        """Build clickable header row."""
        self.header = tk.Frame(self, relief="raised", bd=1)
        self.header.pack(fill="x")
        
        self.toggle_btn = tk.Label(self.header, text="▶", width=2, cursor="hand2")
        self.toggle_btn.pack(side="left", padx=2)
        
        self.title_label = tk.Label(self.header, text="Receiver Configuration", 
                                    font=("TkDefaultFont", 9, "bold"), cursor="hand2")
        self.title_label.pack(side="left", padx=4)
        
        self.summary_label = tk.Label(self.header, text="", fg="gray")
        self.summary_label.pack(side="left", padx=8)
        
        for widget in (self.header, self.toggle_btn, self.title_label, self.summary_label):
            widget.bind("<Button-1>", self._toggle_collapse)
    
    def _build_content(self):
        """Build the expandable content frame."""
        self.content = tk.LabelFrame(self, text="")
        
        self._build_file_info_section()
        self._build_channel_section()
        self._build_spacing_section()
    
    def _build_file_info_section(self):
        """Build file info display section."""
        row = tk.Frame(self.content)
        row.pack(fill="x", padx=4, pady=2)
        
        tk.Label(row, text="File Info:", font=("TkDefaultFont", 9, "bold")).pack(side="left")
        tk.Label(row, text="Channels:").pack(side="left", padx=(8, 2))
        self.n_channels_label = tk.Label(row, textvariable=self.n_channels_file_var, width=4)
        self.n_channels_label.pack(side="left")
        tk.Label(row, text="Spacing:").pack(side="left", padx=(8, 2))
        self.dx_label = tk.Label(row, textvariable=self.dx_file_var, width=6)
        self.dx_label.pack(side="left")
        tk.Label(row, text="m").pack(side="left")
    
    def _build_channel_section(self):
        """Build channel selection section."""
        frame = tk.LabelFrame(self.content, text="Channel Selection")
        frame.pack(fill="x", padx=4, pady=4)
        
        modes = [
            ("all", "All channels"),
            ("first_n", "First N"),
            ("last_n", "Last N"),
            ("range", "Range"),
            ("custom", "Custom indices"),
        ]
        
        row1 = tk.Frame(frame)
        row1.pack(fill="x", padx=4, pady=2)
        
        for i, (val, txt) in enumerate(modes):
            rb = tk.Radiobutton(row1, text=txt, variable=self.channel_mode_var, 
                               value=val, command=self._on_mode_change)
            rb.pack(side="left", padx=2)
        
        row2 = tk.Frame(frame)
        row2.pack(fill="x", padx=4, pady=2)
        
        tk.Label(row2, text="N:").pack(side="left")
        self.n_entry = tk.Entry(row2, textvariable=self.n_channels_use_var, width=5)
        self.n_entry.pack(side="left", padx=2)
        
        tk.Label(row2, text="Start:").pack(side="left", padx=(8, 0))
        self.start_entry = tk.Entry(row2, textvariable=self.channel_start_var, width=5)
        self.start_entry.pack(side="left", padx=2)
        
        tk.Label(row2, text="End:").pack(side="left", padx=(8, 0))
        self.end_entry = tk.Entry(row2, textvariable=self.channel_end_var, width=5)
        self.end_entry.pack(side="left", padx=2)
        
        row3 = tk.Frame(frame)
        row3.pack(fill="x", padx=4, pady=2)
        
        tk.Label(row3, text="Custom indices (comma-separated):").pack(side="left")
        self.indices_entry = tk.Entry(row3, textvariable=self.channel_indices_var, width=30)
        self.indices_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        self._on_mode_change()
    
    def _build_spacing_section(self):
        """Build spacing configuration section."""
        frame = tk.LabelFrame(self.content, text="Geophone Spacing")
        frame.pack(fill="x", padx=4, pady=4)
        
        row1 = tk.Frame(frame)
        row1.pack(fill="x", padx=4, pady=2)
        
        tk.Radiobutton(row1, text="Uniform", variable=self.spacing_mode_var, 
                      value="uniform", command=self._on_spacing_change).pack(side="left")
        tk.Label(row1, text="dx:").pack(side="left", padx=(8, 2))
        self.dx_entry = tk.Entry(row1, textvariable=self.dx_var, width=6)
        self.dx_entry.pack(side="left")
        tk.Label(row1, text="m").pack(side="left", padx=2)
        
        tk.Radiobutton(row1, text="Custom positions", variable=self.spacing_mode_var,
                      value="custom", command=self._on_spacing_change).pack(side="left", padx=(16, 0))
        
        row2 = tk.Frame(frame)
        row2.pack(fill="x", padx=4, pady=2)
        
        tk.Label(row2, text="Positions (comma-separated, meters):").pack(side="left")
        self.positions_entry = tk.Entry(row2, textvariable=self.custom_positions_var, width=40)
        self.positions_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        self._on_spacing_change()
    
    def _on_var_change(self, *args):
        """Handle variable change from Entry fields."""
        self._update_summary()
        if self.on_config_change:
            self.on_config_change()
    
    def _on_mode_change(self):
        """Handle channel mode change."""
        mode = self.channel_mode_var.get()
        
        self.n_entry.config(state="normal" if mode in ("first_n", "last_n") else "disabled")
        self.start_entry.config(state="normal" if mode == "range" else "disabled")
        self.end_entry.config(state="normal" if mode == "range" else "disabled")
        self.indices_entry.config(state="normal" if mode == "custom" else "disabled")
        
        self._update_summary()
        if self.on_config_change:
            self.on_config_change()
    
    def _on_spacing_change(self):
        """Handle spacing mode change."""
        mode = self.spacing_mode_var.get()
        
        self.dx_entry.config(state="normal" if mode == "uniform" else "disabled")
        self.positions_entry.config(state="normal" if mode == "custom" else "disabled")
        
        self._update_summary()
        if self.on_config_change:
            self.on_config_change()
    
    def set_file_info(self, n_channels: int, dx: float, force_reset: bool = False):
        """Set file info from loaded file.
        
        Args:
            n_channels: Number of channels in file
            dx: Channel spacing in meters
            force_reset: If True, reset user-edited values to defaults
        """
        old_n_file = self.n_channels_file_var.get()
        self.n_channels_file_var.set(str(n_channels))
        self.dx_file_var.set(f"{dx:.2f}")
        
        # Only reset user values if this is a new file or force_reset
        if force_reset or old_n_file != str(n_channels):
            self.dx_var.set(f"{dx:.2f}")
            self.n_channels_use_var.set(str(n_channels))
            self.channel_end_var.set(str(n_channels))
        self._update_summary()
    
    def get_config(self) -> ArrayConfig:
        """Get current configuration as ArrayConfig object.
        
        Note: source_position defaults to -10.0, interior_side to 'both'.
        These should be set separately via SourceConfigPanel.
        """
        n_file = int(self.n_channels_file_var.get() or "24")
        dx_file = float(self.dx_file_var.get() or "2.0")
        
        channel_indices = []
        if self.channel_indices_var.get().strip():
            try:
                channel_indices = [int(x.strip()) for x in self.channel_indices_var.get().split(",") if x.strip()]
            except ValueError:
                pass
        
        custom_positions = []
        if self.custom_positions_var.get().strip():
            try:
                custom_positions = [float(x.strip()) for x in self.custom_positions_var.get().split(",") if x.strip()]
            except ValueError:
                pass
        
        return ArrayConfig(
            n_channels_file=n_file,
            dx_file=dx_file,
            channel_mode=self.channel_mode_var.get(),
            n_channels_use=int(self.n_channels_use_var.get() or "24"),
            channel_start=int(self.channel_start_var.get() or "0"),
            channel_end=int(self.channel_end_var.get() or "24"),
            channel_indices=channel_indices,
            spacing_mode=self.spacing_mode_var.get(),
            dx=float(self.dx_var.get() or "2.0"),
            custom_positions=custom_positions,
            source_position=-10.0,  # Default, managed by SourceConfigPanel
            interior_side='both'    # Default, managed by SourceConfigPanel
        )
    
    def set_config(self, config: ArrayConfig):
        """Set configuration from ArrayConfig object."""
        self.n_channels_file_var.set(str(config.n_channels_file))
        self.dx_file_var.set(f"{config.dx_file:.2f}")
        self.channel_mode_var.set(config.channel_mode)
        self.n_channels_use_var.set(str(config.n_channels_use))
        self.channel_start_var.set(str(config.channel_start))
        self.channel_end_var.set(str(config.channel_end))
        self.channel_indices_var.set(",".join(str(i) for i in config.channel_indices))
        self.spacing_mode_var.set(config.spacing_mode)
        self.dx_var.set(f"{config.dx:.2f}")
        self.custom_positions_var.set(",".join(f"{p:.1f}" for p in config.custom_positions))
        
        self._on_mode_change()
        self._on_spacing_change()
        self._update_summary()
    
    def is_custom_mode(self) -> bool:
        """Check if receiver config uses non-standard channel selection."""
        return self.channel_mode_var.get() != 'all'
    
    def _toggle_collapse(self, event=None):
        """Toggle collapsed state."""
        self._collapsed = not self._collapsed
        self._update_collapse_state()
    
    def _update_collapse_state(self):
        """Update UI based on collapsed state."""
        if self._collapsed:
            self.toggle_btn.config(text="▶")
            self.content.pack_forget()
        else:
            self.toggle_btn.config(text="▼")
            self.content.pack(fill="x", padx=4, pady=4)
        self._update_summary()
    
    def _update_summary(self):
        """Update summary label in header."""
        n_ch = self.n_channels_file_var.get()
        dx = self.dx_file_var.get()
        mode = self.channel_mode_var.get()
        self.summary_label.config(text=f"[{n_ch} ch, dx={dx}m, mode={mode}]")
    
    def expand(self):
        """Expand the panel."""
        self._collapsed = False
        self._update_collapse_state()
    
    def collapse(self):
        """Collapse the panel."""
        self._collapsed = True
        self._update_collapse_state()
