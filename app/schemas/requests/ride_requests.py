import uuid

from pydantic import BaseModel, Field


class RideCreateRequest(BaseModel):
    ride_type: str = Field(pattern="^(bike|auto|mini|sedan|suv|luxury)$")
    pickup_address: str = Field(min_length=2, max_length=1000)
    pickup_latitude: float = Field(ge=-90, le=90)
    pickup_longitude: float = Field(ge=-180, le=180)
    dropoff_address: str = Field(min_length=2, max_length=1000)
    dropoff_latitude: float = Field(ge=-90, le=90)
    dropoff_longitude: float = Field(ge=-180, le=180)
    rider_name: str | None = Field(default=None, min_length=2, max_length=255)
    rider_phone_number: str | None = Field(default=None, pattern=r"^[6-9]\d{9}$")


class CancelRideRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=1000)


class PaymentCreateRequest(BaseModel):
    payment_method: str = Field(min_length=2, max_length=64)
    provider: str | None = Field(default=None, max_length=64)
    provider_transaction_id: str | None = Field(default=None, max_length=255)


class RatingCreateRequest(BaseModel):
    ride_id: uuid.UUID
    rated_user_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class RideRatingCreateRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)
