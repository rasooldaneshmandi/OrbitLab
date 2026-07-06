from orbit.data_source import DataSource
from orbit.tracking_state import TrackingState
from recorder.storage import MissionStorage


class MissionReplay(DataSource):
    def __init__(self, filename):
        self.storage = MissionStorage()
        self.records = self.storage.load(filename)
        self.index = 0

    def current_state(self):
        if not self.records:
            return None

        r = self.records[self.index]

        return TrackingState(
            satellite_name=r["satellite"],
            time_utc=r["time"],
            elevation_deg=r["elevation"],
            azimuth_deg=r["azimuth"],
            range_km=r["range"],
            range_rate_m_s=r["range_rate"],
            doppler_khz=r["doppler"],
            visibility=r["visibility"],
            sat_lat_deg=r["lat"],
            sat_lon_deg=r["lon"],
            sat_alt_km=r["alt"],
        )

    def step(self):
        if self.records:
            self.index = (self.index + 1) % len(self.records)

    def reset(self):
        self.index = 0

    def length(self):
        return len(self.records)

    def orbit_track(self, minutes_before=30, minutes_after=30, step_minutes=1):
        if not self.records:
            return []

        start = max(0, self.index - minutes_before)
        stop = min(len(self.records), self.index + minutes_after + 1)

        return [
            {
                "lat": r["lat"],
                "lon": r["lon"],
                "alt": r["alt"],
                "time": r["time"],
            }
            for r in self.records[start:stop]
        ]

    def current_total_minutes(self):
        state = self.current_state()
        if state is None:
            return 0

        hhmm = state.time_utc.split(" ")[1]
        hour, minute = hhmm.split(":")
        return int(hour) * 60 + int(minute)

    def set_time_minutes(self, total_minutes):
        if not self.records:
            return

        best_index = 0
        best_diff = 999999

        for i, r in enumerate(self.records):
            hhmm = r["time"].split(" ")[1]
            hour, minute = hhmm.split(":")
            record_min = int(hour) * 60 + int(minute)

            diff = abs(record_min - total_minutes)

            if diff < best_diff:
                best_diff = diff
                best_index = i

        self.index = best_index