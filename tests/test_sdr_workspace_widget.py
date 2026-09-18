from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from gui.widgets.sdr_workspace_widget import (
    SDRWorkspaceWidget,
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

    workspace = SDRWorkspaceWidget(
        pipeline=pipeline,
        update_interval_ms=50,
        waterfall_history_size=250,
    )

    workspace.center_frequency_requested.connect(
        lambda value: print(
            "Center frequency requested:",
            value,
        )
    )

    workspace.sample_rate_requested.connect(
        lambda value: print(
            "Sample rate requested:",
            value,
        )
    )

    workspace.gain_requested.connect(
        lambda value: print(
            "Gain requested:",
            value,
        )
    )

    workspace.fft_size_requested.connect(
        lambda value: print(
            "FFT size requested:",
            value,
        )
    )

    workspace.averaging_requested.connect(
        lambda value: print(
            "Averaging requested:",
            value,
        )
    )

    workspace.window_requested.connect(
        lambda value: print(
            "Window requested:",
            value,
        )
    )

    workspace.recording_requested.connect(
        lambda active: print(
            "Recording requested:",
            active,
        )
    )

    workspace.resize(
        1400,
        850,
    )

    workspace.setWindowTitle(
        "OrbitLab SDR Workspace Test"
    )

    workspace.show()

    exit_code = app.exec()

    workspace.stop()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
