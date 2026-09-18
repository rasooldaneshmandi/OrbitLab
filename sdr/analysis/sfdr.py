from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SFDRResult:
    fundamental_frequency_hz: float
    fundamental_power_db: float

    spur_frequency_hz: float | None
    spur_power_db: float | None

    sfdr_db: float | None

    fundamental_bin_index: int
    spur_bin_index: int | None


class SFDRAnalyzer:
    """
    Estimate Spurious-Free Dynamic Range from a spectrum.

    SFDR is defined as:

        fundamental_power_db - strongest_spur_power_db

    A guard region around the fundamental is excluded so that
    the main lobe is not incorrectly detected as a spur.
    """

    def __init__(
        self,
        *,
        fundamental_guard_bins: int = 20,
        minimum_spur_power_db: float = -140.0,
    ) -> None:
        if (
            isinstance(fundamental_guard_bins, bool)
            or not isinstance(fundamental_guard_bins, int)
        ):
            raise TypeError(
                "fundamental_guard_bins must be an integer."
            )

        if fundamental_guard_bins < 0:
            raise ValueError(
                "fundamental_guard_bins must not be negative."
            )

        self._fundamental_guard_bins = (
            fundamental_guard_bins
        )

        self._minimum_spur_power_db = float(
            minimum_spur_power_db
        )

    def analyze(
        self,
        frequencies_hz: np.ndarray,
        power_db: np.ndarray,
        *,
        fundamental_frequency_hz: float | None = None,
    ) -> SFDRResult:
        frequencies_hz, power_db = (
            self._validate_input(
                frequencies_hz,
                power_db,
            )
        )

        if fundamental_frequency_hz is None:
            fundamental_index = int(
                np.argmax(power_db)
            )
        else:
            fundamental_index = int(
                np.argmin(
                    np.abs(
                        frequencies_hz
                        - float(
                            fundamental_frequency_hz
                        )
                    )
                )
            )

        fundamental_frequency_hz = float(
            frequencies_hz[
                fundamental_index
            ]
        )

        fundamental_power_db = float(
            power_db[
                fundamental_index
            ]
        )

        spur_mask = np.ones(
            power_db.size,
            dtype=bool,
        )

        guard_start = max(
            0,
            fundamental_index
            - self._fundamental_guard_bins,
        )

        guard_stop = min(
            power_db.size,
            fundamental_index
            + self._fundamental_guard_bins
            + 1,
        )

        spur_mask[
            guard_start:guard_stop
        ] = False

        candidate_indices = np.flatnonzero(
            spur_mask
            & np.isfinite(power_db)
            & (
                power_db
                >= self._minimum_spur_power_db
            )
        )

        if candidate_indices.size == 0:
            return SFDRResult(
                fundamental_frequency_hz=(
                    fundamental_frequency_hz
                ),
                fundamental_power_db=(
                    fundamental_power_db
                ),
                spur_frequency_hz=None,
                spur_power_db=None,
                sfdr_db=None,
                fundamental_bin_index=(
                    fundamental_index
                ),
                spur_bin_index=None,
            )

        candidate_power_db = power_db[
            candidate_indices
        ]

        strongest_candidate_offset = int(
            np.argmax(
                candidate_power_db
            )
        )

        spur_index = int(
            candidate_indices[
                strongest_candidate_offset
            ]
        )

        spur_frequency_hz = float(
            frequencies_hz[
                spur_index
            ]
        )

        spur_power_db = float(
            power_db[
                spur_index
            ]
        )

        sfdr_db = (
            fundamental_power_db
            - spur_power_db
        )

        return SFDRResult(
            fundamental_frequency_hz=(
                fundamental_frequency_hz
            ),
            fundamental_power_db=(
                fundamental_power_db
            ),
            spur_frequency_hz=(
                spur_frequency_hz
            ),
            spur_power_db=(
                spur_power_db
            ),
            sfdr_db=float(
                sfdr_db
            ),
            fundamental_bin_index=(
                fundamental_index
            ),
            spur_bin_index=(
                spur_index
            ),
        )

    @staticmethod
    def _validate_input(
        frequencies_hz: np.ndarray,
        power_db: np.ndarray,
    ) -> tuple[
        np.ndarray,
        np.ndarray,
    ]:
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
