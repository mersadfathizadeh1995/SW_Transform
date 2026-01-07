"""Source configuration panel component.

Provides GUI for configuring per-file source positions:
- Standard mode: Auto-assign from filename parsing
- Custom mode: Manual editing of source positions per file

Features collapsible UI with embedded file table.
"""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional, Tuple


class SourceConfigPanel(tk.Frame):
    """Collapsible panel for configuring source positions per file.
    
    Usage:
        panel = SourceConfigPanel(parent)
        panel.pack(fill="x", padx=6, pady=4)
        
        panel.update_files(file_info_dict)
        positions = panel.get_source_positions()
    """
    
    def __init__(self, parent: tk.Widget, on_config_change: Optional[Callable] = None,
                 start_collapsed: bool = True, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_config_change = on_config_change
        self._collapsed = start_collapsed
        self._file_data: Dict[str, dict] = {}  # base -> {path, offset, source_pos, shot_type}
        self._receiver_positions: List[float] = []
        self._create_variables()
        self._build_ui()
    
    def _create_variables(self):
        """Create tk variables."""
        self.mode_var = tk.StringVar(value="standard")
        self.interior_side_var = tk.StringVar(value="both")
        
        self.mode_var.trace_add("write", self._on_mode_change)
        self.interior_side_var.trace_add("write", self._on_var_change)
    
    def _build_ui(self):
        """Build the collapsible source config panel UI."""
        self._build_header()
        self._build_content()
        self._update_collapse_state()
    
    def _build_header(self):
        """Build clickable header row."""
        self.header = tk.Frame(self, relief="raised", bd=1)
        self.header.pack(fill="x")
        
        self.toggle_btn = tk.Label(self.header, text="▶", width=2, cursor="hand2")
        self.toggle_btn.pack(side="left", padx=2)
        
        self.title_label = tk.Label(self.header, text="Source Configuration",
                                    font=("TkDefaultFont", 9, "bold"), cursor="hand2")
        self.title_label.pack(side="left", padx=4)
        
        self.summary_label = tk.Label(self.header, text="[0 files, mode=standard]", fg="gray")
        self.summary_label.pack(side="left", padx=8)
        
        for widget in (self.header, self.toggle_btn, self.title_label, self.summary_label):
            widget.bind("<Button-1>", self._toggle_collapse)
    
    def _build_content(self):
        """Build the expandable content frame."""
        self.content = tk.LabelFrame(self, text="")
        
        self._build_mode_section()
        self._build_interior_section()
        self._build_table_section()
    
    def _build_mode_section(self):
        """Build mode selection section."""
        row = tk.Frame(self.content)
        row.pack(fill="x", padx=4, pady=4)
        
        tk.Label(row, text="Mode:", font=("TkDefaultFont", 9, "bold")).pack(side="left")
        
        tk.Radiobutton(row, text="Standard (auto from filenames)", 
                      variable=self.mode_var, value="standard").pack(side="left", padx=(8, 4))
        tk.Radiobutton(row, text="Custom (edit table below)",
                      variable=self.mode_var, value="custom").pack(side="left", padx=4)
    
    def _build_interior_section(self):
        """Build interior shot handling section."""
        row = tk.Frame(self.content)
        row.pack(fill="x", padx=4, pady=2)
        
        tk.Label(row, text="Interior shot side:").pack(side="left")
        tk.Radiobutton(row, text="Left", variable=self.interior_side_var,
                      value="left").pack(side="left", padx=4)
        tk.Radiobutton(row, text="Right", variable=self.interior_side_var,
                      value="right").pack(side="left", padx=4)
        tk.Radiobutton(row, text="Both", variable=self.interior_side_var,
                      value="both").pack(side="left", padx=4)
    
    def _build_table_section(self):
        """Build the file table section."""
        frame = tk.LabelFrame(self.content, text="Source Positions per File")
        frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Treeview with scrollbar
        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("file", "offset", "source_pos", "shot_type"),
            show="headings",
            height=6
        )
        
        # Column configuration
        self.tree.heading("file", text="File")
        self.tree.heading("offset", text="Offset")
        self.tree.heading("source_pos", text="Source Pos (m)")
        self.tree.heading("shot_type", text="Shot Type")
        
        self.tree.column("file", width=120)
        self.tree.column("offset", width=60)
        self.tree.column("source_pos", width=100)
        self.tree.column("shot_type", width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Double-click to edit (only in custom mode)
        self.tree.bind("<Double-1>", self._on_double_click)
    
    def _on_mode_change(self, *args):
        """Handle mode change."""
        mode = self.mode_var.get()
        if mode == "standard":
            self._recalculate_standard_positions()
        self._update_summary()
        if self.on_config_change:
            self.on_config_change()
    
    def _on_var_change(self, *args):
        """Handle variable change."""
        self._update_shot_types()
        self._update_summary()
        if self.on_config_change:
            self.on_config_change()
    
    def _on_double_click(self, event):
        """Handle double-click on tree item to edit source position."""
        if self.mode_var.get() != "custom":
            from tkinter import messagebox
            messagebox.showinfo("Edit Source", "Switch to 'Custom' mode to edit source positions.")
            return
        
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        # Get current values
        values = list(self.tree.item(item, "values"))
        base = values[0]
        
        # Always edit the source_pos column (#3) regardless of where clicked
        column = "#3"
        
        # Create entry for editing
        bbox = self.tree.bbox(item, column)
        if not bbox:
            return
        
        x, y, width, height = bbox
        entry = tk.Entry(self.tree, width=10)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, values[2])
        entry.select_range(0, tk.END)
        entry.focus()
        
        def save_edit(event=None):
            try:
                new_val = float(entry.get())
                values[2] = f"{new_val:.1f}"
                self._file_data[base]['source_pos'] = new_val
                self._update_shot_type_for_file(base)
                values[3] = self._file_data[base]['shot_type']
                self.tree.item(item, values=values)
                if self.on_config_change:
                    self.on_config_change()
            except ValueError:
                pass
            entry.destroy()
        
        def cancel_edit(event=None):
            entry.destroy()
        
        entry.bind("<Return>", save_edit)
        entry.bind("<Escape>", cancel_edit)
        entry.bind("<FocusOut>", save_edit)
    
    def update_files(self, file_info: Dict[str, dict]):
        """Update the file list from FileTreePanel.
        
        Args:
            file_info: Dict mapping base name to {path, type, offset, reverse}
        """
        self._file_data.clear()
        
        for base, info in file_info.items():
            offset_str = info.get('offset', '+0')
            source_pos = self._parse_offset_to_position(offset_str)
            
            self._file_data[base] = {
                'path': info.get('path', ''),
                'offset': offset_str,
                'source_pos': source_pos,
                'shot_type': 'unknown'
            }
        
        self._update_shot_types()
        self._refresh_table()
        self._update_summary()
    
    def _parse_offset_to_position(self, offset_str: str) -> float:
        """Parse offset string to source position value."""
        try:
            offset_str = offset_str.strip().replace("m", "")
            if offset_str.startswith("+"):
                return float(offset_str[1:])
            else:
                return float(offset_str)
        except (ValueError, AttributeError):
            return -10.0
    
    def _recalculate_standard_positions(self):
        """Recalculate source positions from offset strings."""
        for base, data in self._file_data.items():
            data['source_pos'] = self._parse_offset_to_position(data['offset'])
        self._update_shot_types()
        self._refresh_table()
    
    def update_receiver_positions(self, positions: List[float]):
        """Update receiver positions for shot type calculation.
        
        Args:
            positions: List of receiver positions in meters
        """
        self._receiver_positions = list(positions) if positions is not None else []
        self._update_shot_types()
        self._refresh_table()
    
    def _update_shot_types(self):
        """Update shot types for all files based on receiver positions."""
        for base in self._file_data:
            self._update_shot_type_for_file(base)
    
    def _update_shot_type_for_file(self, base: str):
        """Update shot type for a specific file."""
        if not self._receiver_positions or len(self._receiver_positions) < 2:
            self._file_data[base]['shot_type'] = 'unknown'
            return
        
        src_pos = self._file_data[base]['source_pos']
        array_start = min(self._receiver_positions)
        array_end = max(self._receiver_positions)
        tolerance = 0.01 * abs(array_end - array_start) if array_end != array_start else 0.1
        
        if abs(src_pos - array_start) < tolerance:
            shot_type = 'edge_left'
        elif abs(src_pos - array_end) < tolerance:
            shot_type = 'edge_right'
        elif src_pos < array_start:
            shot_type = 'exterior_left'
        elif src_pos > array_end:
            shot_type = 'exterior_right'
        else:
            shot_type = 'interior'
        
        self._file_data[base]['shot_type'] = shot_type
    
    def _refresh_table(self):
        """Refresh the treeview with current file data."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add items
        for base, data in sorted(self._file_data.items()):
            self.tree.insert("", "end", values=(
                base,
                data['offset'],
                f"{data['source_pos']:.1f}",
                data['shot_type']
            ))
    
    def get_source_positions(self) -> Dict[str, float]:
        """Get source positions for all files.
        
        Returns:
            Dict mapping base name to source position in meters
        """
        return {base: data['source_pos'] for base, data in self._file_data.items()}
    
    def get_interior_side(self) -> str:
        """Get interior shot side setting."""
        return self.interior_side_var.get()
    
    def is_custom_mode(self) -> bool:
        """Check if custom mode is enabled."""
        return self.mode_var.get() == "custom"
    
    def set_mode(self, mode: str):
        """Set the mode ('standard' or 'custom')."""
        if mode in ('standard', 'custom'):
            self.mode_var.set(mode)
    
    def force_custom_mode(self, force: bool = True):
        """Force custom mode and optionally disable standard option."""
        if force:
            self.mode_var.set("custom")
    
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
            self.content.pack(fill="both", expand=True, padx=4, pady=4)
        self._update_summary()
    
    def _update_summary(self):
        """Update summary label in header."""
        n_files = len(self._file_data)
        mode = self.mode_var.get()
        self.summary_label.config(text=f"[{n_files} files, mode={mode}]")
    
    def expand(self):
        """Expand the panel."""
        self._collapsed = False
        self._update_collapse_state()
    
    def collapse(self):
        """Collapse the panel."""
        self._collapsed = True
        self._update_collapse_state()
    
    def clear(self):
        """Clear all file data."""
        self._file_data.clear()
        self._refresh_table()
        self._update_summary()
