from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ChannelMeasurement:
    center_frequency_hz: float
    lower_frequency_hz: float
    upper_frequency_hz: float
    bandwidth_hz: float
    integrated_power_db: float
    bin_count: int


@dataclass(frozen=True)
class ACPRResult:
    main_channel: ChannelMeasurement
    lower_adjacent: ChannelMeasurement | None
    upper_adjacent: ChannelMeasurement | None

    lower_acpr_db: float | None
    upper_acpr_db: float | None


class ACPRAnalyzer:
    """
    Adjacent Channel Power Ratio analyzer.

    The analyzer integrates spectrum power in:
        - main channel
        - lower adjacent channel
        - upper adjacent channel

    ACPR is calculated as:

        adjacent_power_db - main_power_db

    The result is therefore normally negative in dBc.
    """

    def __init__(
        self,
        *,
        channel_bandwidth_hz: float,
        adjacent_offset_hz: float,
    ) -> None:
        self._channel_bandwidth_hz = self._validate_positive_float(
            channel_bandwidth_hz,
            "channel_bandwidth_hz",
        )

        self._adjacent_offset_hz = self._validate_positive_float(
            adjacent_offset_hz,
            "adjacent_offset_hz",
        )

    def analyze(
        self,
        frequencies_hz: np.ndarray,
        power_db: np.ndarray,
        *,
        main_center_frequency_hz: float,
    ) -> ACPRResult:
        frequencies_hz, power_db = self._validate_input(
            frequencies_hz,
            power_db,
        )

        main_center_frequency_hz = float(
            main_center_frequency_hz
        )

        if not np.isfinite(
            main_center_frequency_hz
        ):
            raise ValueError(
                "main_center_frequency_hz must be finite."
            )

        main_channel = self._measure_channel(
            frequencies_hz,
            power_db,
            main_center_frequency_hz,
        )

        lower_center_frequency_hz = (
            main_center_frequency_hz
            - self._adjacent_offset_hz
        )

        upper_center_frequency_hz = (
            main_center_frequency_hz
            + self._adjacent_offset_hz
        )

        lower_adjacent = self._try_measure_channel(
            frequencies_hz,
            power_db,
            lower_center_frequency_hz,
        )

        upper_adjacent = self._try_measure_channel(
            frequencies_hz,
            power_db,
            upper_center_frequency_hz,
        )

        if lower_adjacent is None:
            lower_acpr_db = None
        else:
            lower_acpr_db = (
                lower_adjacent.integrated_power_db
                - main_channel.integrated_power_db
            )

        if upper_adjacent is None:
            upper_acpr_db = None
        else:
            upper_acpr_db = (
                upper_adjacent.integrated_power_db
                - main_channel.integrated_power_db
            )

        return ACPRResult(
            main_channel=main_channel,
            lower_adjacent=lower_adjacent,
            upper_adjacent=upper_adjacent,
            lower_acpr_db=(
                None
                if lower_acpr_db is None
                else float(lower_acpr_db)
            ),
            upper_acpr_db=(
                None
                if upper_acpr_db is None
                else float(upper_acpr_db)
            ),
        )

    def _try_measure_channel(
        self,
        frequencies_hz: np.ndarray,
        power_db: np.ndarray,
        center_frequency_hz: float,
    ) -> ChannelMeasurement | None:
        half_bandwidth_hz = (
            self._channel_bandwidth_hz
            / 2.0
        )

        lower_frequency_hz = (
            center_frequency_hz
            - half_bandwidth_hz
        )

        upper_frequency_hz = (
            center_frequency_hz
            + half_bandwidth_hz
        )

        spectrum_min_hz = float(
            np.min(frequencies_hz)
        )

        spectrum_max_hz = float(
            np.max(frequencies_hz)
        )

        if (
            lower_frequency_hz
            < spectrum_min_hz
            or upper_frequency_hz
            > spectrum_max_hz
        ):
            return None

        return self._measure_channel(
            frequencies_hz,
            power_db,
            center_frequency_hz,
        )

    def _measure_channel(
        self,
        frequencies_hz: np.ndarray,
        power_db: np.ndarray,
        center_frequency_hz: float,
    ) -> ChannelMeasurement:
        half_bandwidth_hz = (
            self._channel_bandwidth_hz
            / 2.0
        )

        requested_lower_hz = (
            center_frequency_hz
            - half_bandwidth_hz
        )

        requested_upper_hz = (
            center_frequency_hz
            + half_bandwidth_hz
        )

        mask = (
            (frequencies_hz >= requested_lower_hz)
            & (frequencies_hz <= requested_upper_hz)
        )

        indices = np.flatnonzero(
            mask
        )

        if indices.size == 0:
            raise ValueError(
                "No FFT bins fall inside the requested channel."
            )

        channel_power_db = power_db[
            indices
        ]

        integrated_power_db = self._integrate_log_power(
            channel_power_db
        )

        actual_lower_frequency_hz = float(
            frequencies_hz[
                indices[0]
            ]
        )

        actual_upper_frequency_hz = float(
            frequencies_hz[
                indices[-1]
            ]
        )

        actual_center_frequency_hz = (
            actual_lower_frequency_hz
            + actual_upper_frequency_hz
        ) / 2.0

        actual_bandwidth_hz = (
            actual_upper_frequency_hz
            - actual_lower_frequency_hz
        )

        return ChannelMeasurement(
            center_frequency_hz=float(
                actual_center_frequency_hz
            ),
            lower_frequency_hz=(
                actual_lower_frequency_hz
            ),
            upper_frequency_hz=(
                actual_upper_frequency_hz
            ),
            bandwidth_hz=float(
                actual_bandwidth_hz
            ),
            integrated_power_db=float(
                integrated_power_db
            ),
            bin_count=int(
                indices.size
            ),
        )

    @staticmethod
    def _integrate_log_power(
        power_db: np.ndarray,
    ) -> float:
        """
        Numerically stable logarithmic power integration.
        """
        reference_power_db = float(
            np.max(power_db)
        )

        relative_linear_power = np.power(
            10.0,
            (
                power_db
                - reference_power_db
            ) / 10.0,
        )

        total_relative_power = float(
            np.sum(
                relative_linear_power
            )
        )

        if (
            not np.isfinite(
                total_relative_power
            )
            or total_relative_power <= 0.0
        ):
            raise ValueError(
                "Integrated power is invalid."
            )

        return (
            reference_power_db
            + 10.0
            * np.log10(
                total_relative_power
            )
        )

    @staticmethod
    def _validate_positive_float(
        value: float,
        name: str,
    ) -> float:
        value = float(value)

        if not np.isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )

        if value <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

        return value

    @staticmethod
    def _validate_input(
        frequencies_hz: np.ndarray,
        power_db: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        frequencies_hz = np.asarray(
            frequencies_hz,
            dtype=np.float64,
        )

        power_db = np.asarray(
            power_db,
            dtype=np.float64,
        )

        if frequencies_hz.ndim != 1:
            raise ValueError(
                "frequencies_hz must be one-dimensional."
            )

        if power_db.ndim != 1:
            raise ValueError(
                "power_db must be one-dimensional."
            )

        if frequencies_hz.size < 3:
            raise ValueError(
                "Spectrum must contain at least three bins."
            )

        if frequencies_hz.size != power_db.size:
            raise ValueError(
                "Frequency and power arrays must have equal size."
            )

        if not np.all(
            np.isfinite(
                frequencies_hz
            )
        ):
            raise ValueError(
                "Frequency array contains invalid values."
            )

        if not np.all(
            np.isfinite(
                power_db
            )
        ):
            raise ValueError(
                "Power array contains invalid values."
            )

        return (
            frequencies_hz,
            power_db,
        )
