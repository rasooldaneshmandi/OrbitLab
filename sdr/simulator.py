import numpy as np

from sdr.device import ComplexArray, SDRDevice


class SDRSimulator(SDRDevice):
    """
    Virtual SDR device that generates a complex baseband tone
    with additive Gaussian noise.
    """

    def __init__(
        self,
        sample_rate_hz: float = 1_000_000.0,
        center_frequency_hz: float = 437_000_000.0,
        tone_frequency_hz: float = 100_000.0,
        signal_amplitude: float = 1.0,
        noise_power: float = 0.02,
        seed: int | None = None,
    ) -> None:
        if sample_rate_hz <= 0:
            raise ValueError(
                "sample_rate_hz must be greater than zero."
            )

        if center_frequency_hz <= 0:
            raise ValueError(
                "center_frequency_hz must be greater than zero."
            )

        if signal_amplitude < 0:
            raise ValueError(
                "signal_amplitude cannot be negative."
            )

        if noise_power < 0:
            raise ValueError(
                "noise_power cannot be negative."
            )

        nyquist_frequency_hz = sample_rate_hz / 2.0

        if abs(tone_frequency_hz) >= nyquist_frequency_hz:
            raise ValueError(
                "tone_frequency_hz must be inside the Nyquist range."
            )

        self._sample_rate_hz = float(sample_rate_hz)
        self._center_frequency_hz = float(center_frequency_hz)
        self._tone_frequency_hz = float(tone_frequency_hz)
        self._signal_amplitude = float(signal_amplitude)
        self._noise_power = float(noise_power)

        self._phase_radians = 0.0
        self._running = False

        self._random_generator = np.random.default_rng(seed)

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def sample_rate(self) -> float:
        return self._sample_rate_hz

    def center_frequency(self) -> float:
        return self._center_frequency_hz

    def set_center_frequency(
        self,
        frequency_hz: float,
    ) -> None:
        if frequency_hz <= 0:
            raise ValueError(
                "Center frequency must be greater than zero."
            )

        self._center_frequency_hz = float(frequency_hz)

    def tone_frequency(self) -> float:
        return self._tone_frequency_hz

    def set_tone_frequency(
        self,
        frequency_hz: float,
    ) -> None:
        nyquist_frequency_hz = self._sample_rate_hz / 2.0

        if abs(frequency_hz) >= nyquist_frequency_hz:
            raise ValueError(
                "Tone frequency must be inside the Nyquist range."
            )

        self._tone_frequency_hz = float(frequency_hz)

    def read_samples(
        self,
        num_samples: int,
    ) -> ComplexArray:
        if not isinstance(num_samples, int):
            raise TypeError(
                "num_samples must be an integer."
            )

        if num_samples <= 0:
            raise ValueError(
                "num_samples must be greater than zero."
            )

        if not self._running:
            self.start()

        sample_indices = np.arange(
            num_samples,
            dtype=np.float64,
        )

        phase_increment = (
            2.0
            * np.pi
            * self._tone_frequency_hz
            / self._sample_rate_hz
        )

        phases = (
            self._phase_radians
            + phase_increment * sample_indices
        )

        signal = (
            self._signal_amplitude
            * np.exp(1j * phases)
        )

        noise_standard_deviation = np.sqrt(
            self._noise_power / 2.0
        )

        noise = noise_standard_deviation * (
            self._random_generator.standard_normal(
                num_samples
            )
            + 1j
            * self._random_generator.standard_normal(
                num_samples
            )
        )

        self._phase_radians = float(
            (
                phases[-1]
                + phase_increment
            )
            % (2.0 * np.pi)
        )

        iq_samples = signal + noise

        return np.asarray(
            iq_samples,
            dtype=np.complex64,
        )

    def reset_phase(self) -> None:
        self._phase_radians = 0.0