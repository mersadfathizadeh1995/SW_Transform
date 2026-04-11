"""Advanced settings dialog for transform, preprocessing, and image export.

Opens as a modal dialog from the Process tab.  Returns updated
:class:`ProcessingParams` values when accepted.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from sw_transform.masw2d.app.api.models import ProcessingParams

COLORMAPS = [
    "jet", "viridis", "plasma", "inferno", "magma", "cividis",
    "hot", "cool", "coolwarm", "RdYlBu", "Spectral", "turbo",
]


class AdvancedDialog(QDialog):
    """Modal dialog for advanced processing / export settings.

    Parameters
    ----------
    params : ProcessingParams
        Current parameter values to populate the form.
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(
        self,
        params: ProcessingParams,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Advanced Settings")
        self.setMinimumSize(420, 520)
        self._params = params
        self._build_ui()
        self._populate(params)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)

        # Transform settings
        grp_tf = QGroupBox("Transform Settings")
        tf_form = QFormLayout(grp_tf)

        self._spin_grid = QSpinBox()
        self._spin_grid.setRange(100, 16000)
        self._spin_grid.setSingleStep(500)
        tf_form.addRow("Velocity Grid Size:", self._spin_grid)

        self._combo_vspace = QComboBox()
        self._combo_vspace.addItems(["log", "linear"])
        tf_form.addRow("Velocity Spacing:", self._combo_vspace)

        self._chk_vibrosis = QCheckBox("Vibrosis mode (FDBF weighting)")
        tf_form.addRow(self._chk_vibrosis)

        self._chk_cylindrical = QCheckBox("Cylindrical steering (near-field)")
        tf_form.addRow(self._chk_cylindrical)

        layout.addWidget(grp_tf)

        # Peak picking
        grp_pick = QGroupBox("Peak Picking")
        pick_form = QFormLayout(grp_pick)

        self._spin_tol = QDoubleSpinBox()
        self._spin_tol.setRange(0.001, 1.0)
        self._spin_tol.setDecimals(3)
        self._spin_tol.setSingleStep(0.01)
        pick_form.addRow("Tolerance:", self._spin_tol)

        self._spin_power = QDoubleSpinBox()
        self._spin_power.setRange(0.0, 1.0)
        self._spin_power.setDecimals(2)
        self._spin_power.setSingleStep(0.05)
        pick_form.addRow("Power Threshold:", self._spin_power)

        layout.addWidget(grp_pick)

        # Preprocessing
        grp_pre = QGroupBox("Preprocessing")
        pre_form = QFormLayout(grp_pre)

        self._spin_start_t = QDoubleSpinBox()
        self._spin_start_t.setRange(0.0, 10.0)
        self._spin_start_t.setDecimals(3)
        self._spin_start_t.setSuffix(" s")
        pre_form.addRow("Start Time:", self._spin_start_t)

        self._spin_end_t = QDoubleSpinBox()
        self._spin_end_t.setRange(0.01, 30.0)
        self._spin_end_t.setDecimals(3)
        self._spin_end_t.setSuffix(" s")
        pre_form.addRow("End Time:", self._spin_end_t)

        self._chk_downsample = QCheckBox("Downsample")
        pre_form.addRow(self._chk_downsample)

        self._spin_down_factor = QSpinBox()
        self._spin_down_factor.setRange(1, 64)
        pre_form.addRow("Downsample Factor:", self._spin_down_factor)

        self._spin_numf = QSpinBox()
        self._spin_numf.setRange(256, 16384)
        self._spin_numf.setSingleStep(1000)
        pre_form.addRow("FFT Size (numf):", self._spin_numf)

        layout.addWidget(grp_pre)

        # Image export
        grp_img = QGroupBox("Image Export")
        img_form = QFormLayout(grp_img)

        self._combo_cmap = QComboBox()
        self._combo_cmap.addItems(COLORMAPS)
        img_form.addRow("Colormap:", self._combo_cmap)

        self._spin_dpi = QSpinBox()
        self._spin_dpi.setRange(50, 600)
        self._spin_dpi.setSingleStep(50)
        img_form.addRow("DPI:", self._spin_dpi)

        self._combo_style = QComboBox()
        self._combo_style.addItems(["contourf", "pcolormesh"])
        img_form.addRow("Plot Style:", self._combo_style)

        self._spin_contours = QSpinBox()
        self._spin_contours.setRange(5, 200)
        img_form.addRow("Contour Levels:", self._spin_contours)

        layout.addWidget(grp_img)

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        # OK / Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.addButton("Reset Defaults", QDialogButtonBox.ButtonRole.ResetRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.clicked.connect(self._on_button_clicked)
        self._buttons = buttons
        outer.addWidget(buttons)

    # ------------------------------------------------------------------
    # Populate / Read
    # ------------------------------------------------------------------

    def _populate(self, p: ProcessingParams) -> None:
        """Fill form from a ProcessingParams instance."""
        self._spin_grid.setValue(p.grid_n)
        self._combo_vspace.setCurrentText(p.vspace)
        self._chk_vibrosis.setChecked(p.source_type == "vibrosis")
        self._chk_cylindrical.setChecked(p.cylindrical)
        self._spin_tol.setValue(p.tol)
        self._spin_power.setValue(p.power_threshold)
        self._spin_start_t.setValue(p.start_time)
        self._spin_end_t.setValue(p.end_time)
        self._chk_downsample.setChecked(p.downsample)
        self._spin_down_factor.setValue(p.down_factor)
        self._spin_numf.setValue(p.numf)
        self._combo_cmap.setCurrentText("jet")
        self._spin_dpi.setValue(150)
        self._combo_style.setCurrentText("contourf")
        self._spin_contours.setValue(30)

    def get_params(self) -> ProcessingParams:
        """Read current form values into a ProcessingParams."""
        return ProcessingParams(
            method=self._params.method,
            freq_min=self._params.freq_min,
            freq_max=self._params.freq_max,
            vel_min=self._params.vel_min,
            vel_max=self._params.vel_max,
            grid_n=self._spin_grid.value(),
            tol=self._spin_tol.value(),
            vspace=self._combo_vspace.currentText(),
            source_type="vibrosis" if self._chk_vibrosis.isChecked() else "hammer",
            cylindrical=self._chk_cylindrical.isChecked(),
            start_time=self._spin_start_t.value(),
            end_time=self._spin_end_t.value(),
            downsample=self._chk_downsample.isChecked(),
            down_factor=self._spin_down_factor.value(),
            numf=self._spin_numf.value(),
            power_threshold=self._spin_power.value(),
        )

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_button_clicked(self, button) -> None:
        role = self._buttons.buttonRole(button)
        if role == QDialogButtonBox.ButtonRole.ResetRole:
            self._populate(ProcessingParams())
