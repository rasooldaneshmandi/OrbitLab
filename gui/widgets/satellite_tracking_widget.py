from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from orbit.doppler_controller import (
    DopplerControllerState,
)


class SatelliteTrackingWidget(QWidget):
    """
    Ground-station satellite tracking status panel.

    Displays:
        - Satellite
        - Visibility
        - Azimuth
        - Elevation
        - Range
        - Range rate
        - Nominal RX frequency
        - Doppler shift
        - Corrected RX frequency
        - Auto Doppler state
    """

    auto_doppler_changed = pyqtSignal(bool)
    satellite_changed = pyqtSignal(str)

    def __init__(
        self,
        *,
        satellite_keys: tuple[str, ...] = (
            "ISS",
            "NOAA19",
            "TERRA",
            "AQUA",
            "SUOMI_NPP",
        ),
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._satellite_keys = satellite_keys

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        group = QGroupBox(
            "Satellite Tracking"
        )

        form = QFormLayout(
            group
        )

        self._satellite_combo = QComboBox()

        self._satellite_combo.addItems(
            self._satellite_keys
        )

        self._visibility_label = QLabel(
            "---"
        )

        self._azimuth_label = QLabel(
            "---"
        )

        self._elevation_label = QLabel(
            "---"
        )

        self._range_label = QLabel(
            "---"
        )

        self._range_rate_label = QLabel(
            "---"
        )

        self._nominal_frequency_label = QLabel(
            "---"
        )

        self._doppler_label = QLabel(
            "---"
        )

        self._corrected_frequency_label = QLabel(
            "---"
        )

        self._auto_doppler_checkbox = QCheckBox(
            "Enable Auto Doppler"
        )

        self._auto_doppler_checkbox.setChecked(
            True
        )

        form.addRow(
            "Satellite:",
            self._satellite_combo,
        )

        form.addRow(
            "Visibility:",
            self._visibility_label,
        )

        form.addRow(
            "Azimuth:",
            self._azimuth_label,
        )

        form.addRow(
            "Elevation:",
            self._elevation_label,
        )

        form.addRow(
            "Range:",
            self._range_label,
        )

        form.addRow(
            "Range Rate:",
            self._range_rate_label,
        )

        form.addRow(
            "Nominal RX:",
            self._nominal_frequency_label,
        )

        form.addRow(
            "Doppler:",
            self._doppler_label,
        )

        form.addRow(
            "Corrected RX:",
            self._corrected_frequency_label,
        )

        form.addRow(
            "",
            self._auto_doppler_checkbox,
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.addWidget(
            group
        )

        layout.addStretch(1)

    def _connect_signals(self) -> None:
        self._auto_doppler_checkbox.toggled.connect(
            self.auto_doppler_changed.emit
        )

        self._satellite_combo.currentTextChanged.connect(
            self.satellite_changed.emit
        )

    def update_state(
        self,
        state: DopplerControllerState,
    ) -> None:
        if state.visible:
            visibility_text = (
                "VISIBLE"
            )
        else:
            visibility_text = (
                "BELOW HORIZON"
            )

        self._visibility_label.setText(
            visibility_text
        )

        self._azimuth_label.setText(
            f"{state.azimuth_deg:.2f}°"
        )

        self._elevation_label.setText(
            f"{state.elevation_deg:.2f}°"
        )

        self._range_label.setText(
            f"{state.range_km:.1f} km"
        )

        self._range_rate_label.setText(
            f"{state.range_rate_m_s / 1000.0:+.3f} km/s"
        )

        self._nominal_frequency_label.setText(
            f"{state.nominal_frequency_hz / 1_000_000.0:.6f} MHz"
        )

        self._doppler_label.setText(
            f"{state.doppler_shift_hz / 1000.0:+.3f} kHz"
        )

        self._corrected_frequency_label.setText(
            f"{state.corrected_frequency_hz / 1_000_000.0:.6f} MHz"
        )

    def set_auto_doppler_enabled(
        self,
        enabled: bool,
    ) -> None:
        self._auto_doppler_checkbox.blockSignals(
            True
        )

        self._auto_doppler_checkbox.setChecked(
            bool(enabled)
        )

        self._auto_doppler_checkbox.blockSignals(
            False
        )

    def set_satellite(
        self,
        satellite_key: str,
    ) -> None:
        index = self._satellite_combo.findText(
            satellite_key
        )

        if index >= 0:
            self._satellite_combo.blockSignals(
                True
            )

            self._satellite_combo.setCurrentIndex(
                index
            )

            self._satellite_combo.blockSignals(
                False
            )
