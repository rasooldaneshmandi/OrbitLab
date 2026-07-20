from __future__ import annotations

import numpy as np
import pyqtgraph as pg

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)


class WaterfallWidget(QWidget):
    """
    Real-time SDR waterfall display.

    Each new power spectrum is inserted at the top of the image.
    Frequency input is expected in Hz and displayed in MHz.
    """

    def __init__(
        self,
        *,
        history_size: int = 200,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        if isinstance(history_size, bool) or not isinstance(
            history_size,
            int,
        ):
            raise TypeError(
                "history_size must be an integer."
            )

        if history_size <= 0:
            raise ValueError(
                "history_size must be greater than zero."
            )

        self._history_size = history_size
        self._frequency_bins = 0

        self._waterfall_data: np.ndarray | None = None

        self._minimum_power_db = -100.0
        self._maximum_power_db = 80.0

        self._build_ui()

    def _build_ui(self) -> None:
        self._title_label = QLabel(
            "Real-Time SDR Waterfall"
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
            "History",
            units="frames",
        )

        self._plot_widget.showGrid(
            x=True,
            y=False,
            alpha=0.2,
        )

        self._plot_widget.setMouseEnabled(
            x=True,
            y=True,
        )

        self._image_item = pg.ImageItem()
        self._plot_widget.addItem(
            self._image_item
        )

        color_map = pg.colormap.get(
            "viridis"
        )
        self._image_item.setColorMap(
            color_map
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

    def update_waterfall(
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
            rf_frequencies_hz = frequencies_hz

        frequency_bins = int(
            power_db.size
        )

        if (
            self._waterfall_data is None
            or self._frequency_bins
            != frequency_bins
        ):
            self._initialize_buffer(
                frequency_bins
            )

        assert self._waterfall_data is not None

        self._waterfall_data[1:, :] = (
            self._waterfall_data[:-1, :]
        )

        self._waterfall_data[0, :] = (
            power_db
        )

        self._image_item.setImage(
            self._waterfall_data,
            autoLevels=False,
            levels=(
                self._minimum_power_db,
                self._maximum_power_db,
            ),
        )

        minimum_frequency_mhz = float(
            rf_frequencies_hz[0]
            / 1_000_000.0
        )

        maximum_frequency_mhz = float(
            rf_frequencies_hz[-1]
            / 1_000_000.0
        )

        frequency_span_mhz = (
            maximum_frequency_mhz
            - minimum_frequency_mhz
        )

        if frequency_span_mhz <= 0:
            frequency_span_mhz = 1.0

        self._image_item.setRect(
            QRectF(
                minimum_frequency_mhz,
                0.0,
                frequency_span_mhz,
                float(self._history_size),
            )
        )

        peak_index = int(
            np.argmax(power_db)
        )

        peak_frequency_mhz = float(
            rf_frequencies_hz[peak_index]
            / 1_000_000.0
        )

        peak_power_db = float(
            power_db[peak_index]
        )

        self._status_label.setText(
            f"Peak: {peak_frequency_mhz:.6f} MHz"
            f"   |   Power: {peak_power_db:.2f} dB"
            f"   |   FFT bins: {frequency_bins}"
            f"   |   History: {self._history_size}"
        )

    def _initialize_buffer(
        self,
        frequency_bins: int,
    ) -> None:
        self._frequency_bins = (
            frequency_bins
        )

        self._waterfall_data = np.full(
            (
                self._history_size,
                frequency_bins,
            ),
            self._minimum_power_db,
            dtype=np.float32,
        )

    def set_power_range(
        self,
        minimum_power_db: float,
        maximum_power_db: float,
    ) -> None:
        minimum_power_db = float(
            minimum_power_db
        )

        maximum_power_db = float(
            maximum_power_db
        )

        if not np.isfinite(
            minimum_power_db
        ):
            raise ValueError(
                "minimum_power_db must be finite."
            )

        if not np.isfinite(
            maximum_power_db
        ):
            raise ValueError(
                "maximum_power_db must be finite."
            )

        if minimum_power_db >= maximum_power_db:
            raise ValueError(
                "minimum_power_db must be smaller "
                "than maximum_power_db."
            )

        self._minimum_power_db = (
            minimum_power_db
        )

        self._maximum_power_db = (
            maximum_power_db
        )

    def set_colormap(
        self,
        name: str,
    ) -> None:
        if not isinstance(name, str):
            raise TypeError(
                "name must be a string."
            )

        color_map = pg.colormap.get(name)
        self._image_item.setColorMap(
            color_map
        )

    def clear_waterfall(self) -> None:
        if self._waterfall_data is not None:
            self._waterfall_data.fill(
                self._minimum_power_db
            )

            self._image_item.setImage(
                self._waterfall_data,
                autoLevels=False,
                levels=(
                    self._minimum_power_db,
                    self._maximum_power_db,
                ),
            )

        self._status_label.setText(
            "Waiting for spectrum data..."
        )

    @property
    def history_size(self) -> int:
        return self._history_size

    @property
    def frequency_bins(self) -> int:
        return self._frequency_bins
