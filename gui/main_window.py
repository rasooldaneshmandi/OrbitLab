from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QGroupBox,
    QFormLayout,
    QSplitter,
)
from PyQt6.QtCore import Qt, QTimer

from orbit.tracker import Tracker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OrbitLab - Live Satellite Tracking Console")
        self.resize(1100, 700)

        self.tracker = Tracker()

        central = QWidget()
        main_layout = QVBoxLayout()

        title = QLabel("OrbitLab Mission Control")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 26px; font-weight: bold; padding: 12px;"
        )

        splitter = QSplitter(Qt.Orientation.Horizontal)

        earth_view = self.create_earth_view()
        telemetry_panel = self.create_telemetry_panel()

        splitter.addWidget(earth_view)
        splitter.addWidget(telemetry_panel)
        splitter.setSizes([650, 350])

        main_layout.addWidget(title)
        main_layout.addWidget(splitter)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

        self.update_display()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(1000)

    def create_earth_view(self):
        box = QGroupBox("Ground Station View")
        layout = QVBoxLayout()

        self.view_label = QLabel(
            """
                 🛰  ISS


                      |
                      |
                      |
        -------------------------------- Horizon

                  Nürnberg Ground Station
            """
        )

        self.view_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view_label.setStyleSheet(
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

        layout.addWidget(self.view_label)
        box.setLayout(layout)

        return box

    def create_telemetry_panel(self):
        box = QGroupBox("Telemetry")
        form = QFormLayout()

        self.satellite_label = QLabel()
        self.time_label = QLabel()
        self.elevation_label = QLabel()
        self.azimuth_label = QLabel()
        self.range_label = QLabel()
        self.range_rate_label = QLabel()
        self.doppler_label = QLabel()
        self.visibility_label = QLabel()

        form.addRow("Satellite:", self.satellite_label)
        form.addRow("Time UTC:", self.time_label)
        form.addRow("Elevation:", self.elevation_label)
        form.addRow("Azimuth:", self.azimuth_label)
        form.addRow("Range:", self.range_label)
        form.addRow("Range Rate:", self.range_rate_label)
        form.addRow("Doppler @ 437 MHz:", self.doppler_label)
        form.addRow("Visibility:", self.visibility_label)

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

    def update_display(self):
        state = self.tracker.current_state()

        self.satellite_label.setText(state.satellite_name)
        self.time_label.setText(state.time_utc)
        self.elevation_label.setText(f"{state.elevation_deg:.2f}°")
        self.azimuth_label.setText(f"{state.azimuth_deg:.2f}°")
        self.range_label.setText(f"{state.range_km:.2f} km")
        self.range_rate_label.setText(f"{state.range_rate_m_s:.2f} m/s")
        self.doppler_label.setText(f"{state.doppler_khz:.2f} kHz")
        self.visibility_label.setText(state.visibility)

        self.tracker.step()