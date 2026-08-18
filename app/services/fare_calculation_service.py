from math import asin, cos, radians, sin, sqrt


class FareCalculationService:
    BASE_FARES = {
        "bike": 25.0,
        "auto": 35.0,
        "mini": 50.0,
        "sedan": 75.0,
        "suv": 110.0,
        "luxury": 180.0,
    }
    PER_KM = {
        "bike": 8.0,
        "auto": 11.0,
        "mini": 14.0,
        "sedan": 18.0,
        "suv": 24.0,
        "luxury": 40.0,
    }

    def distance_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius_km = 6371.0
        d_lat = radians(lat2 - lat1)
        d_lon = radians(lon2 - lon1)
        a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
        return round(2 * radius_km * asin(sqrt(a)), 2)

    def estimate_fare(self, ride_type: str, distance_km: float, surge_multiplier: float = 1.0) -> float:
        base_fare = self.BASE_FARES[ride_type]
        distance_fare = distance_km * self.PER_KM[ride_type]
        return round((base_fare + distance_fare) * surge_multiplier, 2)
