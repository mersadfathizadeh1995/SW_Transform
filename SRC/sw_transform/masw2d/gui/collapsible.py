"""Collapsible LabelFrame widget for Tkinter.

Matches the visual style of the input tab's ArrayConfigPanel / SourceConfigPanel
headers (tk.Label toggle, relief="raised", cursor="hand2").
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class CollapsibleLabelFrame(tk.Frame):
    """A LabelFrame-like container with a toggle button to collapse/expand.

    The header row uses the same style as the input tab's collapsible panels:
    raised header bar, ▶/▼ label toggle with hand cursor, bold title.

    Usage::

        wrapper = CollapsibleLabelFrame(parent, title="Array Setup")
        panel = ArraySetupPanel(wrapper.content)
        panel.pack(fill="x")
        wrapper.pack(fill="x", padx=4, pady=2)
    """

    def __init__(
        self,
        parent: tk.Widget,
        title: str = "",
        collapsed: bool = False,
        summary_text: str = "",
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self._title = title
        self._collapsed = collapsed

        # Header row — matches input tab style: relief="raised", bd=1
        self._header = tk.Frame(self, relief="raised", bd=1)
        self._header.pack(fill="x")

        self._toggle_lbl = tk.Label(
            self._header,
            text="▶" if collapsed else "▼",
            width=2,
            cursor="hand2",
        )
        self._toggle_lbl.pack(side="left", padx=2)

        self._title_label = tk.Label(
            self._header,
            text=title,
            font=("TkDefaultFont", 9, "bold"),
            cursor="hand2",
        )
        self._title_label.pack(side="left", padx=4)

        self._summary_label = tk.Label(
            self._header, text=summary_text, fg="gray"
        )
        self._summary_label.pack(side="left", padx=8)

        # Bind click on all header widgets
        for widget in (self._header, self._toggle_lbl, self._title_label, self._summary_label):
            widget.bind("<Button-1>", lambda e: self.toggle())

        # Content frame — place child widgets here
        self.content = tk.Frame(self)
        if not collapsed:
            self.content.pack(fill="x", expand=True)

    def toggle(self):
        """Toggle between collapsed and expanded states."""
        if self._collapsed:
            self.expand()
        else:
            self.collapse()

    def collapse(self):
        """Collapse the panel (hide content)."""
        if not self._collapsed:
            self.content.pack_forget()
            self._toggle_lbl.configure(text="▶")
            self._collapsed = True

    def expand(self):
        """Expand the panel (show content)."""
        if self._collapsed:
            self.content.pack(fill="x", expand=True)
            self._toggle_lbl.configure(text="▼")
            self._collapsed = False

    def set_summary(self, text: str):
        """Update the summary label text shown in the header."""
        self._summary_label.configure(text=text)

    @property
    def is_collapsed(self) -> bool:
        """Whether the panel is currently collapsed."""
        return self._collapsed
