import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PaymentModel(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_payments_amount"),
        CheckConstraint("payment_status IN ('pending', 'paid', 'failed', 'refunded', 'cancelled')", name="ck_payments_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ride_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rides.id"), unique=True, nullable=False, index=True)
    payer_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    payment_method: Mapped[str] = mapped_column(String(64), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    ride: Mapped["RideModel"] = relationship(back_populates="payment")
