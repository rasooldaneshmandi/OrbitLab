from __future__ import annotations

import numpy as np

from sdr.spectrum_processor import (
    SpectrumProcessor,
)


def main() -> None:
    frequencies_hz = np.array(
        [
            -200_000.0,
            -100_000.0,
            0.0,
            100_000.0,
            200_000.0,
        ],
        dtype=np.float64,
    )

    processor = SpectrumProcessor(
        averaging_count=3,
        max_hold_enabled=True,
    )

    frame_1 = np.array(
        [-90.0, -80.0, -70.0, -30.0, -85.0]
    )

    frame_2 = np.array(
        [-88.0, -82.0, -69.0, -40.0, -84.0]
    )

    frame_3 = np.array(
        [-91.0, -79.0, -71.0, -20.0, -86.0]
    )

    result_1 = processor.process(
        frequencies_hz,
        frame_1,
    )

    result_2 = processor.process(
        frequencies_hz,
        frame_2,
    )

    result_3 = processor.process(
        frequencies_hz,
        frame_3,
    )

    expected_average = np.mean(
        np.stack(
            [
                frame_1,
                frame_2,
                frame_3,
            ],
            axis=0,
        ),
        axis=0,
    )

    expected_max_hold = np.maximum.reduce(
        [
            frame_1,
            frame_2,
            frame_3,
        ]
    )

    print(
        "Current:",
        result_3.current_power_db,
    )

    print(
        "Average:",
        result_3.average_power_db,
    )

    print(
        "Max hold:",
        result_3.max_hold_power_db,
    )

    print(
        "Peak frequency:",
        result_3.peak_frequency_hz,
    )

    print(
        "Peak power:",
        result_3.peak_power_db,
    )

    assert np.allclose(
        result_3.current_power_db,
        frame_3,
    )

    assert np.allclose(
        result_3.average_power_db,
        expected_average,
    )

    assert np.allclose(
        result_3.max_hold_power_db,
        expected_max_hold,
    )

    assert (
        result_3.peak_frequency_hz
        == 100_000.0
    )

    assert (
        result_3.peak_power_db
        == -20.0
    )

    assert processor.average_frame_count == 3
    assert processor.has_max_hold

    processor.reset_average()

    assert processor.average_frame_count == 0

    processor.reset_max_hold()

    assert not processor.has_max_hold

    processor.set_averaging_count(8)

    assert processor.averaging_count == 8

    processor.set_max_hold_enabled(False)

    assert not processor.max_hold_enabled

    print(
        "SpectrumProcessor test passed."
    )


if __name__ == "__main__":
    main()
