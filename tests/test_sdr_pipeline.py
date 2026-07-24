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

    print("Pipeline object:")
    print(pipeline)
    print()

    pipeline.start()

    assert pipeline.is_running

    print("Pipeline running:", pipeline.is_running)
    print("Sample rate:", pipeline.sample_rate_hz)
    print(
        "Center frequency:",
        pipeline.center_frequency_hz,
    )
    print(
        "Buffer capacity:",
        pipeline.buffer_capacity,
    )
    print(
        "Acquisition block size:",
        pipeline.acquisition_block_size,
    )
    print("FFT size:", pipeline.fft_size)
    print()

    for index in range(4):
        spectrum_ready = pipeline.update()

        print(
            f"Update {index + 1}: "
            f"buffered={pipeline.buffered_samples}, "
            f"spectrum_ready={spectrum_ready}"
        )

    assert pipeline.has_spectrum()

    frequencies_hz, power_db = (
        pipeline.latest_spectrum(update=False)
    )

    assert frequencies_hz.size == pipeline.fft_size
    assert power_db.size == pipeline.fft_size

    peak_index = int(np.argmax(power_db))

    measured_peak_frequency_hz = float(
        frequencies_hz[peak_index]
    )

    measured_peak_power_db = float(
        power_db[peak_index]
    )

    fft_resolution_hz = (
        sample_rate_hz / pipeline.fft_size
    )

    frequency_error_hz = abs(
        measured_peak_frequency_hz
        - tone_frequency_hz
    )

    print()
    print(
        "Measured baseband peak [Hz]:",
        measured_peak_frequency_hz,
    )
    print(
        "Measured RF peak [Hz]:",
        center_frequency_hz
        + measured_peak_frequency_hz,
    )
    print(
        "Measured peak power [dB]:",
        measured_peak_power_db,
    )
    print(
        "Pipeline baseband peak [Hz]:",
        pipeline.latest_peak_frequency_hz,
    )
    print(
        "Pipeline RF peak [Hz]:",
        pipeline.latest_peak_rf_frequency_hz,
    )
    print(
        "Pipeline peak power [dB]:",
        pipeline.latest_peak_power_db,
    )
    print(
        "FFT resolution [Hz]:",
        fft_resolution_hz,
    )
    print(
        "Frequency error [Hz]:",
        frequency_error_hz,
    )

    assert frequency_error_hz <= fft_resolution_hz

    assert (
        pipeline.latest_peak_frequency_hz
        is not None
    )

    assert pipeline.latest_peak_power_db is not None

    rf_frequencies_hz, rf_power_db = (
        pipeline.latest_rf_spectrum(
            update=False
        )
    )

    assert rf_frequencies_hz.size == pipeline.fft_size
    assert rf_power_db.size == pipeline.fft_size

    latest_iq = pipeline.latest_iq(
        pipeline.fft_size
    )

    assert latest_iq.size == pipeline.fft_size
    assert np.iscomplexobj(latest_iq)

    print()
    print(
        "Latest IQ samples:",
        latest_iq.size,
    )
    print(
        "Acquisition cycles:",
        pipeline.total_acquisition_cycles,
    )
    print(
        "Samples acquired:",
        pipeline.total_samples_acquired,
    )
    print(
        "Spectra computed:",
        pipeline.total_spectra_computed,
    )

    # Check backward-compatible acquire() API.
    acquire_result = pipeline.acquire()

    assert isinstance(acquire_result, int)
    assert acquire_result == pipeline.acquisition_block_size

    print(
        "Direct acquire sample count:",
     acquire_result,
)

    pipeline.stop()

    assert not pipeline.is_running

    print()
    print("Pipeline running:", pipeline.is_running)
    print("SDR Pipeline test passed.")


if __name__ == "__main__":
    main()