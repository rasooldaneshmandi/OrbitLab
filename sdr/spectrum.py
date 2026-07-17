import numpy as np


class SpectrumAnalyzer:
    @staticmethod
    def compute_fft(iq_samples, sample_rate_hz):
        window = np.hanning(len(iq_samples))
        samples = iq_samples * window

        spectrum = np.fft.fftshift(np.fft.fft(samples))
        power_db = 20 * np.log10(np.abs(spectrum) + 1e-12)

        freqs = np.fft.fftshift(
            np.fft.fftfreq(len(iq_samples), d=1 / sample_rate_hz)
        )

        return freqs, power_db