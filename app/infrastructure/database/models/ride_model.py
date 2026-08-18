import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RideModel(Base):
    __tablename__ = "rides"
    __table_args__ = (
        CheckConstraint("status IN ('requested', 'accepted', 'in_progress', 'completed', 'cancelled')", name="ck_rides_status"),
        CheckConstraint("ride_type IN ('bike', 'auto', 'mini', 'sedan', 'suv', 'luxury')", name="ck_rides_type"),
        CheckConstraint("estimated_fare IS NULL OR estimated_fare >= 0", name="ck_rides_estimated_fare"),
        CheckConstraint("final_fare IS NULL OR final_fare >= 0", name="ck_rides_final_fare"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    driver_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=True, index=True)
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="requested", index=True)
    ride_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    pickup_address: Mapped[str] = mapped_column(Text, nullable=False)
    pickup_latitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    pickup_longitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    dropoff_address: Mapped[str] = mapped_column(Text, nullable=False)
    dropoff_latitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    dropoff_longitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    rider_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rider_phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    estimated_distance_km: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    actual_distance_km: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    estimated_fare: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    final_fare: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    customer: Mapped["UserModel"] = relationship(foreign_keys=[customer_id])
    driver: Mapped["DriverModel | None"] = relationship(back_populates="rides")
    vehicle: Mapped["VehicleModel | None"] = relationship(back_populates="rides")
    payment: Mapped["PaymentModel | None"] = relationship(back_populates="ride")
    ratings: Mapped[list["RatingModel"]] = relationship(back_populates="ride")
