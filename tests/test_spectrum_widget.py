from __future__ import annotations

import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from gui.widgets.spectrum_widget import (
    SpectrumWidget,
)
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
        buffer_capacity=16_384,
        acquisition_block_size=2048,
        fft_size=4096,
    )

    spectrum_widget = SpectrumWidget()

    spectrum_widget.resize(
        1000,
        600,
    )

    spectrum_widget.show()

    pipeline.start()

    timer = QTimer()

    def update_spectrum() -> None:
        spectrum_ready = pipeline.update()

        if not spectrum_ready:
            return

        frequencies_hz, power_db = (
            pipeline.latest_spectrum(
                update=False
            )
        )

        spectrum_widget.update_spectrum(
            frequencies_hz,
            power_db,
            center_frequency_hz=(
                pipeline.center_frequency_hz
            ),
            frequencies_are_baseband=True,
        )

    timer.timeout.connect(
        update_spectrum
    )

    timer.start(50)

    exit_code = app.exec()

    timer.stop()
    pipeline.stop()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()