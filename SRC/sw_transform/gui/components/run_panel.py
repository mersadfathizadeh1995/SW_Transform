"""Run panel component with method selector and run/compare buttons.

Copied from simple_app.py:
- lines 232-274 (Run tab UI)
- lines 770-779 (_get_worker_count)
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable
import multiprocessing

from sw_transform.processing.registry import METHODS


class RunPanel(tk.Frame):
    """Panel for selecting transform method and running processing.
    
    Provides method selector, run/compare buttons, and options for
    parallel processing and PowerPoint export.
    
    Usage:
        panel = RunPanel(
            parent,
            on_run_single=lambda selected: print(f"Run {selected}"),
            on_run_compare=lambda selected: print(f"Compare {selected}"),
            icon_loader=load_icon,
        )
        panel.pack(fill="x", pady=6)
        
        method = panel.selected_method  # 'fk', 'ps', etc.
        is_parallel = panel.parallel_enabled
        workers = panel.get_worker_count()
    """
    
    def __init__(self, parent: tk.Widget,
                 on_run_single: Callable[[bool], None] | None = None,
                 on_run_compare: Callable[[bool], None] | None = None,
                 icon_loader: Callable[[str, int], tk.PhotoImage | None] | None = None,
                 **kwargs):
        """Initialize the run panel.
        
        Args:
            parent: Parent widget
            on_run_single: Callback for run single (selected_only: bool)
            on_run_compare: Callback for run compare (selected_only: bool)
            icon_loader: Optional function to load icons
            **kwargs: Additional Frame options
        """
        super().__init__(parent, **kwargs)
        
        self.on_run_single = on_run_single or (lambda x: None)
        self.on_run_compare = on_run_compare or (lambda x: None)
        self.icon_loader = icon_loader
        
        self._create_variables()
        self._build_ui()
    
    def _create_variables(self):
        """Create tk variables for panel state."""
        self.method_key = tk.StringVar(value="fk")
        self.ppt_var = tk.BooleanVar(value=False)
        self.parallel_var = tk.BooleanVar(value=True)
        self.worker_count_var = tk.StringVar(value="auto")
    
    def _build_ui(self):
        """Build the run panel UI.
        
        Copied from simple_app.py lines 232-274.
        """
        # Row 1: Transform method selector
        top = tk.Frame(self)
        top.pack(pady=6)
        
        tk.Label(top, text="Transform:").pack(side="left")
        cmb = ttk.Combobox(
            top,
            values=[f"{k} – {d['label']}" for k, d in METHODS.items()],
            state="readonly",
            width=48
        )
        cmb.current(0)
        cmb.pack(side="left", padx=6)
        cmb.bind("<<ComboboxSelected>>", 
                 lambda ev: self.method_key.set(ev.widget.get().split(" –")[0]))
        
        # Row 2: Run buttons
        row = tk.Frame(self)
        row.pack(pady=4)
        
        btn_run_sel = tk.Button(
            row, text=" Run Selected",
            command=lambda: self.on_run_single(True),
            compound="left", padx=8, pady=4
        )
        btn_run_all = tk.Button(
            row, text=" Run All",
            command=lambda: self.on_run_single(False),
            compound="left", padx=8, pady=4
        )
        
        # Load icons if loader provided
        if self.icon_loader:
            ico_run = self.icon_loader("ic_run.png", 32)
            if ico_run is not None:
                btn_run_sel.config(image=ico_run)
                btn_run_all.config(image=ico_run)
                # Keep reference to prevent garbage collection
                btn_run_sel._icon = ico_run
                btn_run_all._icon = ico_run
        
        btn_run_sel.pack(side="left", padx=4)
        btn_run_all.pack(side="left", padx=4)
        
        # Row 3: Compare buttons
        row2 = tk.Frame(self)
        row2.pack(pady=4)
        
        btn_cmp_sel = tk.Button(
            row2, text=" Compare Selected",
            command=lambda: self.on_run_compare(True),
            compound="left", padx=8, pady=4
        )
        btn_cmp_all = tk.Button(
            row2, text=" Compare All",
            command=lambda: self.on_run_compare(False),
            compound="left", padx=8, pady=4
        )
        
        # Load icons if loader provided
        if self.icon_loader:
            ico_cmp = self.icon_loader("ic_compare.png", 32)
            if ico_cmp is not None:
                btn_cmp_sel.config(image=ico_cmp)
                btn_cmp_all.config(image=ico_cmp)
                btn_cmp_sel._icon = ico_cmp
                btn_cmp_all._icon = ico_cmp
        
        btn_cmp_sel.pack(side="left", padx=4)
        btn_cmp_all.pack(side="left", padx=4)
        
        # Row 4: Options
        opt = tk.Frame(self)
        opt.pack(pady=2)
        
        tk.Checkbutton(opt, text="Create PowerPoint after run", 
                       variable=self.ppt_var).pack(side="left")
        tk.Checkbutton(opt, text="Parallel processing", 
                       variable=self.parallel_var).pack(side="left", padx=(16, 0))
        
        # Worker count control
        tk.Label(opt, text="Workers:").pack(side="left", padx=(8, 2))
        max_cpu = multiprocessing.cpu_count()
        worker_combo = ttk.Combobox(
            opt,
            textvariable=self.worker_count_var,
            values=["auto"] + [str(i) for i in range(1, max_cpu + 1)],
            width=5,
            state="readonly"
        )
        worker_combo.pack(side="left")
        tk.Label(opt, text=f"(max {max_cpu})", fg="gray").pack(side="left", padx=(2, 0))
    
    @property
    def selected_method(self) -> str:
        """Get the currently selected transform method key."""
        return self.method_key.get()
    
    @property
    def parallel_enabled(self) -> bool:
        """Check if parallel processing is enabled."""
        return self.parallel_var.get()
    
    @property
    def ppt_enabled(self) -> bool:
        """Check if PowerPoint creation is enabled."""
        return self.ppt_var.get()
    
    def get_worker_count(self, mode: str = 'single') -> int:
        """Get worker count based on user setting or auto mode.
        
        Copied from simple_app.py lines 770-779.
        
        Args:
            mode: 'single' or 'compare' for different defaults
        
        Returns:
            Number of workers to use.
        """
        from sw_transform.workers.parallel import get_optimal_workers
        val = self.worker_count_var.get()
        if val == "auto":
            return get_optimal_workers(mode=mode)
        try:
            return max(1, int(val))
        except ValueError:
            return get_optimal_workers(mode=mode)
