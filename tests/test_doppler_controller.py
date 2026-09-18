from __future__ import annotations

from orbit.doppler_controller import (
    DopplerController,
)
from orbit.tracker import Tracker


class FakeReceiver:
    """
    Minimal SDR receiver used to verify tuning.
    """

    def __init__(self) -> None:
        self.center_frequency_hz: float | None = None
        self.tune_count = 0

    def set_center_frequency(
        self,
        frequency_hz: float,
    ) -> None:

        self.center_frequency_hz = float(
            frequency_hz
        )

        self.tune_count += 1


def main() -> None:

    tracker = Tracker(
        "ISS"
    )

    receiver = FakeReceiver()

    nominal_frequency_hz = (
        437_800_000.0
    )

    controller = DopplerController(
        tracker=tracker,
        receiver=receiver,
        nominal_frequency_hz=(
            nominal_frequency_hz
        ),
        enabled=True,
        tune_only_when_visible=False,
    )

    state = controller.update()

    print(
        "Satellite:",
        tracker.satellite_name,
    )

    print(
        "Visible:",
        state.visible,
    )

    print(
        "Azimuth:",
        state.azimuth_deg,
        "deg",
    )

    print(
        "Elevation:",
        state.elevation_deg,
        "deg",
    )

    print(
        "Range:",
        state.range_km,
        "km",
    )

    print(
        "Range rate:",
        state.range_rate_m_s,
        "m/s",
    )

    print(
        "Nominal RX:",
        state.nominal_frequency_hz,
        "Hz",
    )

    print(
        "Doppler:",
        state.doppler_shift_hz,
        "Hz",
    )

    print(
        "Corrected RX:",
        state.corrected_frequency_hz,
        "Hz",
    )

    print(
        "Receiver tuned to:",
        receiver.center_frequency_hz,
        "Hz",
    )

    print(
        "Tune count:",
        receiver.tune_count,
    )

    assert receiver.tune_count == 1

    assert (
        receiver.center_frequency_hz
        == state.corrected_frequency_hz
    )

    assert (
        abs(
            state.corrected_frequency_hz
            - (
                state.nominal_frequency_hz
                + state.doppler_shift_hz
            )
        )
        < 1e-6
    )

    # --------------------------------------------------------
    # Disable automatic Doppler tuning.
    # --------------------------------------------------------

    controller.set_enabled(
        False
    )

    previous_tune_count = (
        receiver.tune_count
    )

    controller.update()

    assert (
        receiver.tune_count
        == previous_tune_count
    )

    # --------------------------------------------------------
    # Restore nominal frequency.
    # --------------------------------------------------------

    controller.tune_nominal()

    assert (
        receiver.center_frequency_hz
        == nominal_frequency_hz
    )

    print()
    print(
        "DopplerController test passed."
    )


if __name__ == "__main__":
    main()
