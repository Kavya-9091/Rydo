"""add ride rider details

Revision ID: 20260730_0004
Revises: 20260729_0003
Create Date: 2026-07-30 16:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260730_0004"
down_revision: str | None = "20260729_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("rides", sa.Column("rider_name", sa.String(length=255), nullable=True))
    op.add_column("rides", sa.Column("rider_phone_number", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("rides", "rider_phone_number")
    op.drop_column("rides", "rider_name")
