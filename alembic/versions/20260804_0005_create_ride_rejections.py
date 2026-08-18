"""create ride rejections

Revision ID: 20260804_0005
Revises: 20260730_0004
Create Date: 2026-08-04 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260804_0005"
down_revision: str | None = "20260730_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ride_rejections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ride_id", sa.UUID(), nullable=False),
        sa.Column("driver_id", sa.UUID(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ride_id"], ["rides.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ride_id", "driver_id", name="uq_ride_rejections_ride_driver"),
    )
    op.create_index(op.f("ix_ride_rejections_deleted_at"), "ride_rejections", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_ride_rejections_driver_id"), "ride_rejections", ["driver_id"], unique=False)
    op.create_index(op.f("ix_ride_rejections_ride_id"), "ride_rejections", ["ride_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ride_rejections_ride_id"), table_name="ride_rejections")
    op.drop_index(op.f("ix_ride_rejections_driver_id"), table_name="ride_rejections")
    op.drop_index(op.f("ix_ride_rejections_deleted_at"), table_name="ride_rejections")
    op.drop_table("ride_rejections")
