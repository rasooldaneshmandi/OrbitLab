from __future__ import annotations

import numpy as np

from sdr.analysis.sfdr import (
    SFDRAnalyzer,
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
            peak_power_db - 10.0
        )

    if index + 1 < power_db.size:
        power_db[index + 1] = (
            peak_power_db - 10.0
        )


def main() -> None:
    frequencies_hz = np.linspace(
        50_000_000.0,
        550_000_000.0,
        20_001,
    )

    power_db = np.full(
        frequencies_hz.size,
        -120.0,
        dtype=np.float64,
    )

    # Fundamental
    add_peak(
        frequencies_hz,
        power_db,
        100_000_000.0,
        -20.0,
    )

    # Strongest spur
    add_peak(
        frequencies_hz,
        power_db,
        250_000_000.0,
        -58.0,
    )

    # Weaker spur
    add_peak(
        frequencies_hz,
        power_db,
        320_000_000.0,
        -72.0,
    )

    # Another weak component
    add_peak(
        frequencies_hz,
        power_db,
        410_000_000.0,
        -81.0,
    )

    analyzer = SFDRAnalyzer(
        fundamental_guard_bins=20,
        minimum_spur_power_db=-110.0,
    )

    result = analyzer.analyze(
        frequencies_hz,
        power_db,
        fundamental_frequency_hz=(
            100_000_000.0
        ),
    )

    print(
        "Fundamental frequency:",
        result.fundamental_frequency_hz,
    )

    print(
        "Fundamental power:",
        result.fundamental_power_db,
    )

    print(
        "Strongest spur frequency:",
        result.spur_frequency_hz,
    )

    print(
        "Strongest spur power:",
        result.spur_power_db,
    )

    print(
        "SFDR:",
        result.sfdr_db,
        "dB",
    )

    assert np.isclose(
        result.fundamental_frequency_hz,
        100_000_000.0,
    )

    assert np.isclose(
        result.fundamental_power_db,
        -20.0,
    )

    assert result.spur_frequency_hz is not None

    assert np.isclose(
        result.spur_frequency_hz,
        250_000_000.0,
    )

    assert result.spur_power_db is not None

    assert np.isclose(
        result.spur_power_db,
        -58.0,
    )

    assert result.sfdr_db is not None

    assert np.isclose(
        result.sfdr_db,
        38.0,
    )

    print(
        "SFDRAnalyzer test passed."
    )


if __name__ == "__main__":
    main()
