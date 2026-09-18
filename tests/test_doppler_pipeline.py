from __future__ import annotations

from orbit.doppler_controller import DopplerController
from orbit.tracker import Tracker

from sdr.pipeline import SDRPipeline
from sdr.simulator import SDRSimulator


def main() -> None:
    nominal_frequency_hz = 437_800_000.0

    simulator = SDRSimulator(
        sample_rate_hz=1_000_000.0,
        center_frequency_hz=nominal_frequency_hz,
        tone_frequency_hz=100_000.0,
        signal_amplitude=1.0,
        noise_power=0.02,
        seed=42,
    )

    pipeline = SDRPipeline(
        device=simulator,
        buffer_capacity=65_536,
        acquisition_block_size=2048,
        fft_size=4096,
    )

    tracker = Tracker(
        "ISS"
    )

    controller = DopplerController(
        tracker=tracker,
        receiver=pipeline,
        nominal_frequency_hz=nominal_frequency_hz,
        enabled=True,
        tune_only_when_visible=False,
    )

    pipeline.start()

    print(
        "Pipeline frequency before Doppler:",
        pipeline.center_frequency_hz,
    )

    state = controller.update()

    print()
    print(
        "Satellite:",
        tracker.satellite_name,
    )

    print(
        "Visible:",
        state.visible,
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

    print()
    print(
        "Nominal frequency:",
        state.nominal_frequency_hz,
        "Hz",
    )

    print(
        "Doppler shift:",
        state.doppler_shift_hz,
        "Hz",
    )

    print(
        "Corrected frequency:",
        state.corrected_frequency_hz,
        "Hz",
    )

    print(
        "Pipeline frequency after Doppler:",
        pipeline.center_frequency_hz,
        "Hz",
    )

    frequency_error_hz = abs(
        pipeline.center_frequency_hz
        - state.corrected_frequency_hz
    )

    print(
        "Tuning error:",
        frequency_error_hz,
        "Hz",
    )

    assert frequency_error_hz < 1e-6

    controller.set_enabled(
        False
    )

    frequency_before_disabled_update = (
        pipeline.center_frequency_hz
    )

    controller.update()

    assert (
        pipeline.center_frequency_hz
        == frequency_before_disabled_update
    )

    controller.tune_nominal()

    assert (
        abs(
            pipeline.center_frequency_hz
            - nominal_frequency_hz
        )
        < 1e-6
    )

    pipeline.stop()

    print()
    print(
        "DopplerController + SDRPipeline test passed."
    )


if __name__ == "__main__":
    main()
