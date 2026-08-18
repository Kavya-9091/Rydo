from pydantic import BaseModel, Field


class DriverAvailabilityRequest(BaseModel):
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class VehicleCreateRequest(BaseModel):
    vehicle_type: str = Field(pattern="^(bike|auto|mini|sedan|suv|luxury)$")
    make: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    color: str = Field(min_length=1, max_length=50)
    registration_number: str = Field(min_length=3, max_length=64)
    capacity: int = Field(gt=0, le=12)
