from __future__ import annotations

import numpy as np
import pyqtgraph as pg

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from sdr.spectrum_processor import (
    SpectrumProcessingResult,
    SpectrumProcessor,
)


class SpectrumWidget(QWidget):
    """
    Real-time SDR spectrum display.

    Features:
        - Current spectrum
        - Moving-average spectrum
        - Max-hold spectrum
        - Peak marker
        - Runtime visibility controls
        - Backward-compatible update_spectrum() API
    """

    def __init__(
        self,
        *,
        averaging_count: int = 1,
        max_hold_enabled: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._processor = SpectrumProcessor(
            averaging_count=averaging_count,
            max_hold_enabled=max_hold_enabled,
        )

        self._last_result: SpectrumProcessingResult | None = None
        self._last_rf_frequencies_hz: np.ndarray | None = None

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        self._title_label = QLabel(
            "Real-Time SDR Spectrum"
        )
        self._title_label.setAlignment(
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
            axis="x",
            enable=True,
        )

        self._plot_widget.enableAutoRange(
            axis="y",
            enable=True,
        )

        self._plot_widget.addLegend()

        self._current_curve = self._plot_widget.plot(
            [],
            [],
            pen=pg.mkPen(
                width=1.5,
            ),
            name="Current",
        )

        self._average_curve = self._plot_widget.plot(
            [],
            [],
            pen=pg.mkPen(
                width=2.0,
                style=Qt.PenStyle.DashLine,
            ),
            name="Average",
        )

        self._max_hold_curve = self._plot_widget.plot(
            [],
            [],
            pen=pg.mkPen(
                width=1.5,
                style=Qt.PenStyle.DotLine,
            ),
            name="Max Hold",
        )

        self._peak_marker = pg.ScatterPlotItem(
            size=10,
            symbol="o",
        )

        self._plot_widget.addItem(
            self._peak_marker
        )

        self._peak_text = pg.TextItem(
            anchor=(0.5, 1.2),
        )

        self._plot_widget.addItem(
            self._peak_text
        )

        self._current_checkbox = QCheckBox(
            "Current"
        )
        self._current_checkbox.setChecked(True)

        self._average_checkbox = QCheckBox(
            "Average"
        )
        self._average_checkbox.setChecked(
            self._processor.averaging_count > 1
        )

        self._max_hold_checkbox = QCheckBox(
            "Max Hold"
        )
        self._max_hold_checkbox.setChecked(
            self._processor.max_hold_enabled
        )

        self._reset_average_button = QPushButton(
            "Reset Average"
        )

        self._reset_max_hold_button = QPushButton(
            "Reset Max Hold"
        )

        controls_layout = QHBoxLayout()

        controls_layout.addWidget(
            self._current_checkbox
        )

        controls_layout.addWidget(
            self._average_checkbox
        )

        controls_layout.addWidget(
            self._max_hold_checkbox
        )

        controls_layout.addStretch(1)

        controls_layout.addWidget(
            self._reset_average_button
        )

        controls_layout.addWidget(
            self._reset_max_hold_button
        )

        self._status_label = QLabel(
            "Waiting for spectrum data..."
        )

        self._status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout = QVBoxLayout(self)

        layout.addWidget(
            self._title_label
        )

        layout.addLayout(
            controls_layout
        )

        layout.addWidget(
            self._plot_widget,
            stretch=1,
        )

        layout.addWidget(
            self._status_label
        )

    def _connect_signals(self) -> None:
        self._current_checkbox.toggled.connect(
            self._on_visibility_changed
        )

        self._average_checkbox.toggled.connect(
            self._on_visibility_changed
        )

        self._max_hold_checkbox.toggled.connect(
            self._on_max_hold_toggled
        )

        self._reset_average_button.clicked.connect(
            self.reset_average
        )

        self._reset_max_hold_button.clicked.connect(
            self.reset_max_hold
        )

    def update_spectrum(
        self,
        frequencies_hz: np.ndarray,
        power_db: np.ndarray,
        *,
        center_frequency_hz: float = 0.0,
        frequencies_are_baseband: bool = True,
    ) -> None:
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
            return

        if frequencies_hz.size != power_db.size:
            raise ValueError(
                "Frequency and power arrays must have "
                "the same size."
            )

        if not np.all(
            np.isfinite(frequencies_hz)
        ):
            raise ValueError(
                "frequencies_hz contains invalid values."
            )

        if not np.all(
            np.isfinite(power_db)
        ):
            raise ValueError(
                "power_db contains invalid values."
            )

        if frequencies_are_baseband:
            rf_frequencies_hz = (
                frequencies_hz
                + float(center_frequency_hz)
            )
        else:
            rf_frequencies_hz = (
                frequencies_hz.copy()
            )

        result = self._processor.process(
            rf_frequencies_hz,
            power_db,
        )

        self._last_result = result
        self._last_rf_frequencies_hz = (
            rf_frequencies_hz.copy()
        )

        frequencies_mhz = (
            rf_frequencies_hz
            / 1_000_000.0
        )

        self._current_curve.setData(
            frequencies_mhz,
            result.current_power_db,
        )

        self._average_curve.setData(
            frequencies_mhz,
            result.average_power_db,
        )

        self._max_hold_curve.setData(
            frequencies_mhz,
            result.max_hold_power_db,
        )

        peak_frequency_mhz = (
            result.peak_frequency_hz
            / 1_000_000.0
        )

        self._peak_marker.setData(
            [
                {
                    "pos": (
                        peak_frequency_mhz,
                        result.peak_power_db,
                    )
                }
            ]
        )

        self._peak_text.setPos(
            peak_frequency_mhz,
            result.peak_power_db,
        )

        self._peak_text.setText(
            f"{peak_frequency_mhz:.6f} MHz\n"
            f"{result.peak_power_db:.2f} dB"
        )

        self._status_label.setText(
            f"Peak: {peak_frequency_mhz:.6f} MHz"
            f"   |   Power: {result.peak_power_db:.2f} dB"
            f"   |   Average: "
            f"{self._processor.average_frame_count}/"
            f"{self._processor.averaging_count}"
            f"   |   FFT bins: {power_db.size}"
        )

        self._apply_visibility()

    def _on_visibility_changed(
        self,
        checked: bool,
    ) -> None:
        del checked
        self._apply_visibility()

    def _on_max_hold_toggled(
        self,
        enabled: bool,
    ) -> None:
        self._processor.set_max_hold_enabled(
            enabled
        )

        self._apply_visibility()

    def _apply_visibility(self) -> None:
        self._current_curve.setVisible(
            self._current_checkbox.isChecked()
        )

        self._average_curve.setVisible(
            self._average_checkbox.isChecked()
        )

        self._max_hold_curve.setVisible(
            self._max_hold_checkbox.isChecked()
        )

        show_peak = (
            self._current_checkbox.isChecked()
            and self._last_result is not None
        )

        self._peak_marker.setVisible(
            show_peak
        )

        self._peak_text.setVisible(
            show_peak
        )

    def set_averaging_count(
        self,
        averaging_count: int,
    ) -> None:
        self._processor.set_averaging_count(
            averaging_count
        )

        if self._processor.averaging_count > 1:
            self._average_checkbox.setChecked(
                True
            )

        self._status_label.setText(
            f"Averaging count set to {averaging_count}."
        )

    def set_max_hold_enabled(
        self,
        enabled: bool,
    ) -> None:
        enabled = bool(enabled)

        self._processor.set_max_hold_enabled(
            enabled
        )

        self._max_hold_checkbox.setChecked(
            enabled
        )

    def reset_average(self) -> None:
        self._processor.reset_average()

        self._average_curve.clear()

        self._status_label.setText(
            "Average spectrum reset."
        )

    def reset_max_hold(self) -> None:
        self._processor.reset_max_hold()

        self._max_hold_curve.clear()

        self._status_label.setText(
            "Max-hold spectrum reset."
        )

    def clear_spectrum(self) -> None:
        self._processor.reset()

        self._last_result = None
        self._last_rf_frequencies_hz = None

        self._current_curve.clear()
        self._average_curve.clear()
        self._max_hold_curve.clear()

        self._peak_marker.clear()
        self._peak_text.setText("")

        self._status_label.setText(
            "Waiting for spectrum data..."
        )

    @property
    def averaging_count(self) -> int:
        return self._processor.averaging_count

    @property
    def max_hold_enabled(self) -> bool:
        return self._processor.max_hold_enabled

    @property
    def peak_frequency_hz(
        self,
    ) -> float | None:
        if self._last_result is None:
            return None

        return self._last_result.peak_frequency_hz

    @property
    def peak_power_db(
        self,
    ) -> float | None:
        if self._last_result is None:
            return None

        return self._last_result.peak_power_db

    @property
    def processor(self) -> SpectrumProcessor:
        return self._processor


