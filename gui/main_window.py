from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QSplitter, QCheckBox,
    QPushButton, QComboBox, QSlider, QTabWidget, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer

from orbit.tracker import Tracker
from orbit.satellite_catalog import SATELLITES
from orbit.pass_predictor import PassPredictor

from recorder.replay import MissionReplay

from gui.doppler_plot import DopplerPlot
from gui.earth_view import EarthView
from gui.world_map_view import WorldMapView
from gui.status_bar import OrbitStatusBar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OrbitLab - Mission Control")
        self.resize(1200, 900)

        self.tracker = Tracker("ISS")
        self.data_source = self.tracker
        self.mode = "LIVE"

        self.pass_predictor = PassPredictor(self.tracker)
        self.is_running = True

        self.status_bar = OrbitStatusBar()
        self.setStatusBar(self.status_bar)

        central = QWidget()
        main_layout = QVBoxLayout()

        title = QLabel("OrbitLab Mission Control")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: bold; padding: 12px;")

        controls = self.create_controls()
        timeline = self.create_timeline()

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.earth_view = EarthView()
        self.world_map_view = WorldMapView()

        self.view_tabs = QTabWidget()
        self.view_tabs.addTab(self.earth_view, "3D Globe")
        self.view_tabs.addTab(self.world_map_view, "2D World Map")

        telemetry_panel = self.create_telemetry_panel()

        splitter.addWidget(self.view_tabs)
        splitter.addWidget(telemetry_panel)
        splitter.setSizes([750, 350])

        self.doppler_plot = DopplerPlot()

        main_layout.addWidget(title)
        main_layout.addLayout(controls)
        main_layout.addLayout(timeline)
        main_layout.addWidget(splitter)
        main_layout.addWidget(self.doppler_plot)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

        self.update_display(step_time=False)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_display)
        self.timer.start(1000)

    def create_controls(self):
        layout = QHBoxLayout()

        self.satellite_box = QComboBox()
        self.satellite_box.addItems(SATELLITES.keys())
        self.satellite_box.currentTextChanged.connect(self.change_satellite)

        self.play_button = QPushButton("Pause")
        self.play_button.clicked.connect(self.toggle_play)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_simulation)

        self.refresh_tle_button = QPushButton("Refresh TLE")
        self.refresh_tle_button.clicked.connect(self.refresh_tle)

        self.load_replay_button = QPushButton("Load Replay")
        self.load_replay_button.clicked.connect(self.load_replay)

        self.speed_box = QComboBox()
        self.speed_box.addItems([
            "1 min/step",
            "5 min/step",
            "10 min/step",
            "30 min/step"
        ])
        self.speed_box.currentIndexChanged.connect(self.change_speed)

        self.centered_checkbox = QCheckBox("Satellite Centered View")
        self.centered_checkbox.stateChanged.connect(self.toggle_centered_view)

        layout.addWidget(QLabel("Satellite:"))
        layout.addWidget(self.satellite_box)
        layout.addWidget(self.play_button)
        layout.addWidget(self.reset_button)
        layout.addWidget(self.refresh_tle_button)
        layout.addWidget(self.load_replay_button)
        layout.addWidget(QLabel("Speed:"))
        layout.addWidget(self.speed_box)
        layout.addWidget(self.centered_checkbox)

        return layout

    def create_timeline(self):
        layout = QHBoxLayout()

        self.timeline_label = QLabel("Timeline:")
        self.timeline_time_label = QLabel("03:00")

        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setMinimum(0)
        self.timeline_slider.setMaximum(24 * 60 - 1)
        self.timeline_slider.setValue(self.data_source.current_total_minutes())
        self.timeline_slider.sliderMoved.connect(self.timeline_changed)

        layout.addWidget(self.timeline_label)
        layout.addWidget(self.timeline_slider)
        layout.addWidget(self.timeline_time_label)

        return layout

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
        self.lat_label = QLabel()
        self.lon_label = QLabel()
        self.alt_label = QLabel()

        self.aos_label = QLabel()
        self.maxpass_label = QLabel()
        self.los_label = QLabel()
        self.duration_label = QLabel()

        form.addRow("Satellite:", self.satellite_label)
        form.addRow("Time UTC:", self.time_label)
        form.addRow("Elevation:", self.elevation_label)
        form.addRow("Azimuth:", self.azimuth_label)
        form.addRow("Range:", self.range_label)
        form.addRow("Range Rate:", self.range_rate_label)
        form.addRow("Doppler @ 437 MHz:", self.doppler_label)
        form.addRow("Visibility:", self.visibility_label)
        form.addRow("Sat Latitude:", self.lat_label)
        form.addRow("Sat Longitude:", self.lon_label)
        form.addRow("Sat Altitude:", self.alt_label)

        form.addRow(QLabel(""))
        next_pass_title = QLabel("Next Pass")
        next_pass_title.setStyleSheet("font-weight: bold; color: #4FC3F7;")
        form.addRow(next_pass_title)

        form.addRow("AOS:", self.aos_label)
        form.addRow("MAX:", self.maxpass_label)
        form.addRow("LOS:", self.los_label)
        form.addRow("Duration:", self.duration_label)

        box.setLayout(form)
        return box

    def timeline_changed(self, value):
        self.data_source.set_time_minutes(value)
        self.update_display(step_time=False)

    def change_satellite(self, satellite_key):
        self.tracker.set_satellite(satellite_key)
        self.tracker.reset()

        self.data_source = self.tracker
        self.mode = "LIVE"

        self.pass_predictor = PassPredictor(self.tracker)

        self.is_running = True
        self.play_button.setText("Pause")

        self.update_display(step_time=False)

    def toggle_play(self):
        self.is_running = not self.is_running
        self.play_button.setText("Pause" if self.is_running else "Play")

    def reset_simulation(self):
        self.data_source.reset()
        self.update_display(step_time=False)

    def refresh_tle(self):
        if self.mode != "LIVE":
            return

        self.status_bar.update_status(
            satellite_name=self.tracker.satellite.name,
            time_utc=self.tracker.clock.time_string(),
            tle_status="Refreshing...",
            status="Downloading...",
        )

        self.repaint()

        self.tracker.refresh_tle()
        self.pass_predictor = PassPredictor(self.tracker)

        self.update_display(step_time=False)

    def load_replay(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Mission Replay",
            "recordings",
            "JSON Files (*.json)"
        )

        if not filename:
            return

        self.data_source = MissionReplay(filename)
        self.mode = "REPLAY"

        self.is_running = True
        self.play_button.setText("Pause")

        self.update_display(step_time=False)

    def change_speed(self):
        speeds = [1, 5, 10, 30]

        if self.mode == "LIVE":
            self.tracker.set_speed(speeds[self.speed_box.currentIndex()])

    def toggle_centered_view(self):
        self.earth_view.set_centered_mode(
            self.centered_checkbox.isChecked()
        )

    def update_display(self, step_time=True):
        state = self.data_source.current_state()

        if state is None:
            return

        track = self.data_source.orbit_track()

        if self.mode == "LIVE":
            last_update = self.tracker.tle_last_update()
            tle_text = f"Cached ({last_update})" if last_update else "Not Cached"
            status_text = "Tracking"
        else:
            tle_text = "Replay File"
            status_text = "Replay Mode"

        self.status_bar.update_status(
            satellite_name=state.satellite_name,
            time_utc=state.time_utc,
            tle_status=tle_text,
            status=status_text,
        )

        self.satellite_label.setText(state.satellite_name)
        self.time_label.setText(state.time_utc)
        self.elevation_label.setText(f"{state.elevation_deg:.2f}°")
        self.azimuth_label.setText(f"{state.azimuth_deg:.2f}°")
        self.range_label.setText(f"{state.range_km:.2f} km")
        self.range_rate_label.setText(f"{state.range_rate_m_s:.2f} m/s")
        self.doppler_label.setText(f"{state.doppler_khz:.2f} kHz")
        self.visibility_label.setText(state.visibility)

        self.lat_label.setText(f"{state.sat_lat_deg:.2f}°")
        self.lon_label.setText(f"{state.sat_lon_deg:.2f}°")
        self.alt_label.setText(f"{state.sat_alt_km:.2f} km")

        if self.mode == "LIVE":
            pass_info = self.pass_predictor.predict_next_pass()
        else:
            pass_info = None

        if pass_info is not None:
            self.aos_label.setText(pass_info.aos_time)
            self.maxpass_label.setText(
                f"{pass_info.max_time} ({pass_info.max_elevation_deg:.1f}°)"
            )
            self.los_label.setText(pass_info.los_time)
            self.duration_label.setText(f"{pass_info.duration_min} min")
        else:
            self.aos_label.setText("-")
            self.maxpass_label.setText("-")
            self.los_label.setText("-")
            self.duration_label.setText("-")

        total_minutes = self.data_source.current_total_minutes()

        self.timeline_slider.blockSignals(True)
        self.timeline_slider.setValue(total_minutes)
        self.timeline_slider.blockSignals(False)

        h = total_minutes // 60
        m = total_minutes % 60
        self.timeline_time_label.setText(f"{h:02d}:{m:02d}")

        self.earth_view.update_scene(
            state.sat_lat_deg,
            state.sat_lon_deg,
            state.sat_alt_km,
            track,
        )

        self.world_map_view.update_scene(
            state.sat_lat_deg,
            state.sat_lon_deg,
            track,
        )

        if self.mode == "LIVE":
            self.world_map_view.update_pass_markers(pass_info)

        self.world_map_view.update_day_night(state.time_utc)

        self.doppler_plot.update_plot(state.doppler_khz)

        if self.is_running and step_time:
            self.data_source.step()