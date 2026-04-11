"""Shot input panel: pattern-based positions, file assignment, and shot table."""
from __future__ import annotations

import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Any, Callable, Dict, List, Optional, Tuple


def _natural_sort_key(path: str) -> Tuple:
    """Sort key for human-friendly ordering (1.dat, 2.dat, ..., 10.dat)."""
    base = os.path.basename(path)
    parts = re.split(r"(\d+)", base.lower())
    key: List[Any] = []
    for p in parts:
        if p.isdigit():
            key.append(int(p))
        else:
            key.append(p)
    return tuple(key)


class ShotInputPanel(ttk.LabelFrame):
    """Define shot positions from a pattern, assign files, and edit in a table."""

    def __init__(
        self,
        parent: tk.Widget,
        main_app: Optional[Any] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        array_length_getter: Optional[Callable[[], float]] = None,
        on_change: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(parent, text="Shot Input", padding=6, **kwargs)
        self.main_app = main_app
        self.log = log_callback or print
        self.get_array_length = array_length_getter or (lambda: 46.0)
        self.on_change = on_change

        self._rows: List[Dict[str, Any]] = []
        self._build_ui()

    def _notify(self) -> None:
        if self.on_change:
            self.on_change()

    def _build_ui(self) -> None:
        pat = ttk.LabelFrame(self, text="Shot Pattern Generator", padding=6)
        pat.pack(fill="x", pady=2)
        r1 = ttk.Frame(pat)
        r1.pack(fill="x", pady=2)
        ttk.Label(r1, text="Start Position (m):").pack(side="left")
        self._start_var = tk.StringVar(value="-1.0")
        ttk.Entry(r1, textvariable=self._start_var, width=10).pack(side="left", padx=4)
        r2 = ttk.Frame(pat)
        r2.pack(fill="x", pady=2)
        ttk.Label(r2, text="Number of Shots:").pack(side="left")
        self._nshots_var = tk.StringVar(value="1")
        ttk.Entry(r2, textvariable=self._nshots_var, width=10).pack(side="left", padx=4)
        r3 = ttk.Frame(pat)
        r3.pack(fill="x", pady=2)
        ttk.Label(r3, text="Shot Spacing (m):").pack(side="left")
        self._spacing_var = tk.StringVar(value="6.0")
        ttk.Entry(r3, textvariable=self._spacing_var, width=10).pack(side="left", padx=4)
        ttk.Button(pat, text="Generate Positions", command=self._generate_positions).pack(
            anchor="w", pady=4
        )

        fa = ttk.LabelFrame(self, text="File Assignment", padding=6)
        fa.pack(fill="x", pady=4)
        br = ttk.Frame(fa)
        br.pack(fill="x", pady=2)
        ttk.Button(br, text="Browse Files...", command=self._browse_files).pack(side="left")
        ttk.Button(br, text="Import from Project", command=self._import_from_project).pack(
            side="left", padx=4
        )
        br2 = ttk.Frame(fa)
        br2.pack(fill="x", pady=2)
        ttk.Button(br2, text="Auto-Match by Index", command=self._auto_match).pack(side="left")
        ttk.Button(br2, text="Clear All", command=self._clear_all).pack(side="left", padx=4)

        cols = ("No", "File", "Source Position (m)", "Status")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", height=8)
        self._tree.heading("No", text="#")
        self._tree.heading("File", text="File")
        self._tree.heading("Source Position (m)", text="Source Position (m)")
        self._tree.heading("Status", text="Status")
        self._tree.column("No", width=36, stretch=False)
        self._tree.column("File", width=160)
        self._tree.column("Source Position (m)", width=120)
        self._tree.column("Status", width=80, stretch=False)
        self._tree.pack(fill="both", expand=True, pady=4)
        self._tree.bind("<Double-1>", self._on_double_click)
        self._tree.bind("<Button-3>", self._on_context_menu)

        self._ctx = tk.Menu(self, tearoff=0)
        self._ctx.add_command(label="Add Shot", command=self._add_shot_dialog)
        self._ctx.add_command(label="Remove Selected", command=self._remove_selected)
        self._ctx.add_command(label="Edit Position...", command=self._edit_position_selected)

        ttk.Button(self, text="+ Add Shot", command=self._add_shot_dialog).pack(anchor="w", pady=2)

    def _row_status(self, row: Dict[str, Any]) -> str:
        fp = row.get("file") or ""
        if fp and os.path.isfile(fp):
            return "OK"
        if fp:
            return "Missing file"
        return "No file"

    def _refresh_tree(self) -> None:
        for iid in self._tree.get_children():
            self._tree.delete(iid)
        for idx, row in enumerate(self._rows, start=1):
            base = ""
            fp = row.get("file") or ""
            if fp:
                base = os.path.basename(fp)
            pos = row.get("source_position", 0.0)
            self._tree.insert(
                "",
                "end",
                iid=f"r{idx}",
                values=(str(idx), base, f"{pos:.4f}", self._row_status(row)),
            )

    def _generate_positions(self) -> None:
        try:
            start = float(self._start_var.get())
            n = int(self._nshots_var.get())
            step = float(self._spacing_var.get())
        except ValueError:
            messagebox.showerror("Pattern", "Enter valid numbers for start, count, and spacing.")
            return
        if n < 1:
            messagebox.showerror("Pattern", "Number of shots must be at least 1.")
            return
        self._rows = [{"file": "", "source_position": start + i * step} for i in range(n)]
        self._refresh_tree()
        self.log(f"Generated {n} shot positions from pattern.")
        self._notify()

    def _browse_files(self) -> None:
        files = filedialog.askopenfilenames(
            title="Select Shot Files",
            filetypes=[
                ("All supported", "*.dat *.sg2 *.mat"),
                ("SEG-2 files", "*.dat *.sg2"),
                ("Vibrosis .mat", "*.mat"),
                ("All files", "*.*"),
            ],
        )
        if not files:
            return
        sorted_paths = sorted(files, key=_natural_sort_key)
        if not self._rows:
            try:
                start = float(self._start_var.get())
                step = float(self._spacing_var.get())
            except ValueError:
                start, step = 0.0, 1.0
            self._rows = []
            for i, p in enumerate(sorted_paths):
                ext = os.path.splitext(p)[1].lower()
                self._rows.append(
                    {
                        "file": p,
                        "source_position": start + i * step,
                        "file_type": "mat" if ext == ".mat" else "seg2",
                    }
                )
        else:
            for i, p in enumerate(sorted_paths):
                ext = os.path.splitext(p)[1].lower()
                rec = {"file": p, "file_type": "mat" if ext == ".mat" else "seg2"}
                if i < len(self._rows):
                    self._rows[i].update(rec)
                else:
                    sp = self._rows[-1]["source_position"] if self._rows else 0.0
                    rec["source_position"] = float(sp)
                    self._rows.append(rec)
        self._refresh_tree()
        self._notify()

    def _import_from_project(self) -> None:
        if not self.main_app or not hasattr(self.main_app, "file_list"):
            messagebox.showwarning("Import", "No project files available.")
            return
        if not self.main_app.file_list:
            messagebox.showinfo("Import", "No files loaded in project.")
            return
        array_length = self.get_array_length()
        paths = sorted(self.main_app.file_list, key=_natural_sort_key)
        if not self._rows:
            self._rows = []
            for filepath in paths:
                base = os.path.splitext(os.path.basename(filepath))[0]
                ext = os.path.splitext(filepath)[1].lower()
                file_type = "mat" if ext == ".mat" else "seg2"
                offset_str = self.main_app.offsets.get(base, "+0")
                try:
                    source_pos = float(offset_str)
                except ValueError:
                    source_pos = array_length
                self._rows.append(
                    {
                        "file": filepath,
                        "source_position": float(source_pos),
                        "file_type": file_type,
                    }
                )
        else:
            existing = {r.get("file") for r in self._rows}
            for filepath in paths:
                if filepath in existing:
                    continue
                base = os.path.splitext(os.path.basename(filepath))[0]
                ext = os.path.splitext(filepath)[1].lower()
                file_type = "mat" if ext == ".mat" else "seg2"
                offset_str = self.main_app.offsets.get(base, "+0")
                try:
                    source_pos = float(offset_str)
                except ValueError:
                    source_pos = array_length
                self._rows.append(
                    {
                        "file": filepath,
                        "source_position": float(source_pos),
                        "file_type": file_type,
                    }
                )
        self._refresh_tree()
        self.log(f"Imported {len(paths)} file(s) from project.")
        self._notify()

    def _auto_match(self) -> None:
        if not self._rows:
            messagebox.showinfo("Auto-Match", "Generate positions or add shots first.")
            return
        seen: set[str] = set()
        paths: List[str] = []
        for r in self._rows:
            f = r.get("file")
            if f and f not in seen:
                seen.add(f)
                paths.append(f)
        paths = sorted(paths, key=_natural_sort_key)
        if not paths:
            messagebox.showinfo("Auto-Match", "No files in the table. Use Browse or Import.")
            return
        for i in range(len(self._rows)):
            self._rows[i]["file"] = paths[i] if i < len(paths) else ""
        self._refresh_tree()
        self._notify()

    def _clear_all(self) -> None:
        self._rows.clear()
        self._refresh_tree()
        self._notify()

    def _on_double_click(self, ev: tk.Event) -> None:
        item = self._tree.identify_row(ev.y)
        col = self._tree.identify_column(ev.x)
        if not item:
            return
        idx = int(item[1:]) - 1
        if idx < 0 or idx >= len(self._rows):
            return
        col_idx = int(col.replace("#", ""))
        # columns: 1=#, 2=File, 3=Source, 4=Status
        if col_idx == 3:
            self._edit_position_at(idx)
        elif col_idx == 2:
            path = filedialog.askopenfilename(
                title="Select Shot File",
                filetypes=[
                    ("All supported", "*.dat *.sg2 *.mat"),
                    ("All files", "*.*"),
                ],
            )
            if path:
                self._rows[idx]["file"] = path
                ext = os.path.splitext(path)[1].lower()
                self._rows[idx]["file_type"] = "mat" if ext == ".mat" else "seg2"
                self._refresh_tree()
                self._notify()

    def _edit_position_at(self, idx: int) -> None:
        row = self._rows[idx]
        dlg = tk.Toplevel(self)
        dlg.title("Source Position")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        ttk.Label(dlg, text="Source position (m):").pack(padx=8, pady=4)
        v = tk.StringVar(value=str(row["source_position"]))
        e = ttk.Entry(dlg, textvariable=v, width=16)
        e.pack(padx=8, pady=4)

        def ok() -> None:
            try:
                row["source_position"] = float(v.get())
            except ValueError:
                messagebox.showerror("Invalid", "Enter a valid number.", parent=dlg)
                return
            dlg.destroy()
            self._refresh_tree()
            self._notify()

        ttk.Button(dlg, text="OK", command=ok).pack(pady=4)
        e.bind("<Return>", lambda _e: ok())
        e.focus_set()

    def _edit_position_selected(self) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        idx = int(sel[0][1:]) - 1
        if 0 <= idx < len(self._rows):
            self._edit_position_at(idx)

    def _on_context_menu(self, ev: tk.Event) -> None:
        item = self._tree.identify_row(ev.y)
        if item:
            self._tree.selection_set(item)
        try:
            self._ctx.tk_popup(ev.x_root, ev.y_root)
        finally:
            self._ctx.grab_release()

    def _remove_selected(self) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        idx = int(sel[0][1:]) - 1
        if 0 <= idx < len(self._rows):
            del self._rows[idx]
            self._refresh_tree()
            self._notify()

    def _add_shot_dialog(self) -> None:
        dlg = tk.Toplevel(self)
        dlg.title("Add Shot")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        ttk.Label(dlg, text="Source position (m):").pack(padx=8, pady=4)
        pv = tk.StringVar(value="0.0")
        ttk.Entry(dlg, textvariable=pv, width=14).pack(padx=8, pady=2)
        fv = tk.StringVar(value="")

        def browse() -> None:
            p = filedialog.askopenfilename(
                filetypes=[("All supported", "*.dat *.sg2 *.mat"), ("All files", "*.*")]
            )
            if p:
                fv.set(p)

        ttk.Button(dlg, text="Browse file (optional)...", command=browse).pack(pady=2)

        def ok() -> None:
            try:
                pos = float(pv.get())
            except ValueError:
                messagebox.showerror("Invalid", "Enter a valid position.", parent=dlg)
                return
            fp = fv.get().strip()
            rec: Dict[str, Any] = {"file": fp, "source_position": pos}
            if fp:
                ext = os.path.splitext(fp)[1].lower()
                rec["file_type"] = "mat" if ext == ".mat" else "seg2"
            self._rows.append(rec)
            dlg.destroy()
            self._refresh_tree()
            self._notify()

        ttk.Button(dlg, text="Add", command=ok).pack(pady=6)

    def get_shots(self) -> List[Dict[str, Any]]:
        """Return [{file, source_position}, ...] for all rows."""
        out: List[Dict[str, Any]] = []
        for row in self._rows:
            fp = row.get("file") or ""
            out.append({"file": fp, "source_position": float(row["source_position"])})
        return out

    def get_shot_positions(self) -> List[float]:
        """Positions only (for preview)."""
        return [float(r["source_position"]) for r in self._rows]

    @property
    def has_files(self) -> bool:
        return any((r.get("file") or "") and os.path.isfile(str(r.get("file"))) for r in self._rows)

    @property
    def files(self) -> List[str]:
        """Paths that exist on disk."""
        paths: List[str] = []
        for r in self._rows:
            fp = r.get("file") or ""
            if fp and os.path.isfile(fp):
                paths.append(fp)
        return paths

    def has_mat_files(self) -> bool:
        return any(
            str(r.get("file", "")).lower().endswith(".mat") and os.path.isfile(str(r.get("file")))
            for r in self._rows
        )

    def sync_from_main_app(self) -> None:
        """Append new project files like FileManagerPanel."""
        if not self.main_app or not hasattr(self.main_app, "file_list"):
            return
        if not self.main_app.file_list:
            return
        array_length = self.get_array_length()
        existing = {r.get("file") for r in self._rows}
        count = 0
        for filepath in self.main_app.file_list:
            if filepath in existing:
                continue
            base = os.path.splitext(os.path.basename(filepath))[0]
            ext = os.path.splitext(filepath)[1].lower()
            file_type = "mat" if ext == ".mat" else "seg2"
            offset_str = self.main_app.offsets.get(base, "+0")
            try:
                source_pos = float(offset_str)
            except ValueError:
                source_pos = array_length
            self._rows.append(
                {
                    "file": filepath,
                    "source_position": float(source_pos),
                    "file_type": file_type,
                }
            )
            count += 1
        if count > 0:
            self._refresh_tree()
            self.log(f"Auto-synced {count} file(s) from main app.")
            self._notify()
