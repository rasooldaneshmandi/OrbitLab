from dataclasses import dataclass


@dataclass
class PassInfo:
    aos_time: str
    max_time: str
    los_time: str
    max_elevation_deg: float
    duration_min: int


class PassPredictor:
    def __init__(self, tracker):
        self.tracker = tracker

    def predict_next_pass(self, search_minutes=24 * 60):
        """
        Finds the next visible pass using elevation > 0.
        """

        original_time = self.tracker.current_total_minutes()

        in_pass = False
        aos = None
        max_el = -999
        max_time = None

        for offset in range(search_minutes):
            test_minute = (original_time + offset) % (24 * 60)
            self.tracker.set_time_minutes(test_minute)

            state = self.tracker.current_state()
            elevation = state.elevation_deg

            if elevation > 0 and not in_pass:
                in_pass = True
                aos = test_minute
                max_el = elevation
                max_time = test_minute

            if in_pass and elevation > max_el:
                max_el = elevation
                max_time = test_minute

            if in_pass and elevation <= 0:
                los = test_minute

                self.tracker.set_time_minutes(original_time)

                return PassInfo(
                    aos_time=self._format_time(aos),
                    max_time=self._format_time(max_time),
                    los_time=self._format_time(los),
                    max_elevation_deg=max_el,
                    duration_min=(los - aos) % (24 * 60),
                )

        self.tracker.set_time_minutes(original_time)
        return None

    def _format_time(self, total_minutes):
        h = total_minutes // 60
        m = total_minutes % 60
        return f"{h:02d}:{m:02d}"