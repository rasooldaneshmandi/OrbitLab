from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SpurMeasurement:
    rank: int
    frequency_hz: float
    power_db: float
    offset_from_fundamental_hz: float
    relative_power_dbc: float
    bin_index: int


@dataclass(frozen=True)
class SpurAnalysisResult:
    fundamental_frequency_hz: float
    fundamental_power_db: float
    spurs: tuple[SpurMeasurement, ...]


class SpurAnalyzer:
    """
    Detect strongest local spectral spurs outside the
    fundamental guard region.
    """

    def __init__(
        self,
        *,
        maximum_spurs: int = 10,
        fundamental_guard_bins: int = 20,
        minimum_spur_distance_bins: int = 20,
        minimum_spur_power_db: float = -120.0,
    ) -> None:
        if maximum_spurs <= 0:
            raise ValueError(
                "maximum_spurs must be greater than zero."
            )

        if fundamental_guard_bins < 0:
            raise ValueError(
                "fundamental_guard_bins must not be negative."
            )

        if minimum_spur_distance_bins <= 0:
            raise ValueError(
                "minimum_spur_distance_bins must be greater than zero."
            )

        self._maximum_spurs = int(
            maximum_spurs
        )

        self._fundamental_guard_bins = int(
            fundamental_guard_bins
        )

        self._minimum_spur_distance_bins = int(
            minimum_spur_distance_bins
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
    ) -> SpurAnalysisResult:
        frequencies_hz, power_db = self._validate(
            frequencies_hz,
            power_db,
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

        local_maximum_mask = np.zeros(
            power_db.size,
            dtype=bool,
        )

        local_maximum_mask[1:-1] = (
            (power_db[1:-1] > power_db[:-2])
            & (power_db[1:-1] >= power_db[2:])
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

        local_maximum_mask[
            guard_start:guard_stop
        ] = False

        candidate_indices = np.flatnonzero(
            local_maximum_mask
            & (
                power_db
                >= self._minimum_spur_power_db
            )
        )

        if candidate_indices.size == 0:
            return SpurAnalysisResult(
                fundamental_frequency_hz=(
                    fundamental_frequency_hz
                ),
                fundamental_power_db=(
                    fundamental_power_db
                ),
                spurs=(),
            )

        sorted_candidates = candidate_indices[
            np.argsort(
                power_db[
                    candidate_indices
                ]
            )[::-1]
        ]

        accepted_indices: list[int] = []

        for candidate_index in sorted_candidates:
            candidate_index = int(
                candidate_index
            )

            far_enough = all(
                abs(
                    candidate_index
                    - accepted_index
                )
                >= self._minimum_spur_distance_bins
                for accepted_index in accepted_indices
            )

            if not far_enough:
                continue

            accepted_indices.append(
                candidate_index
            )

            if (
                len(accepted_indices)
                >= self._maximum_spurs
            ):
                break

        spurs: list[SpurMeasurement] = []

        for rank, spur_index in enumerate(
            accepted_indices,
            start=1,
        ):
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

            spurs.append(
                SpurMeasurement(
                    rank=rank,
                    frequency_hz=(
                        spur_frequency_hz
                    ),
                    power_db=(
                        spur_power_db
                    ),
                    offset_from_fundamental_hz=(
                        spur_frequency_hz
                        - fundamental_frequency_hz
                    ),
                    relative_power_dbc=(
                        spur_power_db
                        - fundamental_power_db
                    ),
                    bin_index=(
                        spur_index
                    ),
                )
            )

        return SpurAnalysisResult(
            fundamental_frequency_hz=(
                fundamental_frequency_hz
            ),
            fundamental_power_db=(
                fundamental_power_db
            ),
            spurs=tuple(spurs),
        )

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
