class DopplerCalculator:
    SPEED_OF_LIGHT = 299_792_458  # m/s

    @staticmethod
    def compute_hz(range_rate_m_s: float, carrier_frequency_hz: float) -> float:
        """
        Positive Doppler means the satellite is approaching.
        Negative Doppler means the satellite is moving away.
        """
        return -range_rate_m_s / DopplerCalculator.SPEED_OF_LIGHT * carrier_frequency_hz

    @staticmethod
    def compute_khz(range_rate_m_s: float, carrier_frequency_hz: float) -> float:
        return DopplerCalculator.compute_hz(range_rate_m_s, carrier_frequency_hz) / 1000