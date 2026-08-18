from app.services.fare_calculation_service import FareCalculationService


def test_distance_and_fare_are_positive() -> None:
    service = FareCalculationService()
    distance = service.distance_km(12.9716, 77.5946, 13.0827, 80.2707)
    assert distance > 0
    assert service.estimate_fare("sedan", distance) > 0
