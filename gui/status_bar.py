from PyQt6.QtWidgets import QStatusBar, QLabel


class OrbitStatusBar(QStatusBar):
    def __init__(self):
        super().__init__()

        self.satellite_label = QLabel("Satellite: -")
        self.tle_label = QLabel("TLE: -")
        self.time_label = QLabel("UTC: -")
        self.status_label = QLabel("Ready")

        self.addPermanentWidget(self.satellite_label)
        self.addPermanentWidget(self.tle_label)
        self.addPermanentWidget(self.time_label)
        self.addPermanentWidget(self.status_label)

    def update_status(self, satellite_name, time_utc, tle_status="Cached", status="Ready"):
        self.satellite_label.setText(f"Satellite: {satellite_name}")
        self.tle_label.setText(f"TLE: {tle_status}")
        self.time_label.setText(f"UTC: {time_utc}")
        self.status_label.setText(status)