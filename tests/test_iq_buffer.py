import numpy as np

from sdr.iq_buffer import IQCircularBuffer
from sdr.simulator import SDRSimulator
from sdr.spectrum import SpectrumAnalyzer


def main() -> None:
    sample_rate_hz = 1_000_000
    tone_frequency_hz = 100_000
    fft_size = 4096
    buffer_capacity = 16_384

    simulator = SDRSimulator(
        sample_rate_hz=sample_rate_hz,
        center_frequency_hz=437_000_000,
        tone_frequency_hz=tone_frequency_hz,
        signal_amplitude=1.0,
        noise_power=0.02,
        seed=42,
    )

    iq_buffer = IQCircularBuffer(
        capacity=buffer_capacity
    )

    simulator.start()

    print("SDR running:", simulator.is_running())
    print("Sample rate:", simulator.sample_rate())
    print(
        "Center frequency:",
        simulator.center_frequency(),
    )
    print("Buffer capacity:", iq_buffer.capacity)

    for block_index in range(6):
        samples = simulator.read_samples(2048)
        written = iq_buffer.write(samples)

        print(
            f"Block {block_index + 1}: "
            f"written={written}, "
            f"buffer_size={iq_buffer.size}, "
            f"free_space={iq_buffer.free_space}"
        )

    latest_samples = iq_buffer.read_latest(
        fft_size
    )

    frequencies_hz, power_db = (
        SpectrumAnalyzer.compute_fft(
            latest_samples,
            simulator.sample_rate(),
        )
    )

    peak_index = int(np.argmax(power_db))

    peak_frequency_hz = frequencies_hz[
        peak_index
    ]
    peak_power_db = power_db[peak_index]

    print()
    print("Latest IQ samples:", latest_samples[:5])
    print(
        "Peak frequency [Hz]:",
        peak_frequency_hz,
    )
    print(
        "Peak power [dB]:",
        peak_power_db,
    )
    print(
        "Total samples written:",
        iq_buffer.total_samples_written,
    )

    expected_frequency_error = abs(
        peak_frequency_hz
        - tone_frequency_hz
    )

    fft_resolution_hz = (
        sample_rate_hz / fft_size
    )

    assert latest_samples.dtype == np.complex64
    assert iq_buffer.size == 12_288
    assert expected_frequency_error <= (
        fft_resolution_hz
    )

    simulator.stop()

    print()
    print("SDR running:", simulator.is_running())
    print("IQ Circular Buffer test passed.")


if __name__ == "__main__":
    main()