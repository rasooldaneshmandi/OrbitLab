from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class SDRControlWidget(QWidget):
    """
    Control panel for configuring and controlling an SDR device.

    This widget does not directly access SDR hardware. It emits Qt signals
    that can be connected to SDRPipeline or MainWindow methods.
    """

    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    record_requested = pyqtSignal(bool)

    center_frequency_changed = pyqtSignal(float)
    sample_rate_changed = pyqtSignal(float)
    gain_changed = pyqtSignal(float)
    fft_size_changed = pyqtSignal(int)
    averaging_changed = pyqtSignal(int)
    window_changed = pyqtSignal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._recording = False

        self._build_ui()
        self._connect_signals()
        self.set_running(False)

    def _build_ui(self) -> None:
        self._title_label = QLabel(
            "<b>SDR Control Panel</b>"
        )

        self._device_label = QLabel(
            "Device: SDR Simulator"
        )

        self._status_label = QLabel(
            "Status: Stopped"
        )

        settings_group = QGroupBox(
            "Receiver Settings"
        )

        settings_layout = QFormLayout(
            settings_group
        )

        self._center_frequency_spin = (
            QDoubleSpinBox()
        )
        self._center_frequency_spin.setRange(
            100_000.0,
            6_000_000_000.0,
        )
        self._center_frequency_spin.setDecimals(0)
        self._center_frequency_spin.setSingleStep(
            1_000.0
        )
        self._center_frequency_spin.setValue(
            437_000_000.0
        )
        self._center_frequency_spin.setSuffix(
            " Hz"
        )

        self._sample_rate_combo = QComboBox()
        self._sample_rate_combo.addItem(
            "250 kS/s",
            250_000.0,
        )
        self._sample_rate_combo.addItem(
            "1 MS/s",
            1_000_000.0,
        )
        self._sample_rate_combo.addItem(
            "2 MS/s",
            2_000_000.0,
        )
        self._sample_rate_combo.addItem(
            "2.4 MS/s",
            2_400_000.0,
        )
        self._sample_rate_combo.setCurrentIndex(1)

        self._gain_spin = QDoubleSpinBox()
        self._gain_spin.setRange(
            0.0,
            100.0,
        )
        self._gain_spin.setDecimals(1)
        self._gain_spin.setSingleStep(1.0)
        self._gain_spin.setValue(20.0)
        self._gain_spin.setSuffix(" dB")

        self._fft_size_combo = QComboBox()

        for fft_size in (
            1024,
            2048,
            4096,
            8192,
            16384,
        ):
            self._fft_size_combo.addItem(
                str(fft_size),
                fft_size,
            )

        self._fft_size_combo.setCurrentText(
            "4096"
        )

        self._averaging_spin = QSpinBox()
        self._averaging_spin.setRange(
            1,
            128,
        )
        self._averaging_spin.setValue(1)

        self._window_combo = QComboBox()
        self._window_combo.addItems(
            [
                "Hann",
                "Hamming",
                "Blackman",
                "Rectangular",
            ]
        )

        settings_layout.addRow(
            "Center frequency:",
            self._center_frequency_spin,
        )
        settings_layout.addRow(
            "Sample rate:",
            self._sample_rate_combo,
        )
        settings_layout.addRow(
            "Gain:",
            self._gain_spin,
        )
        settings_layout.addRow(
            "FFT size:",
            self._fft_size_combo,
        )
        settings_layout.addRow(
            "Averaging:",
            self._averaging_spin,
        )
        settings_layout.addRow(
            "Window:",
            self._window_combo,
        )

        self._start_button = QPushButton(
            "Start"
        )
        self._stop_button = QPushButton(
            "Stop"
        )
        self._record_button = QPushButton(
            "Start Recording"
        )

        start_stop_layout = QHBoxLayout()
        start_stop_layout.addWidget(
            self._start_button
        )
        start_stop_layout.addWidget(
            self._stop_button
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self._title_label)
        layout.addWidget(self._device_label)
        layout.addWidget(self._status_label)
        layout.addWidget(settings_group)
        layout.addLayout(start_stop_layout)
        layout.addWidget(self._record_button)
        layout.addStretch(1)

        self.setMaximumWidth(340)

    def _connect_signals(self) -> None:
        self._start_button.clicked.connect(
            self._on_start_clicked
        )

        self._stop_button.clicked.connect(
            self._on_stop_clicked
        )

        self._record_button.clicked.connect(
            self._on_record_clicked
        )

        self._center_frequency_spin.valueChanged.connect(
            self.center_frequency_changed.emit
        )

        self._sample_rate_combo.currentIndexChanged.connect(
            self._emit_sample_rate
        )

        self._gain_spin.valueChanged.connect(
            self.gain_changed.emit
        )

        self._fft_size_combo.currentIndexChanged.connect(
            self._emit_fft_size
        )

        self._averaging_spin.valueChanged.connect(
            self.averaging_changed.emit
        )

        self._window_combo.currentTextChanged.connect(
            self.window_changed.emit
        )

    def _on_start_clicked(self) -> None:
        self.set_running(True)
        self.start_requested.emit()

    def _on_stop_clicked(self) -> None:
        self.set_running(False)
        self.stop_requested.emit()

    def _on_record_clicked(self) -> None:
        self._recording = not self._recording

        if self._recording:
            self._record_button.setText(
                "Stop Recording"
            )
        else:
            self._record_button.setText(
                "Start Recording"
            )

        self.record_requested.emit(
            self._recording
        )

    def _emit_sample_rate(self) -> None:
        sample_rate_hz = float(
            self._sample_rate_combo.currentData()
        )

        self.sample_rate_changed.emit(
            sample_rate_hz
        )

    def _emit_fft_size(self) -> None:
        fft_size = int(
            self._fft_size_combo.currentData()
        )

        self.fft_size_changed.emit(
            fft_size
        )

    def set_running(
        self,
        running: bool,
    ) -> None:
        running = bool(running)

        self._start_button.setEnabled(
            not running
        )
        self._stop_button.setEnabled(
            running
        )

        if running:
            self._status_label.setText(
                "Status: Running"
            )
        else:
            self._status_label.setText(
                "Status: Stopped"
            )

    def set_device_name(
        self,
        device_name: str,
    ) -> None:
        self._device_label.setText(
            f"Device: {device_name}"
        )

    def set_center_frequency(
        self,
        frequency_hz: float,
    ) -> None:
        self._center_frequency_spin.setValue(
            float(frequency_hz)
        )

    def set_fft_size(
        self,
        fft_size: int,
    ) -> None:
        index = self._fft_size_combo.findData(
            int(fft_size)
        )

        if index >= 0:
            self._fft_size_combo.setCurrentIndex(
                index
            )

    @property
    def center_frequency_hz(self) -> float:
        return float(
            self._center_frequency_spin.value()
        )

    @property
    def sample_rate_hz(self) -> float:
        return float(
            self._sample_rate_combo.currentData()
        )

    @property
    def gain_db(self) -> float:
        return float(
            self._gain_spin.value()
        )

    @property
    def fft_size(self) -> int:
        return int(
            self._fft_size_combo.currentData()
        )

    @property
    def averaging(self) -> int:
        return int(
            self._averaging_spin.value()
        )

    @property
    def window_name(self) -> str:
        return self._window_combo.currentText()

    @property
    def is_recording(self) -> bool:
        return self._recording
