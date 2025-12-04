"""Output settings panel component.

Copied from masw2d_tab.py lines 280-308.
"""
from __future__ import annotations

import multiprocessing
import tkinter as tk
from tkinter import ttk, filedialog


class OutputPanel(ttk.LabelFrame):
    """Output settings panel with directory and parallel options.
    
    Usage:
        panel = OutputPanel(parent)
        panel.pack(fill="x", padx=4, pady=4)
        
        values = panel.get_values()
    """
    
    def __init__(self, parent: tk.Widget, **kwargs):
        """Initialize the output panel.
        
        Args:
            parent: Parent widget
            **kwargs: Additional LabelFrame options
        """
        super().__init__(parent, text="Output", padding=6, **kwargs)
        
        self._create_variables()
        self._build_ui()
    
    def _create_variables(self):
        """Create tk variables."""
        self.output_dir_var = tk.StringVar(value="")
        self.parallel_var = tk.BooleanVar(value=True)
        self.worker_var = tk.StringVar(value="auto")
        self.include_images_var = tk.BooleanVar(value=True)
    
    def _build_ui(self):
        """Build the panel UI.
        
        Copied from masw2d_tab.py lines 280-308.
        """
        # Directory row
        row_dir = ttk.Frame(self)
        row_dir.pack(fill="x", pady=2)
        ttk.Entry(row_dir, textvariable=self.output_dir_var, width=30).pack(
            side="left", fill="x", expand=True)
        ttk.Button(row_dir, text="Browse...", 
                   command=self._select_output_dir).pack(side="left", padx=4)
        
        # Parallel row
        row_par = ttk.Frame(self)
        row_par.pack(fill="x", pady=4)
        ttk.Checkbutton(row_par, text="Parallel", variable=self.parallel_var).pack(side="left")
        ttk.Label(row_par, text="Workers:").pack(side="left", padx=(10, 2))
        
        max_cpu = multiprocessing.cpu_count()
        worker_combo = ttk.Combobox(row_par, textvariable=self.worker_var,
                                     values=["auto"] + [str(i) for i in range(1, max_cpu + 1)],
                                     width=5, state="readonly")
        worker_combo.pack(side="left")
        
        # Image export option
        row_img = ttk.Frame(self)
        row_img.pack(fill="x", pady=2)
        ttk.Checkbutton(row_img, text="Export Dispersion Images", 
                        variable=self.include_images_var).pack(side="left")
    
    def _select_output_dir(self):
        """Select output directory.
        
        Copied from masw2d_tab.py lines 539-542.
        """
        dir_path = filedialog.askdirectory(title="Select Output Directory")
        if dir_path:
            self.output_dir_var.set(dir_path)
    
    def get_values(self) -> dict:
        """Get current values as a dictionary.
        
        Returns:
            Dict with output_dir, parallel, workers, include_images
        """
        workers = self.worker_var.get()
        max_workers = None if workers == "auto" else int(workers)
        
        return {
            'output_dir': self.output_dir_var.get(),
            'parallel': self.parallel_var.get(),
            'max_workers': max_workers,
            'include_images': self.include_images_var.get(),
        }
    
    @property
    def output_dir(self) -> str:
        """Get output directory."""
        return self.output_dir_var.get()
    
    @property
    def parallel_enabled(self) -> bool:
        """Check if parallel processing is enabled."""
        return self.parallel_var.get()
