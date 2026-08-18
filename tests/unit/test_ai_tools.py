from app.ai.tool_calling.schemas import ToolExecutionContext
from app.ai.tool_calling.tools import create_ride_tool_registry, estimate_fare


def test_ride_tool_registry_exposes_phase_three_tools() -> None:
    tool_names = {definition.name for definition in create_ride_tool_registry().definitions()}

    assert {
        "book_ride",
        "cancel_ride",
        "get_ride_status",
        "estimate_fare",
        "get_driver_location",
        "ride_history",
        "rate_ride",
        "payment_status",
        "nearest_driver",
    }.issubset(tool_names)


def test_estimate_fare_requires_locations() -> None:
    result = estimate_fare({"vehicle_type": "sedan"}, ToolExecutionContext(db=object(), user=object()))

    assert result.success is False
    assert "Missing required fare details" in result.message


def test_estimate_fare_rejects_invalid_vehicle_type() -> None:
    result = estimate_fare(
        {
            "pickup_latitude": 12.9,
            "pickup_longitude": 77.5,
            "dropoff_latitude": 13.0,
            "dropoff_longitude": 77.6,
            "vehicle_type": "rocket",
        },
        ToolExecutionContext(db=object(), user=object()),
    )

    assert result.success is False
    assert "Invalid vehicle type" in result.message
