"""Collapsible section widget — click header to expand/collapse content."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class CollapsibleSection(QWidget):
    """A section with a clickable header that toggles content visibility.

    Parameters
    ----------
    title : str
        Header text.
    parent : QWidget, optional
        Parent widget.
    collapsed : bool
        Initial state.
    """

    toggled = pyqtSignal(bool)

    def __init__(
        self,
        title: str = "",
        parent: QWidget | None = None,
        collapsed: bool = False,
    ):
        super().__init__(parent)
        self._collapsed = collapsed

        # Header
        self._toggle_btn = QToolButton()
        self._toggle_btn.setStyleSheet("QToolButton { border: none; }")
        self._toggle_btn.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self._toggle_btn.setArrowType(
            Qt.ArrowType.RightArrow if collapsed else Qt.ArrowType.DownArrow
        )
        self._toggle_btn.setText(title)
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setChecked(not collapsed)
        self._toggle_btn.clicked.connect(self._on_toggle)
        self._toggle_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        header = QFrame()
        header.setStyleSheet(
            "QFrame { background: #e8e8e8; border-radius: 3px; }"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(4, 2, 4, 2)
        header_layout.addWidget(self._toggle_btn)

        # Content area
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(4, 4, 4, 4)
        self._content.setVisible(not collapsed)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(header)
        layout.addWidget(self._content)

    @property
    def content(self) -> QWidget:
        """The container widget — add child widgets to its layout."""
        return self._content

    @property
    def content_layout(self) -> QVBoxLayout:
        """Layout of the content area."""
        return self._content_layout

    def is_collapsed(self) -> bool:
        """Return True if the section is collapsed."""
        return self._collapsed

    def set_collapsed(self, collapsed: bool) -> None:
        """Expand or collapse the section."""
        self._collapsed = collapsed
        self._content.setVisible(not collapsed)
        self._toggle_btn.setArrowType(
            Qt.ArrowType.RightArrow if collapsed else Qt.ArrowType.DownArrow
        )
        self._toggle_btn.setChecked(not collapsed)

    def set_title(self, title: str) -> None:
        """Update the header text."""
        self._toggle_btn.setText(title)

    def _on_toggle(self) -> None:
        self._collapsed = not self._collapsed
        self._content.setVisible(not self._collapsed)
        self._toggle_btn.setArrowType(
            Qt.ArrowType.RightArrow if self._collapsed else Qt.ArrowType.DownArrow
        )
        self.toggled.emit(not self._collapsed)
