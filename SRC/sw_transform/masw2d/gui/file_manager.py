"""Shot file manager panel component.

Copied from masw2d_tab.py lines 178-198, 449-531.
Updated to support Vibrosis .mat files for MASW 2D processing.
"""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Any, Callable, Dict, List, Optional


class FileManagerPanel(ttk.LabelFrame):
    """Shot file management panel with import/add/clear.
    
    Supports both SEG-2 (.dat/.sg2) and Vibrosis (.mat) files.
    
    Usage:
        panel = FileManagerPanel(parent, main_app=self.main_app, log_callback=print)
        panel.pack(fill="x", padx=4, pady=4)
        
        files = panel.files
        data = panel.data  # List of dicts with file, offset, reverse, source_position, file_type
        has_mat = panel.has_mat_files  # True if any .mat files loaded
    """
    
    def __init__(self, parent: tk.Widget,
                 main_app: Optional[Any] = None,
                 log_callback: Optional[Callable[[str], None]] = None,
                 array_length_getter: Optional[Callable[[], float]] = None,
                 on_files_changed: Optional[Callable[[], None]] = None,
                 **kwargs):
        """Initialize the file manager panel.
        
        Args:
            parent: Parent widget
            main_app: Reference to main app for importing project files
            log_callback: Function for logging messages
            array_length_getter: Function that returns current array length
            on_files_changed: Callback when files are added/removed
            **kwargs: Additional LabelFrame options
        """
        super().__init__(parent, text="Shot Files", padding=6, **kwargs)
        
        self.main_app = main_app
        self.log = log_callback or print
        self.get_array_length = array_length_getter or (lambda: 46.0)
        self.on_files_changed = on_files_changed
        
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
        
        # Treeview with Type column
        columns = ("File", "Type", "Offset", "Rev", "Source Pos")
        self.shot_tree = ttk.Treeview(self, columns=columns, show="headings", height=5)
        self.shot_tree.heading("File", text="File")
        self.shot_tree.heading("Type", text="Type")
        self.shot_tree.heading("Offset", text="Offset")
        self.shot_tree.heading("Rev", text="Rev")
        self.shot_tree.heading("Source Pos", text="Source Pos")
        self.shot_tree.column("File", width=100)
        self.shot_tree.column("Type", width=40)
        self.shot_tree.column("Offset", width=50)
        self.shot_tree.column("Rev", width=35)
        self.shot_tree.column("Source Pos", width=70)
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
            ext = os.path.splitext(filepath)[1].lower()
            
            # Determine file type
            file_type = 'mat' if ext == '.mat' else 'seg2'
            
            # Get offset and reverse from main app
            offset_str = self.main_app.offsets.get(base, "+0")
            is_reverse = self.main_app.reverse_flags.get(base, False)
            
            # Parse offset as absolute source position
            try:
                source_pos = float(offset_str)
            except ValueError:
                source_pos = array_length  # Default: at array end
            
            # For .mat files, try to get channel count
            n_channels = None
            if file_type == 'mat':
                try:
                    from sw_transform.processing.vibrosis import detect_array_from_mat
                    info = detect_array_from_mat(filepath)
                    n_channels = info.get('n_channels')
                except Exception:
                    pass
            
            # Check if already added
            existing = [s for s in self.shot_data if s["file"] == filepath]
            if not existing:
                shot_info = {
                    "file": filepath,
                    "offset": offset_str,
                    "reverse": is_reverse,
                    "source_position": source_pos,
                    "file_type": file_type,
                    "n_channels": n_channels
                }
                self.shot_data.append(shot_info)
                self.shot_files.append(filepath)
                rev_mark = "Yes" if is_reverse else "No"
                type_label = "MAT" if file_type == 'mat' else "SEG2"
                self.shot_tree.insert("", "end", values=(
                    base, type_label, offset_str, rev_mark, f"{source_pos:.1f}m"
                ))
                count += 1
        
        if count > 0:
            self.log(f"Imported {count} files from project")
            if self.on_files_changed:
                self.on_files_changed()
        else:
            messagebox.showinfo("Import", "All project files already added.")
    
    def _add_shot_files(self):
        """Add shot files via dialog with auto-detection of offsets.
        
        Supports both SEG-2 (.dat/.sg2) and Vibrosis (.mat) files.
        """
        files = filedialog.askopenfilenames(
            title="Select Shot Files",
            filetypes=[
                ("All supported", "*.dat *.sg2 *.mat"),
                ("SEG-2 files", "*.dat *.sg2"),
                ("Vibrosis .mat", "*.mat"),
                ("All files", "*.*")
            ]
        )
        if not files:
            return
        
        array_length = self.get_array_length()
        
        # Try to auto-detect offsets from filenames (for SEG-2)
        try:
            from sw_transform.io.file_assignment import assign_files
            seg2_files = [f for f in files if not f.lower().endswith('.mat')]
            if seg2_files:
                rows = assign_files(seg2_files, recursive=False, include_unknown=True)
                file_info = {str(r.file_path): r for r in rows}
            else:
                file_info = {}
        except Exception:
            file_info = {}
        
        for f in files:
            if f not in self.shot_files:
                self.shot_files.append(f)
                base = os.path.basename(f)
                base_no_ext = os.path.splitext(base)[0]
                ext = os.path.splitext(f)[1].lower()
                
                # Determine file type
                file_type = 'mat' if ext == '.mat' else 'seg2'
                n_channels = None
                
                if file_type == 'mat':
                    # Vibrosis .mat file
                    try:
                        from sw_transform.processing.vibrosis import get_vibrosis_file_info
                        info = get_vibrosis_file_info(f)
                        n_channels = info.get('n_channels')
                        parsed_offset = info.get('parsed_offset')
                        if parsed_offset is not None:
                            source_pos = float(parsed_offset)
                            sign = "+" if source_pos >= 0 else ""
                            offset_str = f"{sign}{int(round(source_pos))}"
                        else:
                            offset_str = "+0"
                            source_pos = array_length
                    except Exception:
                        offset_str = "+0"
                        source_pos = array_length
                    is_reverse = False  # .mat files don't have reverse concept
                else:
                    # SEG-2 file - try to get auto-detected offset
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
                    "source_position": source_pos,
                    "file_type": file_type,
                    "n_channels": n_channels
                }
                self.shot_data.append(shot_info)
                rev_mark = "Yes" if is_reverse else "No"
                type_label = "MAT" if file_type == 'mat' else "SEG2"
                self.shot_tree.insert("", "end", values=(
                    base_no_ext, type_label, offset_str, rev_mark, f"{source_pos:.1f}m"
                ))
        
        if self.on_files_changed:
            self.on_files_changed()
    
    def _clear_shot_files(self):
        """Clear all shot files.
        
        Copied from masw2d_tab.py lines 533-537.
        """
        self.shot_files.clear()
        self.shot_data.clear()
        for item in self.shot_tree.get_children():
            self.shot_tree.delete(item)
        if self.on_files_changed:
            self.on_files_changed()
    
    @property
    def files(self) -> List[str]:
        """Get list of shot file paths."""
        return self.shot_files.copy()
    
    @property
    def data(self) -> List[Dict[str, Any]]:
        """Get list of shot data dicts."""
        return self.shot_data.copy()
    
    @property
    def has_mat_files(self) -> bool:
        """Check if any .mat (vibrosis) files are loaded."""
        return any(s.get("file_type") == "mat" for s in self.shot_data)
    
    @property
    def has_seg2_files(self) -> bool:
        """Check if any SEG-2 files are loaded."""
        return any(s.get("file_type", "seg2") == "seg2" for s in self.shot_data)
    
    @property
    def has_mixed_files(self) -> bool:
        """Check if both .mat and SEG-2 files are loaded (not recommended)."""
        return self.has_mat_files and self.has_seg2_files
    
    def clear(self):
        """Public method to clear all files."""
        self._clear_shot_files()
