from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QFormLayout,
    QSplitter,
)
from PyQt6.QtCore import Qt

from orbit.satellite import Satellite
from geometry.calculator import GeometryCalculator
from geometry.doppler import DopplerCalculator
from geometry.visibility import VisibilityChecker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OrbitLab - Satellite Tracking Console")
        self.resize(1100, 700)

        self.iss = Satellite("ISS (ZARYA)")

        observer = self.iss.observer(
            lat_deg=49.4521,
            lon_deg=11.0767,
            elevation_m=300,
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

        central = QWidget()
        main_layout = QVBoxLayout()

        title = QLabel("OrbitLab Mission Control")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 26px; font-weight: bold; padding: 12px;"
        )

        splitter = QSplitter(Qt.Orientation.Horizontal)

        earth_view = self.create_earth_view()
        telemetry_panel = self.create_telemetry_panel(
            elevation,
            azimuth,
            range_km,
            range_rate,
            doppler,
            visibility,
        )

        splitter.addWidget(earth_view)
        splitter.addWidget(telemetry_panel)
        splitter.setSizes([650, 350])

        main_layout.addWidget(title)
        main_layout.addWidget(splitter)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

    def create_earth_view(self):
        box = QGroupBox("Ground Station View")
        layout = QVBoxLayout()

        view = QLabel(
            """
                 🛰  ISS


                      |
                      |
                      |
        -------------------------------- Horizon

                  Nürnberg Ground Station
            """
        )

        view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        view.setStyleSheet(
            """
            QLabel {
                font-size: 22px;
                background-color: #111827;
                color: #E5E7EB;
                border-radius: 8px;
                padding: 20px;
            }
            """
        )

        layout.addWidget(view)
        box.setLayout(layout)

        return box

    def create_telemetry_panel(
        self,
        elevation,
        azimuth,
        range_km,
        range_rate,
        doppler,
        visibility,
    ):
        box = QGroupBox("Telemetry")
        form = QFormLayout()

        form.addRow("Satellite:", QLabel(self.iss.name))
        form.addRow("Time UTC:", QLabel("2026-06-23 03:00"))
        form.addRow("Elevation:", QLabel(f"{elevation:.2f}°"))
        form.addRow("Azimuth:", QLabel(f"{azimuth:.2f}°"))
        form.addRow("Range:", QLabel(f"{range_km:.2f} km"))
        form.addRow("Range Rate:", QLabel(f"{range_rate:.2f} m/s"))
        form.addRow("Doppler @ 437 MHz:", QLabel(f"{doppler:.2f} kHz"))
        form.addRow("Visibility:", QLabel(visibility))

        box.setLayout(form)
        box.setStyleSheet(
            """
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                margin-top: 10px;
            }
            QLabel {
                font-size: 16px;
                padding: 4px;
            }
            """
        )

        return box