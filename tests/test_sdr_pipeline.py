import numpy as np

from sdr.pipeline import SDRPipeline
from sdr.simulator import SDRSimulator


def main() -> None:
    sample_rate_hz = 1_000_000
    center_frequency_hz = 437_000_000
    tone_frequency_hz = 100_000

    simulator = SDRSimulator(
        sample_rate_hz=sample_rate_hz,
        center_frequency_hz=center_frequency_hz,
        tone_frequency_hz=tone_frequency_hz,
        signal_amplitude=1.0,
        noise_power=0.02,
        seed=42,
    )

    pipeline = SDRPipeline(
        device=simulator,
        buffer_capacity=16_384,
        acquisition_block_size=2048,
        fft_size=4096,
    )

    pipeline.start()

    print("Pipeline running:", pipeline.is_running)
    print("Sample rate:", pipeline.sample_rate_hz)
    print(
        "Center frequency:",
        pipeline.center_frequency_hz,
    )

    for update_index in range(4):
        spectrum_ready = pipeline.update()

        print(
            f"Update {update_index + 1}: "
            f"buffered={pipeline.buffered_samples}, "
            f"spectrum_ready={spectrum_ready}"
        )

    frequencies_hz, power_db = (
        pipeline.latest_spectrum(update=False)
    )

    assert frequencies_hz.size == 4096
    assert power_db.size == 4096

    peak_index = int(np.argmax(power_db))
    peak_frequency_hz = float(
        frequencies_hz[peak_index]
    )

    peak_power_db = float(
        power_db[peak_index]
    )

    fft_resolution_hz = (
        sample_rate_hz / pipeline.fft_size
    )

    frequency_error_hz = abs(
        peak_frequency_hz
        - tone_frequency_hz
    )

    print()
    print(
        "Peak baseband frequency [Hz]:",
        peak_frequency_hz,
    )
    print(
        "Peak RF frequency [Hz]:",
        center_frequency_hz
        + peak_frequency_hz,
    )
    print(
        "Peak power [dB]:",
        peak_power_db,
    )
    print(
        "Pipeline peak property [Hz]:",
        pipeline.latest_peak_frequency_hz,
    )

    assert frequency_error_hz <= fft_resolution_hz
    assert pipeline.latest_peak_frequency_hz is not None
    assert pipeline.latest_peak_power_db is not None

    iq_samples = pipeline.latest_iq(4096)

    assert iq_samples.size == 4096
    assert iq_samples.dtype == np.complex64

    pipeline.stop()

    assert not pipeline.is_running

    print()
    print("Pipeline running:", pipeline.is_running)
    print("SDR Pipeline test passed.")


if __name__ == "__main__":
    main()
