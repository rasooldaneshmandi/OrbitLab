from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import cartopy.crs as ccrs
import cartopy.feature as cfeature


class EarthView(FigureCanvasQTAgg):
    def __init__(self):
        self.figure = Figure(figsize=(7, 5), facecolor="#0B1020")
        super().__init__(self.figure)

        self.projection = ccrs.Orthographic(
            central_longitude=10,
            central_latitude=30,
        )

        self.ax = self.figure.add_subplot(
            111,
            projection=self.projection,
        )

        self.ax.set_global()
        self.ax.set_facecolor("#07111F")

        self.ax.add_feature(cfeature.OCEAN, facecolor="#07111F")
        self.ax.add_feature(cfeature.LAND, facecolor="#4B5563")
        self.ax.add_feature(
            cfeature.COASTLINE,
            edgecolor="#D1D5DB",
            linewidth=0.6,
        )
        self.ax.add_feature(
            cfeature.BORDERS,
            edgecolor="#6B7280",
            linewidth=0.3,
        )

        self.ax.gridlines(
            color="#374151",
            linewidth=0.5,
            linestyle="--",
        )

        self.ground_station, = self.ax.plot(
            11.0767,
            49.4521,
            marker="^",
            markersize=9,
            color="yellow",
            transform=ccrs.PlateCarree(),
            label="Nürnberg",
        )

        self.past_track, = self.ax.plot(
            [],
            [],
            color="#22C55E",
            linewidth=2,
            transform=ccrs.PlateCarree(),
            label="Past Orbit",
        )

        self.future_track, = self.ax.plot(
            [],
            [],
            color="#3B82F6",
            linewidth=2,
            transform=ccrs.PlateCarree(),
            label="Future Orbit",
        )

        self.satellite, = self.ax.plot(
            0,
            0,
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

        self.ax.set_title(
            "3D Globe View",
            color="white",
            fontsize=14,
        )

        self.draw()

    def update_satellite(self, latitude_deg, longitude_deg):
        self.satellite.set_data(
            [longitude_deg],
            [latitude_deg],
        )

        self.draw_idle()

    def update_track(self, track):
        if len(track) < 3:
            return

        center = len(track) // 2

        past = track[:center]
        future = track[center:]

        past_lon = [p["lon"] for p in past]
        past_lat = [p["lat"] for p in past]

        future_lon = [p["lon"] for p in future]
        future_lat = [p["lat"] for p in future]

        self.past_track.set_data(
            past_lon,
            past_lat,
        )

        self.future_track.set_data(
            future_lon,
            future_lat,
        )

        self.draw_idle()