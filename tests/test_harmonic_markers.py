from __future__ import annotations

import sys

import numpy as np

from PyQt6.QtWidgets import QApplication

from gui.widgets.spectrum_widget import (
    SpectrumWidget,
)

from sdr.analysis.harmonic_analysis import (
    HarmonicAnalyzer,
)


def add_peak(
    frequencies_hz: np.ndarray,
    power_db: np.ndarray,
    frequency_hz: float,
    peak_power_db: float,
) -> None:
    index = int(
        np.argmin(
            np.abs(
                frequencies_hz
                - frequency_hz
            )
        )
    )

    power_db[index] = peak_power_db

    if index > 0:
        power_db[index - 1] = (
            peak_power_db - 8.0
        )

    if index + 1 < power_db.size:
        power_db[index + 1] = (
            peak_power_db - 8.0
        )


def main() -> None:
    app = QApplication(sys.argv)

    frequencies_hz = np.linspace(
        50_000_000.0,
        550_000_000.0,
        10_001,
    )

    power_db = np.full(
        frequencies_hz.size,
        -110.0,
        dtype=np.float64,
    )

    add_peak(
        frequencies_hz,
        power_db,
        100_000_000.0,
        -20.0,
    )

    add_peak(
        frequencies_hz,
        power_db,
        200_000_000.0,
        -50.0,
    )

    add_peak(
        frequencies_hz,
        power_db,
        300_000_000.0,
        -62.0,
    )

    add_peak(
        frequencies_hz,
        power_db,
        400_000_000.0,
        -73.0,
    )

    analyzer = HarmonicAnalyzer(
        maximum_order=5,
        search_radius_bins=5,
        minimum_relative_power_dbc=-80.0,
    )

    result = analyzer.analyze(
        frequencies_hz,
        power_db,
        fundamental_frequency_hz=(
            100_000_000.0
        ),
    )

    widget = SpectrumWidget()

    widget.update_spectrum(
        frequencies_hz,
        power_db,
        frequencies_are_baseband=False,
    )

    widget.update_harmonic_markers(
        result
    )

    widget.resize(
        1300,
        700,
    )

    widget.setWindowTitle(
        "OrbitLab Harmonic Marker Test"
    )

    widget.show()

    print(
        "Harmonic markers:",
        widget.harmonic_marker_count,
    )

    assert (
        widget.harmonic_marker_count
        == 4
    )

    assert (
        result.measurements[0].detected
    )

    assert (
        result.measurements[1].detected
    )

    assert (
        result.measurements[2].detected
    )

    assert (
        result.measurements[3].detected
    )

    assert not (
        result.measurements[4].detected
    )

    print(
        "Harmonic Marker test passed."
    )

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()
