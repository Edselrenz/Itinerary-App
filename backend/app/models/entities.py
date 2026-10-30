"""SQLAlchemy 2.0 ORM models for the Nueva Ecija Travel Itinerary MVP (Steps 1-2)."""

import uuid
from datetime import date, datetime, time, timezone
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid
from app.core.database import Base

# Portable JSON type: uses JSONB on PostgreSQL and standard JSON on SQLite tests
JsonType = JSON().with_variant(JSONB(), "postgresql")


def utcnow() -> datetime:
    """Returns timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class User(Base):
    """Registered traveler account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    username_normalized: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email_normalized: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    identities: Mapped[list["AuthIdentity"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    itineraries: Mapped[list["Itinerary"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class AuthIdentity(Base):
    """Linked OAuth provider identity (Google, and conditional Apple)."""

    __tablename__ = "auth_identities"
    __table_args__ = (
        UniqueConstraint("provider", "provider_subject", name="uq_provider_subject"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="identities")


class Municipality(Base):
    """City or municipality within Nueva Ecija province."""

    __tablename__ = "municipalities"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    is_city: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    center_lat: Mapped[float] = mapped_column(Float, nullable=False)
    center_lng: Mapped[float] = mapped_column(Float, nullable=False)
    boundary_geojson: Mapped[dict | None] = mapped_column(JsonType, nullable=True)

    places: Mapped[list["Place"]] = relationship(back_populates="municipality")


class Place(Base):
    """Point of Interest (POI) within Nueva Ecija imported from OSM or curated."""

    __tablename__ = "places"
    __table_args__ = (
        UniqueConstraint("source_name", "source_record_id", name="uq_place_source_record"),
        Index("ix_places_lat_lng", "latitude", "longitude"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    municipality_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("municipalities.id", ondelete="SET NULL"), index=True
    )
    address_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    opening_hours: Mapped[str | None] = mapped_column(String(255), nullable=True)
    estimated_cost_min: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    estimated_cost_max: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    cost_currency: Mapped[str] = mapped_column(String(3), default="PHP", nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_license: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_name: Mapped[str] = mapped_column(String(64), default="OpenStreetMap", nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JsonType, default=list, nullable=False)

    municipality: Mapped["Municipality | None"] = relationship(back_populates="places")


class Itinerary(Base):
    """Saved multi-day travel itinerary owned by an authenticated user."""

    __tablename__ = "itineraries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    destination: Mapped[str] = mapped_column(String(120), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    daily_budget: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    preferences: Mapped[list[str]] = mapped_column(JsonType, default=list, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'suggested' | 'custom'
    assumptions: Mapped[list[str]] = mapped_column(JsonType, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    user: Mapped["User"] = relationship(back_populates="itineraries")
    days: Mapped[list["ItineraryDay"]] = relationship(
        back_populates="itinerary",
        cascade="all, delete-orphan",
        order_by="ItineraryDay.day_number",
    )


class ItineraryDay(Base):
    """Single calendar day within an itinerary."""

    __tablename__ = "itinerary_days"
    __table_args__ = (
        UniqueConstraint("itinerary_id", "day_number", name="uq_itinerary_day_num"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    itinerary_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("itineraries.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    travel_date: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)

    itinerary: Mapped["Itinerary"] = relationship(back_populates="days")
    items: Mapped[list["ItineraryItem"]] = relationship(
        back_populates="day",
        cascade="all, delete-orphan",
        order_by="ItineraryItem.sort_order",
    )


class ItineraryItem(Base):
    """Scheduled stop (linked POI or custom stop) on an itinerary day."""

    __tablename__ = "itinerary_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    day_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("itinerary_days.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    place_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("places.id", ondelete="SET NULL"),
        nullable=True,
    )
    custom_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    custom_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    custom_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    planned_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_cost_min: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    estimated_cost_max: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    day: Mapped["ItineraryDay"] = relationship(back_populates="items")
