from __future__ import annotations

import numpy as np
import pyqtgraph as pg

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)


class EyeDiagramWidget(QWidget):
    """
    Real-time eye diagram display.

    The widget expects a 1-D real-valued signal and a known
    number of samples per symbol.

    Each trace spans multiple symbol periods and is overlaid
    with the others to form the eye diagram.
    """

    def __init__(
        self,
        *,
        samples_per_symbol: int = 10,
        symbols_per_trace: int = 2,
        maximum_traces: int = 200,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        if samples_per_symbol <= 1:
            raise ValueError(
                "samples_per_symbol must be greater than 1."
            )

        if symbols_per_trace <= 0:
            raise ValueError(
                "symbols_per_trace must be greater than zero."
            )

        if maximum_traces <= 0:
            raise ValueError(
                "maximum_traces must be greater than zero."
            )

        self._samples_per_symbol = int(
            samples_per_symbol
        )

        self._symbols_per_trace = int(
            symbols_per_trace
        )

        self._maximum_traces = int(
            maximum_traces
        )

        self._latest_signal: np.ndarray | None = None

        self._curves: list[
            pg.PlotDataItem
        ] = []

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        self._title_label = QLabel(
            "Eye Diagram"
        )

        self._title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self._samples_per_symbol_spin = QSpinBox()
        self._samples_per_symbol_spin.setRange(
            2,
            1024,
        )
        self._samples_per_symbol_spin.setValue(
            self._samples_per_symbol
        )

        self._symbols_per_trace_spin = QSpinBox()
        self._symbols_per_trace_spin.setRange(
            1,
            10,
        )
        self._symbols_per_trace_spin.setValue(
            self._symbols_per_trace
        )

        self._maximum_traces_spin = QSpinBox()
        self._maximum_traces_spin.setRange(
            10,
            5000,
        )
        self._maximum_traces_spin.setValue(
            self._maximum_traces
        )

        controls_layout = QHBoxLayout()

        controls_layout.addWidget(
            QLabel("Samples/symbol:")
        )
        controls_layout.addWidget(
            self._samples_per_symbol_spin
        )

        controls_layout.addWidget(
            QLabel("Symbols/trace:")
        )
        controls_layout.addWidget(
            self._symbols_per_trace_spin
        )

        controls_layout.addWidget(
            QLabel("Max traces:")
        )
        controls_layout.addWidget(
            self._maximum_traces_spin
        )

        controls_layout.addStretch(1)

        self._plot_widget = pg.PlotWidget()

        self._plot_widget.setLabel(
            "bottom",
            "Time",
            units="symbols",
        )

        self._plot_widget.setLabel(
            "left",
            "Amplitude",
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

        self._timing_line = pg.InfiniteLine(
            pos=1.0,
            angle=90,
            movable=False,
        )

        self._plot_widget.addItem(
            self._timing_line
        )

        self._status_label = QLabel(
            "Waiting for signal samples..."
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
        self._samples_per_symbol_spin.valueChanged.connect(
            self._on_configuration_changed
        )

        self._symbols_per_trace_spin.valueChanged.connect(
            self._on_configuration_changed
        )

        self._maximum_traces_spin.valueChanged.connect(
            self._on_configuration_changed
        )

    def _on_configuration_changed(
        self,
        value: int,
    ) -> None:
        del value

        self._samples_per_symbol = int(
            self._samples_per_symbol_spin.value()
        )

        self._symbols_per_trace = int(
            self._symbols_per_trace_spin.value()
        )

        self._maximum_traces = int(
            self._maximum_traces_spin.value()
        )

        if self._latest_signal is not None:
            self.update_signal(
                self._latest_signal
            )

    def update_signal(
        self,
        signal_samples: np.ndarray,
    ) -> None:
        signal_samples = np.asarray(
            signal_samples,
            dtype=np.float64,
        )

        if signal_samples.ndim != 1:
            raise ValueError(
                "signal_samples must be one-dimensional."
            )

        if signal_samples.size == 0:
            self.clear()
            return

        if not np.all(
            np.isfinite(signal_samples)
        ):
            raise ValueError(
                "signal_samples contains invalid values."
            )

        self._latest_signal = (
            signal_samples.copy()
        )

        samples_per_trace = (
            self._samples_per_symbol
            * self._symbols_per_trace
        )

        if signal_samples.size < samples_per_trace:
            self._status_label.setText(
                "Not enough samples for one eye trace."
            )
            self._clear_curves()
            return

        available_traces = (
            signal_samples.size
            // self._samples_per_symbol
        ) - (
            self._symbols_per_trace
            - 1
        )

        number_of_traces = min(
            available_traces,
            self._maximum_traces,
        )

        if number_of_traces <= 0:
            self._clear_curves()
            return

        self._ensure_curve_count(
            number_of_traces
        )

        time_axis = (
            np.arange(
                samples_per_trace,
                dtype=np.float64,
            )
            / float(
                self._samples_per_symbol
            )
        )

        for trace_index in range(
            number_of_traces
        ):
            start = (
                trace_index
                * self._samples_per_symbol
            )

            stop = (
                start
                + samples_per_trace
            )

            trace = signal_samples[
                start:stop
            ]

            if trace.size != samples_per_trace:
                self._curves[
                    trace_index
                ].setData(
                    [],
                    [],
                )
                continue

            self._curves[
                trace_index
            ].setData(
                time_axis,
                trace,
            )

        for unused_index in range(
            number_of_traces,
            len(self._curves),
        ):
            self._curves[
                unused_index
            ].setData(
                [],
                [],
            )

        rms = float(
            np.sqrt(
                np.mean(
                    signal_samples ** 2
                )
            )
        )

        peak = float(
            np.max(
                np.abs(signal_samples)
            )
        )

        self._status_label.setText(
            f"Traces: {number_of_traces}"
            f"   |   Samples/symbol: "
            f"{self._samples_per_symbol}"
            f"   |   RMS: {rms:.4f}"
            f"   |   Peak: {peak:.4f}"
        )

    def update_iq(
        self,
        iq_samples: np.ndarray,
        *,
        component: str = "I",
    ) -> None:
        """
        Convenience method for IQ data.

        component:
            I         -> real component
            Q         -> imaginary component
            magnitude -> absolute value
        """
        iq_samples = np.asarray(
            iq_samples,
            dtype=np.complex64,
        )

        normalized_component = (
            component.strip().lower()
        )

        if normalized_component == "i":
            signal = np.real(
                iq_samples
            )

        elif normalized_component == "q":
            signal = np.imag(
                iq_samples
            )

        elif normalized_component == "magnitude":
            signal = np.abs(
                iq_samples
            )

        else:
            raise ValueError(
                "component must be I, Q, or magnitude."
            )

        self.update_signal(
            signal
        )

    def _ensure_curve_count(
        self,
        required_count: int,
    ) -> None:
        while len(
            self._curves
        ) < required_count:
            curve = self._plot_widget.plot(
                [],
                [],
                pen=pg.mkPen(
                    width=1.0,
                ),
            )

            self._curves.append(
                curve
            )

    def _clear_curves(self) -> None:
        for curve in self._curves:
            curve.setData(
                [],
                [],
            )

    def clear(self) -> None:
        self._latest_signal = None

        self._clear_curves()

        self._status_label.setText(
            "Waiting for signal samples..."
        )

    @property
    def samples_per_symbol(
        self,
    ) -> int:
        return self._samples_per_symbol

    @property
    def symbols_per_trace(
        self,
    ) -> int:
        return self._symbols_per_trace

    @property
    def latest_signal(
        self,
    ) -> np.ndarray | None:
        if self._latest_signal is None:
            return None

        return self._latest_signal.copy()
