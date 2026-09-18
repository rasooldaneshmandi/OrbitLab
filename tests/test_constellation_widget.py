from __future__ import annotations

import sys

import numpy as np

from PyQt6.QtWidgets import QApplication

from gui.widgets.constellation_widget import (
    ConstellationWidget,
)


def generate_qpsk(
    number_of_symbols: int,
    *,
    noise_std: float = 0.08,
    seed: int = 42,
) -> np.ndarray:
    rng = np.random.default_rng(
        seed
    )

    symbol_indices = rng.integers(
        0,
        4,
        size=number_of_symbols,
    )

    constellation = np.array(
        [
            1.0 + 1.0j,
            -1.0 + 1.0j,
            -1.0 - 1.0j,
            1.0 - 1.0j,
        ],
        dtype=np.complex64,
    )

    symbols = constellation[
        symbol_indices
    ]

    noise = (
        rng.normal(
            0.0,
            noise_std,
            number_of_symbols,
        )
        + 1j
        * rng.normal(
            0.0,
            noise_std,
            number_of_symbols,
        )
    )

    iq_samples = (
        symbols
        + noise
    ).astype(
        np.complex64
    )

    return iq_samples


def main() -> None:
    app = QApplication(
        sys.argv
    )

    iq_samples = generate_qpsk(
        10_000,
        noise_std=0.08,
        seed=42,
    )

    widget = ConstellationWidget(
        maximum_points=4000,
    )

    widget.update_iq(
        iq_samples
    )

    widget.resize(
        800,
        800,
    )

    widget.setWindowTitle(
        "OrbitLab IQ Constellation Test"
    )

    widget.show()

    assert (
        widget.latest_iq
        is not None
    )

    assert (
        widget.latest_iq.size
        == iq_samples.size
    )

    assert np.iscomplexobj(
        widget.latest_iq
    )

    mean_magnitude = float(
        np.mean(
            np.abs(iq_samples)
        )
    )

    print(
        "IQ samples:",
        iq_samples.size,
    )

    print(
        "Mean magnitude:",
        mean_magnitude,
    )

    print(
        "ConstellationWidget test passed."
    )

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()
