import json
from pathlib import Path
from datetime import datetime


class MissionStorage:
    RECORDINGS_DIR = Path("recordings")

    def __init__(self):
        self.RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

    def generate_filename(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.RECORDINGS_DIR / f"mission_{timestamp}.json"

    def save(self, data, filename=None):
        if filename is None:
            filename = self.generate_filename()

        path = Path(filename)

        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        return path

    def load(self, filename):
        path = Path(filename)

        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)