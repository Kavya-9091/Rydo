import uuid
from datetime import datetime

from app.schemas.common import TimestampedResponse


class RideDriverDetailsResponse(TimestampedResponse):
    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    phone_number: str
    average_rating: float | None
    total_rides: int


class RideVehicleDetailsResponse(TimestampedResponse):
    id: uuid.UUID
    vehicle_type: str
    make: str
    model: str
    color: str
    registration_number: str


class RideResponse(TimestampedResponse):
    id: uuid.UUID
    customer_id: uuid.UUID
    driver_id: uuid.UUID | None
    vehicle_id: uuid.UUID | None
    status: str
    ride_type: str
    pickup_address: str
    pickup_latitude: float
    pickup_longitude: float
    dropoff_address: str
    dropoff_latitude: float
    dropoff_longitude: float
    rider_name: str | None
    rider_phone_number: str | None
    estimated_distance_km: float | None
    actual_distance_km: float | None
    estimated_fare: float | None
    final_fare: float | None
    currency: str
    requested_at: datetime
    accepted_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    driver_details: RideDriverDetailsResponse | None = None
    vehicle_details: RideVehicleDetailsResponse | None = None


class PaymentResponse(TimestampedResponse):
    id: uuid.UUID
    ride_id: uuid.UUID
    payer_user_id: uuid.UUID
    amount: float
    currency: str
    payment_method: str
    payment_status: str
    provider: str | None
    provider_transaction_id: str | None


class RatingResponse(TimestampedResponse):
    id: uuid.UUID
    ride_id: uuid.UUID
    rated_by_user_id: uuid.UUID
    rated_user_id: uuid.UUID
    rating: int
    comment: str | None
