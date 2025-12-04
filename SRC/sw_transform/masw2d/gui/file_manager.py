"""Shot file manager panel component.

Copied from masw2d_tab.py lines 178-198, 449-531.
"""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Any, Callable, Dict, List, Optional


class FileManagerPanel(ttk.LabelFrame):
    """Shot file management panel with import/add/clear.
    
    Usage:
        panel = FileManagerPanel(parent, main_app=self.main_app, log_callback=print)
        panel.pack(fill="x", padx=4, pady=4)
        
        files = panel.files
        data = panel.data  # List of dicts with file, offset, reverse, source_position
    """
    
    def __init__(self, parent: tk.Widget,
                 main_app: Optional[Any] = None,
                 log_callback: Optional[Callable[[str], None]] = None,
                 array_length_getter: Optional[Callable[[], float]] = None,
                 **kwargs):
        """Initialize the file manager panel.
        
        Args:
            parent: Parent widget
            main_app: Reference to main app for importing project files
            log_callback: Function for logging messages
            array_length_getter: Function that returns current array length
            **kwargs: Additional LabelFrame options
        """
        super().__init__(parent, text="Shot Files", padding=6, **kwargs)
        
        self.main_app = main_app
        self.log = log_callback or print
        self.get_array_length = array_length_getter or (lambda: 46.0)
        
        # State
        self.shot_files: List[str] = []
        self.shot_data: List[Dict[str, Any]] = []
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the panel UI.
        
        Copied from masw2d_tab.py lines 178-198.
        """
        # Button row
        btn_row = ttk.Frame(self)
        btn_row.pack(fill="x", pady=2)
        ttk.Button(btn_row, text="Import from Project", 
                   command=self._import_from_project).pack(side="left")
        ttk.Button(btn_row, text="Add Files...", 
                   command=self._add_shot_files).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Clear", 
                   command=self._clear_shot_files).pack(side="left", padx=4)
        
        # Treeview
        columns = ("File", "Offset", "Rev", "Source Pos")
        self.shot_tree = ttk.Treeview(self, columns=columns, show="headings", height=5)
        self.shot_tree.heading("File", text="File")
        self.shot_tree.heading("Offset", text="Offset")
        self.shot_tree.heading("Rev", text="Rev")
        self.shot_tree.heading("Source Pos", text="Source Pos")
        self.shot_tree.column("File", width=120)
        self.shot_tree.column("Offset", width=60)
        self.shot_tree.column("Rev", width=40)
        self.shot_tree.column("Source Pos", width=80)
        self.shot_tree.pack(fill="x", pady=4)
    
    def _import_from_project(self):
        """Import files from main project panel with offsets.
        
        Copied from masw2d_tab.py lines 449-494.
        """
        if not self.main_app or not hasattr(self.main_app, 'file_list'):
            messagebox.showwarning("Import", "No project files available")
            return
        
        if not self.main_app.file_list:
            messagebox.showinfo("Import", "No files loaded in project")
            return
        
        array_length = self.get_array_length()
        
        count = 0
        for filepath in self.main_app.file_list:
            base = os.path.splitext(os.path.basename(filepath))[0]
            
            # Get offset and reverse from main app
            offset_str = self.main_app.offsets.get(base, "+0")
            is_reverse = self.main_app.reverse_flags.get(base, False)
            
            # Parse offset as absolute source position
            try:
                source_pos = float(offset_str)
            except ValueError:
                source_pos = array_length  # Default: at array end
            
            # Check if already added
            existing = [s for s in self.shot_data if s["file"] == filepath]
            if not existing:
                shot_info = {
                    "file": filepath,
                    "offset": offset_str,
                    "reverse": is_reverse,
                    "source_position": source_pos
                }
                self.shot_data.append(shot_info)
                self.shot_files.append(filepath)
                rev_mark = "Yes" if is_reverse else "No"
                self.shot_tree.insert("", "end", values=(
                    base, offset_str, rev_mark, f"{source_pos:.1f}m"
                ))
                count += 1
        
        if count > 0:
            self.log(f"Imported {count} files from project")
        else:
            messagebox.showinfo("Import", "All project files already added.")
    
    def _add_shot_files(self):
        """Add shot files via dialog with auto-detection of offsets.
        
        Copied from masw2d_tab.py lines 496-531.
        """
        files = filedialog.askopenfilenames(
            title="Select Shot Files",
            filetypes=[("SEG-2 files", "*.dat *.sg2"), ("All files", "*.*")]
        )
        if not files:
            return
        
        array_length = self.get_array_length()
        
        # Try to auto-detect offsets from filenames
        try:
            from sw_transform.io.file_assignment import assign_files
            rows = assign_files(files, recursive=False, include_unknown=True)
            file_info = {str(r.file_path): r for r in rows}
        except Exception:
            file_info = {}
        
        for f in files:
            if f not in self.shot_files:
                self.shot_files.append(f)
                base = os.path.basename(f)
                
                # Try to get auto-detected offset
                row = file_info.get(f)
                if row and row.offset_m is not None:
                    source_pos = float(row.offset_m)
                    is_reverse = bool(row.reverse)
                    if source_pos >= 0:
                        offset_to_end = source_pos - array_length
                        offset_str = f"+{int(offset_to_end)}"
                    else:
                        offset_str = f"{int(source_pos)}"
                else:
                    offset_str = "+0"
                    is_reverse = False
                    source_pos = array_length
                
                shot_info = {
                    "file": f, 
                    "offset": offset_str, 
                    "reverse": is_reverse, 
                    "source_position": source_pos
                }
                self.shot_data.append(shot_info)
                rev_mark = "Yes" if is_reverse else "No"
                self.shot_tree.insert("", "end", values=(
                    base, offset_str, rev_mark, f"{source_pos:.1f}m"
                ))
    
    def _clear_shot_files(self):
        """Clear all shot files.
        
        Copied from masw2d_tab.py lines 533-537.
        """
        self.shot_files.clear()
        self.shot_data.clear()
        for item in self.shot_tree.get_children():
            self.shot_tree.delete(item)
    
    @property
    def files(self) -> List[str]:
        """Get list of shot file paths."""
        return self.shot_files.copy()
    
    @property
    def data(self) -> List[Dict[str, Any]]:
        """Get list of shot data dicts."""
        return self.shot_data.copy()
    
    def clear(self):
        """Public method to clear all files."""
        self._clear_shot_files()
