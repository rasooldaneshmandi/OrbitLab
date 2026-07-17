from datetime import datetime, timedelta
from hashlib import sha256
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from skyfield.api import load


class TLEManager:
    """
    Download, cache and manage TLE files.

    Features:
    - Windows-safe cache filenames
    - Separate cache file for each NORAD catalog number
    - Configurable cache expiration
    - Forced TLE refresh
    - Basic downloaded-file validation
    """

    CACHE_DIR = Path("cache") / "tle"

    def __init__(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _cache_file(self, tle_url: str) -> Path:
        """
        Convert a TLE URL into a safe local cache path.

        Example:

        https://celestrak.org/NORAD/elements/
        gp.php?CATNR=25544&FORMAT=tle

        becomes:

        cache/tle/celestrak_25544.tle
        """
        parsed_url = urlparse(tle_url)
        query = parse_qs(parsed_url.query)

        catalog_numbers = query.get("CATNR")

        if catalog_numbers:
            catalog_number = catalog_numbers[0].strip()

            if catalog_number.isdigit():
                return self.CACHE_DIR / (
                    f"celestrak_{catalog_number}.tle"
                )

        groups = query.get("GROUP")

        if groups:
            group_name = self._safe_filename(groups[0])

            if group_name:
                return self.CACHE_DIR / (
                    f"celestrak_group_{group_name}.tle"
                )

        original_filename = Path(parsed_url.path).name
        safe_filename = self._safe_filename(original_filename)

        if (
            safe_filename
            and safe_filename.lower() != "gp.php"
        ):
            return self.CACHE_DIR / safe_filename

        url_hash = sha256(
            tle_url.encode("utf-8")
        ).hexdigest()[:16]

        return self.CACHE_DIR / f"tle_{url_hash}.tle"

    @staticmethod
    def _safe_filename(value: str) -> str:
        """
        Replace characters that are invalid in Windows filenames.
        """
        invalid_characters = '<>:"/\\|?*'

        safe_value = value.strip()

        for character in invalid_characters:
            safe_value = safe_value.replace(character, "_")

        safe_value = safe_value.replace("&", "_")
        safe_value = safe_value.replace("=", "_")
        safe_value = safe_value.replace(" ", "_")

        while "__" in safe_value:
            safe_value = safe_value.replace("__", "_")

        return safe_value.strip("._")

    def load_tle_file(
        self,
        tle_url: str,
        max_age_hours: int = 24,
    ) -> Path:
        """
        Return a local TLE file.

        The TLE is downloaded when:

        - No cached file exists
        - The cached file is empty
        - The cached file is older than max_age_hours
        """
        if max_age_hours < 0:
            raise ValueError(
                "max_age_hours cannot be negative."
            )

        cache_path = self._cache_file(tle_url)

        if self._needs_refresh(
            cache_path=cache_path,
            max_age_hours=max_age_hours,
        ):
            self._download_tle(
                tle_url=tle_url,
                cache_path=cache_path,
                action="Downloading",
            )
        else:
            print(
                f"[TLE] Using cached file: "
                f"{cache_path.name}"
            )

        return cache_path

    def _needs_refresh(
        self,
        cache_path: Path,
        max_age_hours: int,
    ) -> bool:
        """
        Determine whether the local TLE cache must be refreshed.
        """
        if not cache_path.exists():
            return True

        if not cache_path.is_file():
            return True

        if cache_path.stat().st_size == 0:
            return True

        modification_time = datetime.fromtimestamp(
            cache_path.stat().st_mtime
        )

        age = datetime.now() - modification_time
        maximum_age = timedelta(hours=max_age_hours)

        return age >= maximum_age

    def _download_tle(
        self,
        tle_url: str,
        cache_path: Path,
        action: str,
    ) -> None:
        """
        Download and validate a TLE file.
        """
        cache_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(f"[TLE] {action}: {tle_url}")
        print(f"[TLE] Cache file: {cache_path}")

        try:
            load.download(
                tle_url,
                filename=str(cache_path),
            )
        except Exception:
            self._remove_empty_file(cache_path)
            raise

        self._validate_tle_file(cache_path)

    @staticmethod
    def _validate_tle_file(cache_path: Path) -> None:
        """
        Perform basic validation on a downloaded TLE file.
        """
        if not cache_path.exists():
            raise FileNotFoundError(
                f"TLE download did not create: {cache_path}"
            )

        if cache_path.stat().st_size == 0:
            cache_path.unlink(missing_ok=True)

            raise ValueError(
                "Downloaded TLE file is empty."
            )

        content = cache_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).strip()

        lines = [
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ]

        has_line_1 = any(
            line.startswith("1 ")
            for line in lines
        )

        has_line_2 = any(
            line.startswith("2 ")
            for line in lines
        )

        if not has_line_1 or not has_line_2:
            cache_path.unlink(missing_ok=True)

            raise ValueError(
                "Downloaded file does not contain a valid "
                "two-line element set."
            )

    @staticmethod
    def _remove_empty_file(cache_path: Path) -> None:
        """
        Delete an incomplete empty file after a failed download.
        """
        if (
            cache_path.exists()
            and cache_path.is_file()
            and cache_path.stat().st_size == 0
        ):
            cache_path.unlink(missing_ok=True)

    def last_update(self, tle_url: str):
        """
        Return the last cache-update time as a formatted string.
        """
        cache_path = self._cache_file(tle_url)

        if not cache_path.exists():
            return None

        if not cache_path.is_file():
            return None

        return datetime.fromtimestamp(
            cache_path.stat().st_mtime
        ).strftime("%Y-%m-%d %H:%M:%S")

    def force_refresh(self, tle_url: str) -> Path:
        """
        Download the requested TLE even when a valid cache exists.
        """
        cache_path = self._cache_file(tle_url)

        self._download_tle(
            tle_url=tle_url,
            cache_path=cache_path,
            action="Refreshing",
        )

        return cache_path