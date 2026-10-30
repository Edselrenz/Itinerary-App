"""Initial Nueva Ecija Travel Itinerary schema (7 core tables).

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-30
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JsonType = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("first_name", sa.String(length=80), nullable=False),
        sa.Column("last_name", sa.String(length=80), nullable=False),
        sa.Column("username_normalized", sa.String(length=50), nullable=False),
        sa.Column("email_normalized", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_username_normalized", "users", ["username_normalized"], unique=True)
    op.create_index("ix_users_email_normalized", "users", ["email_normalized"], unique=True)

    op.create_table(
        "auth_identities",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_subject", sa.String(length=255), nullable=False),
        sa.Column("provider_email", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("provider", "provider_subject", name="uq_provider_subject"),
    )
    op.create_index("ix_auth_identities_user_id", "auth_identities", ["user_id"])

    op.create_table(
        "municipalities",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("is_city", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("center_lat", sa.Float(), nullable=False),
        sa.Column("center_lng", sa.Float(), nullable=False),
        sa.Column("boundary_geojson", JsonType, nullable=True),
    )
    op.create_index("ix_municipalities_slug", "municipalities", ["slug"], unique=True)

    op.create_table(
        "places",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column(
            "municipality_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("municipalities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("address_text", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("opening_hours", sa.String(length=255), nullable=True),
        sa.Column("estimated_cost_min", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("estimated_cost_max", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("cost_currency", sa.String(length=3), nullable=False, server_default="PHP"),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("image_license", sa.String(length=255), nullable=True),
        sa.Column(
            "source_name", sa.String(length=64), nullable=False, server_default="OpenStreetMap"
        ),
        sa.Column("source_record_id", sa.String(length=128), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("tags", JsonType, nullable=False),
        sa.UniqueConstraint("source_name", "source_record_id", name="uq_place_source_record"),
    )
    op.create_index("ix_places_name", "places", ["name"])
    op.create_index("ix_places_category", "places", ["category"])
    op.create_index("ix_places_municipality_id", "places", ["municipality_id"])
    op.create_index("ix_places_is_featured", "places", ["is_featured"])
    op.create_index("ix_places_is_active", "places", ["is_active"])
    op.create_index("ix_places_lat_lng", "places", ["latitude", "longitude"])

    op.create_table(
        "itineraries",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("destination", sa.String(length=120), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("daily_budget", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("preferences", JsonType, nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("assumptions", JsonType, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_itineraries_user_id", "itineraries", ["user_id"])

    op.create_table(
        "itinerary_days",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "itinerary_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("itineraries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("travel_date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=True),
        sa.UniqueConstraint("itinerary_id", "day_number", name="uq_itinerary_day_num"),
    )
    op.create_index("ix_itinerary_days_itinerary_id", "itinerary_days", ["itinerary_id"])

    op.create_table(
        "itinerary_items",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "day_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("itinerary_days.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "place_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("places.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("custom_title", sa.String(length=200), nullable=True),
        sa.Column("custom_lat", sa.Float(), nullable=True),
        sa.Column("custom_lng", sa.Float(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("planned_time", sa.Time(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("estimated_cost_min", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("estimated_cost_max", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_itinerary_items_day_id", "itinerary_items", ["day_id"])


def downgrade() -> None:
    op.drop_table("itinerary_items")
    op.drop_table("itinerary_days")
    op.drop_table("itineraries")
    op.drop_table("places")
    op.drop_table("municipalities")
    op.drop_table("auth_identities")
    op.drop_table("users")
