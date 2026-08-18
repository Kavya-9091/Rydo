from dataclasses import dataclass


@dataclass(frozen=True)
class GeocodedLocation:
    display_name: str
    latitude: float
    longitude: float


BENGALURU_LOCATIONS: dict[str, GeocodedLocation] = {
    "airport": GeocodedLocation("Kempegowda International Airport, Bengaluru", 13.1986, 77.7066),
    "kempegowda international airport": GeocodedLocation("Kempegowda International Airport, Bengaluru", 13.1986, 77.7066),
    "mg road": GeocodedLocation("MG Road, Bengaluru", 12.9756, 77.6068),
    "marathahalli": GeocodedLocation("Marathahalli, Bengaluru", 12.9592, 77.6974),
    "majestic": GeocodedLocation("Majestic, Bengaluru", 12.9767, 77.5713),
    "mejestic": GeocodedLocation("Majestic, Bengaluru", 12.9767, 77.5713),
    "kempegowda bus station": GeocodedLocation("Majestic, Bengaluru", 12.9767, 77.5713),
    "kr puram": GeocodedLocation("KR Puram, Bengaluru", 13.0075, 77.6959),
    "krpuram": GeocodedLocation("KR Puram, Bengaluru", 13.0075, 77.6959),
    "k r puram": GeocodedLocation("KR Puram, Bengaluru", 13.0075, 77.6959),
    "hosakote": GeocodedLocation("Hoskote, Bengaluru Rural", 13.0707, 77.7981),
    "hoskote": GeocodedLocation("Hoskote, Bengaluru Rural", 13.0707, 77.7981),
    "electronic city": GeocodedLocation("Electronic City, Bengaluru", 12.8452, 77.6602),
    "hebbal": GeocodedLocation("Hebbal, Bengaluru", 13.0358, 77.5970),
    "yelahanka": GeocodedLocation("Yelahanka, Bengaluru", 13.1007, 77.5963),
    "yelahanka old town": GeocodedLocation("Yelahanka Old Town, Bengaluru", 13.1015, 77.5888),
    "yelahanka new town": GeocodedLocation("Yelahanka New Town, Bengaluru", 13.0939, 77.5828),
    "indiranagar": GeocodedLocation("Indiranagar, Bengaluru", 12.9784, 77.6408),
    "whitefield": GeocodedLocation("Whitefield, Bengaluru", 12.9698, 77.7500),
    "koramangala": GeocodedLocation("Koramangala, Bengaluru", 12.9352, 77.6245),
    "hsr layout": GeocodedLocation("HSR Layout, Bengaluru", 12.9116, 77.6474),
    "btm layout": GeocodedLocation("BTM Layout, Bengaluru", 12.9166, 77.6101),
}


def geocode_bengaluru_location(query: str) -> GeocodedLocation | None:
    normalized = " ".join(query.lower().replace(",", " ").split())
    if normalized in BENGALURU_LOCATIONS:
        return BENGALURU_LOCATIONS[normalized]
    for key, location in BENGALURU_LOCATIONS.items():
        if key in normalized or normalized in key:
            return location
    return None
