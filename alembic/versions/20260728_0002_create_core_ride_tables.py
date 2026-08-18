"""create core ride booking tables

Revision ID: 20260728_0002
Revises: 20260728_0001
Create Date: 2026-07-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260728_0002"
down_revision: str | None = "20260728_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "drivers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approval_status", sa.String(length=32), nullable=False),
        sa.Column("availability_status", sa.String(length=32), nullable=False),
        sa.Column("current_latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("current_longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("average_rating", sa.Numeric(3, 2), nullable=True),
        sa.Column("total_rides", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("approval_status IN ('pending', 'approved', 'rejected', 'suspended')", name="ck_drivers_approval_status"),
        sa.CheckConstraint("availability_status IN ('offline', 'online', 'busy')", name="ck_drivers_availability_status"),
        sa.CheckConstraint("current_latitude IS NULL OR current_latitude BETWEEN -90 AND 90", name="ck_drivers_latitude"),
        sa.CheckConstraint("current_longitude IS NULL OR current_longitude BETWEEN -180 AND 180", name="ck_drivers_longitude"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_drivers_approval_status", "drivers", ["approval_status"])
    op.create_index("ix_drivers_availability_status", "drivers", ["availability_status"])
    op.create_index("ix_drivers_deleted_at", "drivers", ["deleted_at"])
    op.create_index("ix_drivers_user_id", "drivers", ["user_id"])

    op.create_table(
        "vehicles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vehicle_type", sa.String(length=32), nullable=False),
        sa.Column("make", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=50), nullable=False),
        sa.Column("registration_number", sa.String(length=64), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("approval_status", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("vehicle_type IN ('bike', 'auto', 'mini', 'sedan', 'suv', 'luxury')", name="ck_vehicles_type"),
        sa.CheckConstraint("approval_status IN ('pending', 'approved', 'rejected', 'suspended')", name="ck_vehicles_approval_status"),
        sa.CheckConstraint("capacity > 0", name="ck_vehicles_capacity"),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vehicles_approval_status", "vehicles", ["approval_status"])
    op.create_index("ix_vehicles_deleted_at", "vehicles", ["deleted_at"])
    op.create_index("ix_vehicles_driver_id", "vehicles", ["driver_id"])
    op.create_index("ix_vehicles_is_active", "vehicles", ["is_active"])
    op.create_index("ix_vehicles_registration_number", "vehicles", ["registration_number"], unique=True)
    op.create_index("ix_vehicles_vehicle_type", "vehicles", ["vehicle_type"])

    op.create_table(
        "rides",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("ride_type", sa.String(length=32), nullable=False),
        sa.Column("pickup_address", sa.Text(), nullable=False),
        sa.Column("pickup_latitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("pickup_longitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("dropoff_address", sa.Text(), nullable=False),
        sa.Column("dropoff_latitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("dropoff_longitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("estimated_distance_km", sa.Numeric(8, 2), nullable=True),
        sa.Column("actual_distance_km", sa.Numeric(8, 2), nullable=True),
        sa.Column("estimated_fare", sa.Numeric(10, 2), nullable=True),
        sa.Column("final_fare", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('requested', 'accepted', 'in_progress', 'completed', 'cancelled')", name="ck_rides_status"),
        sa.CheckConstraint("ride_type IN ('bike', 'auto', 'mini', 'sedan', 'suv', 'luxury')", name="ck_rides_type"),
        sa.CheckConstraint("estimated_fare IS NULL OR estimated_fare >= 0", name="ck_rides_estimated_fare"),
        sa.CheckConstraint("final_fare IS NULL OR final_fare >= 0", name="ck_rides_final_fare"),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rides_customer_id", "rides", ["customer_id"])
    op.create_index("ix_rides_deleted_at", "rides", ["deleted_at"])
    op.create_index("ix_rides_driver_id", "rides", ["driver_id"])
    op.create_index("ix_rides_ride_type", "rides", ["ride_type"])
    op.create_index("ix_rides_status", "rides", ["status"])
    op.create_index("ix_rides_vehicle_id", "rides", ["vehicle_id"])

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ride_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payer_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("payment_method", sa.String(length=64), nullable=False),
        sa.Column("payment_status", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("provider_transaction_id", sa.String(length=255), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("amount >= 0", name="ck_payments_amount"),
        sa.CheckConstraint("payment_status IN ('pending', 'paid', 'failed', 'refunded', 'cancelled')", name="ck_payments_status"),
        sa.ForeignKeyConstraint(["payer_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["ride_id"], ["rides.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_transaction_id"),
        sa.UniqueConstraint("ride_id"),
    )
    op.create_index("ix_payments_deleted_at", "payments", ["deleted_at"])
    op.create_index("ix_payments_payer_user_id", "payments", ["payer_user_id"])
    op.create_index("ix_payments_payment_status", "payments", ["payment_status"])
    op.create_index("ix_payments_ride_id", "payments", ["ride_id"])

    op.create_table(
        "ratings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ride_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rated_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rated_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_ratings_rating"),
        sa.ForeignKeyConstraint(["rated_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["rated_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["ride_id"], ["rides.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ride_id", "rated_by_user_id", "rated_user_id", name="uq_rating_once_per_pair"),
    )
    op.create_index("ix_ratings_deleted_at", "ratings", ["deleted_at"])
    op.create_index("ix_ratings_rated_by_user_id", "ratings", ["rated_by_user_id"])
    op.create_index("ix_ratings_rated_user_id", "ratings", ["rated_user_id"])
    op.create_index("ix_ratings_ride_id", "ratings", ["ride_id"])

    op.create_table(
        "ai_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ride_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("conversation_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("user_message", sa.Text(), nullable=False),
        sa.Column("assistant_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("conversation_type IN ('ride_booking', 'customer_support', 'trip_summary')", name="ck_ai_conversations_type"),
        sa.CheckConstraint("status IN ('active', 'completed', 'failed')", name="ck_ai_conversations_status"),
        sa.ForeignKeyConstraint(["ride_id"], ["rides.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_conversations_conversation_type", "ai_conversations", ["conversation_type"])
    op.create_index("ix_ai_conversations_deleted_at", "ai_conversations", ["deleted_at"])
    op.create_index("ix_ai_conversations_ride_id", "ai_conversations", ["ride_id"])
    op.create_index("ix_ai_conversations_status", "ai_conversations", ["status"])
    op.create_index("ix_ai_conversations_user_id", "ai_conversations", ["user_id"])


def downgrade() -> None:
    for index, table in [
        ("ix_ai_conversations_user_id", "ai_conversations"),
        ("ix_ai_conversations_status", "ai_conversations"),
        ("ix_ai_conversations_ride_id", "ai_conversations"),
        ("ix_ai_conversations_deleted_at", "ai_conversations"),
        ("ix_ai_conversations_conversation_type", "ai_conversations"),
    ]:
        op.drop_index(index, table_name=table)
    op.drop_table("ai_conversations")
    for index in ["ix_ratings_ride_id", "ix_ratings_rated_user_id", "ix_ratings_rated_by_user_id", "ix_ratings_deleted_at"]:
        op.drop_index(index, table_name="ratings")
    op.drop_table("ratings")
    for index in ["ix_payments_ride_id", "ix_payments_payment_status", "ix_payments_payer_user_id", "ix_payments_deleted_at"]:
        op.drop_index(index, table_name="payments")
    op.drop_table("payments")
    for index in ["ix_rides_vehicle_id", "ix_rides_status", "ix_rides_ride_type", "ix_rides_driver_id", "ix_rides_deleted_at", "ix_rides_customer_id"]:
        op.drop_index(index, table_name="rides")
    op.drop_table("rides")
    for index in ["ix_vehicles_vehicle_type", "ix_vehicles_registration_number", "ix_vehicles_is_active", "ix_vehicles_driver_id", "ix_vehicles_deleted_at", "ix_vehicles_approval_status"]:
        op.drop_index(index, table_name="vehicles")
    op.drop_table("vehicles")
    for index in ["ix_drivers_user_id", "ix_drivers_deleted_at", "ix_drivers_availability_status", "ix_drivers_approval_status"]:
        op.drop_index(index, table_name="drivers")
    op.drop_table("drivers")
