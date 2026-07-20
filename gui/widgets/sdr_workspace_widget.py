from __future__ import annotations

import numpy as np

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QSplitter,
    QWidget,
)

from gui.widgets.sdr_control_widget import SDRControlWidget
from gui.widgets.sdr_display_widget import SDRDisplayWidget


class SDRWorkspaceWidget(QWidget):
    """
    Complete SDR workspace.

    Layout:
        Left:
            SDRControlWidget

        Right:
            SpectrumWidget
            WaterfallWidget

    The workspace manages:
        - SDR pipeline start and stop
        - Periodic acquisition and FFT updates
        - Spectrum and waterfall refresh
        - Basic runtime status
    """

    center_frequency_requested = pyqtSignal(float)
    sample_rate_requested = pyqtSignal(float)
    gain_requested = pyqtSignal(float)
    fft_size_requested = pyqtSignal(int)
    averaging_requested = pyqtSignal(int)
    window_requested = pyqtSignal(str)
    recording_requested = pyqtSignal(bool)

    def __init__(
        self,
        pipeline,
        *,
        update_interval_ms: int = 50,
        waterfall_history_size: int = 250,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        if pipeline is None:
            raise ValueError(
                "pipeline must not be None."
            )

        if (
            isinstance(update_interval_ms, bool)
            or not isinstance(update_interval_ms, int)
        ):
            raise TypeError(
                "update_interval_ms must be an integer."
            )

        if update_interval_ms <= 0:
            raise ValueError(
                "update_interval_ms must be greater than zero."
            )

        self._pipeline = pipeline
        self._update_interval_ms = update_interval_ms

        self._control_widget = SDRControlWidget(
            parent=self,
        )

        self._display_widget = SDRDisplayWidget(
            waterfall_history_size=waterfall_history_size,
            parent=self,
        )

        self._timer = QTimer(self)
        self._timer.setInterval(
            self._update_interval_ms
        )

        self._build_ui()
        self._connect_signals()
        self._initialize_controls()

    def _build_ui(self) -> None:
        splitter = QSplitter(self)

        splitter.addWidget(
            self._control_widget
        )

        splitter.addWidget(
            self._display_widget
        )

        splitter.setStretchFactor(
            0,
            0,
        )

        splitter.setStretchFactor(
            1,
            1,
        )

        splitter.setSizes(
            [300, 1000]
        )

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.addWidget(splitter)

    def _connect_signals(self) -> None:
        self._control_widget.start_requested.connect(
            self.start
        )

        self._control_widget.stop_requested.connect(
            self.stop
        )

        self._control_widget.record_requested.connect(
            self.recording_requested.emit
        )

        self._control_widget.center_frequency_changed.connect(
            self._on_center_frequency_changed
        )

        self._control_widget.sample_rate_changed.connect(
            self._on_sample_rate_changed
        )

        self._control_widget.gain_changed.connect(
            self._on_gain_changed
        )

        self._control_widget.fft_size_changed.connect(
            self._on_fft_size_changed
        )

        self._control_widget.averaging_changed.connect(
            self._on_averaging_changed
        )

        self._control_widget.window_changed.connect(
            self._on_window_changed
        )

        self._timer.timeout.connect(
            self._update_sdr
        )

    def _initialize_controls(self) -> None:
        device_name = type(
            getattr(
                self._pipeline,
                "device",
                self._pipeline,
            )
        ).__name__

        self._control_widget.set_device_name(
            device_name
        )

        center_frequency_hz = getattr(
            self._pipeline,
            "center_frequency_hz",
            None,
        )

        if center_frequency_hz is not None:
            self._control_widget.set_center_frequency(
                float(center_frequency_hz)
            )

        self._control_widget.set_running(
            False
        )

    def start(self) -> None:
        if self.is_running:
            return

        try:
            self._pipeline.start()

            self._timer.start()

            self._control_widget.set_running(
                True
            )

        except Exception as error:
            self._control_widget.set_running(
                False
            )

            QMessageBox.critical(
                self,
                "SDR Start Error",
                str(error),
            )

    def stop(self) -> None:
        self._timer.stop()

        try:
            self._pipeline.stop()

        except Exception as error:
            QMessageBox.warning(
                self,
                "SDR Stop Error",
                str(error),
            )

        finally:
            self._control_widget.set_running(
                False
            )

    def _update_sdr(self) -> None:
        try:
            spectrum_ready = self._pipeline.update()

            if not spectrum_ready:
                return

            spectrum = self._pipeline.latest_spectrum(
                update=False
            )

            if spectrum is None:
                return

            frequencies_hz, power_db = spectrum

            frequencies_hz = np.asarray(
                frequencies_hz,
                dtype=np.float64,
            )

            power_db = np.asarray(
                power_db,
                dtype=np.float64,
            )

            if frequencies_hz.size == 0:
                return

            if power_db.size == 0:
                return

            center_frequency_hz = float(
                getattr(
                    self._pipeline,
                    "center_frequency_hz",
                    self._control_widget.center_frequency_hz,
                )
            )

            self._display_widget.update_display(
                frequencies_hz,
                power_db,
                center_frequency_hz=center_frequency_hz,
                frequencies_are_baseband=True,
            )

        except Exception as error:
            self.stop()

            QMessageBox.critical(
                self,
                "SDR Update Error",
                str(error),
            )

    def _on_center_frequency_changed(
        self,
        frequency_hz: float,
    ) -> None:
        frequency_hz = float(
            frequency_hz
        )

        self.center_frequency_requested.emit(
            frequency_hz
        )

        self._try_set_pipeline_value(
            names=(
                "set_center_frequency",
                "set_center_frequency_hz",
            ),
            value=frequency_hz,
        )

    def _on_sample_rate_changed(
        self,
        sample_rate_hz: float,
    ) -> None:
        sample_rate_hz = float(
            sample_rate_hz
        )

        self.sample_rate_requested.emit(
            sample_rate_hz
        )

        self._try_set_pipeline_value(
            names=(
                "set_sample_rate",
                "set_sample_rate_hz",
            ),
            value=sample_rate_hz,
        )

    def _on_gain_changed(
        self,
        gain_db: float,
    ) -> None:
        gain_db = float(
            gain_db
        )

        self.gain_requested.emit(
            gain_db
        )

        self._try_set_pipeline_value(
            names=(
                "set_gain",
                "set_gain_db",
            ),
            value=gain_db,
        )

    def _on_fft_size_changed(
        self,
        fft_size: int,
    ) -> None:
        fft_size = int(
            fft_size
        )

        self.fft_size_requested.emit(
            fft_size
        )

        self._try_set_pipeline_value(
            names=(
                "set_fft_size",
            ),
            value=fft_size,
        )

    def _on_averaging_changed(
        self,
        averaging: int,
    ) -> None:
        averaging = int(
            averaging
        )

        self.averaging_requested.emit(
            averaging
        )

        self._try_set_pipeline_value(
            names=(
                "set_averaging",
                "set_average_count",
            ),
            value=averaging,
        )

    def _on_window_changed(
        self,
        window_name: str,
    ) -> None:
        window_name = str(
            window_name
        )

        self.window_requested.emit(
            window_name
        )

        self._try_set_pipeline_value(
            names=(
                "set_window",
                "set_window_name",
            ),
            value=window_name,
        )

    def _try_set_pipeline_value(
        self,
        *,
        names: tuple[str, ...],
        value,
    ) -> bool:
        targets = [
            self._pipeline,
            getattr(
                self._pipeline,
                "device",
                None,
            ),
        ]

        for target in targets:
            if target is None:
                continue

            for method_name in names:
                method = getattr(
                    target,
                    method_name,
                    None,
                )

                if callable(method):
                    try:
                        method(value)
                        return True

                    except Exception as error:
                        print(
                            f"{method_name} failed:",
                            error,
                        )

        return False

    def clear_display(self) -> None:
        self._display_widget.clear()

    def closeEvent(self, event) -> None:
        self.stop()
        event.accept()

    @property
    def is_running(self) -> bool:
        pipeline_state = getattr(
            self._pipeline,
            "is_running",
            None,
        )

        if isinstance(pipeline_state, bool):
            return pipeline_state

        return self._timer.isActive()

    @property
    def pipeline(self):
        return self._pipeline

    @property
    def control_widget(self) -> SDRControlWidget:
        return self._control_widget

    @property
    def display_widget(self) -> SDRDisplayWidget:
        return self._display_widget
