from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from orbit.tracker import (
    SatelliteRadioState,
    Tracker,
)


class FrequencyTunable(Protocol):
    """
    Minimal interface required by DopplerController.

    Any SDR device or pipeline implementing
    set_center_frequency() can be used.
    """

    def set_center_frequency(
        self,
        frequency_hz: float,
    ) -> None:
        ...


@dataclass(frozen=True)
class DopplerControllerState:
    """
    Snapshot of one Doppler tracking update.
    """

    nominal_frequency_hz: float
    corrected_frequency_hz: float
    doppler_shift_hz: float

    azimuth_deg: float
    elevation_deg: float

    range_km: float
    range_rate_m_s: float

    visible: bool


class DopplerController:
    """
    Connect satellite tracking to SDR tuning.

    Processing chain:

        Tracker
            ->
        Range Rate
            ->
        Doppler
            ->
        Corrected RX Frequency
            ->
        SDR set_center_frequency()

    The controller itself does not create a timer.
    The GUI or acquisition loop decides how often
    update() is called.
    """

    def __init__(
        self,
        *,
        tracker: Tracker,
        receiver: FrequencyTunable,
        nominal_frequency_hz: float,
        enabled: bool = True,
        tune_only_when_visible: bool = False,
    ) -> None:

        nominal_frequency_hz = float(
            nominal_frequency_hz
        )

        if nominal_frequency_hz <= 0.0:
            raise ValueError(
                "nominal_frequency_hz must be greater than zero."
            )

        self._tracker = tracker
        self._receiver = receiver

        self._nominal_frequency_hz = (
            nominal_frequency_hz
        )

        self._enabled = bool(
            enabled
        )

        self._tune_only_when_visible = bool(
            tune_only_when_visible
        )

        self._latest_state: (
            DopplerControllerState | None
        ) = None

    def update(
        self,
        when=None,
    ) -> DopplerControllerState:
        """
        Perform one satellite/Doppler update.

        If automatic tuning is enabled, the SDR
        center frequency is updated accordingly.
        """

        radio_state: SatelliteRadioState = (
            self._tracker.radio_state(
                self._nominal_frequency_hz,
                when=when,
            )
        )

        corrected_frequency_hz = float(
            radio_state
            .doppler
            .received_frequency_hz
        )

        state = DopplerControllerState(
            nominal_frequency_hz=(
                self._nominal_frequency_hz
            ),
            corrected_frequency_hz=(
                corrected_frequency_hz
            ),
            doppler_shift_hz=float(
                radio_state
                .doppler
                .doppler_shift_hz
            ),
            azimuth_deg=float(
                radio_state.azimuth_deg
            ),
            elevation_deg=float(
                radio_state.elevation_deg
            ),
            range_km=float(
                radio_state.range_km
            ),
            range_rate_m_s=float(
                radio_state.range_rate_m_s
            ),
            visible=bool(
                radio_state.visible
            ),
        )

        self._latest_state = state

        should_tune = (
            self._enabled
            and (
                state.visible
                or not self._tune_only_when_visible
            )
        )

        if should_tune:
            self._receiver.set_center_frequency(
                corrected_frequency_hz
            )

        return state

    def tune_nominal(
        self,
    ) -> None:
        """
        Tune back to the nominal satellite frequency.
        """

        self._receiver.set_center_frequency(
            self._nominal_frequency_hz
        )

    def set_enabled(
        self,
        enabled: bool,
    ) -> None:
        self._enabled = bool(
            enabled
        )

    def set_nominal_frequency(
        self,
        frequency_hz: float,
    ) -> None:

        frequency_hz = float(
            frequency_hz
        )

        if frequency_hz <= 0.0:
            raise ValueError(
                "frequency_hz must be greater than zero."
            )

        self._nominal_frequency_hz = (
            frequency_hz
        )

    @property
    def enabled(
        self,
    ) -> bool:
        return self._enabled

    @property
    def nominal_frequency_hz(
        self,
    ) -> float:
        return self._nominal_frequency_hz

    @property
    def latest_state(
        self,
    ) -> DopplerControllerState | None:
        return self._latest_state

    @property
    def tracker(
        self,
    ) -> Tracker:
        return self._tracker
