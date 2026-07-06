from dataclasses import dataclass


@dataclass
class TrackingState:
    satellite_name: str
    time_utc: str

    elevation_deg: float
    azimuth_deg: float

    range_km: float
    range_rate_m_s: float

    doppler_khz: float

    visibility: str

    sat_lat_deg: float
    sat_lon_deg: float
    sat_alt_km: float