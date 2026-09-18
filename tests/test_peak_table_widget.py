from __future__ import annotations

import sys

import numpy as np

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from gui.widgets.peak_table_widget import (
    PeakTableWidget,
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

    widget = PeakTableWidget(
        maximum_peaks=10,
        minimum_distance_bins=20,
        minimum_power_db=-120.0,
    )

    widget.peak_selected.connect(
        lambda frequency_hz, power_db: print(
            "Selected peak:",
            frequency_hz,
            "Hz,",
            power_db,
            "dB",
        )
    )

    widget.resize(
        700,
        500,
    )

    widget.setWindowTitle(
        "OrbitLab Peak Table Test"
    )

    widget.show()

    pipeline.start()

    timer = QTimer()

    def update_table() -> None:
        if not pipeline.update():
            return

        frequencies_hz, power_db = (
            pipeline.latest_rf_spectrum(
                update=False
            )
        )

        peaks = widget.update_spectrum(
            frequencies_hz,
            power_db,
        )

        if peaks:
            strongest = peaks[0]

            assert np.isfinite(
                strongest.frequency_hz
            )

            assert np.isfinite(
                strongest.power_db
            )

    timer.timeout.connect(
        update_table
    )

    timer.start(100)

    exit_code = app.exec()

    timer.stop()
    pipeline.stop()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
