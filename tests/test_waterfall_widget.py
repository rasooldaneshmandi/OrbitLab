from __future__ import annotations

import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from gui.widgets.waterfall_widget import (
    WaterfallWidget,
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
        buffer_capacity=65_536,
        acquisition_block_size=2048,
        fft_size=4096,
    )

    waterfall_widget = WaterfallWidget(
        history_size=250,
    )

    waterfall_widget.resize(
        1100,
        650,
    )

    waterfall_widget.show()

    pipeline.start()

    timer = QTimer()

    def update_waterfall() -> None:
        spectrum_ready = (
            pipeline.update()
        )

        if not spectrum_ready:
            return

        frequencies_hz, power_db = (
            pipeline.latest_spectrum(
                update=False
            )
        )

        waterfall_widget.update_waterfall(
            frequencies_hz,
            power_db,
            center_frequency_hz=(
                pipeline.center_frequency_hz
            ),
            frequencies_are_baseband=True,
        )

    timer.timeout.connect(
        update_waterfall
    )

    timer.start(50)

    exit_code = app.exec()

    timer.stop()
    pipeline.stop()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()