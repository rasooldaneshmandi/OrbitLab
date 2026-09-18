class VisibilityChecker:
    @staticmethod
    def is_visible(elevation_deg: float) -> bool:
        return elevation_deg > 0

    @staticmethod
    def status(elevation_deg: float) -> str:
        if elevation_deg > 0:
            return "VISIBLE"
        elif elevation_deg == 0:
            return "ON HORIZON"
        else:
            return "NOT VISIBLE"