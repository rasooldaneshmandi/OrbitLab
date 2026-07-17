import numpy as np

from sdr.device import SDRDevice


class SDRSimulator(SDRDevice):
    def __init__(
        self,
        sample_rate_hz=1_000_000,
        tone_frequency_hz=100_000,
        noise_power=0.02,
    ):
        self.fs = sample_rate_hz
        self.f0 = tone_frequency_hz
        self.noise_power = noise_power
        self.phase = 0.0

    def sample_rate(self):
        return self.fs

    def read_samples(self, num_samples: int):
        n = np.arange(num_samples)

        phase_increment = 2 * np.pi * self.f0 / self.fs

        phase = self.phase + phase_increment * n

        signal = np.exp(1j * phase)

        noise = np.sqrt(self.noise_power) * (
            np.random.randn(num_samples) + 1j * np.random.randn(num_samples)
        )

        self.phase = (phase[-1] + phase_increment) % (2 * np.pi)

        return signal + noise