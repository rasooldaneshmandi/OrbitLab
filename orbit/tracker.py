from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

from orbit.clock import SimulationClock
from orbit.data_source import DataSource
from orbit.doppler import (
    DopplerCalculator,
    DopplerResult,
)
from orbit.satellite import Satellite
from orbit.satellite_catalog import SATELLITES
from orbit.tracking_state import TrackingState

from geometry.calculator import GeometryCalculator
from geometry.visibility import VisibilityChecker


@dataclass(frozen=True)
class SatelliteState:
    """
    Ground-station geometry at one instant.
    """

    timestamp_utc: datetime

    azimuth_deg: float
    elevation_deg: float

    range_km: float
    range_rate_m_s: float

    visible: bool


@dataclass(frozen=True)
class SatelliteRadioState:
    """
    Ground-station geometry plus Doppler information.
    """

    timestamp_utc: datetime

    azimuth_deg: float
    elevation_deg: float

    range_km: float
    range_rate_m_s: float

    visible: bool

    doppler: DopplerResult


class Tracker(DataSource):
    """
    Unified OrbitLab satellite tracker.

    Supports both:

        Legacy Mission-Control API
        Ground-Station / SDR Doppler API
    """

    DEFAULT_LATITUDE_DEG = 51.4818
    DEFAULT_LONGITUDE_DEG = 7.2162
    DEFAULT_ELEVATION_M = 100.0

    def __init__(
        self,
        satellite_key: str = "ISS",
        lat_deg: float = DEFAULT_LATITUDE_DEG,
        lon_deg: float = DEFAULT_LONGITUDE_DEG,
        elevation_m: float = DEFAULT_ELEVATION_M,
        carrier_frequency_hz: float = 437e6,
        *,
        latitude_deg: float | None = None,
        longitude_deg: float | None = None,
    ) -> None:
        """
        Args:
            satellite_key:
                Satellite catalogue key.

            lat_deg / lon_deg:
                Legacy ground-station coordinate arguments.

            latitude_deg / longitude_deg:
                New aliases for the same coordinates.

            elevation_m:
                Ground-station altitude.

            carrier_frequency_hz:
                Legacy Mission-Control carrier used for
                TrackingState.doppler_khz.
        """

        self.clock = SimulationClock()

        if latitude_deg is not None:
            lat_deg = float(
                latitude_deg
            )

        if longitude_deg is not None:
            lon_deg = float(
                longitude_deg
            )

        self.lat_deg = float(
            lat_deg
        )

        self.lon_deg = float(
            lon_deg
        )

        self.elevation_m = float(
            elevation_m
        )

        self.carrier_frequency_hz = float(
            carrier_frequency_hz
        )

        self._validate_ground_station(
            self.lat_deg,
            self.lon_deg,
        )

        self._satellite_key: str | None = None

        self.satellite: Satellite | None = None
        self.observer = None

        self.set_satellite(
            satellite_key
        )

    # ============================================================
    # Satellite selection
    # ============================================================

    def set_satellite(
        self,
        satellite_key: str,
    ) -> None:
        satellite_key = str(
            satellite_key
        ).strip().upper()

        if satellite_key not in SATELLITES:
            available = ", ".join(
                SATELLITES.keys()
            )

            raise ValueError(
                f"Satellite '{satellite_key}' not found. "
                f"Available: {available}"
            )

        sat_info = SATELLITES[
            satellite_key
        ]

        self.satellite = Satellite(
            name=sat_info["name"],
            tle_url=sat_info["tle_url"],
        )

        self._satellite_key = satellite_key

        self.observer = self.satellite.observer(
            self.lat_deg,
            self.lon_deg,
            self.elevation_m,
        )

    # ============================================================
    # Legacy Mission-Control API
    # ============================================================

    def current_state(
        self,
    ) -> TrackingState:
        year, month, day, hour, minute = (
            self.clock.current_time()
        )

        return self.state_at(
            year,
            month,
            day,
            hour,
            minute,
        )

    def step(
        self,
    ) -> None:
        self.clock.step()

    def set_speed(
        self,
        step_minutes,
    ) -> None:
        self.clock.set_step_minutes(
            step_minutes
        )

    def set_time_minutes(
        self,
        total_minutes,
    ) -> None:
        self.clock.set_total_minutes(
            total_minutes
        )

    def current_total_minutes(
        self,
    ):
        return (
            self.clock.current_total_minutes()
        )

    def reset(
        self,
    ) -> None:
        self.clock.reset()

    def refresh_tle(
        self,
    ) -> None:
        self._require_satellite().refresh_tle()

    def tle_last_update(
        self,
    ):
        return (
            self._require_satellite()
            .tle_last_update()
        )

    def state_at(
        self,
        year,
        month,
        day,
        hour,
        minute,
    ) -> TrackingState:
        satellite = self._require_satellite()

        t = satellite.time_utc(
            year,
            month,
            day,
            hour,
            minute,
        )

        (
            next_year,
            next_month,
            next_day,
            next_hour,
            next_minute,
        ) = self.clock.next_time()

        t_next = satellite.time_utc(
            next_year,
            next_month,
            next_day,
            next_hour,
            next_minute,
        )

        topo = satellite.topocentric(
            self.observer,
            t,
        )

        topo_next = satellite.topocentric(
            self.observer,
            t_next,
        )

        elevation = (
            GeometryCalculator.elevation_deg(
                topo
            )
        )

        azimuth = (
            GeometryCalculator.azimuth_deg(
                topo
            )
        )

        range_km = (
            GeometryCalculator.range_km(
                topo
            )
        )

        d1 = GeometryCalculator.distance_m(
            topo
        )

        d2 = GeometryCalculator.distance_m(
            topo_next
        )

        range_rate = (
            GeometryCalculator.range_rate_m_s(
                d1,
                d2,
                self.clock.step_minutes * 60,
            )
        )

        doppler = (
            DopplerCalculator.calculate(
                nominal_frequency_hz=self.carrier_frequency_hz,
                radial_velocity_m_s=range_rate,
            ).doppler_shift_hz
            / 1000.0
        )

        visibility = (
            VisibilityChecker.status(
                elevation
            )
        )

        (
            sat_lat,
            sat_lon,
            sat_alt,
        ) = satellite.subpoint(
            t
        )

        return TrackingState(
            satellite_name=satellite.name,
            time_utc=self.clock.time_string(),

            elevation_deg=elevation,
            azimuth_deg=azimuth,

            range_km=range_km,
            range_rate_m_s=range_rate,

            doppler_khz=doppler,

            visibility=visibility,

            sat_lat_deg=sat_lat,
            sat_lon_deg=sat_lon,
            sat_alt_km=sat_alt,
        )

    def orbit_track(
        self,
        minutes_before=30,
        minutes_after=30,
        step_minutes=1,
    ):
        satellite = self._require_satellite()

        (
            year,
            month,
            day,
            hour,
            minute,
        ) = self.clock.current_time()

        current_total_minutes = (
            hour * 60 + minute
        )

        start = (
            current_total_minutes
            - minutes_before
        )

        stop = (
            current_total_minutes
            + minutes_after
        )

        track = []

        for total_minutes in range(
            start,
            stop + 1,
            step_minutes,
        ):
            h = (
                total_minutes // 60
            ) % 24

            m = (
                total_minutes % 60
            )

            t = satellite.time_utc(
                year,
                month,
                day,
                h,
                m,
            )

            lat, lon, alt = (
                satellite.subpoint(
                    t
                )
            )

            track.append(
                {
                    "lat": lat,
                    "lon": lon,
                    "alt": alt,
                    "time": (
                        f"{h:02d}:{m:02d}"
                    ),
                }
            )

        return track

    # ============================================================
    # Ground-station API
    # ============================================================

    def state(
        self,
        when=None,
    ) -> SatelliteState:
        """
        Calculate high-resolution topocentric state.

        If `when` is omitted, the current SimulationClock time
        is used. This keeps Mission Control, Pass Prediction and
        SDR Doppler synchronized.
        """

        satellite = self._require_satellite()

        if when is None:
            when = self._clock_skyfield_time()

        topocentric = satellite.topocentric(
            self.observer,
            when,
        )

        altitude, azimuth, distance = (
            topocentric.altaz()
        )

        position_km = np.asarray(
            topocentric.position.km,
            dtype=np.float64,
        )

        velocity_km_s = np.asarray(
            topocentric.velocity.km_per_s,
            dtype=np.float64,
        )

        range_km = float(
            np.linalg.norm(
                position_km
            )
        )

        if (
            not np.isfinite(range_km)
            or range_km <= 0.0
        ):
            raise RuntimeError(
                "Invalid satellite slant range."
            )

        # dr/dt = (r dot v) / |r|
        range_rate_km_s = float(
            np.dot(
                position_km,
                velocity_km_s,
            )
            / range_km
        )

        range_rate_m_s = (
            range_rate_km_s
            * 1000.0
        )

        timestamp_utc = (
            when.utc_datetime()
        )

        if timestamp_utc.tzinfo is None:
            timestamp_utc = (
                timestamp_utc.replace(
                    tzinfo=timezone.utc
                )
            )

        elevation_deg = float(
            altitude.degrees
        )

        return SatelliteState(
            timestamp_utc=(
                timestamp_utc
            ),
            azimuth_deg=float(
                azimuth.degrees
            ),
            elevation_deg=(
                elevation_deg
            ),
            range_km=float(
                distance.km
            ),
            range_rate_m_s=float(
                range_rate_m_s
            ),
            visible=(
                elevation_deg > 0.0
            ),
        )

    def radio_state(
        self,
        nominal_frequency_hz: float,
        when=None,
    ) -> SatelliteRadioState:
        nominal_frequency_hz = float(
            nominal_frequency_hz
        )

        if nominal_frequency_hz <= 0.0:
            raise ValueError(
                "nominal_frequency_hz must be greater than zero."
            )

        geometry = self.state(
            when=when
        )

        doppler = DopplerCalculator.calculate(
            nominal_frequency_hz=(
                nominal_frequency_hz
            ),
            radial_velocity_m_s=(
                geometry.range_rate_m_s
            ),
        )

        return SatelliteRadioState(
            timestamp_utc=(
                geometry.timestamp_utc
            ),
            azimuth_deg=(
                geometry.azimuth_deg
            ),
            elevation_deg=(
                geometry.elevation_deg
            ),
            range_km=(
                geometry.range_km
            ),
            range_rate_m_s=(
                geometry.range_rate_m_s
            ),
            visible=(
                geometry.visible
            ),
            doppler=doppler,
        )

    def doppler_shift_hz(
        self,
        nominal_frequency_hz: float,
        when=None,
    ) -> float:
        return (
            self.radio_state(
                nominal_frequency_hz,
                when=when,
            )
            .doppler
            .doppler_shift_hz
        )

    def corrected_receive_frequency_hz(
        self,
        nominal_frequency_hz: float,
        when=None,
    ) -> float:
        return (
            self.radio_state(
                nominal_frequency_hz,
                when=when,
            )
            .doppler
            .received_frequency_hz
        )

    def is_visible(
        self,
        when=None,
    ) -> bool:
        return self.state(
            when=when
        ).visible

    def set_ground_station(
        self,
        *,
        latitude_deg: float,
        longitude_deg: float,
        elevation_m: float = 0.0,
    ) -> None:
        latitude_deg = float(
            latitude_deg
        )

        longitude_deg = float(
            longitude_deg
        )

        elevation_m = float(
            elevation_m
        )

        self._validate_ground_station(
            latitude_deg,
            longitude_deg,
        )

        self.lat_deg = latitude_deg
        self.lon_deg = longitude_deg
        self.elevation_m = elevation_m

        satellite = self._require_satellite()

        self.observer = satellite.observer(
            self.lat_deg,
            self.lon_deg,
            self.elevation_m,
        )

    # ============================================================
    # Helpers
    # ============================================================

    def _clock_skyfield_time(
        self,
    ):
        (
            year,
            month,
            day,
            hour,
            minute,
        ) = self.clock.current_time()

        return (
            self._require_satellite()
            .time_utc(
                year,
                month,
                day,
                hour,
                minute,
            )
        )

    def _require_satellite(
        self,
    ) -> Satellite:
        if self.satellite is None:
            raise RuntimeError(
                "No satellite selected."
            )

        return self.satellite

    @staticmethod
    def _validate_ground_station(
        latitude_deg: float,
        longitude_deg: float,
    ) -> None:
        if not (
            -90.0
            <= latitude_deg
            <= 90.0
        ):
            raise ValueError(
                "Latitude must be between -90 and 90 degrees."
            )

        if not (
            -180.0
            <= longitude_deg
            <= 180.0
        ):
            raise ValueError(
                "Longitude must be between -180 and 180 degrees."
            )

    # ============================================================
    # Properties
    # ============================================================

    @property
    def satellite_key(
        self,
    ) -> str:
        if self._satellite_key is None:
            raise RuntimeError(
                "No satellite selected."
            )

        return self._satellite_key

    @property
    def satellite_name(
        self,
    ) -> str:
        return self._require_satellite().name

    @property
    def latitude_deg(
        self,
    ) -> float:
        return self.lat_deg

    @property
    def longitude_deg(
        self,
    ) -> float:
        return self.lon_deg
