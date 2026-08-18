import uuid

from pydantic import BaseModel

from app.schemas.common import TimestampedResponse


class DriverResponse(TimestampedResponse):
    id: uuid.UUID
    user_id: uuid.UUID
    approval_status: str
    availability_status: str
    current_latitude: float | None
    current_longitude: float | None
    average_rating: float | None
    total_rides: int


class VehicleResponse(TimestampedResponse):
    id: uuid.UUID
    driver_id: uuid.UUID
    vehicle_type: str
    make: str
    model: str
    color: str
    registration_number: str
    capacity: int
    approval_status: str
    is_active: bool


class NearbyVehicleResponse(BaseModel):
    driver_id: uuid.UUID
    vehicle_id: uuid.UUID
    vehicle_type: str
    distance_km: float
    eta_minutes: int
    current_latitude: float
    current_longitude: float
