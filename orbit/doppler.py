from __future__ import annotations

from dataclasses import dataclass

SPEED_OF_LIGHT_M_S = 299_792_458.0


@dataclass(frozen=True)
class DopplerResult:
    nominal_frequency_hz: float
    radial_velocity_m_s: float
    doppler_shift_hz: float
    received_frequency_hz: float


class DopplerCalculator:
    """
    Calculate first-order Doppler shift for satellite links.

    Convention:
        radial_velocity_m_s < 0:
            satellite is approaching the observer

        radial_velocity_m_s > 0:
            satellite is moving away from the observer

    Therefore:
        approaching -> positive frequency shift
        receding    -> negative frequency shift
    """

    @staticmethod
    def calculate(
        nominal_frequency_hz: float,
        radial_velocity_m_s: float,
    ) -> DopplerResult:

        nominal_frequency_hz = float(
            nominal_frequency_hz
        )

        radial_velocity_m_s = float(
            radial_velocity_m_s
        )

        if nominal_frequency_hz <= 0.0:
            raise ValueError(
                "nominal_frequency_hz must be greater than zero."
            )

        doppler_shift_hz = (
            -radial_velocity_m_s
            / SPEED_OF_LIGHT_M_S
            * nominal_frequency_hz
        )

        received_frequency_hz = (
            nominal_frequency_hz
            + doppler_shift_hz
        )

        return DopplerResult(
            nominal_frequency_hz=nominal_frequency_hz,
            radial_velocity_m_s=radial_velocity_m_s,
            doppler_shift_hz=doppler_shift_hz,
            received_frequency_hz=received_frequency_hz,
        )
