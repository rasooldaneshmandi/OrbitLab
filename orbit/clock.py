class SimulationClock:
    def __init__(
        self,
        year=2026,
        month=6,
        day=23,
        hour=3,
        minute=0,
        step_minutes=1,
    ):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.step_minutes = step_minutes

    def current_time(self):
        return self.year, self.month, self.day, self.hour, self.minute

    def next_time(self):
        next_minute = self.minute + self.step_minutes
        next_hour = self.hour + next_minute // 60
        next_minute = next_minute % 60

        return self.year, self.month, self.day, next_hour, next_minute

    def step(self):
        self.minute += self.step_minutes

        if self.minute >= 60:
            self.hour += self.minute // 60
            self.minute = self.minute % 60

        if self.hour >= 24:
            self.hour = self.hour % 24

    def time_string(self):
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d} {self.hour:02d}:{self.minute:02d}"