from __future__ import annotations

import numpy as np

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from gui.widgets.spectrum_widget import SpectrumWidget
from gui.widgets.waterfall_widget import WaterfallWidget


class SDRDisplayWidget(QWidget):
    """
    Combined spectrum + waterfall display.
    """

    def __init__(
        self,
        *,
        waterfall_history_size: int = 250,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._spectrum_widget = SpectrumWidget()

        self._waterfall_widget = WaterfallWidget(
            history_size=waterfall_history_size
        )

        self._build_ui()

    def _build_ui(self) -> None:

        splitter = QSplitter(
            Qt.Orientation.Vertical
        )

        splitter.addWidget(
            self._spectrum_widget
        )

        splitter.addWidget(
            self._waterfall_widget
        )

        splitter.setStretchFactor(
            0,
            2,
        )

        splitter.setStretchFactor(
            1,
            3,
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.addWidget(splitter)

    def update_display(
        self,
        frequencies_hz: np.ndarray,
        power_db: np.ndarray,
        *,
        center_frequency_hz: float = 0.0,
        frequencies_are_baseband: bool = True,
    ) -> None:

        self._spectrum_widget.update_spectrum(
            frequencies_hz,
            power_db,
            center_frequency_hz=center_frequency_hz,
            frequencies_are_baseband=frequencies_are_baseband,
        )

        self._waterfall_widget.update_waterfall(
            frequencies_hz,
            power_db,
            center_frequency_hz=center_frequency_hz,
            frequencies_are_baseband=frequencies_are_baseband,
        )

    def clear(self) -> None:

        self._spectrum_widget.clear_spectrum()
        self._waterfall_widget.clear_waterfall()

    @property
    def spectrum_widget(
        self,
    ) -> SpectrumWidget:
        return self._spectrum_widget

    @property
    def waterfall_widget(
        self,
    ) -> WaterfallWidget:
        return self._waterfall_widget
