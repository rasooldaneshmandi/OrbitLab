from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout
)

from orbit.satellite import Satellite
from geometry.calculator import GeometryCalculator
from geometry.doppler import DopplerCalculator
from geometry.visibility import VisibilityChecker


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("OrbitLab")
        self.resize(900, 600)

        self.iss = Satellite("ISS (ZARYA)")

        observer = self.iss.observer(
            49.4521,
            11.0767,
            300
        )

        t = self.iss.time_utc(2026, 6, 23, 3, 0)
        t_next = self.iss.time_utc(2026, 6, 23, 3, 1)

        topo = self.iss.topocentric(observer, t)
        topo_next = self.iss.topocentric(observer, t_next)

        elevation = GeometryCalculator.elevation_deg(topo)
        azimuth = GeometryCalculator.azimuth_deg(topo)
        range_km = GeometryCalculator.range_km(topo)

        d1 = GeometryCalculator.distance_m(topo)
        d2 = GeometryCalculator.distance_m(topo_next)

        range_rate = GeometryCalculator.range_rate_m_s(d1, d2, 60)
        doppler = DopplerCalculator.compute_khz(range_rate, 437e6)
        visibility = VisibilityChecker.status(elevation)

        info = QLabel(
            f"""
OrbitLab

Satellite : {self.iss.name}

Elevation : {elevation:.2f}°

Azimuth : {azimuth:.2f}°

Range : {range_km:.2f} km

Range Rate : {range_rate:.2f} m/s

Doppler : {doppler:.2f} kHz

Visibility : {visibility}
"""
        )

        info.setStyleSheet("font-size:18px;")

        layout = QVBoxLayout()
        layout.addWidget(info)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)