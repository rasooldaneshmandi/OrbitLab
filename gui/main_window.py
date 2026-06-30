from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QGroupBox,
    QFormLayout,
    QSplitter,
)
from PyQt6.QtCore import Qt

from orbit.tracker import Tracker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OrbitLab - Satellite Tracking Console")
        self.resize(1100, 700)

        self.tracker = Tracker()
        state = self.tracker.current_state()

        central = QWidget()
        main_layout = QVBoxLayout()

        title = QLabel("OrbitLab Mission Control")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 26px; font-weight: bold; padding: 12px;"
        )

        splitter = QSplitter(Qt.Orientation.Horizontal)

        earth_view = self.create_earth_view()
        telemetry_panel = self.create_telemetry_panel(state)

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

    def create_telemetry_panel(self, state):
        box = QGroupBox("Telemetry")
        form = QFormLayout()

        form.addRow("Satellite:", QLabel(state.satellite_name))
        form.addRow("Time UTC:", QLabel(state.time_utc))
        form.addRow("Elevation:", QLabel(f"{state.elevation_deg:.2f}°"))
        form.addRow("Azimuth:", QLabel(f"{state.azimuth_deg:.2f}°"))
        form.addRow("Range:", QLabel(f"{state.range_km:.2f} km"))
        form.addRow("Range Rate:", QLabel(f"{state.range_rate_m_s:.2f} m/s"))
        form.addRow("Doppler @ 437 MHz:", QLabel(f"{state.doppler_khz:.2f} kHz"))
        form.addRow("Visibility:", QLabel(state.visibility))

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