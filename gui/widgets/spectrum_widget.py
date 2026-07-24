from __future__ import annotations

import numpy as np
import pyqtgraph as pg

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SpectrumWidget(QWidget):
    """
    Real-time SDR spectrum display with an interactive user marker.

    Features:
        - Current spectrum
        - Automatic peak marker
        - User marker by mouse click
        - Draggable user-marker line
        - Clear Marker button
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._latest_peak_frequency_hz: float | None = None
        self._latest_peak_power_db: float | None = None

        self._latest_rf_frequencies_hz: np.ndarray | None = None
        self._latest_power_db: np.ndarray | None = None

        self._marker_frequency_hz: float | None = None
        self._marker_power_db: float | None = None

        self._updating_marker_line = False

        self._build_ui()
        self._connect_signals()

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

        self._spectrum_curve = self._plot_widget.plot(
            [],
            [],
            pen=pg.mkPen(width=1.5),
            name="Spectrum",
        )

        # Automatic strongest-peak marker.
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

        # Interactive user marker.
        self._marker_line = pg.InfiniteLine(
            angle=90,
            movable=True,
        )
        self._marker_line.setVisible(False)
        self._plot_widget.addItem(
            self._marker_line
        )

        self._marker_point = pg.ScatterPlotItem(
            size=12,
            symbol="x",
        )
        self._marker_point.setVisible(False)
        self._plot_widget.addItem(
            self._marker_point
        )

        self._marker_text = pg.TextItem(
            text="",
            anchor=(0.5, 1.3),
        )
        self._marker_text.setVisible(False)
        self._plot_widget.addItem(
            self._marker_text
        )

        self._clear_marker_button = QPushButton(
            "Clear Marker"
        )

        controls_layout = QHBoxLayout()
        controls_layout.addStretch(1)
        controls_layout.addWidget(
            self._clear_marker_button
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
        self._plot_widget.scene().sigMouseClicked.connect(
            self._on_plot_clicked
        )

        self._marker_line.sigPositionChanged.connect(
            self._on_marker_line_moved
        )

        self._clear_marker_button.clicked.connect(
            self.clear_marker
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

        if not np.all(np.isfinite(frequencies_hz)):
            raise ValueError(
                "frequencies_hz contains invalid values."
            )

        if not np.all(np.isfinite(power_db)):
            raise ValueError(
                "power_db contains invalid values."
            )

        if frequencies_are_baseband:
            rf_frequencies_hz = (
                frequencies_hz
                + float(center_frequency_hz)
            )
        else:
            rf_frequencies_hz = frequencies_hz.copy()

        self._latest_rf_frequencies_hz = (
            rf_frequencies_hz.copy()
        )

        self._latest_power_db = power_db.copy()

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

        # Keep an existing user marker attached to the
        # nearest FFT bin as new frames arrive.
        if self._marker_frequency_hz is not None:
            self._set_marker_from_frequency(
                self._marker_frequency_hz
            )
        else:
            self._status_label.setText(
                f"Peak: {peak_frequency_mhz:.6f} MHz"
                f"   |   Power: {peak_power_db:.2f} dB"
                f"   |   FFT bins: {frequencies_hz.size}"
            )

    def _on_plot_clicked(
        self,
        event,
    ) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return

        if self._latest_rf_frequencies_hz is None:
            return

        if self._latest_power_db is None:
            return

        scene_position = event.scenePos()
        view_box = self._plot_widget.getPlotItem().vb

        # Ignore clicks outside the actual plotting area.
        if not view_box.sceneBoundingRect().contains(
            scene_position
        ):
            return

        view_position = view_box.mapSceneToView(
            scene_position
        )

        clicked_frequency_hz = (
            float(view_position.x())
            * 1_000_000.0
        )

        self._set_marker_from_frequency(
            clicked_frequency_hz
        )

    def _on_marker_line_moved(
        self,
    ) -> None:
        if self._updating_marker_line:
            return

        if self._latest_rf_frequencies_hz is None:
            return

        dragged_frequency_hz = (
            float(self._marker_line.value())
            * 1_000_000.0
        )

        self._set_marker_from_frequency(
            dragged_frequency_hz
        )

    def _set_marker_from_frequency(
        self,
        requested_frequency_hz: float,
    ) -> None:
        """
        Place the marker on the strongest local peak
        near the requested frequency.
        """
        if self._latest_rf_frequencies_hz is None:
            return

        if self._latest_power_db is None:
            return

        frequencies_hz = self._latest_rf_frequencies_hz
        power_db = self._latest_power_db

        if frequencies_hz.size == 0:
            return

        if power_db.size == 0:
            return

        nearest_index = int(
            np.argmin(
                np.abs(
                    frequencies_hz
                    - float(requested_frequency_hz)
                )
            )
        )

        search_radius_bins = 20

        search_start = max(
            0,
            nearest_index - search_radius_bins,
        )

        search_stop = min(
            power_db.size,
            nearest_index + search_radius_bins + 1,
        )

        local_power_db = power_db[
            search_start:search_stop
        ]

        if local_power_db.size == 0:
            marker_index = nearest_index
        else:
            local_peak_index = int(
                np.argmax(local_power_db)
            )

            marker_index = (
                search_start
                + local_peak_index
            )

        marker_frequency_hz = float(
            frequencies_hz[
                marker_index
            ]
        )

        marker_power_db = float(
            power_db[
                marker_index
            ]
        )

        marker_frequency_mhz = (
            marker_frequency_hz
            / 1_000_000.0
        )

        self._marker_frequency_hz = (
            marker_frequency_hz
        )

        self._marker_power_db = (
            marker_power_db
        )

        self._updating_marker_line = True

        try:
            self._marker_line.setValue(
                marker_frequency_mhz
            )
        finally:
            self._updating_marker_line = False

        self._marker_point.setData(
            [marker_frequency_mhz],
            [marker_power_db],
        )

        self._marker_text.setText(
            f"M1\n"
            f"{marker_frequency_mhz:.6f} MHz\n"
            f"{marker_power_db:.2f} dB"
        )

        self._marker_text.setPos(
            marker_frequency_mhz,
            marker_power_db,
        )

        self._marker_line.setVisible(True)
        self._marker_point.setVisible(True)
        self._marker_text.setVisible(True)

        frequency_error_hz = (
            marker_frequency_hz
            - float(requested_frequency_hz)
        )

        self._status_label.setText(
            f"M1: {marker_frequency_mhz:.6f} MHz"
            f"   |   Power: {marker_power_db:.2f} dB"
            f"   |   Snap: "
            f"{frequency_error_hz / 1_000.0:+.2f} kHz"
        )
    def clear_marker(self) -> None:
        self._marker_frequency_hz = None
        self._marker_power_db = None

        self._marker_line.setVisible(False)
        self._marker_point.setVisible(False)
        self._marker_text.setVisible(False)

        self._marker_point.setData(
            [],
            [],
        )

        self._marker_text.setText("")

        if self._latest_peak_frequency_hz is None:
            self._status_label.setText(
                "Waiting for spectrum data..."
            )
            return

        self._status_label.setText(
            f"Peak: "
            f"{self._latest_peak_frequency_hz / 1_000_000.0:.6f} MHz"
            f"   |   Power: "
            f"{self._latest_peak_power_db:.2f} dB"
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

        self.clear_marker()

        self._latest_peak_frequency_hz = None
        self._latest_peak_power_db = None

        self._latest_rf_frequencies_hz = None
        self._latest_power_db = None

        self._status_label.setText(
            "Waiting for spectrum data..."
        )

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

    @property
    def marker_frequency_hz(
        self,
    ) -> float | None:
        return self._marker_frequency_hz

    @property
    def marker_power_db(
        self,
    ) -> float | None:
        return self._marker_power_db

