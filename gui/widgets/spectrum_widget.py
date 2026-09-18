from __future__ import annotations

import numpy as np
import pyqtgraph as pg

from PyQt6.QtCore import Qt
from gui.widgets.harmonic_marker_overlay import (
    HarmonicMarkerOverlay,
)

from sdr.analysis.harmonic_analysis import (
    HarmonicAnalysisResult,
)

from PyQt6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SpectrumWidget(QWidget):
    """
    Real-time SDR spectrum display.

    Features:
        - Automatic peak detection
        - Interactive M1 and M2 markers
        - Snap to local peak
        - Draggable markers
        - Delta frequency and delta power
    """

    SNAP_RADIUS_BINS = 20

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._latest_peak_frequency_hz: float | None = None
        self._latest_peak_power_db: float | None = None

        self._latest_rf_frequencies_hz: np.ndarray | None = None
        self._latest_power_db: np.ndarray | None = None

        self._marker1_frequency_hz: float | None = None
        self._marker1_power_db: float | None = None

        self._marker2_frequency_hz: float | None = None
        self._marker2_power_db: float | None = None

        self._active_marker = 1
        self._updating_marker_lines = False

        self._peak_tracking_enabled = False

        self._obw_enabled = False
        self._obw_percentage = 99.0

        self._obw_lower_frequency_hz: float | None = None
        self._obw_upper_frequency_hz: float | None = None
        self._obw_center_frequency_hz: float | None = None
        self._occupied_bandwidth_hz: float | None = None

        self._channel_power_enabled = False
        self._channel_power_db: float | None = None
        self._channel_lower_frequency_hz: float | None = None
        self._channel_upper_frequency_hz: float | None = None
        self._channel_bandwidth_hz: float | None = None

        self._build_ui()

        self._harmonic_overlay = HarmonicMarkerOverlay(
            self._plot_widget
        )

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

        self._obw_status_label = QLabel(
            "Occupied Bandwidth: disabled"
        )
        self._obw_status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self._channel_power_status_label = QLabel(
            "Channel Power: disabled"
        )
        self._channel_power_status_label.setAlignment(
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

        # Automatic strongest peak
        self._peak_marker = pg.ScatterPlotItem(
            size=10,
            symbol="t",
            pen=pg.mkPen("r"),
            brush=pg.mkBrush("r"),
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

        self._obw_region = pg.LinearRegionItem(
            values=(0.0, 0.0),
            orientation="vertical",
            movable=False,
        )
        self._obw_region.setZValue(-10)
        self._obw_region.setVisible(False)

        self._plot_widget.addItem(
            self._obw_region
        )

        self._channel_power_region = pg.LinearRegionItem(
            values=(0.0, 0.0),
            orientation="vertical",
            movable=False,
        )
        self._channel_power_region.setZValue(-9)
        self._channel_power_region.setVisible(False)

        self._plot_widget.addItem(
            self._channel_power_region
        )

        # Marker M1
        self._marker1_line = pg.InfiniteLine(
            angle=90,
            movable=True,
            pen=pg.mkPen("y", width=2),
        )
        self._marker1_line.setVisible(False)
        self._plot_widget.addItem(
            self._marker1_line
        )

        self._marker1_point = pg.ScatterPlotItem(
            size=12,
            symbol="x",
            pen=pg.mkPen("y", width=2),
        )
        self._marker1_point.setVisible(False)
        self._plot_widget.addItem(
            self._marker1_point
        )

        self._marker1_text = pg.TextItem(
            text="",
            anchor=(0.5, 1.3),
            color="y",
        )
        self._marker1_text.setVisible(False)
        self._plot_widget.addItem(
            self._marker1_text
        )

        # Marker M2
        self._marker2_line = pg.InfiniteLine(
            angle=90,
            movable=True,
            pen=pg.mkPen("c", width=2),
        )
        self._marker2_line.setVisible(False)
        self._plot_widget.addItem(
            self._marker2_line
        )

        self._marker2_point = pg.ScatterPlotItem(
            size=12,
            symbol="x",
            pen=pg.mkPen("c", width=2),
        )
        self._marker2_point.setVisible(False)
        self._plot_widget.addItem(
            self._marker2_point
        )

        self._marker2_text = pg.TextItem(
            text="",
            anchor=(0.5, 1.3),
            color="c",
        )
        self._marker2_text.setVisible(False)
        self._plot_widget.addItem(
            self._marker2_text
        )

        self._m1_button = QPushButton(
            "M1"
        )
        self._m1_button.setCheckable(True)
        self._m1_button.setChecked(True)

        self._m2_button = QPushButton(
            "M2"
        )
        self._m2_button.setCheckable(True)

        self._marker_button_group = QButtonGroup(
            self
        )
        self._marker_button_group.setExclusive(True)
        self._marker_button_group.addButton(
            self._m1_button,
            1,
        )
        self._marker_button_group.addButton(
            self._m2_button,
            2,
        )

        self._clear_m1_button = QPushButton(
            "Clear M1"
        )

        self._clear_m2_button = QPushButton(
            "Clear M2"
        )

        self._clear_all_button = QPushButton(
            "Clear All"
        )

        self._track_m1_button = QPushButton(
            "Track M1"
        )
        self._track_m1_button.setCheckable(
            True
        )
        self._track_m1_button.setToolTip(
            "Automatically follow the local peak near M1"
        )

        self._obw_button = QPushButton(
            "OBW 99%"
        )
        self._obw_button.setCheckable(
            True
        )
        self._obw_button.setToolTip(
            "Measure the bandwidth containing 99 percent "
            "of the total spectrum power"
        )

        self._channel_power_button = QPushButton(
            "Channel Power"
        )
        self._channel_power_button.setCheckable(
            True
        )
        self._channel_power_button.setToolTip(
            "Integrate spectrum power between M1 and M2"
        )

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(
            QLabel("Active marker:")
        )
        controls_layout.addWidget(
            self._m1_button
        )
        controls_layout.addWidget(
            self._m2_button
        )
        controls_layout.addWidget(
            self._track_m1_button
        )
        controls_layout.addWidget(
            self._obw_button
        )
        controls_layout.addWidget(
            self._channel_power_button
        )
        controls_layout.addStretch(1)
        controls_layout.addWidget(
            self._clear_m1_button
        )
        controls_layout.addWidget(
            self._clear_m2_button
        )
        controls_layout.addWidget(
            self._clear_all_button
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

        layout.addWidget(
            self._obw_status_label
        )

        layout.addWidget(
            self._channel_power_status_label
        )

    def _connect_signals(self) -> None:
        self._plot_widget.scene().sigMouseClicked.connect(
            self._on_plot_clicked
        )

        self._marker_button_group.idClicked.connect(
            self._set_active_marker
        )

        self._marker1_line.sigPositionChanged.connect(
            self._on_marker1_line_moved
        )

        self._marker2_line.sigPositionChanged.connect(
            self._on_marker2_line_moved
        )

        self._clear_m1_button.clicked.connect(
            self.clear_marker1
        )

        self._clear_m2_button.clicked.connect(
            self.clear_marker2
        )

        self._clear_all_button.clicked.connect(
            self.clear_markers
        )

        self._track_m1_button.toggled.connect(
            self._set_peak_tracking_enabled
        )

        self._obw_button.toggled.connect(
            self._set_obw_enabled
        )

        self._channel_power_button.toggled.connect(
            self._set_channel_power_enabled
        )

    def _set_channel_power_enabled(
        self,
        enabled: bool,
    ) -> None:
        self._channel_power_enabled = bool(
            enabled
        )

        if not self._channel_power_enabled:
            self._clear_channel_power_display()
            return

        self._update_channel_power()

    def _set_obw_enabled(
        self,
        enabled: bool,
    ) -> None:
        self._obw_enabled = bool(
            enabled
        )

        if not self._obw_enabled:
            self._clear_obw_display()
            return

        self._update_occupied_bandwidth()

    def _set_peak_tracking_enabled(
        self,
        enabled: bool,
    ) -> None:
        self._peak_tracking_enabled = bool(
            enabled
        )

        if (
            self._peak_tracking_enabled
            and self._marker1_frequency_hz is not None
        ):
            self._place_marker(
                marker_number=1,
                requested_frequency_hz=(
                    self._marker1_frequency_hz
                ),
                snap_to_peak=True,
            )

        self._update_status()

    def _set_active_marker(
        self,
        marker_number: int,
    ) -> None:
        self._active_marker = int(
            marker_number
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

        peak_power_db = float(
            power_db[peak_index]
        )

        peak_frequency_mhz = (
            peak_frequency_hz / 1_000_000.0
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
            f"Peak\n"
            f"{peak_frequency_mhz:.6f} MHz\n"
            f"{peak_power_db:.2f} dB"
        )

        self._peak_text.setPos(
            peak_frequency_mhz,
            peak_power_db,
        )

        # Keep existing markers on their current
        # frequencies while new FFT frames arrive.
        if self._marker1_frequency_hz is not None:
            self._place_marker(
                marker_number=1,
                requested_frequency_hz=(
                    self._marker1_frequency_hz
                ),
                snap_to_peak=(
                    self._peak_tracking_enabled
                ),
            )

        if self._marker2_frequency_hz is not None:
            self._place_marker(
                marker_number=2,
                requested_frequency_hz=(
                    self._marker2_frequency_hz
                ),
                snap_to_peak=False,
            )

        if self._obw_enabled:
            self._update_occupied_bandwidth()

        if self._channel_power_enabled:
            self._update_channel_power()

        self._update_status()

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

        if not view_box.sceneBoundingRect().contains(
            scene_position
        ):
            return

        view_position = view_box.mapSceneToView(
            scene_position
        )

        requested_frequency_hz = (
            float(view_position.x())
            * 1_000_000.0
        )

        self._place_marker(
            marker_number=self._active_marker,
            requested_frequency_hz=(
                requested_frequency_hz
            ),
            snap_to_peak=True,
        )

    def _on_marker1_line_moved(
        self,
    ) -> None:
        if self._updating_marker_lines:
            return

        requested_frequency_hz = (
            float(self._marker1_line.value())
            * 1_000_000.0
        )

        self._place_marker(
            marker_number=1,
            requested_frequency_hz=(
                requested_frequency_hz
            ),
            snap_to_peak=True,
        )

    def _on_marker2_line_moved(
        self,
    ) -> None:
        if self._updating_marker_lines:
            return

        requested_frequency_hz = (
            float(self._marker2_line.value())
            * 1_000_000.0
        )

        self._place_marker(
            marker_number=2,
            requested_frequency_hz=(
                requested_frequency_hz
            ),
            snap_to_peak=True,
        )

    def _place_marker(
        self,
        marker_number: int,
        requested_frequency_hz: float,
        *,
        snap_to_peak: bool,
    ) -> None:
        if self._latest_rf_frequencies_hz is None:
            return

        if self._latest_power_db is None:
            return

        frequencies_hz = (
            self._latest_rf_frequencies_hz
        )
        power_db = self._latest_power_db

        if frequencies_hz.size == 0:
            return

        nearest_index = int(
            np.argmin(
                np.abs(
                    frequencies_hz
                    - float(requested_frequency_hz)
                )
            )
        )

        marker_index = nearest_index

        if snap_to_peak:
            search_start = max(
                0,
                nearest_index - self.SNAP_RADIUS_BINS,
            )

            search_stop = min(
                power_db.size,
                nearest_index
                + self.SNAP_RADIUS_BINS
                + 1,
            )

            local_power_db = power_db[
                search_start:search_stop
            ]

            if local_power_db.size > 0:
                marker_index = (
                    search_start
                    + int(np.argmax(local_power_db))
                )

        marker_frequency_hz = float(
            frequencies_hz[marker_index]
        )

        marker_power_db = float(
            power_db[marker_index]
        )

        marker_frequency_mhz = (
            marker_frequency_hz
            / 1_000_000.0
        )

        self._updating_marker_lines = True

        try:
            if marker_number == 1:
                self._marker1_frequency_hz = (
                    marker_frequency_hz
                )
                self._marker1_power_db = (
                    marker_power_db
                )

                self._marker1_line.setValue(
                    marker_frequency_mhz
                )

                self._marker1_point.setData(
                    [marker_frequency_mhz],
                    [marker_power_db],
                )

                self._marker1_text.setText(
                    f"M1\n"
                    f"{marker_frequency_mhz:.6f} MHz\n"
                    f"{marker_power_db:.2f} dB"
                )

                self._marker1_text.setPos(
                    marker_frequency_mhz,
                    marker_power_db,
                )

                self._marker1_line.setVisible(True)
                self._marker1_point.setVisible(True)
                self._marker1_text.setVisible(True)

            elif marker_number == 2:
                self._marker2_frequency_hz = (
                    marker_frequency_hz
                )
                self._marker2_power_db = (
                    marker_power_db
                )

                self._marker2_line.setValue(
                    marker_frequency_mhz
                )

                self._marker2_point.setData(
                    [marker_frequency_mhz],
                    [marker_power_db],
                )

                self._marker2_text.setText(
                    f"M2\n"
                    f"{marker_frequency_mhz:.6f} MHz\n"
                    f"{marker_power_db:.2f} dB"
                )

                self._marker2_text.setPos(
                    marker_frequency_mhz,
                    marker_power_db,
                )

                self._marker2_line.setVisible(True)
                self._marker2_point.setVisible(True)
                self._marker2_text.setVisible(True)

            else:
                raise ValueError(
                    "marker_number must be 1 or 2."
                )

        finally:
            self._updating_marker_lines = False

        if self._channel_power_enabled:
            self._update_channel_power()

        self._update_status()

    def _update_channel_power(self) -> None:
        """
        Integrate the linear power of all FFT bins between
        Marker M1 and Marker M2.

        The returned unit uses the same logarithmic reference
        as the incoming power_db values. For calibrated dBm-bin
        input, the result is dBm. For uncalibrated FFT data, the
        result is relative integrated dB.
        """
        if not self._channel_power_enabled:
            self._clear_channel_power_display()
            return

        if self._latest_rf_frequencies_hz is None:
            self._clear_channel_power_display()
            return

        if self._latest_power_db is None:
            self._clear_channel_power_display()
            return

        if (
            self._marker1_frequency_hz is None
            or self._marker2_frequency_hz is None
        ):
            self._clear_channel_power_display()
            return

        frequencies_hz = np.asarray(
            self._latest_rf_frequencies_hz,
            dtype=np.float64,
        )

        power_db = np.asarray(
            self._latest_power_db,
            dtype=np.float64,
        )

        if frequencies_hz.size == 0:
            self._clear_channel_power_display()
            return

        if frequencies_hz.size != power_db.size:
            self._clear_channel_power_display()
            return

        lower_frequency_hz = min(
            self._marker1_frequency_hz,
            self._marker2_frequency_hz,
        )

        upper_frequency_hz = max(
            self._marker1_frequency_hz,
            self._marker2_frequency_hz,
        )

        channel_mask = (
            (frequencies_hz >= lower_frequency_hz)
            & (frequencies_hz <= upper_frequency_hz)
        )

        channel_indices = np.flatnonzero(
            channel_mask
        )

        if channel_indices.size == 0:
            self._clear_channel_power_display()
            return

        channel_power_db_bins = power_db[
            channel_indices
        ]

        # Numerically stable conversion from logarithmic
        # power to linear power.
        reference_power_db = float(
            np.max(channel_power_db_bins)
        )

        relative_power_linear = np.power(
            10.0,
            (
                channel_power_db_bins
                - reference_power_db
            ) / 10.0,
        )

        integrated_relative_power = float(
            np.sum(relative_power_linear)
        )

        if (
            not np.isfinite(integrated_relative_power)
            or integrated_relative_power <= 0.0
        ):
            self._clear_channel_power_display()
            return

        channel_power_db = (
            reference_power_db
            + 10.0
            * np.log10(
                integrated_relative_power
            )
        )

        actual_lower_frequency_hz = float(
            frequencies_hz[channel_indices[0]]
        )

        actual_upper_frequency_hz = float(
            frequencies_hz[channel_indices[-1]]
        )

        channel_bandwidth_hz = abs(
            actual_upper_frequency_hz
            - actual_lower_frequency_hz
        )

        self._channel_power_db = float(
            channel_power_db
        )

        self._channel_lower_frequency_hz = (
            actual_lower_frequency_hz
        )

        self._channel_upper_frequency_hz = (
            actual_upper_frequency_hz
        )

        self._channel_bandwidth_hz = (
            channel_bandwidth_hz
        )

        self._channel_power_region.setRegion(
            (
                actual_lower_frequency_hz
                / 1_000_000.0,
                actual_upper_frequency_hz
                / 1_000_000.0,
            )
        )

        self._channel_power_region.setVisible(
            True
        )

        self._channel_power_status_label.setText(
            f"Channel Power: "
            f"{channel_power_db:.2f} dB"
            f"   |   Bandwidth: "
            f"{channel_bandwidth_hz / 1_000.0:.3f} kHz"
            f"   |   Lower: "
            f"{actual_lower_frequency_hz / 1_000_000.0:.6f} MHz"
            f"   |   Upper: "
            f"{actual_upper_frequency_hz / 1_000_000.0:.6f} MHz"
            f"   |   Bins: "
            f"{channel_indices.size}"
        )

    def _clear_channel_power_display(self) -> None:
        self._channel_power_db = None
        self._channel_lower_frequency_hz = None
        self._channel_upper_frequency_hz = None
        self._channel_bandwidth_hz = None

        self._channel_power_region.setVisible(
            False
        )

        if self._channel_power_enabled:
            self._channel_power_status_label.setText(
                "Channel Power: place M1 and M2 "
                "at the channel boundaries"
            )
        else:
            self._channel_power_status_label.setText(
                "Channel Power: disabled"
            )

    def _update_occupied_bandwidth(self) -> None:
        """
        Calculate the bandwidth containing the requested
        percentage of the total spectral power.

        For 99 percent OBW, 0.5 percent of the accumulated
        power is removed from each side of the spectrum.
        """
        if not self._obw_enabled:
            self._clear_obw_display()
            return

        if self._latest_rf_frequencies_hz is None:
            self._clear_obw_display()
            return

        if self._latest_power_db is None:
            self._clear_obw_display()
            return

        frequencies_hz = np.asarray(
            self._latest_rf_frequencies_hz,
            dtype=np.float64,
        )

        power_db = np.asarray(
            self._latest_power_db,
            dtype=np.float64,
        )

        if frequencies_hz.size < 2:
            self._clear_obw_display()
            return

        if frequencies_hz.size != power_db.size:
            self._clear_obw_display()
            return

        # Convert dB values into linear power.
        maximum_power_db = float(
            np.max(power_db)
        )

        relative_power_linear = np.power(
            10.0,
            (power_db - maximum_power_db) / 10.0,
        )

        total_power = float(
            np.sum(relative_power_linear)
        )

        if (
            not np.isfinite(total_power)
            or total_power <= 0.0
        ):
            self._clear_obw_display()
            return

        cumulative_power = np.cumsum(
            relative_power_linear
        )

        excluded_fraction = (
            1.0
            - self._obw_percentage / 100.0
        )

        lower_target = (
            total_power
            * excluded_fraction
            / 2.0
        )

        upper_target = (
            total_power
            * (1.0 - excluded_fraction / 2.0)
        )

        lower_index = int(
            np.searchsorted(
                cumulative_power,
                lower_target,
                side="left",
            )
        )

        upper_index = int(
            np.searchsorted(
                cumulative_power,
                upper_target,
                side="left",
            )
        )

        lower_index = int(
            np.clip(
                lower_index,
                0,
                frequencies_hz.size - 1,
            )
        )

        upper_index = int(
            np.clip(
                upper_index,
                lower_index,
                frequencies_hz.size - 1,
            )
        )

        lower_frequency_hz = float(
            frequencies_hz[lower_index]
        )

        upper_frequency_hz = float(
            frequencies_hz[upper_index]
        )

        occupied_bandwidth_hz = abs(
            upper_frequency_hz
            - lower_frequency_hz
        )

        center_frequency_hz = (
            lower_frequency_hz
            + upper_frequency_hz
        ) / 2.0

        self._obw_lower_frequency_hz = (
            lower_frequency_hz
        )

        self._obw_upper_frequency_hz = (
            upper_frequency_hz
        )

        self._obw_center_frequency_hz = (
            center_frequency_hz
        )

        self._occupied_bandwidth_hz = (
            occupied_bandwidth_hz
        )

        self._obw_region.setRegion(
            (
                lower_frequency_hz / 1_000_000.0,
                upper_frequency_hz / 1_000_000.0,
            )
        )

        self._obw_region.setVisible(
            True
        )

        self._obw_status_label.setText(
            f"{self._obw_percentage:.0f}% OBW: "
            f"{occupied_bandwidth_hz / 1_000.0:.3f} kHz"
            f"   |   Center: "
            f"{center_frequency_hz / 1_000_000.0:.6f} MHz"
            f"   |   Lower: "
            f"{lower_frequency_hz / 1_000_000.0:.6f} MHz"
            f"   |   Upper: "
            f"{upper_frequency_hz / 1_000_000.0:.6f} MHz"
        )

    def _clear_obw_display(self) -> None:
        self._obw_lower_frequency_hz = None
        self._obw_upper_frequency_hz = None
        self._obw_center_frequency_hz = None
        self._occupied_bandwidth_hz = None

        self._obw_region.setVisible(
            False
        )

        if self._obw_enabled:
            self._obw_status_label.setText(
                "Occupied Bandwidth: waiting for spectrum data..."
            )
        else:
            self._obw_status_label.setText(
                "Occupied Bandwidth: disabled"
            )

    def _update_status(self) -> None:
        if (
            self._marker1_frequency_hz is not None
            and self._marker1_power_db is not None
            and self._marker2_frequency_hz is not None
            and self._marker2_power_db is not None
        ):
            delta_frequency_hz = (
                self._marker2_frequency_hz
                - self._marker1_frequency_hz
            )

            delta_power_db = (
                self._marker2_power_db
                - self._marker1_power_db
            )

            self._status_label.setText(
                f"M1: "
                f"{self._marker1_frequency_hz / 1_000_000.0:.6f} MHz"
                f"  |  "
                f"M2: "
                f"{self._marker2_frequency_hz / 1_000_000.0:.6f} MHz"
                f"  |  "
                f"Δf: {delta_frequency_hz / 1_000.0:+.3f} kHz"
                f"  |  "
                f"ΔP: {delta_power_db:+.2f} dB"
            )
            return

        if (
            self._marker1_frequency_hz is not None
            and self._marker1_power_db is not None
        ):
            self._status_label.setText(
                f"M1: "
                f"{self._marker1_frequency_hz / 1_000_000.0:.6f} MHz"
                f"  |  "
                f"Power: {self._marker1_power_db:.2f} dB"
            )
            return

        if (
            self._marker2_frequency_hz is not None
            and self._marker2_power_db is not None
        ):
            self._status_label.setText(
                f"M2: "
                f"{self._marker2_frequency_hz / 1_000_000.0:.6f} MHz"
                f"  |  "
                f"Power: {self._marker2_power_db:.2f} dB"
            )
            return

        if (
            self._latest_peak_frequency_hz is not None
            and self._latest_peak_power_db is not None
        ):
            self._status_label.setText(
                f"Peak: "
                f"{self._latest_peak_frequency_hz / 1_000_000.0:.6f} MHz"
                f"  |  "
                f"Power: {self._latest_peak_power_db:.2f} dB"
            )
            return

        self._status_label.setText(
            "Waiting for spectrum data..."
        )

    def set_marker1_from_frequency(
        self,
        frequency_hz: float,
        *,
        snap_to_peak: bool = True,
    ) -> None:
        """
        Place Marker M1 at the requested RF frequency.

        This public method is used by other widgets, such as
        PeakTableWidget, to move M1 programmatically.
        """
        if not np.isfinite(frequency_hz):
            raise ValueError(
                "frequency_hz must be finite."
            )

        if self._latest_rf_frequencies_hz is None:
            return

        if self._latest_power_db is None:
            return

        self._active_marker = 1
        self._m1_button.setChecked(True)

        self._place_marker(
            marker_number=1,
            requested_frequency_hz=float(
                frequency_hz
            ),
            snap_to_peak=bool(
                snap_to_peak
            ),
        )
    def update_harmonic_markers(
        self,
        result: HarmonicAnalysisResult,
    ) -> None:
        """
        Display harmonic-analysis results on the spectrum.
        """
        self._harmonic_overlay.update_result(
            result
        )

    def clear_harmonic_markers(
        self,
    ) -> None:
        self._harmonic_overlay.clear()

    def set_harmonic_markers_visible(
        self,
        visible: bool,
    ) -> None:
        self._harmonic_overlay.set_visible(
            visible
        )

    @property
    def harmonic_marker_count(
        self,
    ) -> int:
        return self._harmonic_overlay.marker_count
    def clear_marker1(self) -> None:
        self._marker1_frequency_hz = None
        self._marker1_power_db = None

        self._marker1_line.setVisible(False)
        self._marker1_point.setVisible(False)
        self._marker1_text.setVisible(False)

        self._marker1_point.setData(
            [],
            [],
        )
        self._marker1_text.setText("")

        if self._channel_power_enabled:
            self._update_channel_power()

        self._update_status()

    def clear_marker2(self) -> None:
        self._marker2_frequency_hz = None
        self._marker2_power_db = None

        self._marker2_line.setVisible(False)
        self._marker2_point.setVisible(False)
        self._marker2_text.setVisible(False)

        self._marker2_point.setData(
            [],
            [],
        )
        self._marker2_text.setText("")

        if self._channel_power_enabled:
            self._update_channel_power()

        self._update_status()

    def clear_markers(self) -> None:
        self.clear_marker1()
        self.clear_marker2()

    def clear_marker(self) -> None:
        """
        Backward-compatible method.

        Clears M1, which was the original single marker.
        """
        self.clear_marker1()

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

        self._marker1_line.setVisible(False)
        self._marker1_point.setVisible(False)
        self._marker1_text.setVisible(False)

        self._marker2_line.setVisible(False)
        self._marker2_point.setVisible(False)
        self._marker2_text.setVisible(False)

        self._marker1_point.setData([], [])
        self._marker2_point.setData([], [])

        self._marker1_text.setText("")
        self._marker2_text.setText("")

        self._clear_obw_display()
        self._clear_channel_power_display()

        self._latest_peak_frequency_hz = None
        self._latest_peak_power_db = None

        self._latest_rf_frequencies_hz = None
        self._latest_power_db = None

        self._marker1_frequency_hz = None
        self._marker1_power_db = None

        self._marker2_frequency_hz = None
        self._marker2_power_db = None

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
        """
        Backward-compatible M1 frequency property.
        """
        return self._marker1_frequency_hz

    @property
    def marker_power_db(
        self,
    ) -> float | None:
        """
        Backward-compatible M1 power property.
        """
        return self._marker1_power_db

    @property
    def marker1_frequency_hz(
        self,
    ) -> float | None:
        return self._marker1_frequency_hz

    @property
    def marker1_power_db(
        self,
    ) -> float | None:
        return self._marker1_power_db

    @property
    def marker2_frequency_hz(
        self,
    ) -> float | None:
        return self._marker2_frequency_hz

    @property
    def marker2_power_db(
        self,
    ) -> float | None:
        return self._marker2_power_db

    @property
    def delta_frequency_hz(
        self,
    ) -> float | None:
        if (
            self._marker1_frequency_hz is None
            or self._marker2_frequency_hz is None
        ):
            return None

        return (
            self._marker2_frequency_hz
            - self._marker1_frequency_hz
        )

    @property
    def delta_power_db(
        self,
    ) -> float | None:
        if (
            self._marker1_power_db is None
            or self._marker2_power_db is None
        ):
            return None

        return (
            self._marker2_power_db
            - self._marker1_power_db
        )
    @property
    def occupied_bandwidth_hz(
        self,
    ) -> float | None:
        return self._occupied_bandwidth_hz

    @property
    def obw_center_frequency_hz(
        self,
    ) -> float | None:
        return self._obw_center_frequency_hz

    @property
    def obw_lower_frequency_hz(
        self,
    ) -> float | None:
        return self._obw_lower_frequency_hz

    @property
    def obw_upper_frequency_hz(
        self,
    ) -> float | None:
        return self._obw_upper_frequency_hz
    @property
    def channel_power_db(
        self,
    ) -> float | None:
        return self._channel_power_db

    @property
    def channel_bandwidth_hz(
        self,
    ) -> float | None:
        return self._channel_bandwidth_hz

    @property
    def channel_lower_frequency_hz(
        self,
    ) -> float | None:
        return self._channel_lower_frequency_hz

    @property
    def channel_upper_frequency_hz(
        self,
    ) -> float | None:
        return self._channel_upper_frequency_hz



