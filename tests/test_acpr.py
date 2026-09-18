from __future__ import annotations

import numpy as np

from sdr.analysis.acpr import (
    ACPRAnalyzer,
)


def add_flat_channel(
    frequencies_hz: np.ndarray,
    power_db: np.ndarray,
    *,
    center_frequency_hz: float,
    bandwidth_hz: float,
    bin_power_db: float,
) -> None:
    half_bandwidth_hz = (
        bandwidth_hz / 2.0
    )

    mask = (
        frequencies_hz
        >= center_frequency_hz
        - half_bandwidth_hz
    ) & (
        frequencies_hz
        <= center_frequency_hz
        + half_bandwidth_hz
    )

    power_db[mask] = float(
        bin_power_db
    )


def main() -> None:
    frequencies_hz = np.linspace(
        90_000_000.0,
        110_000_000.0,
        20_001,
    )

    power_db = np.full(
        frequencies_hz.size,
        -130.0,
        dtype=np.float64,
    )

    channel_bandwidth_hz = (
        1_000_000.0
    )

    adjacent_offset_hz = (
        3_000_000.0
    )

    # Main channel
    add_flat_channel(
        frequencies_hz,
        power_db,
        center_frequency_hz=(
            100_000_000.0
        ),
        bandwidth_hz=(
            channel_bandwidth_hz
        ),
        bin_power_db=-50.0,
    )

    # Lower adjacent channel:
    # 30 dB lower per FFT bin.
    add_flat_channel(
        frequencies_hz,
        power_db,
        center_frequency_hz=(
            97_000_000.0
        ),
        bandwidth_hz=(
            channel_bandwidth_hz
        ),
        bin_power_db=-80.0,
    )

    # Upper adjacent channel:
    # 40 dB lower per FFT bin.
    add_flat_channel(
        frequencies_hz,
        power_db,
        center_frequency_hz=(
            103_000_000.0
        ),
        bandwidth_hz=(
            channel_bandwidth_hz
        ),
        bin_power_db=-90.0,
    )

    analyzer = ACPRAnalyzer(
        channel_bandwidth_hz=(
            channel_bandwidth_hz
        ),
        adjacent_offset_hz=(
            adjacent_offset_hz
        ),
    )

    result = analyzer.analyze(
        frequencies_hz,
        power_db,
        main_center_frequency_hz=(
            100_000_000.0
        ),
    )

    print(
        "Main power:",
        result.main_channel.integrated_power_db,
    )

    print(
        "Main bins:",
        result.main_channel.bin_count,
    )

    assert (
        result.lower_adjacent
        is not None
    )

    assert (
        result.upper_adjacent
        is not None
    )

    print(
        "Lower adjacent power:",
        result.lower_adjacent.integrated_power_db,
    )

    print(
        "Upper adjacent power:",
        result.upper_adjacent.integrated_power_db,
    )

    print(
        "Lower ACPR:",
        result.lower_acpr_db,
        "dBc",
    )

    print(
        "Upper ACPR:",
        result.upper_acpr_db,
        "dBc",
    )

    assert (
        result.lower_acpr_db
        is not None
    )

    assert (
        result.upper_acpr_db
        is not None
    )

    assert np.isclose(
        result.lower_acpr_db,
        -30.0,
        atol=0.05,
    )

    assert np.isclose(
        result.upper_acpr_db,
        -40.0,
        atol=0.05,
    )

    assert np.isclose(
        result.main_channel.center_frequency_hz,
        100_000_000.0,
        atol=1_000.0,
    )

    assert np.isclose(
        result.lower_adjacent.center_frequency_hz,
        97_000_000.0,
        atol=1_000.0,
    )

    assert np.isclose(
        result.upper_adjacent.center_frequency_hz,
        103_000_000.0,
        atol=1_000.0,
    )

    print(
        "ACPRAnalyzer test passed."
    )


if __name__ == "__main__":
    main()
