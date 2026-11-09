"""Widen places.phone column to String(255).

Revision ID: 0003_widen_phone_column
Revises: 0002_google_places_and_routing
Create Date: 2026-11-09
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0003_widen_phone_column"
down_revision: Union[str, None] = "0002_google_places_and_routing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "places",
        "phone",
        existing_type=sa.String(length=64),
        type_=sa.String(length=255),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "places",
        "phone",
        existing_type=sa.String(length=255),
        type_=sa.String(length=64),
        existing_nullable=True,
    )
