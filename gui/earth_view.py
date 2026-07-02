from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import cartopy.crs as ccrs
import cartopy.feature as cfeature


class EarthView(FigureCanvasQTAgg):
    def __init__(self):
        self.figure = Figure(figsize=(7, 4), facecolor="#0B1020")
        super().__init__(self.figure)

        self.ax = self.figure.add_subplot(111, projection=ccrs.PlateCarree())
        self.ax.set_global()
        self.ax.set_facecolor("#07111F")

        self.ax.add_feature(cfeature.OCEAN, facecolor="#07111F")
        self.ax.add_feature(cfeature.LAND, facecolor="#4B5563", edgecolor="#9CA3AF", linewidth=0.4)
        self.ax.add_feature(cfeature.COASTLINE, edgecolor="#D1D5DB", linewidth=0.5)
        self.ax.add_feature(cfeature.BORDERS, edgecolor="#6B7280", linewidth=0.3)

        self.ax.gridlines(draw_labels=True, color="#374151", linewidth=0.5, linestyle="--")

        self.ground_station, = self.ax.plot(
            11.0767, 49.4521,
            marker="^", markersize=8, color="yellow",
            transform=ccrs.PlateCarree(), label="Nürnberg"
        )

        self.track_line, = self.ax.plot(
            [], [],
            color="#38BDF8",
            linewidth=1.5,
            transform=ccrs.PlateCarree(),
            label="Orbit Track"
        )

        self.satellite, = self.ax.plot(
            0, 0,
            marker="o", markersize=7, color="red",
            transform=ccrs.PlateCarree(), label="ISS"
        )

        self.ax.legend(
            loc="lower left",
            facecolor="#111827",
            edgecolor="#9CA3AF",
            labelcolor="white"
        )

        self.ax.set_title("World Map View", color="white", fontsize=14)
        self.draw()

    def update_satellite(self, latitude_deg, longitude_deg):
        self.satellite.set_data([longitude_deg], [latitude_deg])
        self.draw_idle()

    def update_track(self, track):
        lats = [p["lat"] for p in track]
        lons = [p["lon"] for p in track]

        self.track_line.set_data(lons, lats)
        self.draw_idle()