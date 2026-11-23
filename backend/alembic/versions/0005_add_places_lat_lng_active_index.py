"""Add composite bounding-box index ix_places_lat_lng_active on places.

Revision ID: 0005_add_places_lat_lng_active_index
Revises: 0004_add_user_profile_fields
Create Date: 2026-11-23
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0005_add_places_lat_lng_active_index"
down_revision: Union[str, None] = "0004_add_user_profile_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    existing_indexes = {idx["name"] for idx in insp.get_indexes("places")}
    if "ix_places_lat_lng_active" not in existing_indexes:
        op.create_index(
            "ix_places_lat_lng_active",
            "places",
            ["latitude", "longitude", "is_active"],
            unique=False,
        )


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    existing_indexes = {idx["name"] for idx in insp.get_indexes("places")}
    if "ix_places_lat_lng_active" in existing_indexes:
        op.drop_index("ix_places_lat_lng_active", table_name="places")
