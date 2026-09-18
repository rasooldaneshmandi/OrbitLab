from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SpectrumProcessingResult:
    """
    Result produced by SpectrumProcessor.
    """

    current_power_db: np.ndarray
    average_power_db: np.ndarray
    max_hold_power_db: np.ndarray
    peak_frequency_hz: float
    peak_power_db: float


class SpectrumProcessor:
    """
    Stateful spectrum post-processor.

    Features:
        - Moving FFT average
        - Max hold
        - Peak detection
        - Automatic reset when FFT shape or frequency axis changes

    Power values are expected in dB.
    """

    def __init__(
        self,
        *,
        averaging_count: int = 1,
        max_hold_enabled: bool = True,
    ) -> None:
        self._averaging_count = self._validate_averaging_count(
            averaging_count
        )

        self._max_hold_enabled = bool(
            max_hold_enabled
        )

        self._average_history: deque[np.ndarray] = deque(
            maxlen=self._averaging_count
        )

        self._max_hold_power_db: np.ndarray | None = None
        self._reference_frequencies_hz: np.ndarray | None = None

    @staticmethod
    def _validate_averaging_count(
        averaging_count: int,
    ) -> int:
        if isinstance(averaging_count, bool) or not isinstance(
            averaging_count,
            int,
        ):
            raise TypeError(
                "averaging_count must be an integer."
            )

        if averaging_count <= 0:
            raise ValueError(
                "averaging_count must be greater than zero."
            )

        return averaging_count

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

        if frequencies_hz.size == 0:
            raise ValueError(
                "frequencies_hz must not be empty."
            )

        if power_db.size == 0:
            raise ValueError(
                "power_db must not be empty."
            )

        if frequencies_hz.size != power_db.size:
            raise ValueError(
                "frequencies_hz and power_db must have "
                "the same number of elements."
            )

        if not np.all(
            np.isfinite(frequencies_hz)
        ):
            raise ValueError(
                "frequencies_hz contains invalid values."
            )

        if not np.all(
            np.isfinite(power_db)
        ):
            raise ValueError(
                "power_db contains invalid values."
            )

        return frequencies_hz, power_db

    def process(
        self,
        frequencies_hz: np.ndarray,
        power_db: np.ndarray,
    ) -> SpectrumProcessingResult:
        frequencies_hz, power_db = self._validate_input(
            frequencies_hz,
            power_db,
        )

        if self._configuration_changed(
            frequencies_hz
        ):
            self.reset()

        self._reference_frequencies_hz = (
            frequencies_hz.copy()
        )

        current_power_db = power_db.copy()

        self._average_history.append(
            current_power_db
        )

        history_matrix = np.stack(
            tuple(self._average_history),
            axis=0,
        )

        average_power_db = np.mean(
            history_matrix,
            axis=0,
        )

        if self._max_hold_enabled:
            if self._max_hold_power_db is None:
                self._max_hold_power_db = (
                    current_power_db.copy()
                )
            else:
                self._max_hold_power_db = np.maximum(
                    self._max_hold_power_db,
                    current_power_db,
                )
        else:
            self._max_hold_power_db = (
                current_power_db.copy()
            )

        peak_index = int(
            np.argmax(current_power_db)
        )

        peak_frequency_hz = float(
            frequencies_hz[peak_index]
        )

        peak_power_db = float(
            current_power_db[peak_index]
        )

        return SpectrumProcessingResult(
            current_power_db=current_power_db,
            average_power_db=average_power_db.copy(),
            max_hold_power_db=self._max_hold_power_db.copy(),
            peak_frequency_hz=peak_frequency_hz,
            peak_power_db=peak_power_db,
        )

    def _configuration_changed(
        self,
        frequencies_hz: np.ndarray,
    ) -> bool:
        if self._reference_frequencies_hz is None:
            return False

        if (
            self._reference_frequencies_hz.shape
            != frequencies_hz.shape
        ):
            return True

        return not np.allclose(
            self._reference_frequencies_hz,
            frequencies_hz,
            rtol=1e-9,
            atol=1e-6,
        )

    def set_averaging_count(
        self,
        averaging_count: int,
    ) -> None:
        averaging_count = self._validate_averaging_count(
            averaging_count
        )

        if averaging_count == self._averaging_count:
            return

        old_history = list(
            self._average_history
        )

        self._averaging_count = averaging_count

        self._average_history = deque(
            old_history[-averaging_count:],
            maxlen=averaging_count,
        )

    def set_max_hold_enabled(
        self,
        enabled: bool,
    ) -> None:
        self._max_hold_enabled = bool(
            enabled
        )

        if not self._max_hold_enabled:
            self._max_hold_power_db = None

    def reset_average(self) -> None:
        self._average_history.clear()

    def reset_max_hold(self) -> None:
        self._max_hold_power_db = None

    def reset(self) -> None:
        self._average_history.clear()
        self._max_hold_power_db = None
        self._reference_frequencies_hz = None

    @property
    def averaging_count(self) -> int:
        return self._averaging_count

    @property
    def max_hold_enabled(self) -> bool:
        return self._max_hold_enabled

    @property
    def average_frame_count(self) -> int:
        return len(
            self._average_history
        )

    @property
    def has_max_hold(self) -> bool:
        return self._max_hold_power_db is not None

    @property
    def max_hold_power_db(
        self,
    ) -> np.ndarray | None:
        if self._max_hold_power_db is None:
            return None

        return self._max_hold_power_db.copy()
