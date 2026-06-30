from dataclasses import dataclass

from orbit.satellite import Satellite
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


class Tracker:
    def __init__(
        self,
        satellite_name: str = "ISS (ZARYA)",
        lat_deg: float = 49.4521,
        lon_deg: float = 11.0767,
        elevation_m: float = 300,
        carrier_frequency_hz: float = 437e6,
    ):
        self.satellite = Satellite(satellite_name)
        self.observer = self.satellite.observer(
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            elevation_m=elevation_m,
        )
        self.carrier_frequency_hz = carrier_frequency_hz

    def state_at(self, year: int, month: int, day: int, hour: int, minute: int) -> TrackingState:
        t = self.satellite.time_utc(year, month, day, hour, minute)
        t_next = self.satellite.time_utc(year, month, day, hour, minute + 1)

        topo = self.satellite.topocentric(self.observer, t)
        topo_next = self.satellite.topocentric(self.observer, t_next)

        elevation = GeometryCalculator.elevation_deg(topo)
        azimuth = GeometryCalculator.azimuth_deg(topo)
        range_km = GeometryCalculator.range_km(topo)

        d1 = GeometryCalculator.distance_m(topo)
        d2 = GeometryCalculator.distance_m(topo_next)

        range_rate = GeometryCalculator.range_rate_m_s(d1, d2, 60)
        doppler = DopplerCalculator.compute_khz(
            range_rate,
            self.carrier_frequency_hz,
        )
        visibility = VisibilityChecker.status(elevation)

        return TrackingState(
            satellite_name=self.satellite.name,
            time_utc=f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
            elevation_deg=elevation,
            azimuth_deg=azimuth,
            range_km=range_km,
            range_rate_m_s=range_rate,
            doppler_khz=doppler,
            visibility=visibility,
        )