from __future__ import annotations

import numpy as np

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

    print(
        "Fundamental:",
        result.fundamental_frequency_hz,
        "Hz",
    )

    print(
        "Fundamental power:",
        result.fundamental_power_db,
        "dB",
    )

    for measurement in result.measurements:
        print(
            f"H{measurement.order}:",
            "expected=",
            measurement.expected_frequency_hz,
            "measured=",
            measurement.measured_frequency_hz,
            "power=",
            measurement.power_db,
            "dBc=",
            measurement.relative_power_dbc,
            "detected=",
            measurement.detected,
        )

    harmonic_1 = result.measurements[0]
    harmonic_2 = result.measurements[1]
    harmonic_3 = result.measurements[2]
    harmonic_4 = result.measurements[3]
    harmonic_5 = result.measurements[4]

    assert harmonic_1.detected
    assert harmonic_2.detected
    assert harmonic_3.detected
    assert harmonic_4.detected

    assert np.isclose(
        harmonic_1.relative_power_dbc,
        0.0,
    )

    assert np.isclose(
        harmonic_2.relative_power_dbc,
        -30.0,
    )

    assert np.isclose(
        harmonic_3.relative_power_dbc,
        -42.0,
    )

    assert np.isclose(
        harmonic_4.relative_power_dbc,
        -53.0,
    )

    assert not harmonic_5.detected

    assert harmonic_5.measured_frequency_hz is not None

    assert np.isclose(
        harmonic_5.relative_power_dbc,
        -90.0,
    )

    print(
        "HarmonicAnalyzer test passed."
    )


if __name__ == "__main__":
    main()

