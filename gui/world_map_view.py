from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import cartopy.crs as ccrs
import cartopy.feature as cfeature


class WorldMapView(FigureCanvasQTAgg):
    def __init__(self):
        self.figure = Figure(figsize=(7, 4), facecolor="#0B1020")
        super().__init__(self.figure)

        self.ax = self.figure.add_subplot(111, projection=ccrs.PlateCarree())

        self.ax.set_global()
        self.ax.set_facecolor("#07111F")

        self.ax.add_feature(cfeature.OCEAN, facecolor="#07111F")
        self.ax.add_feature(cfeature.LAND, facecolor="#4B5563")
        self.ax.add_feature(cfeature.COASTLINE, edgecolor="#D1D5DB", linewidth=0.5)
        self.ax.add_feature(cfeature.BORDERS, edgecolor="#6B7280", linewidth=0.3)

        self.ax.gridlines(
            draw_labels=True,
            color="#374151",
            linewidth=0.5,
            linestyle="--",
        )

        self.ground_station, = self.ax.plot(
            11.0767,
            49.4521,
            marker="^",
            markersize=8,
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
            markersize=7,
            color="red",
            transform=ccrs.PlateCarree(),
            label="Satellite",
        )

        self.ax.legend(
            loc="lower left",
            facecolor="#111827",
            edgecolor="#9CA3AF",
            labelcolor="white",
        )

        self.ax.set_title("2D Ground Track View", color="white", fontsize=14)

        self.draw()

    def update_scene(self, sat_lat, sat_lon, track):
        if len(track) >= 3:
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

        self.satellite.set_data([sat_lon], [sat_lat])

        self.draw_idle()