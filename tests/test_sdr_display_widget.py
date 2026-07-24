from __future__ import annotations

import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from gui.widgets.sdr_display_widget import SDRDisplayWidget
from sdr.pipeline import SDRPipeline
from sdr.simulator import SDRSimulator


def main() -> None:

    app = QApplication(sys.argv)

    simulator = SDRSimulator(
        sample_rate_hz=1_000_000,
        center_frequency_hz=437_000_000,
        tone_frequency_hz=100_000,
        signal_amplitude=1.0,
        noise_power=0.02,
        seed=42,
    )

    pipeline = SDRPipeline(
        device=simulator,
        buffer_capacity=65536,
        acquisition_block_size=2048,
        fft_size=4096,
    )

    widget = SDRDisplayWidget()

    widget.resize(
        1200,
        800,
    )

    widget.show()

    pipeline.start()

    timer = QTimer()

    def update():

        if not pipeline.update():
            return

        freq, power = pipeline.latest_spectrum(
            update=False
        )

        widget.update_display(
            freq,
            power,
            center_frequency_hz=pipeline.center_frequency_hz,
        )

    timer.timeout.connect(update)

    timer.start(50)

    app.exec()

    pipeline.stop()


if __name__ == "__main__":
    main()