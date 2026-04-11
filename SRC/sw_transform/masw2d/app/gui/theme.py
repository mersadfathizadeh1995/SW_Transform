"""Light theme stylesheet for the MASW 2D Profiler."""

from __future__ import annotations

from PyQt6.QtWidgets import QApplication


_LIGHT_QSS = """
QMainWindow {
    background: #f5f5f5;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #ccc;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 14px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}

QTabBar::tab {
    padding: 8px 18px;
    margin-right: 2px;
    border: 1px solid #ccc;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    background: #e8e8e8;
}
QTabBar::tab:selected {
    background: #ffffff;
    border-bottom: 2px solid #1f77b4;
    font-weight: bold;
}
QTabBar::tab:hover:!selected {
    background: #f0f0f0;
}

QTableWidget {
    gridline-color: #ddd;
    selection-background-color: #cce5ff;
    selection-color: #333;
    alternate-background-color: #fafafa;
}
QTableWidget::item {
    padding: 3px 6px;
}
QHeaderView::section {
    background: #e8e8e8;
    padding: 4px 6px;
    border: 1px solid #ccc;
    font-weight: bold;
}

QPushButton {
    padding: 5px 12px;
    border: 1px solid #bbb;
    border-radius: 3px;
    background: #f0f0f0;
}
QPushButton:hover {
    background: #e0e0e0;
}
QPushButton:pressed {
    background: #d0d0d0;
}
QPushButton:disabled {
    color: #999;
    background: #eee;
}

QProgressBar {
    border: 1px solid #ccc;
    border-radius: 4px;
    text-align: center;
    height: 20px;
}
QProgressBar::chunk {
    background: #1f77b4;
    border-radius: 3px;
}

QScrollArea {
    border: none;
}

QSplitter::handle {
    background: #ddd;
    width: 3px;
}
QSplitter::handle:hover {
    background: #1f77b4;
}

QStatusBar {
    background: #e8e8e8;
    border-top: 1px solid #ccc;
}
"""


def apply_theme(app: QApplication, theme: str = "light") -> None:
    """Apply a QSS theme to the application.

    Parameters
    ----------
    app : QApplication
        The application instance.
    theme : str
        Theme name.  Currently only ``"light"`` is supported.
    """
    if theme == "light":
        app.setStyleSheet(_LIGHT_QSS)
