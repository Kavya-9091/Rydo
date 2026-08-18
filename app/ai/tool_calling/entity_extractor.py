import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from app.ai.tool_calling.geocoder import geocode_bengaluru_location
from app.ai.tool_calling.tools import VALID_VEHICLE_TYPES


@dataclass
class ExtractedEntities:
    intent: str
    pickup: str | None = None
    destination: str | None = None
    ride_time: str | None = None
    vehicle_type: str | None = None
    ride_id: str | None = None
    payment_id: str | None = None
    registration_numbers: list[str] = field(default_factory=list)
    rating: int | None = None
    pickup_latitude: float | None = None
    pickup_longitude: float | None = None
    dropoff_latitude: float | None = None
    dropoff_longitude: float | None = None
    missing_fields: list[str] = field(default_factory=list)

    def as_prompt_context(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "pickup_address": self.pickup,
            "pickup_latitude": self.pickup_latitude,
            "pickup_longitude": self.pickup_longitude,
            "dropoff_address": self.destination,
            "dropoff_latitude": self.dropoff_latitude,
            "dropoff_longitude": self.dropoff_longitude,
            "ride_time": self.ride_time,
            "vehicle_type": self.vehicle_type,
            "ride_id": self.ride_id,
            "payment_id": self.payment_id,
            "registration_numbers": self.registration_numbers,
            "rating": self.rating,
            "missing_fields": self.missing_fields,
        }


def extract_entities(message: str) -> ExtractedEntities:
    normalized = " ".join(message.strip().split())
    lower = normalized.lower()
    intent = _intent(lower)
    entities = ExtractedEntities(intent=intent)
    entities.vehicle_type = _vehicle_type(lower)
    entities.ride_id = _uuid_in_text(normalized)
    entities.registration_numbers = _registration_numbers(normalized)
    entities.rating = _rating(lower)
    entities.ride_time = _ride_time(lower)

    pickup, destination = _pickup_destination(normalized)
    entities.pickup = pickup
    entities.destination = destination

    if entities.pickup:
        coordinates = geocode_bengaluru_location(entities.pickup)
        if coordinates:
            entities.pickup = coordinates.display_name
            entities.pickup_latitude = coordinates.latitude
            entities.pickup_longitude = coordinates.longitude
    if entities.destination:
        coordinates = geocode_bengaluru_location(entities.destination)
        if coordinates:
            entities.destination = coordinates.display_name
            entities.dropoff_latitude = coordinates.latitude
            entities.dropoff_longitude = coordinates.longitude

    entities.missing_fields = _missing_for_intent(entities)
    return entities


def _intent(lower: str) -> str:
    if "approve" in lower and ("vehicle" in lower or "vehicles" in lower):
        return "approve_vehicles"
    if re.fullmatch(r"(accept|accept recent|accept ride|accept this ride)", lower) or re.search(r"\baccept\b", lower):
        return "accept_ride"
    if re.fullmatch(r"(reject|reject recent|reject ride|reject this ride|decline|decline ride)", lower) or re.search(r"\b(reject|decline)\b", lower):
        return "reject_ride"
    if re.fullmatch(r"(start|start ride|begin ride|pickup started)", lower) or re.search(r"\b(start|begin)\s+(?:the\s+)?ride\b", lower):
        return "start_ride"
    if (
        re.fullmatch(r"(complete|completed|complete ride|completed ride|finish ride|finished ride|end ride|completed pay now)", lower)
        or re.search(r"\b(complete|completed|finish|finished|end)\s+(?:the\s+)?ride\b", lower)
    ):
        return "complete_ride"
    if any(word in lower for word in ["cancel", "stop my ride"]):
        return "cancel_ride"
    if re.search(r"\b(pay|payment|paid)\b", lower):
        return "payment_status"
    if "status" in lower or "where is" in lower or "track" in lower:
        return "get_ride_status"
    if "history" in lower or "past rides" in lower:
        return "ride_history"
    if "rate" in lower or "rating" in lower or re.search(r"\b[1-5]\s*star", lower):
        return "rate_ride"
    if "fare" in lower or "price" in lower or "estimate" in lower:
        return "estimate_fare"
    if "driver" in lower and ("near" in lower or "nearest" in lower or "location" in lower):
        return "nearest_driver"
    if any(word in lower for word in ["book", "ride", "go to", "take me", "pickup", "destination", "dropoff"]):
        return "book_ride"
    return "general"


def _vehicle_type(lower: str) -> str | None:
    for vehicle_type in sorted(VALID_VEHICLE_TYPES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(vehicle_type)}\b", lower):
            return vehicle_type
    return None


def _uuid_in_text(text: str) -> str | None:
    match = re.search(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", text)
    if not match:
        return None
    try:
        return str(uuid.UUID(match.group(0)))
    except ValueError:
        return None


def _registration_numbers(text: str) -> list[str]:
    matches = re.findall(r"\b[A-Z]{2}\s*\d{2}\s*[A-Z]{0,2}\s*\d{3,4}\b", text.upper())
    return ["".join(match.split()) for match in matches]


def _rating(lower: str) -> int | None:
    match = re.search(r"\b([1-5])\s*(?:star|stars|rating)?\b", lower)
    return int(match.group(1)) if match else None


def _ride_time(lower: str) -> str | None:
    now = datetime.now(UTC)
    if "tomorrow" in lower:
        target = now + timedelta(days=1)
    elif "today" in lower or "now" in lower or "current" in lower:
        target = now
    else:
        target = now

    time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", lower)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        meridiem = time_match.group(3)
        if meridiem == "pm" and hour < 12:
            hour += 12
        if meridiem == "am" and hour == 12:
            hour = 0
        target = target.replace(hour=hour, minute=minute, second=0, microsecond=0)

    return target.isoformat()


def _pickup_destination(message: str) -> tuple[str | None, str | None]:
    cleaned = _remove_vehicle_phrase(message)
    labelled_match = re.search(
        r"\bpickup(?:\s+location)?\s*:?\s*(.+?)\s+(?:and\s+)?(?:destination|destinantion|drop|dropoff|drop-off)(?:\s+location)?\s*:?\s*(.+)$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if labelled_match:
        return _clean_location(labelled_match.group(1)), _clean_location(labelled_match.group(2))

    match = re.search(r"\bfrom\s+(.+?)\s+\bto\s+(.+)$", cleaned, flags=re.IGNORECASE)
    if match:
        return _clean_location(match.group(1)), _clean_location(match.group(2))

    match = re.search(r"\bto\s+(.+?)(?:\s+from\s+(.+))?$", cleaned, flags=re.IGNORECASE)
    if match:
        destination = _clean_location(match.group(1))
        pickup = _clean_location(match.group(2)) if match.group(2) else None
        return pickup, destination

    return None, None


def _remove_vehicle_phrase(message: str) -> str:
    return re.sub(r"\b(vehicle|cab|car)\s+(bike|auto|mini|sedan|suv|luxury)\b", "", message, flags=re.IGNORECASE)


def _clean_location(value: str | None) -> str | None:
    if not value:
        return None
    if re.search(r"\b(current location|my location)\b", value, flags=re.IGNORECASE):
        return "current location"
    value = re.sub(r"\b(today|tomorrow|now|at\s+\d{1,2}(:\d{2})?\s*(am|pm))\b", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\b(vehicle|bike|auto|mini|sedan|suv|luxury)\b", "", value, flags=re.IGNORECASE)
    value = " ".join(value.strip(" .,-").split())
    return value or None


def _missing_for_intent(entities: ExtractedEntities) -> list[str]:
    if entities.intent == "book_ride":
        required = {
            "pickup": entities.pickup,
            "pickup_coordinates": entities.pickup_latitude is not None and entities.pickup_longitude is not None,
            "destination": entities.destination,
            "destination_coordinates": entities.dropoff_latitude is not None and entities.dropoff_longitude is not None,
            "vehicle_type": entities.vehicle_type,
            "ride_time": entities.ride_time,
        }
        return [field for field, value in required.items() if not value]
    if entities.intent in {"cancel_ride", "get_ride_status", "payment_status"} and not entities.ride_id:
        return ["ride_id"]
    if entities.intent == "rate_ride":
        missing = []
        if not entities.ride_id:
            missing.append("ride_id")
        if not entities.rating:
            missing.append("rating")
        return missing
    if entities.intent == "approve_vehicles" and not entities.registration_numbers:
        return ["registration_numbers"]
    return []
