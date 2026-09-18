from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class HarmonicMeasurement:
    order: int
    expected_frequency_hz: float
    measured_frequency_hz: float | None
    power_db: float | None
    relative_power_dbc: float | None
    frequency_error_hz: float | None
    detected: bool


@dataclass(frozen=True)
class HarmonicAnalysisResult:
    fundamental_frequency_hz: float
    fundamental_power_db: float
    measurements: tuple[HarmonicMeasurement, ...]


class HarmonicAnalyzer:
    """
    Detect a fundamental signal and its harmonics in an FFT spectrum.

    The input frequency axis must contain absolute positive RF
    frequencies when analysing ordinary RF harmonics.
    """

    def __init__(
        self,
        *,
        maximum_order: int = 5,
        search_radius_bins: int = 20,
        minimum_relative_power_dbc: float = -80.0,
    ) -> None:
        if maximum_order < 1:
            raise ValueError(
                "maximum_order must be at least 1."
            )

        if search_radius_bins < 0:
            raise ValueError(
                "search_radius_bins must not be negative."
            )

        self._maximum_order = int(maximum_order)
        self._search_radius_bins = int(
            search_radius_bins
        )
        self._minimum_relative_power_dbc = float(
            minimum_relative_power_dbc
        )

    def analyze(
        self,
        frequencies_hz: np.ndarray,
        power_db: np.ndarray,
        *,
        fundamental_frequency_hz: float | None = None,
    ) -> HarmonicAnalysisResult:
        frequencies_hz, power_db = self._validate(
            frequencies_hz,
            power_db,
        )

        if fundamental_frequency_hz is None:
            fundamental_index = int(
                np.argmax(power_db)
            )
        else:
            fundamental_index = self._find_local_peak(
                frequencies_hz,
                power_db,
                float(fundamental_frequency_hz),
            )

        fundamental_frequency_hz = float(
            frequencies_hz[fundamental_index]
        )

        fundamental_power_db = float(
            power_db[fundamental_index]
        )

        measurements: list[HarmonicMeasurement] = []

        minimum_frequency_hz = float(
            np.min(frequencies_hz)
        )

        maximum_frequency_hz = float(
            np.max(frequencies_hz)
        )

        for order in range(
            1,
            self._maximum_order + 1,
        ):
            expected_frequency_hz = (
                fundamental_frequency_hz
                * order
            )

            if not (
                minimum_frequency_hz
                <= expected_frequency_hz
                <= maximum_frequency_hz
            ):
                measurements.append(
                    HarmonicMeasurement(
                        order=order,
                        expected_frequency_hz=(
                            expected_frequency_hz
                        ),
                        measured_frequency_hz=None,
                        power_db=None,
                        relative_power_dbc=None,
                        frequency_error_hz=None,
                        detected=False,
                    )
                )
                continue

            peak_index = self._find_local_peak(
                frequencies_hz,
                power_db,
                expected_frequency_hz,
            )

            measured_frequency_hz = float(
                frequencies_hz[peak_index]
            )

            measured_power_db = float(
                power_db[peak_index]
            )

            relative_power_dbc = (
                measured_power_db
                - fundamental_power_db
            )

            detected = (
                order == 1
                or relative_power_dbc
                >= self._minimum_relative_power_dbc
            )

            measurements.append(
                HarmonicMeasurement(
                    order=order,
                    expected_frequency_hz=(
                        expected_frequency_hz
                    ),
                    measured_frequency_hz=(
                        measured_frequency_hz
                    ),
                    power_db=measured_power_db,
                    relative_power_dbc=(
                        relative_power_dbc
                    ),
                    frequency_error_hz=(
                        measured_frequency_hz
                        - expected_frequency_hz
                    ),
                    detected=detected,
                )
            )

        return HarmonicAnalysisResult(
            fundamental_frequency_hz=(
                fundamental_frequency_hz
            ),
            fundamental_power_db=(
                fundamental_power_db
            ),
            measurements=tuple(measurements),
        )

    def _find_local_peak(
        self,
        frequencies_hz: np.ndarray,
        power_db: np.ndarray,
        requested_frequency_hz: float,
    ) -> int:
        nearest_index = int(
            np.argmin(
                np.abs(
                    frequencies_hz
                    - requested_frequency_hz
                )
            )
        )

        start = max(
            0,
            nearest_index - self._search_radius_bins,
        )

        stop = min(
            power_db.size,
            nearest_index
            + self._search_radius_bins
            + 1,
        )

        local_index = int(
            np.argmax(
                power_db[start:stop]
            )
        )

        return start + local_index

    @staticmethod
    def _validate(
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

        if not np.all(np.isfinite(frequencies_hz)):
            raise ValueError(
                "Frequency array contains invalid values."
            )

        if not np.all(np.isfinite(power_db)):
            raise ValueError(
                "Power array contains invalid values."
            )

        return frequencies_hz, power_db
