from __future__ import annotations

from orbit.tracker import Tracker


def main() -> None:

    tracker = Tracker(
        "ISS"
    )

    print(
        "Satellite:",
        tracker.satellite_name,
    )

    print(
        "Ground station:",
        tracker.latitude_deg,
        tracker.longitude_deg,
        tracker.elevation_m,
    )

    state = tracker.state()

    print()
    print("Satellite geometry")
    print(
        "Azimuth [deg]:",
        state.azimuth_deg,
    )
    print(
        "Elevation [deg]:",
        state.elevation_deg,
    )
    print(
        "Range [km]:",
        state.range_km,
    )
    print(
        "Range rate [m/s]:",
        state.range_rate_m_s,
    )
    print(
        "Visible:",
        state.visible,
    )

    radio = tracker.radio_state(
        437_800_000.0
    )

    print()
    print("Radio state")

    print(
        "Nominal RX [Hz]:",
        radio.doppler.nominal_frequency_hz,
    )

    print(
        "Doppler [Hz]:",
        radio.doppler.doppler_shift_hz,
    )

    print(
        "Corrected RX [Hz]:",
        radio.doppler.received_frequency_hz,
    )

    assert (
        0.0
        <= state.azimuth_deg
        <= 360.0
    )

    assert (
        -90.0
        <= state.elevation_deg
        <= 90.0
    )

    assert state.range_km > 0.0

    assert (
        abs(
            state.range_rate_m_s
        )
        < 20_000.0
    )

    assert (
        radio.doppler.nominal_frequency_hz
        == 437_800_000.0
    )

    print()
    print(
        "Tracker + Doppler test passed."
    )


if __name__ == "__main__":
    main()
