from __future__ import annotations

import numpy as np
import pyqtgraph as pg

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)


class SpectrumWidget(QWidget):
    """
    Real-time SDR spectrum display.

    The input frequency axis is expected to be in Hz.
    Internally, RF frequencies are displayed in MHz.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._latest_peak_frequency_hz: float | None = None
        self._latest_peak_power_db: float | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        self._title_label = QLabel(
            "Real-Time SDR Spectrum"
        )

        self._title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self._status_label = QLabel(
            "Waiting for spectrum data..."
        )

        self._status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self._plot_widget = pg.PlotWidget()

        self._plot_widget.setLabel(
            "bottom",
            "RF Frequency",
            units="MHz",
        )

        self._plot_widget.setLabel(
            "left",
            "Power",
            units="dB",
        )

        self._plot_widget.showGrid(
            x=True,
            y=True,
            alpha=0.25,
        )

        self._plot_widget.setMouseEnabled(
            x=True,
            y=True,
        )

        self._plot_widget.enableAutoRange(
            axis="y",
            enable=True,
        )

        self._spectrum_curve = (
            self._plot_widget.plot(
                [],
                [],
                pen=pg.mkPen(width=1.5),
                name="Spectrum",
            )
        )

        self._peak_marker = pg.ScatterPlotItem(
            size=10,
            symbol="t",
        )

        self._plot_widget.addItem(
            self._peak_marker
        )

        self._peak_text = pg.TextItem(
            text="",
            anchor=(0.5, 1.3),
        )

        self._plot_widget.addItem(
            self._peak_text
        )

        layout = QVBoxLayout(self)

        layout.addWidget(
            self._title_label
        )

        layout.addWidget(
            self._plot_widget,
            stretch=1,
        )

        layout.addWidget(
            self._status_label
        )

    def update_spectrum(
        self,
        frequencies_hz: np.ndarray,
        power_db: np.ndarray,
        *,
        center_frequency_hz: float = 0.0,
        frequencies_are_baseband: bool = True,
    ) -> None:
        """
        Update the displayed spectrum.

        Args:
            frequencies_hz:
                Frequency axis in Hz.

            power_db:
                Spectrum power in dB.

            center_frequency_hz:
                SDR center frequency in Hz.

            frequencies_are_baseband:
                When True, center_frequency_hz is added to
                frequencies_hz before plotting.
        """
        frequencies_hz = np.asarray(
            frequencies_hz,
            dtype=np.float64,
        )

        power_db = np.asarray(
            power_db,
            dtype=np.float64,
        )

        if frequencies_hz.ndim != 1:
            raise ValueError(
                "frequencies_hz must be one-dimensional."
            )

        if power_db.ndim != 1:
            raise ValueError(
                "power_db must be one-dimensional."
            )

        if frequencies_hz.size == 0:
            self.clear_spectrum()
            return

        if frequencies_hz.size != power_db.size:
            raise ValueError(
                "Frequency and power arrays must have "
                "the same size."
            )

        if frequencies_are_baseband:
            rf_frequencies_hz = (
                frequencies_hz
                + float(center_frequency_hz)
            )
        else:
            rf_frequencies_hz = frequencies_hz

        frequencies_mhz = (
            rf_frequencies_hz / 1_000_000.0
        )

        self._spectrum_curve.setData(
            frequencies_mhz,
            power_db,
        )

        peak_index = int(
            np.argmax(power_db)
        )

        peak_frequency_hz = float(
            rf_frequencies_hz[peak_index]
        )

        peak_frequency_mhz = (
            peak_frequency_hz / 1_000_000.0
        )

        peak_power_db = float(
            power_db[peak_index]
        )

        self._latest_peak_frequency_hz = (
            peak_frequency_hz
        )

        self._latest_peak_power_db = (
            peak_power_db
        )

        self._peak_marker.setData(
            [peak_frequency_mhz],
            [peak_power_db],
        )

        self._peak_text.setText(
            f"{peak_frequency_mhz:.6f} MHz\n"
            f"{peak_power_db:.2f} dB"
        )

        self._peak_text.setPos(
            peak_frequency_mhz,
            peak_power_db,
        )

        self._status_label.setText(
            f"Peak: {peak_frequency_mhz:.6f} MHz"
            f"   |   Power: {peak_power_db:.2f} dB"
            f"   |   FFT bins: {frequencies_hz.size}"
        )

    def clear_spectrum(self) -> None:
        self._spectrum_curve.setData(
            [],
            [],
        )

        self._peak_marker.setData(
            [],
            [],
        )

        self._peak_text.setText("")

        self._status_label.setText(
            "Waiting for spectrum data..."
        )

        self._latest_peak_frequency_hz = None
        self._latest_peak_power_db = None

    @property
    def latest_peak_frequency_hz(
        self,
    ) -> float | None:
        return self._latest_peak_frequency_hz

    @property
    def latest_peak_power_db(
        self,
    ) -> float | None:
        return self._latest_peak_power_db