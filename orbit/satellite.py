from skyfield.api import load, wgs84

from orbit.tle_manager import TLEManager


class Satellite:
    def __init__(
        self,
        name: str = "ISS (ZARYA)",
        tle_url: str = "https://celestrak.org/NORAD/elements/stations.txt",
    ):
        self.name = name
        self.tle_url = tle_url

        self.tle_manager = TLEManager()
        tle_path = self.tle_manager.load_tle_file(self.tle_url)

        satellites = load.tle_file(str(tle_path))
        matches = [sat for sat in satellites if sat.name == self.name]

        if not matches:
            available = [sat.name for sat in satellites[:10]]
            raise ValueError(
                f"Satellite '{self.name}' not found. "
                f"Examples available: {available}"
            )

        self.skyfield_sat = matches[0]
        self.ts = load.timescale()

    def time_utc(self, year, month, day, hour, minute, second=0):
        return self.ts.utc(year, month, day, hour, minute, second)

    def position_km(self, t):
        return self.skyfield_sat.at(t).position.km

    def velocity_km_s(self, t):
        return self.skyfield_sat.at(t).velocity.km_per_s

    def observer(self, lat_deg: float, lon_deg: float, elevation_m: float = 0):
        return wgs84.latlon(lat_deg, lon_deg, elevation_m=elevation_m)

    def topocentric(self, observer, t):
        return (self.skyfield_sat - observer).at(t)

    def subpoint(self, t):
        subpoint = self.skyfield_sat.at(t).subpoint()

        return (
            subpoint.latitude.degrees,
            subpoint.longitude.degrees,
            subpoint.elevation.km,
        )

    def tle_last_update(self):
        return self.tle_manager.last_update(self.tle_url)

    def refresh_tle(self):
        tle_path = self.tle_manager.force_refresh(self.tle_url)
        satellites = load.tle_file(str(tle_path))
        matches = [sat for sat in satellites if sat.name == self.name]

        if not matches:
            raise ValueError(f"Satellite '{self.name}' not found after refresh.")

        self.skyfield_sat = matches[0]