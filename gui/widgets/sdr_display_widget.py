from __future__ import annotations

import numpy as np

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gui.widgets.constellation_widget import (
    ConstellationWidget,
)
from gui.widgets.eye_diagram_widget import (
    EyeDiagramWidget,
)
from gui.widgets.peak_table_widget import (
    PeakTableWidget,
)
from gui.widgets.spectrum_widget import (
    SpectrumWidget,
)
from gui.widgets.waterfall_widget import (
    WaterfallWidget,
)


class SDRDisplayWidget(QWidget):
    """
    Complete SDR visualization workspace.

    RF tab:
        Spectrum
        Waterfall
        Peak Table

    IQ tab:
        Constellation
        Eye Diagram
    """

    def __init__(
        self,
        *,
        waterfall_history_size: int = 250,
        maximum_table_peaks: int = 10,
        eye_samples_per_symbol: int = 10,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._spectrum_widget = SpectrumWidget(
            parent=self,
        )

        self._waterfall_widget = WaterfallWidget(
            history_size=waterfall_history_size,
            parent=self,
        )

        self._peak_table_widget = PeakTableWidget(
            maximum_peaks=maximum_table_peaks,
            minimum_distance_bins=20,
            minimum_power_db=-120.0,
            parent=self,
        )

        self._constellation_widget = ConstellationWidget(
            maximum_points=4000,
            parent=self,
        )

        self._eye_diagram_widget = EyeDiagramWidget(
            samples_per_symbol=eye_samples_per_symbol,
            symbols_per_trace=2,
            maximum_traces=250,
            parent=self,
        )

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        self._tabs = QTabWidget(
            self
        )

        # ------------------------------------------------
        # RF Analysis Tab
        # ------------------------------------------------

        self._rf_tab = QWidget()

        self._rf_splitter = QSplitter(
            Qt.Orientation.Vertical,
            self._rf_tab,
        )

        self._rf_splitter.addWidget(
            self._spectrum_widget
        )

        self._rf_splitter.addWidget(
            self._waterfall_widget
        )

        self._rf_splitter.addWidget(
            self._peak_table_widget
        )

        self._rf_splitter.setStretchFactor(
            0,
            4,
        )

        self._rf_splitter.setStretchFactor(
            1,
            4,
        )

        self._rf_splitter.setStretchFactor(
            2,
            2,
        )

        self._rf_splitter.setSizes(
            [
                350,
                350,
                200,
            ]
        )

        rf_layout = QVBoxLayout(
            self._rf_tab
        )

        rf_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        rf_layout.addWidget(
            self._rf_splitter
        )

        # ------------------------------------------------
        # IQ Analysis Tab
        # ------------------------------------------------

        self._iq_tab = QWidget()

        self._iq_splitter = QSplitter(
            Qt.Orientation.Horizontal,
            self._iq_tab,
        )

        self._iq_splitter.addWidget(
            self._constellation_widget
        )

        self._iq_splitter.addWidget(
            self._eye_diagram_widget
        )

        self._iq_splitter.setStretchFactor(
            0,
            1,
        )

        self._iq_splitter.setStretchFactor(
            1,
            1,
        )

        self._iq_splitter.setSizes(
            [
                600,
                600,
            ]
        )

        iq_layout = QVBoxLayout(
            self._iq_tab
        )

        iq_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        iq_layout.addWidget(
            self._iq_splitter
        )

        # ------------------------------------------------

        self._tabs.addTab(
            self._rf_tab,
            "RF Spectrum",
        )

        self._tabs.addTab(
            self._iq_tab,
            "IQ Analysis",
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
            self._tabs
        )

    def _connect_signals(self) -> None:
        self._peak_table_widget.peak_selected.connect(
            self._on_peak_selected
        )

    def _on_peak_selected(
        self,
        frequency_hz: float,
        power_db: float,
    ) -> None:
        del power_db

        self._spectrum_widget.set_marker1_from_frequency(
            frequency_hz,
            snap_to_peak=True,
        )

    def update_display(
        self,
        frequencies_hz: np.ndarray,
        power_db: np.ndarray,
        *,
        center_frequency_hz: float = 0.0,
        frequencies_are_baseband: bool = True,
    ) -> None:
        """
        Update RF-domain widgets.
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

        if frequencies_hz.size != power_db.size:
            raise ValueError(
                "Frequency and power arrays must have equal size."
            )

        if frequencies_hz.size == 0:
            self.clear_rf()
            return

        self._spectrum_widget.update_spectrum(
            frequencies_hz,
            power_db,
            center_frequency_hz=(
                center_frequency_hz
            ),
            frequencies_are_baseband=(
                frequencies_are_baseband
            ),
        )

        self._waterfall_widget.update_waterfall(
            frequencies_hz,
            power_db,
            center_frequency_hz=(
                center_frequency_hz
            ),
            frequencies_are_baseband=(
                frequencies_are_baseband
            ),
        )

        if frequencies_are_baseband:
            table_frequencies_hz = (
                frequencies_hz
                + float(center_frequency_hz)
            )
        else:
            table_frequencies_hz = (
                frequencies_hz
            )

        self._peak_table_widget.update_spectrum(
            table_frequencies_hz,
            power_db,
        )

    def update_iq(
        self,
        iq_samples: np.ndarray,
    ) -> None:
        """
        Update IQ-domain widgets.
        """
        iq_samples = np.asarray(
            iq_samples,
            dtype=np.complex64,
        )

        if iq_samples.ndim != 1:
            raise ValueError(
                "iq_samples must be one-dimensional."
            )

        if iq_samples.size == 0:
            self.clear_iq()
            return

        self._constellation_widget.update_iq(
            iq_samples
        )

        self._eye_diagram_widget.update_iq(
            iq_samples,
            component="I",
        )

    def clear_rf(self) -> None:
        self._spectrum_widget.clear_spectrum()
        self._waterfall_widget.clear_waterfall()
        self._peak_table_widget.clear()

    def clear_iq(self) -> None:
        self._constellation_widget.clear()
        self._eye_diagram_widget.clear()

    def clear(self) -> None:
        self.clear_rf()
        self.clear_iq()

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

    @property
    def peak_table_widget(
        self,
    ) -> PeakTableWidget:
        return self._peak_table_widget

    @property
    def constellation_widget(
        self,
    ) -> ConstellationWidget:
        return self._constellation_widget

    @property
    def eye_diagram_widget(
        self,
    ) -> EyeDiagramWidget:
        return self._eye_diagram_widget
