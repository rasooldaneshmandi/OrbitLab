import numpy as np

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle


class EarthView(FigureCanvasQTAgg):

    def __init__(self):

        self.figure = Figure(figsize=(6, 6))
        super().__init__(self.figure)

        self.ax = self.figure.add_subplot(111)

        self.ax.set_aspect("equal")
        self.ax.set_xlim(-1.3, 1.3)
        self.ax.set_ylim(-1.3, 1.3)

        self.ax.set_xticks([])
        self.ax.set_yticks([])

        self.ax.set_facecolor("#0B1020")

        earth = Circle(
            (0, 0),
            1,
            facecolor="#2E86DE",
            edgecolor="white",
            linewidth=2,
        )

        self.ax.add_patch(earth)

        self.satellite, = self.ax.plot(
            [0],
            [1.1],
            "ro",
            markersize=10,
        )

        self.ax.set_title(
            "Earth View",
            color="white",
            fontsize=14,
        )

        # زاویه‌ای که روی صفحه نمایش داده می‌شود
        self.display_angle = None

        self.draw()

    def update_satellite(self, azimuth_deg):

        if self.display_angle is None:
            self.display_angle = azimuth_deg

        # کوتاه‌ترین مسیر بین دو زاویه
        diff = (azimuth_deg - self.display_angle + 180) % 360 - 180

        # حرکت نرم
        self.display_angle += diff * 0.15

        angle = np.deg2rad(self.display_angle)

        r = 1.10

        x = r * np.cos(angle)
        y = r * np.sin(angle)

        self.satellite.set_data([x], [y])

        self.draw_idle()