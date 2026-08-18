import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VehicleModel(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        CheckConstraint("vehicle_type IN ('bike', 'auto', 'mini', 'sedan', 'suv', 'luxury')", name="ck_vehicles_type"),
        CheckConstraint("approval_status IN ('pending', 'approved', 'rejected', 'suspended')", name="ck_vehicles_approval_status"),
        CheckConstraint("capacity > 0", name="ck_vehicles_capacity"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=False, index=True)
    vehicle_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(50), nullable=False)
    registration_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    capacity: Mapped[int] = mapped_column(nullable=False)
    approval_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    driver: Mapped["DriverModel"] = relationship(back_populates="vehicles")
    rides: Mapped[list["RideModel"]] = relationship(back_populates="vehicle")
