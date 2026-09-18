from __future__ import annotations

import sys

import numpy as np

from PyQt6.QtWidgets import (
    QApplication,
)

from gui.widgets.eye_diagram_widget import (
    EyeDiagramWidget,
)


def generate_bpsk_waveform(
    number_of_symbols: int,
    *,
    samples_per_symbol: int,
    noise_std: float = 0.05,
    seed: int = 42,
) -> np.ndarray:
    rng = np.random.default_rng(
        seed
    )

    bits = rng.integers(
        0,
        2,
        size=number_of_symbols,
    )

    symbols = np.where(
        bits == 0,
        -1.0,
        1.0,
    )

    waveform = np.repeat(
        symbols,
        samples_per_symbol,
    ).astype(
        np.float64
    )

    # Mild smoothing to create more realistic transitions.
    filter_kernel = np.array(
        [
            0.05,
            0.15,
            0.30,
            0.30,
            0.15,
            0.05,
        ],
        dtype=np.float64,
    )

    filter_kernel /= np.sum(
        filter_kernel
    )

    waveform = np.convolve(
        waveform,
        filter_kernel,
        mode="same",
    )

    noise = rng.normal(
        0.0,
        noise_std,
        size=waveform.size,
    )

    return (
        waveform
        + noise
    )


def main() -> None:
    app = QApplication(
        sys.argv
    )

    samples_per_symbol = 10

    waveform = generate_bpsk_waveform(
        2000,
        samples_per_symbol=(
            samples_per_symbol
        ),
        noise_std=0.05,
        seed=42,
    )

    widget = EyeDiagramWidget(
        samples_per_symbol=(
            samples_per_symbol
        ),
        symbols_per_trace=2,
        maximum_traces=250,
    )

    widget.update_signal(
        waveform
    )

    widget.resize(
        1000,
        700,
    )

    widget.setWindowTitle(
        "OrbitLab Eye Diagram Test"
    )

    widget.show()

    assert (
        widget.latest_signal
        is not None
    )

    assert (
        widget.latest_signal.size
        == waveform.size
    )

    assert (
        widget.samples_per_symbol
        == samples_per_symbol
    )

    assert (
        widget.symbols_per_trace
        == 2
    )

    print(
        "Samples:",
        waveform.size,
    )

    print(
        "Samples per symbol:",
        samples_per_symbol,
    )

    print(
        "EyeDiagramWidget test passed."
    )

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()
