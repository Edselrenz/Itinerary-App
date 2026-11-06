"""Add Google Places API (New) metadata, route polylines, and geospatial cache.

Revision ID: 0002_google_places_and_routing
Revises: 0001_initial_schema
Create Date: 2026-11-06
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_google_places_and_routing"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JsonType = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    # 1. Expand places table
    op.add_column("places", sa.Column("google_place_id", sa.String(length=128), nullable=True))
    op.create_index("ix_places_google_place_id", "places", ["google_place_id"], unique=True)

    op.add_column(
        "places",
        sa.Column("google_types", JsonType, nullable=False, server_default=sa.text("'[]'")),
    )
    op.add_column("places", sa.Column("editorial_summary", sa.Text(), nullable=True))
    op.add_column("places", sa.Column("regular_opening_hours", JsonType, nullable=True))
    op.add_column("places", sa.Column("rating", sa.Float(), nullable=True))
    op.create_index("ix_places_rating", "places", ["rating"], unique=False)

    op.add_column("places", sa.Column("user_rating_count", sa.Integer(), nullable=True))
    op.add_column("places", sa.Column("price_level", sa.Integer(), nullable=True))
    op.add_column(
        "places",
        sa.Column("photos", JsonType, nullable=False, server_default=sa.text("'[]'")),
    )
    op.add_column(
        "places",
        sa.Column("reviews", JsonType, nullable=False, server_default=sa.text("'[]'")),
    )
    op.add_column("places", sa.Column("business_status", sa.String(length=40), nullable=True))
    op.add_column("places", sa.Column("google_maps_uri", sa.String(length=500), nullable=True))
    op.add_column("places", sa.Column("details_cached_at", sa.DateTime(timezone=True), nullable=True))

    # 2. Expand itinerary_days table
    op.add_column("itinerary_days", sa.Column("day_overview_polyline", sa.Text(), nullable=True))
    op.add_column("itinerary_days", sa.Column("total_distance_meters", sa.Integer(), nullable=True))
    op.add_column("itinerary_days", sa.Column("total_travel_duration_seconds", sa.Integer(), nullable=True))
    op.add_column(
        "itinerary_days",
        sa.Column("route_legs", JsonType, nullable=False, server_default=sa.text("'[]'")),
    )

    # 3. Expand itinerary_items table
    op.add_column("itinerary_items", sa.Column("google_place_id", sa.String(length=128), nullable=True))
    op.create_index("ix_itinerary_items_google_place_id", "itinerary_items", ["google_place_id"], unique=False)
    op.add_column("itinerary_items", sa.Column("travel_mode_from_prev", sa.String(length=20), nullable=True))
    op.add_column("itinerary_items", sa.Column("travel_distance_meters", sa.Integer(), nullable=True))
    op.add_column("itinerary_items", sa.Column("travel_duration_seconds", sa.Integer(), nullable=True))
    op.add_column("itinerary_items", sa.Column("route_polyline_from_prev", sa.Text(), nullable=True))

    # 4. Create geospatial_cache table
    op.create_table(
        "geospatial_cache",
        sa.Column("cache_key", sa.String(length=255), primary_key=True, nullable=False),
        sa.Column("cache_type", sa.String(length=32), nullable=False),
        sa.Column("payload", JsonType, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_geospatial_cache_cache_type", "geospatial_cache", ["cache_type"], unique=False)
    op.create_index("ix_geospatial_cache_expires_at", "geospatial_cache", ["expires_at"], unique=False)


def downgrade() -> None:
    # 1. Drop geospatial_cache
    op.drop_index("ix_geospatial_cache_expires_at", table_name="geospatial_cache")
    op.drop_index("ix_geospatial_cache_cache_type", table_name="geospatial_cache")
    op.drop_table("geospatial_cache")

    # 2. Revert itinerary_items
    op.drop_column("itinerary_items", "route_polyline_from_prev")
    op.drop_column("itinerary_items", "travel_duration_seconds")
    op.drop_column("itinerary_items", "travel_distance_meters")
    op.drop_column("itinerary_items", "travel_mode_from_prev")
    op.drop_index("ix_itinerary_items_google_place_id", table_name="itinerary_items")
    op.drop_column("itinerary_items", "google_place_id")

    # 3. Revert itinerary_days
    op.drop_column("itinerary_days", "route_legs")
    op.drop_column("itinerary_days", "total_travel_duration_seconds")
    op.drop_column("itinerary_days", "total_distance_meters")
    op.drop_column("itinerary_days", "day_overview_polyline")

    # 4. Revert places
    op.drop_column("places", "details_cached_at")
    op.drop_column("places", "google_maps_uri")
    op.drop_column("places", "business_status")
    op.drop_column("places", "reviews")
    op.drop_column("places", "photos")
    op.drop_column("places", "price_level")
    op.drop_column("places", "user_rating_count")
    op.drop_index("ix_places_rating", table_name="places")
    op.drop_column("places", "rating")
    op.drop_column("places", "regular_opening_hours")
    op.drop_column("places", "editorial_summary")
    op.drop_column("places", "google_types")
    op.drop_index("ix_places_google_place_id", table_name="places")
    op.drop_column("places", "google_place_id")

