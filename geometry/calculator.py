class GeometryCalculator:

    @staticmethod
    def elevation_deg(topocentric):
        elevation, _, _ = topocentric.altaz()
        return elevation.degrees

    @staticmethod
    def azimuth_deg(topocentric):
        _, azimuth, _ = topocentric.altaz()
        return azimuth.degrees

    @staticmethod
    def range_km(topocentric):
        _, _, distance = topocentric.altaz()
        return distance.km

    @staticmethod
    def distance_m(topocentric):
        return topocentric.distance().m

    @staticmethod
    def range_rate_m_s(distance_now_m, distance_next_m, dt_seconds):
        return (distance_next_m - distance_now_m) / dt_seconds