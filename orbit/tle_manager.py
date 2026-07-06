from pathlib import Path
from datetime import datetime, timedelta
from skyfield.api import load


class TLEManager:
    """
    Responsible for downloading, caching and loading TLE files.
    """

    CACHE_DIR = Path("cache/tle")

    def __init__(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _cache_file(self, tle_url: str) -> Path:
        filename = tle_url.split("/")[-1]
        return self.CACHE_DIR / filename

    def load_tle_file(self, tle_url: str, max_age_hours: int = 24):
        """
        Returns a local TLE file.
        Downloads it only if:
            - file doesn't exist
            - file is older than max_age_hours
        """

        cache_path = self._cache_file(tle_url)

        refresh = True

        if cache_path.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)

            if age < timedelta(hours=max_age_hours):
                refresh = False

        if refresh:
            print(f"[TLE] Downloading {tle_url}")
            load.download(tle_url, filename=str(cache_path))
        else:
            print(f"[TLE] Using cached file {cache_path.name}")

        return cache_path

    def last_update(self, tle_url: str):
        cache_path = self._cache_file(tle_url)

        if not cache_path.exists():
            return None

        return datetime.fromtimestamp(
            cache_path.stat().st_mtime
        ).strftime("%Y-%m-%d %H:%M:%S")

    def force_refresh(self, tle_url: str):
        cache_path = self._cache_file(tle_url)

        print(f"[TLE] Refreshing {tle_url}")
        load.download(tle_url, filename=str(cache_path))

        return cache_path