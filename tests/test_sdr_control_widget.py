from __future__ import annotations

import sys

from PyQt6.QtWidgets import (
    QApplication,
)

from gui.widgets.sdr_control_widget import (
    SDRControlWidget,
)


def main() -> None:
    app = QApplication(sys.argv)

    widget = SDRControlWidget()

    widget.set_device_name(
        "OrbitLab SDR Simulator"
    )

    widget.resize(
        340,
        600,
    )

    widget.start_requested.connect(
        lambda: print(
            "Start requested"
        )
    )

    widget.stop_requested.connect(
        lambda: print(
            "Stop requested"
        )
    )

    widget.record_requested.connect(
        lambda active: print(
            "Recording:",
            active,
        )
    )

    widget.center_frequency_changed.connect(
        lambda value: print(
            "Center frequency:",
            value,
        )
    )

    widget.sample_rate_changed.connect(
        lambda value: print(
            "Sample rate:",
            value,
        )
    )

    widget.gain_changed.connect(
        lambda value: print(
            "Gain:",
            value,
        )
    )

    widget.fft_size_changed.connect(
        lambda value: print(
            "FFT size:",
            value,
        )
    )

    widget.averaging_changed.connect(
        lambda value: print(
            "Averaging:",
            value,
        )
    )

    widget.window_changed.connect(
        lambda value: print(
            "Window:",
            value,
        )
    )

    widget.show()

    print(
        "Initial center frequency:",
        widget.center_frequency_hz,
    )

    print(
        "Initial sample rate:",
        widget.sample_rate_hz,
    )

    print(
        "Initial FFT size:",
        widget.fft_size,
    )

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
