from __future__ import annotations

import sys

import numpy as np

from PyQt6.QtWidgets import (
    QApplication,
)

from gui.widgets.spur_table_widget import (
    SpurTableWidget,
)

from sdr.analysis.spur_analysis import (
    SpurAnalyzer,
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
    app = QApplication(sys.argv)

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

    add_peak(
        frequencies_hz,
        power_db,
        100_000_000.0,
        -20.0,
    )

    add_peak(
        frequencies_hz,
        power_db,
        250_000_000.0,
        -58.0,
    )

    add_peak(
        frequencies_hz,
        power_db,
        320_000_000.0,
        -72.0,
    )

    add_peak(
        frequencies_hz,
        power_db,
        410_000_000.0,
        -81.0,
    )

    analyzer = SpurAnalyzer(
        maximum_spurs=10,
        fundamental_guard_bins=20,
        minimum_spur_distance_bins=20,
        minimum_spur_power_db=-110.0,
    )

    result = analyzer.analyze(
        frequencies_hz,
        power_db,
        fundamental_frequency_hz=(
            100_000_000.0
        ),
    )

    widget = SpurTableWidget()

    widget.spur_selected.connect(
        lambda frequency_hz, power_db: print(
            "Selected spur:",
            f"{frequency_hz / 1_000_000.0:.6f} MHz,",
            f"{power_db:.2f} dB",
        )
    )

    widget.update_result(
        result
    )

    widget.resize(
        900,
        500,
    )

    widget.setWindowTitle(
        "OrbitLab Spur Table Test"
    )

    widget.show()

    print(
        "Spurs detected:",
        len(result.spurs),
    )

    assert len(
        result.spurs
    ) == 3

    assert np.isclose(
        result.spurs[0].frequency_hz,
        250_000_000.0,
    )

    assert np.isclose(
        result.spurs[0].power_db,
        -58.0,
    )

    assert np.isclose(
        result.spurs[0].relative_power_dbc,
        -38.0,
    )

    assert np.isclose(
        result.spurs[1].frequency_hz,
        320_000_000.0,
    )

    assert np.isclose(
        result.spurs[2].frequency_hz,
        410_000_000.0,
    )

    print(
        "SpurTableWidget test passed."
    )

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()
