"""File tree panel component for managing data files.

Copied from simple_app.py:
- lines 60-70 (file state variables)
- lines 160-165 (Treeview setup)
- lines 398-410 (_refresh_file_tree)
- lines 653-670 (_edit_cell)
- lines 351-396 (_add_files_to_list)
"""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Callable


class FileTreePanel(tk.Frame):
    """File treeview panel with editing support.
    
    Provides a treeview for displaying data files with columns for
    filename, type, offset, and reverse flag. Supports double-click
    editing of offset and reverse columns.
    
    Usage:
        panel = FileTreePanel(parent, log_callback=print)
        panel.pack(fill="both", expand=True)
        
        panel.add_files(["/path/to/file1.dat", "/path/to/file2.mat"])
        files = panel.files  # List of file paths
        data = panel.file_data  # Dict with offset/reverse info
    """
    
    def __init__(self, parent: tk.Widget, 
                 log_callback: Callable[[str], None] | None = None,
                 **kwargs):
        """Initialize the file tree panel.
        
        Args:
            parent: Parent widget
            log_callback: Optional callback for logging messages
            **kwargs: Additional Frame options
        """
        super().__init__(parent, **kwargs)
        self.log = log_callback or (lambda msg: None)
        
        # State - copied from simple_app.py lines 60-70
        self.file_list: list[str] = []
        self.file_types: dict[str, str] = {}  # base -> 'seg2' or 'mat'
        self.offsets: dict[str, str] = {}
        self.reverse_flags: dict[str, bool] = {}
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the treeview UI.
        
        Copied from simple_app.py lines 160-165:
            self.tree = ttk.Treeview(left, columns=("file","type","offset","rev"), show="headings", height=24)
            for col, w in zip(("file","type","offset","rev"), (180, 40, 60, 40)):
                self.tree.heading(col, text=col.capitalize()); self.tree.column(col, width=w)
            self.tree.pack(fill="y", padx=8, pady=4, expand=True)
            self.tree.bind("<Double-1>", self._edit_cell)
        """
        self.tree = ttk.Treeview(
            self, 
            columns=("file", "type", "offset", "rev"), 
            show="headings", 
            height=24
        )
        
        for col, w in zip(("file", "type", "offset", "rev"), (180, 40, 60, 40)):
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=w)
        
        self.tree.pack(fill="both", padx=8, pady=4, expand=True)
        self.tree.bind("<Double-1>", self._edit_cell)
    
    def add_files(self, files: list[str] | tuple[str, ...], auto_detect: bool = True):
        """Add files to the file list.
        
        Copied from simple_app.py lines 351-396 (_add_files_to_list).
        
        Args:
            files: List of file paths to add
            auto_detect: Whether to auto-detect file type and offset
        """
        new_files = list(files)
        
        # Extend existing lists (mixed mode)
        self.file_list.extend(new_files)
        
        # Process each new file
        for f in new_files:
            base = os.path.splitext(os.path.basename(f))[0]
            ext = os.path.splitext(f)[1].lower()
            
            if ext == '.mat':
                # Vibrosis .mat file
                self.file_types[base] = 'mat'
                self.reverse_flags[base] = False
                
                # Try to detect array info and parse offset
                if auto_detect:
                    try:
                        from sw_transform.processing.vibrosis import get_vibrosis_file_info
                        info = get_vibrosis_file_info(f)
                        parsed_offset = info.get('parsed_offset')
                        if parsed_offset is not None:
                            sign = "+" if parsed_offset >= 0 else ""
                            self.offsets[base] = f"{sign}{int(round(parsed_offset))}"
                        else:
                            self.offsets[base] = "+0"
                    except Exception:
                        self.offsets[base] = "+0"
                else:
                    self.offsets[base] = "+0"
            else:
                # SEG-2 .dat file
                self.file_types[base] = 'seg2'
                self.offsets[base] = "+0"
                self.reverse_flags[base] = False
        
        # Refresh tree view
        self._refresh()
    
    def _refresh(self):
        """Refresh the treeview with current file list.
        
        Copied from simple_app.py lines 398-410 (_refresh_file_tree).
        """
        self.tree.delete(*self.tree.get_children())
        for f in self.file_list:
            base = os.path.splitext(os.path.basename(f))[0]
            ftype = self.file_types.get(base, 'seg2')
            offset = self.offsets.get(base, '+0')
            rev = self.reverse_flags.get(base, False)
            type_label = "MAT" if ftype == 'mat' else "SEG2"
            rev_label = "☑" if rev else "☐"
            self.tree.insert("", "end", values=(base, type_label, offset, rev_label))
    
    def _edit_cell(self, ev):
        """Handle double-click editing in file tree.
        
        Columns: (file, type, offset, rev)
        - Column 1 (file): not editable
        - Column 2 (type): not editable
        - Column 3 (offset): editable text entry
        - Column 4 (rev): toggle checkbox
        
        Copied from simple_app.py lines 653-670.
        """
        item = self.tree.identify_row(ev.y)
        col = self.tree.identify_column(ev.x)
        if not item:
            return
        
        col_idx = int(col.lstrip("#"))
        vals = list(self.tree.item(item, "values"))
        base = vals[0]
        
        x, y, w, h = self.tree.bbox(item, col)
        
        if col_idx == 3:  # Offset column
            e = tk.Entry(self.winfo_toplevel())
            e.insert(0, vals[2])
            e.place(
                x=x + self.tree.winfo_rootx() - self.winfo_toplevel().winfo_rootx(),
                y=y + self.tree.winfo_rooty() - self.winfo_toplevel().winfo_rooty(),
                width=w, height=h
            )
            e.focus()
            
            def _done(_):
                vals[2] = e.get()
                self.offsets[base] = vals[2]
                self.tree.item(item, values=vals)
                e.destroy()
            
            e.bind("<Return>", _done)
            e.bind("<FocusOut>", _done)
            
        elif col_idx == 4:  # Reverse column
            flag = vals[3] != "☑"
            self.reverse_flags[base] = flag
            vals[3] = "☑" if flag else "☐"
            self.tree.item(item, values=vals)
    
    def clear(self):
        """Clear all files from the list."""
        self.file_list.clear()
        self.file_types.clear()
        self.offsets.clear()
        self.reverse_flags.clear()
        self._refresh()
    
    def get_selected(self) -> list[str]:
        """Get list of selected file paths.
        
        Returns:
            List of full paths for selected files.
        """
        sel = self.tree.selection()
        if not sel:
            return []
        
        selected_bases = {self.tree.item(i, "values")[0] for i in sel}
        return [p for p in self.file_list 
                if os.path.splitext(os.path.basename(p))[0] in selected_bases]
    
    def get_selected_bases(self) -> set[str]:
        """Get set of selected file base names.
        
        Returns:
            Set of base names (without extension) for selected files.
        """
        sel = self.tree.selection()
        if not sel:
            return set()
        return {self.tree.item(i, "values")[0] for i in sel}
    
    @property
    def files(self) -> list[str]:
        """Get list of all file paths."""
        return list(self.file_list)
    
    @property
    def file_data(self) -> dict[str, dict]:
        """Get file data as dict mapping base name to info.
        
        Returns:
            Dict mapping base name to dict with:
            - path: Full file path
            - type: 'seg2' or 'mat'
            - offset: Offset string
            - reverse: Reverse flag bool
        """
        result = {}
        for path in self.file_list:
            base = os.path.splitext(os.path.basename(path))[0]
            result[base] = {
                'path': path,
                'type': self.file_types.get(base, 'seg2'),
                'offset': self.offsets.get(base, '+0'),
                'reverse': self.reverse_flags.get(base, False),
            }
        return result
    
    def has_mat_files(self) -> bool:
        """Check if any .mat files are loaded.
        
        Returns:
            True if any files have type 'mat'.
        """
        return any(t == 'mat' for t in self.file_types.values())
    
    def selection(self):
        """Get treeview selection (for compatibility)."""
        return self.tree.selection()
    
    def item(self, item_id, option=None):
        """Get treeview item info (for compatibility)."""
        return self.tree.item(item_id, option)
