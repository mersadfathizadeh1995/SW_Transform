"""Entry point for the MASW 2D Profiler GUI."""

import sys

import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication

from sw_transform.masw2d.app.gui.main_window import MainWindow
from sw_transform.masw2d.app.gui.theme import apply_theme


def main():
    """Launch the MASW 2D Profiler application."""
    pg.setConfigOptions(antialias=True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    apply_theme(app, "light")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
