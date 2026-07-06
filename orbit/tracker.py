from dataclasses import dataclass

from orbit.satellite import Satellite
from orbit.clock import SimulationClock
from orbit.satellite_catalog import SATELLITES

from geometry.calculator import GeometryCalculator
from geometry.doppler import DopplerCalculator
from geometry.visibility import VisibilityChecker


@dataclass
class TrackingState:
    satellite_name: str
    time_utc: str

    elevation_deg: float
    azimuth_deg: float
    range_km: float
    range_rate_m_s: float
    doppler_khz: float
    visibility: str

    sat_lat_deg: float
    sat_lon_deg: float
    sat_alt_km: float


class Tracker:
    def __init__(
        self,
        satellite_key="ISS",
        lat_deg=49.4521,
        lon_deg=11.0767,
        elevation_m=300,
        carrier_frequency_hz=437e6,
    ):
        self.clock = SimulationClock()

        self.lat_deg = lat_deg
        self.lon_deg = lon_deg
        self.elevation_m = elevation_m
        self.carrier_frequency_hz = carrier_frequency_hz

        self.set_satellite(satellite_key)

    def set_satellite(self, satellite_key):
        if satellite_key not in SATELLITES:
            raise ValueError(f"Satellite '{satellite_key}' not found in catalog.")

        sat_info = SATELLITES[satellite_key]

        self.satellite = Satellite(
            name=sat_info["name"],
            tle_url=sat_info["tle_url"],
        )

        self.observer = self.satellite.observer(
            self.lat_deg,
            self.lon_deg,
            self.elevation_m,
        )

    def current_state(self):
        year, month, day, hour, minute = self.clock.current_time()
        return self.state_at(year, month, day, hour, minute)

    def step(self):
        self.clock.step()

    def set_speed(self, step_minutes):
        self.clock.set_step_minutes(step_minutes)

    def set_time_minutes(self, total_minutes):
        self.clock.set_total_minutes(total_minutes)

    def current_total_minutes(self):
        return self.clock.current_total_minutes()

    def reset(self):
        self.clock.reset()

    def refresh_tle(self):
        self.satellite.refresh_tle()

    def tle_last_update(self):
        return self.satellite.tle_last_update()

    def state_at(self, year, month, day, hour, minute):
        t = self.satellite.time_utc(year, month, day, hour, minute)

        next_year, next_month, next_day, next_hour, next_minute = (
            self.clock.next_time()
        )

        t_next = self.satellite.time_utc(
            next_year,
            next_month,
            next_day,
            next_hour,
            next_minute,
        )

        topo = self.satellite.topocentric(self.observer, t)
        topo_next = self.satellite.topocentric(self.observer, t_next)

        elevation = GeometryCalculator.elevation_deg(topo)
        azimuth = GeometryCalculator.azimuth_deg(topo)
        range_km = GeometryCalculator.range_km(topo)

        d1 = GeometryCalculator.distance_m(topo)
        d2 = GeometryCalculator.distance_m(topo_next)

        range_rate = GeometryCalculator.range_rate_m_s(
            d1,
            d2,
            self.clock.step_minutes * 60,
        )

        doppler = DopplerCalculator.compute_khz(
            range_rate,
            self.carrier_frequency_hz,
        )

        visibility = VisibilityChecker.status(elevation)

        sat_lat, sat_lon, sat_alt = self.satellite.subpoint(t)

        return TrackingState(
            satellite_name=self.satellite.name,
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
        year, month, day, hour, minute = self.clock.current_time()

        current_total_minutes = hour * 60 + minute
        start = current_total_minutes - minutes_before
        stop = current_total_minutes + minutes_after

        track = []

        for total_minutes in range(start, stop + 1, step_minutes):
            h = (total_minutes // 60) % 24
            m = total_minutes % 60

            t = self.satellite.time_utc(year, month, day, h, m)
            lat, lon, alt = self.satellite.subpoint(t)

            track.append(
                {
                    "lat": lat,
                    "lon": lon,
                    "alt": alt,
                    "time": f"{h:02d}:{m:02d}",
                }
            )

        return track