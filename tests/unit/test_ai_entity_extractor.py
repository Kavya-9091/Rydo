from app.ai.tool_calling.entity_extractor import extract_entities
from app.ai.tool_calling.orchestrator import _entities_with_memory


def test_extract_booking_entities_with_bengaluru_locations() -> None:
    entities = extract_entities("book ride from majestic to yelahanka old town vehicle bike")

    assert entities.intent == "book_ride"
    assert entities.vehicle_type == "bike"
    assert entities.pickup == "Majestic, Bengaluru"
    assert entities.destination == "Yelahanka Old Town, Bengaluru"
    assert entities.pickup_latitude is not None
    assert entities.dropoff_longitude is not None
    assert entities.missing_fields == []


def test_extract_booking_missing_pickup_coordinates() -> None:
    entities = extract_entities("book a sedan to airport")

    assert entities.intent == "book_ride"
    assert entities.destination == "Kempegowda International Airport, Bengaluru"
    assert "pickup" in entities.missing_fields
    assert "pickup_coordinates" in entities.missing_fields


def test_extract_ride_status_requires_ride_id() -> None:
    entities = extract_entities("what is my ride status")

    assert entities.intent == "get_ride_status"
    assert entities.missing_fields == ["ride_id"]


def test_extract_booking_with_common_majestic_typo() -> None:
    entities = extract_entities("book ride vehicle bike from marathahalli to mejestic")

    assert entities.vehicle_type == "bike"
    assert entities.pickup == "Marathahalli, Bengaluru"
    assert entities.destination == "Majestic, Bengaluru"
    assert entities.missing_fields == []


def test_extract_labelled_pickup_and_destination_follow_up() -> None:
    entities = extract_entities("pickup location: hsr layout and destination: marathahalli")

    assert entities.intent == "book_ride"
    assert entities.pickup == "HSR Layout, Bengaluru"
    assert entities.destination == "Marathahalli, Bengaluru"
    assert "vehicle_type" in entities.missing_fields


def test_extract_booking_from_current_location_to_majestic_typo() -> None:
    entities = extract_entities("book ride vehicle bike from current location to mejestic")

    assert entities.intent == "book_ride"
    assert entities.vehicle_type == "bike"
    assert entities.pickup == "current location"
    assert entities.destination == "Majestic, Bengaluru"
    assert "pickup_coordinates" in entities.missing_fields
    assert "destination" not in entities.missing_fields


def test_merge_booking_follow_ups_message_by_message() -> None:
    entities = _entities_with_memory(
        "bike",
        {
            "chat_history": [
                {"role": "user", "content": "book ride vehicle bike from current location to mejestic"},
                {"role": "user", "content": "pickup location: hsr layout and destination: marathahalli"},
            ]
        },
    )

    assert entities.intent == "book_ride"
    assert entities.vehicle_type == "bike"
    assert entities.pickup == "HSR Layout, Bengaluru"
    assert entities.destination == "Marathahalli, Bengaluru"
    assert entities.missing_fields == []


def test_driver_accept_recent_is_not_booking() -> None:
    entities = extract_entities("accept ride recent")

    assert entities.intent == "accept_ride"
    assert entities.missing_fields == []


def test_driver_start_uses_recent_ride_id_from_chat_context() -> None:
    ride_id = "a6305cd6-9ceb-4eaf-a2e3-ddd7c8e7b437"
    entities = _entities_with_memory(
        "start",
        {
            "chat_history": [
                {"role": "assistant", "content": f"Ride accepted. Ride ID: {ride_id}. Head to pickup."},
            ]
        },
    )

    assert entities.intent == "start_ride"
    assert entities.ride_id == ride_id


def test_admin_approve_vehicle_registration_numbers() -> None:
    entities = extract_entities("KA078625,KA078625 approve these vehicles")

    assert entities.intent == "approve_vehicles"
    assert entities.registration_numbers == ["KA078625", "KA078625"]
    assert entities.missing_fields == []


def test_extract_booking_with_loose_pickup_destination_labels_and_typos() -> None:
    entities = extract_entities("book bike ride from pickup location :hosakote to destinantion krpuram")

    assert entities.intent == "book_ride"
    assert entities.vehicle_type == "bike"
    assert entities.pickup == "Hoskote, Bengaluru Rural"
    assert entities.destination == "KR Puram, Bengaluru"
    assert entities.missing_fields == []
