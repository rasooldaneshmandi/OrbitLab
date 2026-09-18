from recorder.storage import MissionStorage


class MissionRecorder:
    def __init__(self):
        self.storage = MissionStorage()

        self.is_recording = False
        self.records = []

    def start(self):
        self.records.clear()
        self.is_recording = True

    def stop(self):
        self.is_recording = False

        if len(self.records) == 0:
            return None

        return self.storage.save(self.records)

    def record(self, state):
        if not self.is_recording:
            return

        self.records.append({
            "time": state.time_utc,

            "satellite": state.satellite_name,

            "lat": state.sat_lat_deg,
            "lon": state.sat_lon_deg,
            "alt": state.sat_alt_km,

            "elevation": state.elevation_deg,
            "azimuth": state.azimuth_deg,

            "range": state.range_km,
            "range_rate": state.range_rate_m_s,

            "doppler": state.doppler_khz,

            "visibility": state.visibility
        })

    @property
    def count(self):
        return len(self.records)