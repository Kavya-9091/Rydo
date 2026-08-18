import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DriverModel(Base):
    __tablename__ = "drivers"
    __table_args__ = (
        CheckConstraint("approval_status IN ('pending', 'approved', 'rejected', 'suspended')", name="ck_drivers_approval_status"),
        CheckConstraint("availability_status IN ('offline', 'online', 'busy')", name="ck_drivers_availability_status"),
        CheckConstraint("current_latitude IS NULL OR current_latitude BETWEEN -90 AND 90", name="ck_drivers_latitude"),
        CheckConstraint("current_longitude IS NULL OR current_longitude BETWEEN -180 AND 180", name="ck_drivers_longitude"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    approval_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    availability_status: Mapped[str] = mapped_column(String(32), nullable=False, default="offline", index=True)
    current_latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    current_longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    average_rating: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    total_rides: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    vehicles: Mapped[list["VehicleModel"]] = relationship(back_populates="driver")
    rides: Mapped[list["RideModel"]] = relationship(back_populates="driver")
