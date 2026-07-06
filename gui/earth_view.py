import numpy as np

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import cartopy.crs as ccrs
import cartopy.feature as cfeature


class EarthView(FigureCanvasQTAgg):
    EARTH_RADIUS_KM = 6371.0

    def __init__(self):
        self.figure = Figure(figsize=(7, 5), facecolor="#0B1020")
        super().__init__(self.figure)

        self.centered_mode = False
        self.last_lon = 10
        self.last_lat = 30

        self._build_map(10, 30)

    def set_centered_mode(self, enabled: bool):
        self.centered_mode = enabled

    def _build_map(self, center_lon, center_lat):
        self.figure.clear()

        projection = ccrs.Orthographic(
            central_longitude=center_lon,
            central_latitude=center_lat,
        )

        self.ax = self.figure.add_subplot(111, projection=projection)
        self.ax.set_global()
        self.ax.set_facecolor("#07111F")

        self.ax.add_feature(cfeature.OCEAN, facecolor="#07111F")
        self.ax.add_feature(cfeature.LAND, facecolor="#4B5563")
        self.ax.add_feature(cfeature.COASTLINE, edgecolor="#D1D5DB", linewidth=0.6)
        self.ax.add_feature(cfeature.BORDERS, edgecolor="#6B7280", linewidth=0.3)

        self.ax.gridlines(color="#374151", linewidth=0.5, linestyle="--")

        self.ax.set_title(
            "3D Globe View - Satellite Centered" if self.centered_mode else "3D Globe View - Earth Fixed",
            color="white",
            fontsize=14,
        )

        self.ground_station, = self.ax.plot(
            11.0767, 49.4521,
            marker="^",
            markersize=9,
            color="yellow",
            transform=ccrs.PlateCarree(),
            label="Nürnberg",
        )

        self.footprint, = self.ax.plot(
            [], [],
            color="#F59E0B",
            linewidth=1.5,
            linestyle="--",
            transform=ccrs.PlateCarree(),
            label="Footprint",
        )

        self.past_track, = self.ax.plot(
            [], [],
            color="#22C55E",
            linewidth=2,
            transform=ccrs.PlateCarree(),
            label="Past Orbit",
        )

        self.future_track, = self.ax.plot(
            [], [],
            color="#3B82F6",
            linewidth=2,
            transform=ccrs.PlateCarree(),
            label="Future Orbit",
        )

        self.satellite, = self.ax.plot(
            0, 0,
            marker="o",
            markersize=8,
            color="red",
            transform=ccrs.PlateCarree(),
            label="ISS",
        )

        self.ax.legend(
            loc="lower left",
            facecolor="#111827",
            edgecolor="#9CA3AF",
            labelcolor="white",
        )

    def update_scene(self, sat_lat, sat_lon, sat_alt, track):
        if self.centered_mode:
            self._build_map(sat_lon, sat_lat)
        else:
            self._build_map(10, 30)

        self.update_track(track)
        self.update_satellite(sat_lat, sat_lon)
        self.update_footprint(sat_lat, sat_lon, sat_alt)

        self.draw_idle()

    def update_satellite(self, latitude_deg, longitude_deg):
        self.satellite.set_data([longitude_deg], [latitude_deg])

    def update_track(self, track):
        if len(track) < 3:
            return

        center = len(track) // 2
        past = track[:center]
        future = track[center:]

        self.past_track.set_data(
            [p["lon"] for p in past],
            [p["lat"] for p in past],
        )

        self.future_track.set_data(
            [p["lon"] for p in future],
            [p["lat"] for p in future],
        )

    def update_footprint(self, sat_lat_deg, sat_lon_deg, sat_alt_km):
        earth_radius = self.EARTH_RADIUS_KM
        angular_radius = np.arccos(earth_radius / (earth_radius + sat_alt_km))

        lat0 = np.deg2rad(sat_lat_deg)
        lon0 = np.deg2rad(sat_lon_deg)

        bearings = np.linspace(0, 2 * np.pi, 181)

        lat = np.arcsin(
            np.sin(lat0) * np.cos(angular_radius)
            + np.cos(lat0) * np.sin(angular_radius) * np.cos(bearings)
        )

        lon = lon0 + np.arctan2(
            np.sin(bearings) * np.sin(angular_radius) * np.cos(lat0),
            np.cos(angular_radius) - np.sin(lat0) * np.sin(lat),
        )

        lat_deg = np.rad2deg(lat)
        lon_deg = (np.rad2deg(lon) + 180) % 360 - 180

        self.footprint.set_data(lon_deg, lat_deg)