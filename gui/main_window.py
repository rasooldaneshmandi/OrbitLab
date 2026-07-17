from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from orbit.pass_predictor import PassPredictor
from orbit.satellite_catalog import SATELLITES
from orbit.tracker import Tracker

from recorder.recorder import MissionRecorder
from recorder.replay import MissionReplay

from gui.doppler_plot import DopplerPlot
from gui.earth_view import EarthView
from gui.spectrum_plot import SpectrumPlot
from gui.status_bar import OrbitStatusBar
from gui.world_map_view import WorldMapView

from sdr.simulator import SDRSimulator
from sdr.spectrum import SpectrumAnalyzer


class MainWindow(QMainWindow):
    """
    Main OrbitLab mission-control window.

    The window integrates:

    - Live satellite tracking
    - Mission replay
    - Mission recording
    - Pass prediction
    - 3D Earth visualization
    - 2D world-map visualization
    - Doppler history
    - Simulated SDR IQ source
    - Live SDR spectrum analyzer
    """

    SDR_SAMPLE_RATE_HZ = 1_000_000
    SDR_TONE_FREQUENCY_HZ = 100_000
    SDR_FFT_SIZE = 4096

    def __init__(self):
        super().__init__()

        self.setWindowTitle("OrbitLab - Mission Control")
        self.resize(1400, 950)

        # --------------------------------------------------------------
        # Orbit tracking
        # --------------------------------------------------------------
        self.tracker = Tracker("ISS")
        self.data_source = self.tracker
        self.mode = "LIVE"

        self.pass_predictor = PassPredictor(self.tracker)

        # --------------------------------------------------------------
        # Mission recorder
        # --------------------------------------------------------------
        self.recorder = MissionRecorder()

        # --------------------------------------------------------------
        # SDR simulator
        # --------------------------------------------------------------
        self.sdr = SDRSimulator(
            sample_rate_hz=self.SDR_SAMPLE_RATE_HZ,
            tone_frequency_hz=self.SDR_TONE_FREQUENCY_HZ,
            noise_power=0.02,
        )

        self.is_running = True

        # --------------------------------------------------------------
        # Status bar
        # --------------------------------------------------------------
        self.status_bar = OrbitStatusBar()
        self.setStatusBar(self.status_bar)

        # --------------------------------------------------------------
        # Main widget
        # --------------------------------------------------------------
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        title = QLabel("OrbitLab Mission Control")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            """
            QLabel {
                font-size: 26px;
                font-weight: bold;
                padding: 12px;
            }
            """
        )

        main_layout.addWidget(title)
        main_layout.addLayout(self.create_controls())
        main_layout.addLayout(self.create_timeline())
        main_layout.addWidget(self.create_main_splitter())

        self.setCentralWidget(central_widget)

        # --------------------------------------------------------------
        # Initial display update
        # --------------------------------------------------------------
        self.update_display(step_time=False)

        # --------------------------------------------------------------
        # Main refresh timer
        # --------------------------------------------------------------
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_display)
        self.timer.start(1000)

    def create_main_splitter(self):
        """
        Create the main horizontal splitter.

        Left side:
            Earth and map views.

        Right side:
            Telemetry, Doppler plot and SDR spectrum.
        """
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.earth_view = EarthView()
        self.world_map_view = WorldMapView()

        self.view_tabs = QTabWidget()
        self.view_tabs.addTab(self.earth_view, "3D Globe")
        self.view_tabs.addTab(self.world_map_view, "2D World Map")

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.telemetry_panel = self.create_telemetry_panel()
        self.doppler_plot = DopplerPlot()
        self.spectrum_plot = SpectrumPlot()

        self.analysis_tabs = QTabWidget()
        self.analysis_tabs.addTab(self.doppler_plot, "Doppler")
        self.analysis_tabs.addTab(self.spectrum_plot, "SDR Spectrum")

        right_layout.addWidget(self.telemetry_panel)
        right_layout.addWidget(self.analysis_tabs)

        splitter.addWidget(self.view_tabs)
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([850, 550])

        return splitter

    def create_controls(self):
        """
        Create the main control row.
        """
        layout = QHBoxLayout()

        self.satellite_box = QComboBox()
        self.satellite_box.addItems(SATELLITES.keys())
        self.satellite_box.setCurrentText("ISS")
        self.satellite_box.currentTextChanged.connect(
            self.change_satellite
        )

        self.play_button = QPushButton("Pause")
        self.play_button.clicked.connect(self.toggle_play)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_simulation)

        self.refresh_tle_button = QPushButton("Refresh TLE")
        self.refresh_tle_button.clicked.connect(self.refresh_tle)

        self.start_record_button = QPushButton("Start Recording")
        self.start_record_button.clicked.connect(self.start_recording)

        self.stop_record_button = QPushButton("Stop Recording")
        self.stop_record_button.clicked.connect(self.stop_recording)

        self.load_replay_button = QPushButton("Load Replay")
        self.load_replay_button.clicked.connect(self.load_replay)

        self.return_live_button = QPushButton("Return to Live")
        self.return_live_button.clicked.connect(self.return_to_live)
        self.return_live_button.setEnabled(False)

        self.speed_box = QComboBox()
        self.speed_box.addItems(
            [
                "1 min/step",
                "5 min/step",
                "10 min/step",
                "30 min/step",
            ]
        )
        self.speed_box.currentIndexChanged.connect(self.change_speed)

        self.centered_checkbox = QCheckBox(
            "Satellite Centered View"
        )
        self.centered_checkbox.stateChanged.connect(
            self.toggle_centered_view
        )

        layout.addWidget(QLabel("Satellite:"))
        layout.addWidget(self.satellite_box)
        layout.addWidget(self.play_button)
        layout.addWidget(self.reset_button)
        layout.addWidget(self.refresh_tle_button)
        layout.addWidget(self.start_record_button)
        layout.addWidget(self.stop_record_button)
        layout.addWidget(self.load_replay_button)
        layout.addWidget(self.return_live_button)
        layout.addWidget(QLabel("Speed:"))
        layout.addWidget(self.speed_box)
        layout.addWidget(self.centered_checkbox)

        return layout

    def create_timeline(self):
        """
        Create the 24-hour mission timeline.
        """
        layout = QHBoxLayout()

        self.timeline_label = QLabel("Timeline:")
        self.timeline_time_label = QLabel("00:00")

        self.timeline_slider = QSlider(
            Qt.Orientation.Horizontal
        )
        self.timeline_slider.setMinimum(0)
        self.timeline_slider.setMaximum(24 * 60 - 1)

        initial_minutes = self.data_source.current_total_minutes()
        self.timeline_slider.setValue(initial_minutes)

        self.timeline_slider.sliderMoved.connect(
            self.timeline_changed
        )

        layout.addWidget(self.timeline_label)
        layout.addWidget(self.timeline_slider)
        layout.addWidget(self.timeline_time_label)

        return layout

    def create_telemetry_panel(self):
        """
        Create satellite telemetry and next-pass information panel.
        """
        box = QGroupBox("Telemetry")
        form = QFormLayout()

        self.satellite_label = QLabel("-")
        self.time_label = QLabel("-")
        self.elevation_label = QLabel("-")
        self.azimuth_label = QLabel("-")
        self.range_label = QLabel("-")
        self.range_rate_label = QLabel("-")
        self.doppler_label = QLabel("-")
        self.visibility_label = QLabel("-")
        self.lat_label = QLabel("-")
        self.lon_label = QLabel("-")
        self.alt_label = QLabel("-")

        self.aos_label = QLabel("-")
        self.maxpass_label = QLabel("-")
        self.los_label = QLabel("-")
        self.duration_label = QLabel("-")

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
        next_pass_title.setStyleSheet(
            "font-weight: bold; color: #4FC3F7;"
        )
        form.addRow(next_pass_title)

        form.addRow("AOS:", self.aos_label)
        form.addRow("MAX:", self.maxpass_label)
        form.addRow("LOS:", self.los_label)
        form.addRow("Duration:", self.duration_label)

        box.setLayout(form)

        return box

    def timeline_changed(self, value):
        """
        Move the active data source to the selected minute of the day.
        """
        try:
            self.data_source.set_time_minutes(value)
            self.update_display(step_time=False)
        except AttributeError:
            self.show_status_message(
                "Current data source does not support timeline control."
            )

    def change_satellite(self, satellite_key):
        """
        Change the active satellite and return to live mode.
        """
        if not satellite_key:
            return

        try:
            self.tracker.set_satellite(satellite_key)
            self.tracker.reset()

            self.data_source = self.tracker
            self.mode = "LIVE"

            self.pass_predictor = PassPredictor(self.tracker)

            self.is_running = True
            self.play_button.setText("Pause")

            self.update_mode_controls()
            self.update_display(step_time=False)

        except Exception as error:
            self.show_status_message(
                f"Satellite change failed: {error}"
            )

    def toggle_play(self):
        """
        Pause or resume simulation/replay stepping.
        """
        self.is_running = not self.is_running

        if self.is_running:
            self.play_button.setText("Pause")
        else:
            self.play_button.setText("Play")

    def reset_simulation(self):
        """
        Reset the active data source.
        """
        try:
            self.data_source.reset()
            self.update_display(step_time=False)
        except Exception as error:
            self.show_status_message(
                f"Reset failed: {error}"
            )

    def refresh_tle(self):
        """
        Download and reload the TLE for the active satellite.
        """
        if self.mode != "LIVE":
            self.show_status_message(
                "TLE refresh is only available in live mode."
            )
            return

        try:
            self.status_bar.update_status(
                satellite_name=self.tracker.satellite.name,
                time_utc=self.tracker.clock.time_string(),
                tle_status="Refreshing...",
                status="Downloading TLE...",
            )

            self.repaint()

            self.tracker.refresh_tle()
            self.pass_predictor = PassPredictor(self.tracker)

            self.update_display(step_time=False)

        except Exception as error:
            self.show_status_message(
                f"TLE refresh failed: {error}"
            )

    def start_recording(self):
        """
        Start recording live tracking states.
        """
        if self.mode != "LIVE":
            self.show_status_message(
                "Recording is only available in live mode."
            )
            return

        if self.recorder.is_recording:
            self.show_status_message(
                "Mission recording is already active."
            )
            return

        self.recorder.start()

        self.status_bar.update_status(
            satellite_name=self.tracker.satellite.name,
            time_utc=self.tracker.clock.time_string(),
            tle_status="Cached",
            status="Recording...",
        )

    def stop_recording(self):
        """
        Stop mission recording and save its JSON file.
        """
        try:
            path = self.recorder.stop()

            if path is None:
                state = self.data_source.current_state()

                if state is not None:
                    self.status_bar.update_status(
                        satellite_name=state.satellite_name,
                        time_utc=state.time_utc,
                        tle_status="Cached",
                        status="No recording saved",
                    )

                return

            state = self.data_source.current_state()

            if state is not None:
                self.status_bar.update_status(
                    satellite_name=state.satellite_name,
                    time_utc=state.time_utc,
                    tle_status="Cached",
                    status=f"Saved: {path.name}",
                )

        except Exception as error:
            self.show_status_message(
                f"Recording stop failed: {error}"
            )

    def load_replay(self):
        """
        Load a mission JSON recording and switch to replay mode.
        """
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Mission Replay",
            "recordings",
            "JSON Files (*.json)",
        )

        if not filename:
            return

        try:
            if self.recorder.is_recording:
                self.recorder.stop()

            replay = MissionReplay(filename)

            initial_state = replay.current_state()

            if initial_state is None:
                self.show_status_message(
                    "The selected replay file contains no mission states."
                )
                return

            self.data_source = replay
            self.mode = "REPLAY"

            self.is_running = True
            self.play_button.setText("Pause")

            self.update_mode_controls()
            self.update_display(step_time=False)

        except Exception as error:
            self.show_status_message(
                f"Replay loading failed: {error}"
            )

    def return_to_live(self):
        """
        Exit replay mode and return to the live tracker.
        """
        self.data_source = self.tracker
        self.mode = "LIVE"

        self.pass_predictor = PassPredictor(self.tracker)

        self.is_running = True
        self.play_button.setText("Pause")

        self.update_mode_controls()
        self.update_display(step_time=False)

    def update_mode_controls(self):
        """
        Enable and disable controls according to the active mode.
        """
        live_mode = self.mode == "LIVE"

        self.satellite_box.setEnabled(live_mode)
        self.refresh_tle_button.setEnabled(live_mode)
        self.start_record_button.setEnabled(live_mode)
        self.stop_record_button.setEnabled(live_mode)
        self.speed_box.setEnabled(live_mode)

        self.return_live_button.setEnabled(not live_mode)

    def change_speed(self):
        """
        Change live simulation stepping speed.
        """
        speeds = [1, 5, 10, 30]

        if self.mode != "LIVE":
            return

        selected_speed = speeds[
            self.speed_box.currentIndex()
        ]

        self.tracker.set_speed(selected_speed)

    def toggle_centered_view(self):
        """
        Enable or disable satellite-centered globe view.
        """
        self.earth_view.set_centered_mode(
            self.centered_checkbox.isChecked()
        )

    def update_display(self, step_time=True):
        """
        Refresh all mission-control widgets.

        This function is called once per second by the main timer.
        """
        try:
            state = self.data_source.current_state()

            if state is None:
                if self.mode == "REPLAY":
                    self.is_running = False
                    self.play_button.setText("Play")
                    self.show_status_message(
                        "Replay finished."
                    )
                return

            track = self.data_source.orbit_track()

            pass_info = self.update_status_and_pass(state)

            self.update_telemetry(state, pass_info)
            self.update_timeline()
            self.update_visualizations(
                state,
                track,
                pass_info,
            )
            self.update_sdr_spectrum()

            if (
                self.mode == "LIVE"
                and self.recorder.is_recording
            ):
                self.recorder.record(state)

            if self.is_running and step_time:
                self.data_source.step()

        except Exception as error:
            self.is_running = False
            self.play_button.setText("Play")

            self.show_status_message(
                f"Display update failed: {error}"
            )

    def update_status_and_pass(self, state):
        """
        Update the status bar and return current pass information.
        """
        if self.mode == "LIVE":
            last_update = self.tracker.tle_last_update()

            if last_update:
                tle_text = f"Cached ({last_update})"
            else:
                tle_text = "Not Cached"

            if self.recorder.is_recording:
                status_text = "Recording..."
            else:
                status_text = "Tracking"

            try:
                pass_info = (
                    self.pass_predictor.predict_next_pass()
                )
            except Exception:
                pass_info = None

        else:
            tle_text = "Replay File"
            status_text = "Replay Mode"
            pass_info = None

        self.status_bar.update_status(
            satellite_name=state.satellite_name,
            time_utc=state.time_utc,
            tle_status=tle_text,
            status=status_text,
        )

        return pass_info

    def update_telemetry(self, state, pass_info):
        """
        Update satellite telemetry labels.
        """
        self.satellite_label.setText(
            state.satellite_name
        )
        self.time_label.setText(
            state.time_utc
        )
        self.elevation_label.setText(
            f"{state.elevation_deg:.2f}°"
        )
        self.azimuth_label.setText(
            f"{state.azimuth_deg:.2f}°"
        )
        self.range_label.setText(
            f"{state.range_km:.2f} km"
        )
        self.range_rate_label.setText(
            f"{state.range_rate_m_s:.2f} m/s"
        )
        self.doppler_label.setText(
            f"{state.doppler_khz:.2f} kHz"
        )
        self.visibility_label.setText(
            state.visibility
        )
        self.lat_label.setText(
            f"{state.sat_lat_deg:.2f}°"
        )
        self.lon_label.setText(
            f"{state.sat_lon_deg:.2f}°"
        )
        self.alt_label.setText(
            f"{state.sat_alt_km:.2f} km"
        )

        if pass_info is None:
            self.aos_label.setText("-")
            self.maxpass_label.setText("-")
            self.los_label.setText("-")
            self.duration_label.setText("-")
            return

        self.aos_label.setText(
            pass_info.aos_time
        )
        self.maxpass_label.setText(
            f"{pass_info.max_time} "
            f"({pass_info.max_elevation_deg:.1f}°)"
        )
        self.los_label.setText(
            pass_info.los_time
        )
        self.duration_label.setText(
            f"{pass_info.duration_min} min"
        )

    def update_timeline(self):
        """
        Synchronize the timeline slider with the active data source.
        """
        total_minutes = (
            self.data_source.current_total_minutes()
        )

        total_minutes = max(
            0,
            min(total_minutes, 24 * 60 - 1),
        )

        self.timeline_slider.blockSignals(True)
        self.timeline_slider.setValue(total_minutes)
        self.timeline_slider.blockSignals(False)

        hours = total_minutes // 60
        minutes = total_minutes % 60

        self.timeline_time_label.setText(
            f"{hours:02d}:{minutes:02d}"
        )

    def update_visualizations(
        self,
        state,
        track,
        pass_info,
    ):
        """
        Update all orbit and Doppler visualizations.
        """
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
            self.world_map_view.update_pass_markers(
                pass_info
            )
        else:
            self.world_map_view.update_pass_markers(
                None
            )

        self.world_map_view.update_day_night(
            state.time_utc
        )

        self.doppler_plot.update_plot(
            state.doppler_khz
        )

    def update_sdr_spectrum(self):
        """
        Generate simulated IQ data and update the spectrum plot.
        """
        iq_samples = self.sdr.read_samples(
            self.SDR_FFT_SIZE
        )

        frequencies_hz, power_db = (
            SpectrumAnalyzer.compute_fft(
                iq_samples,
                self.sdr.sample_rate(),
            )
        )

        self.spectrum_plot.update_spectrum(
            frequencies_hz,
            power_db,
        )

    def show_status_message(self, message):
        """
        Display an application message in the status bar.
        """
        try:
            state = self.data_source.current_state()
        except Exception:
            state = None

        if state is not None:
            satellite_name = state.satellite_name
            time_utc = state.time_utc
        else:
            satellite_name = "-"
            time_utc = "-"

        if self.mode == "LIVE":
            tle_status = "Cached"
        else:
            tle_status = "Replay File"

        self.status_bar.update_status(
            satellite_name=satellite_name,
            time_utc=time_utc,
            tle_status=tle_status,
            status=message,
        )

    def closeEvent(self, event):
        """
        Stop timers and safely finish recording before closing.
        """
        self.timer.stop()

        if self.recorder.is_recording:
            try:
                self.recorder.stop()
            except Exception:
                pass

        event.accept()