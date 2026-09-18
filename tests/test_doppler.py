from __future__ import annotations

import math

from orbit.doppler import DopplerCalculator


def main() -> None:

    nominal_frequency_hz = 437_500_000.0

    # Satellite approaching at 6 km/s
    approaching = DopplerCalculator.calculate(
        nominal_frequency_hz,
        -6000.0,
    )

    print("Approaching satellite")
    print(
        "Nominal:",
        approaching.nominal_frequency_hz,
        "Hz",
    )
    print(
        "Velocity:",
        approaching.radial_velocity_m_s,
        "m/s",
    )
    print(
        "Doppler:",
        approaching.doppler_shift_hz,
        "Hz",
    )
    print(
        "Received:",
        approaching.received_frequency_hz,
        "Hz",
    )

    assert approaching.doppler_shift_hz > 0.0
    assert (
        approaching.received_frequency_hz
        > nominal_frequency_hz
    )

    # Closest approach
    zero_velocity = DopplerCalculator.calculate(
        nominal_frequency_hz,
        0.0,
    )

    assert math.isclose(
        zero_velocity.doppler_shift_hz,
        0.0,
        abs_tol=1e-12,
    )

    assert math.isclose(
        zero_velocity.received_frequency_hz,
        nominal_frequency_hz,
    )

    # Satellite receding at 6 km/s
    receding = DopplerCalculator.calculate(
        nominal_frequency_hz,
        6000.0,
    )

    print()
    print("Receding satellite")
    print(
        "Doppler:",
        receding.doppler_shift_hz,
        "Hz",
    )
    print(
        "Received:",
        receding.received_frequency_hz,
        "Hz",
    )

    assert receding.doppler_shift_hz < 0.0
    assert (
        receding.received_frequency_hz
        < nominal_frequency_hz
    )

    assert math.isclose(
        approaching.doppler_shift_hz,
        -receding.doppler_shift_hz,
        rel_tol=1e-12,
    )

    print()
    print("DopplerCalculator test passed.")


if __name__ == "__main__":
    main()
