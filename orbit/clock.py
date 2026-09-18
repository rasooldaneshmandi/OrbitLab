class SimulationClock:
    def __init__(self, year=2026, month=6, day=23, hour=3, minute=0, step_minutes=1):
        self.start_year = year
        self.start_month = month
        self.start_day = day
        self.start_hour = hour
        self.start_minute = minute

        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.step_minutes = step_minutes

    def current_time(self):
        return self.year, self.month, self.day, self.hour, self.minute

    def current_total_minutes(self):
        return self.hour * 60 + self.minute

    def next_time(self):
        total = self.current_total_minutes() + self.step_minutes
        return self.year, self.month, self.day, (total // 60) % 24, total % 60

    def step(self):
        self.set_total_minutes(self.current_total_minutes() + self.step_minutes)

    def set_step_minutes(self, step_minutes):
        self.step_minutes = step_minutes

    def set_total_minutes(self, total_minutes):
        total_minutes = total_minutes % (24 * 60)
        self.hour = total_minutes // 60
        self.minute = total_minutes % 60

    def reset(self):
        self.year = self.start_year
        self.month = self.start_month
        self.day = self.start_day
        self.hour = self.start_hour
        self.minute = self.start_minute

    def time_string(self):
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d} {self.hour:02d}:{self.minute:02d}"