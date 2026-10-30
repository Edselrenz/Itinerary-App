#!/usr/bin/env python3
"""Scaffolds the complete Steps 0-2 backend and data pipeline for Nueva Ecija Travel Itinerary MVP."""

import os

BASE_DIR = "."

FILES: dict[str, str] = {}

FILES[".gitignore"] = """# Environment & secrets
.env
*.env
*.pem
*.key
client_secret*.json

# Python
__pycache__/
*.py[cod]
.venv/
venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Node / Ionic / Capacitor
Project/node_modules/
Project/www/
Project/.angular/
Project/android/app/build/
Project/ios/App/Pods/
mobile/node_modules/
mobile/www/
mobile/.angular/
mobile/android/app/build/
mobile/ios/App/Pods/

# Data dumps & database backups
data/raw/*
!data/raw/.gitkeep
*.sql.gz
*.dump
"""

FILES[".env.example"] = """# Nueva Ecija Travel Itinerary — Backend Environment Template
APP_ENV=development
API_V1_PREFIX=/api/v1
DATABASE_URL=postgresql+psycopg://ne_travel_user:change_me_local_only@127.0.0.1:5432/nueva_ecija_travel
# For quick local testing without PostgreSQL, SQLite can also be used:
# DATABASE_URL=sqlite:///./nueva_ecija_travel.db
JWT_SECRET_KEY=replace_with_64_char_hex_generated_via_openssl_rand_hex_32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=["http://localhost:8100","http://localhost:4200","capacitor://localhost","http://localhost"]
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
ENABLE_APPLE_AUTH=false
DEFAULT_DEST_RADIUS_KM=25.0
"""

FILES["backend/requirements.txt"] = """fastapi>=0.115.0
uvicorn[standard]>=0.30.0
sqlalchemy>=2.0.30
psycopg[binary]>=3.2.0
alembic>=1.13.2
pydantic>=2.8.0
pydantic-settings>=2.4.0
email-validator>=2.2.0
pwdlib[argon2]>=0.2.1
pyjwt>=2.9.0
google-auth>=2.34.0
requests>=2.32.0
httpx>=0.27.0
slowapi>=0.1.9
pytest>=8.3.0
ruff>=0.6.0
mypy>=1.11.0
"""

FILES["backend/app/__init__.py"] = '"""Nueva Ecija Travel Itinerary Backend Package."""\n'
FILES["backend/app/core/__init__.py"] = ""
FILES["backend/app/models/__init__.py"] = ""
FILES["backend/app/schemas/__init__.py"] = ""
FILES["backend/app/api/__init__.py"] = ""
FILES["backend/app/api/v1/__init__.py"] = ""

FILES["backend/app/core/config.py"] = '''"""Application configuration loaded from environment variables."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Validated backend configuration for the Nueva Ecija Travel Itinerary API."""

    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = (
        "postgresql+psycopg://ne_travel_user:change_me_local_only@127.0.0.1:5432/nueva_ecija_travel"
    )
    jwt_secret_key: str = "dev_only_replace_before_pilot_with_openssl_rand_hex_32"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: list[str] = [
        "http://localhost:8100",
        "http://localhost:4200",
        "capacitor://localhost",
        "http://localhost",
    ]
    google_oauth_client_id: str = ""
    enable_apple_auth: bool = False
    default_dest_radius_km: float = 25.0

    model_config = SettingsConfigDict(
        env_file=(str(ROOT_ENV), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
'''

FILES["backend/app/core/database.py"] = '''"""SQLAlchemy 2.0 database engine, declarative base, and session dependency."""

from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy ORM models."""


def get_db() -> Generator[Session, None, None]:
    """Yields a database session per request and ensures deterministic closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''

FILES["backend/app/models/entities.py"] = '''"""SQLAlchemy 2.0 ORM models for the Nueva Ecija Travel Itinerary MVP (Steps 1-2)."""

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
'''

FILES["backend/app/schemas/place.py"] = '''"""Pydantic v2 response schemas for Municipalities and Places."""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class MunicipalityOut(BaseModel):
    """Serialized municipality or city within Nueva Ecija."""

    id: uuid.UUID
    name: str
    slug: str
    is_city: bool
    center_lat: float
    center_lng: float

    model_config = ConfigDict(from_attributes=True)


class PlaceOut(BaseModel):
    """Serialized Point of Interest (POI) with provenance and verification status."""

    id: uuid.UUID
    name: str
    category: str
    latitude: float
    longitude: float
    municipality_id: uuid.UUID | None = None
    municipality_name: str | None = None
    address_text: str | None = None
    description: str | None = None
    phone: str | None = None
    website: str | None = None
    opening_hours: str | None = None
    estimated_cost_min: float | None = None
    estimated_cost_max: float | None = None
    cost_currency: str = "PHP"
    image_url: str | None = None
    image_license: str | None = None
    source_name: str
    source_record_id: str
    source_url: str | None = None
    imported_at: datetime
    verified_at: datetime | None = None
    is_featured: bool
    tags: list[str]
    directions_url: str

    model_config = ConfigDict(from_attributes=True)


class PaginatedPlacesOut(BaseModel):
    """Paginated response wrapper for GET /api/v1/places."""

    total: int
    limit: int
    offset: int
    items: list[PlaceOut]
'''

FILES["backend/app/api/v1/places.py"] = '''"""REST endpoints for Nueva Ecija municipalities and POI search/filtering."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.entities import Municipality, Place
from app.schemas.place import MunicipalityOut, PaginatedPlacesOut, PlaceOut

router = APIRouter(tags=["places"])

CANONICAL_CATEGORIES: set[str] = {
    "cafe",
    "restaurant",
    "hotel_accommodation",
    "tourist_attraction",
    "nature_park",
    "resort_swimming",
    "church_religious",
    "museum_cultural",
    "shopping_market",
    "transport_terminal",
    "hospital_clinic",
    "pharmacy",
    "bank_atm",
    "fuel_station",
    "convenience_store",
    "public_facility",
}


def serialize_place(place: Place) -> PlaceOut:
    """Converts a Place ORM instance into a PlaceOut response with external Google Maps URL."""
    return PlaceOut(
        id=place.id,
        name=place.name,
        category=place.category,
        latitude=place.latitude,
        longitude=place.longitude,
        municipality_id=place.municipality_id,
        municipality_name=place.municipality.name if place.municipality else None,
        address_text=place.address_text,
        description=place.description,
        phone=place.phone,
        website=place.website,
        opening_hours=place.opening_hours,
        estimated_cost_min=(
            float(place.estimated_cost_min) if place.estimated_cost_min is not None else None
        ),
        estimated_cost_max=(
            float(place.estimated_cost_max) if place.estimated_cost_max is not None else None
        ),
        cost_currency=place.cost_currency,
        image_url=place.image_url,
        image_license=place.image_license,
        source_name=place.source_name,
        source_record_id=place.source_record_id,
        source_url=place.source_url,
        imported_at=place.imported_at,
        verified_at=place.verified_at,
        is_featured=place.is_featured,
        tags=place.tags or [],
        directions_url=(
            f"https://www.google.com/maps/dir/?api=1&destination={place.latitude},{place.longitude}"
        ),
    )


@router.get("/municipalities", response_model=list[MunicipalityOut])
def list_municipalities(
    q: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
) -> list[Municipality]:
    """Returns searchable Nueva Ecija cities and municipalities."""
    stmt = select(Municipality)
    if q and q.strip():
        stmt = stmt.where(Municipality.name.ilike(f"%{q.strip()}%"))
    stmt = stmt.order_by(Municipality.is_city.desc(), Municipality.name.asc())
    return list(db.scalars(stmt).all())


@router.get("/places", response_model=PaginatedPlacesOut)
def list_places(
    q: str | None = Query(default=None, max_length=100),
    categories: list[str] | None = Query(default=None),
    municipality_id: uuid.UUID | None = Query(default=None),
    featured: bool | None = Query(default=None),
    min_lat: float | None = Query(default=None),
    max_lat: float | None = Query(default=None),
    min_lng: float | None = Query(default=None),
    max_lng: float | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PaginatedPlacesOut:
    """Searches and filters active Nueva Ecija POIs for Home search and Map bounds."""
    stmt = (
        select(Place)
        .outerjoin(Municipality, Place.municipality_id == Municipality.id)
        .options(joinedload(Place.municipality))
        .where(Place.is_active.is_(True))
    )

    if q and q.strip():
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Place.name.ilike(pattern),
                Place.address_text.ilike(pattern),
                Place.category.ilike(pattern),
                Municipality.name.ilike(pattern),
            )
        )

    if categories:
        # Support both repeated params (?categories=a&categories=b) and comma-separated (?categories=a,b)
        flat_categories: list[str] = []
        for item in categories:
            flat_categories.extend([c.strip() for c in item.split(",") if c.strip()])

        invalid = [c for c in flat_categories if c not in CANONICAL_CATEGORIES]
        if invalid:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported category filter(s): {', '.join(invalid)}",
            )
        stmt = stmt.where(Place.category.in_(flat_categories))

    if municipality_id is not None:
        stmt = stmt.where(Place.municipality_id == municipality_id)

    if featured is not None:
        stmt = stmt.where(Place.is_featured.is_(featured))

    if None not in (min_lat, max_lat, min_lng, max_lng):
        stmt = stmt.where(
            Place.latitude.between(min_lat, max_lat),
            Place.longitude.between(min_lng, max_lng),
        )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    rows = (
        db.scalars(
            stmt.order_by(Place.is_featured.desc(), Place.name.asc())
            .limit(limit)
            .offset(offset)
        )
        .unique()
        .all()
    )

    return PaginatedPlacesOut(
        total=total,
        limit=limit,
        offset=offset,
        items=[serialize_place(p) for p in rows],
    )


@router.get("/places/{place_id}", response_model=PlaceOut)
def get_place_detail(
    place_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> PlaceOut:
    """Returns full details and verification provenance for one Nueva Ecija POI."""
    stmt = (
        select(Place)
        .options(joinedload(Place.municipality))
        .where(Place.id == place_id, Place.is_active.is_(True))
    )
    place = db.scalar(stmt)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return serialize_place(place)
'''

FILES["backend/app/main.py"] = '''"""FastAPI entry point for the Nueva Ecija Travel Itinerary API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.places import router as places_router
from app.core.config import settings

app = FastAPI(
    title="Nueva Ecija Travel Itinerary API",
    version="0.1.0",
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url="/redoc" if settings.app_env == "development" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(places_router, prefix=settings.api_v1_prefix)


@app.get(f"{settings.api_v1_prefix}/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Liveness health check verifying API availability without leaking secrets."""
    return {
        "status": "ok",
        "province_scope": "Nueva Ecija",
        "environment": settings.app_env,
    }
'''

FILES["backend/alembic.ini"] = """[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

FILES["backend/alembic/env.py"] = '''"""Alembic migration environment configured against app.models.entities.Base."""

from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.core.config import settings
from app.core.database import Base
import app.models.entities  # noqa: F401 — registers all 7 ORM tables

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

FILES["backend/alembic/versions/0001_initial_nueva_ecija_schema.py"] = '''"""Initial Nueva Ecija Travel Itinerary schema (7 core tables).

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
'''

FILES["scripts/import_osm.py"] = '''#!/usr/bin/env python3
"""Step 2 — Idempotent OpenStreetMap / Overpass POI importer for Nueva Ecija.

Usage:
    python3 scripts/import_osm.py data/raw/nueva_ecija_osm.json --dry-run
    python3 scripts/import_osm.py data/raw/nueva_ecija_osm.json
"""

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend directory to sys.path so scripts can import app.*
BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.entities import Municipality, Place

# Nueva Ecija province bounding box
NE_BOUNDS = {
    "min_lat": 15.15,
    "max_lat": 16.15,
    "min_lng": 120.70,
    "max_lng": 121.40,
}


def is_within_nueva_ecija(lat: float, lng: float) -> bool:
    """Returns True if coordinates fall within Nueva Ecija's bounding box."""
    return (
        NE_BOUNDS["min_lat"] <= lat <= NE_BOUNDS["max_lat"]
        and NE_BOUNDS["min_lng"] <= lng <= NE_BOUNDS["max_lng"]
    )


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Computes great-circle distance in kilometers between two coordinates."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def normalize_name(s: str) -> str:
    """Normalizes municipality and city names for robust fuzzy matching."""
    return (
        s.lower()
        .replace("ñ", "n")
        .replace("city", "")
        .replace("science", "")
        .replace("of", "")
        .replace(".", "")
        .replace("-", " ")
        .strip()
    )


def map_osm_tags_to_category(tags: dict[str, str]) -> str | None:
    """Maps raw OpenStreetMap element tags to one of the 16 canonical MVP categories."""
    amenity = tags.get("amenity")
    tourism = tags.get("tourism")
    leisure = tags.get("leisure")
    historic = tags.get("historic")
    shop = tags.get("shop")
    waterway = tags.get("waterway")
    natural = tags.get("natural")
    public_transport = tags.get("public_transport")

    if amenity == "cafe":
        return "cafe"
    if amenity in {"restaurant", "fast_food", "food_court"}:
        return "restaurant"
    if tourism in {"hotel", "guest_house", "hostel", "motel", "chalet"}:
        return "hotel_accommodation"
    if tourism in {"attraction", "viewpoint"} or historic in {"monument", "memorial", "ruins"}:
        return "tourist_attraction"
    if (
        leisure in {"park", "nature_reserve", "garden"}
        or waterway == "waterfall"
        or natural in {"peak", "spring"}
    ):
        return "nature_park"
    if tourism == "resort" or leisure in {"water_park", "swimming_pool"}:
        return "resort_swimming"
    if amenity == "place_of_worship":
        return "church_religious"
    if tourism in {"museum", "gallery"} or historic == "heritage" or amenity == "arts_centre":
        return "museum_cultural"
    if shop in {"mall", "supermarket", "department_store"} or amenity == "marketplace":
        return "shopping_market"
    if amenity in {"bus_station", "ferry_terminal"} or public_transport in {"station", "stop_area"}:
        return "transport_terminal"
    if amenity in {"hospital", "clinic", "doctors"}:
        return "hospital_clinic"
    if amenity == "pharmacy":
        return "pharmacy"
    if amenity in {"bank", "atm"}:
        return "bank_atm"
    if amenity == "fuel":
        return "fuel_station"
    if shop == "convenience":
        return "convenience_store"
    if amenity in {"townhall", "police", "fire_station", "community_centre", "library"}:
        return "public_facility"
    return None


def resolve_municipality_id(
    tags: dict[str, str],
    lat: float,
    lng: float,
    municipalities: list[Municipality],
) -> object | None:
    """Matches a POI to a seeded Nueva Ecija municipality by addr:city tag or nearest center."""
    if not municipalities:
        return None
    city_tag = (tags.get("addr:city") or tags.get("addr:municipality") or "").strip()
    if city_tag:
        norm_tag = normalize_name(city_tag)
        for m in municipalities:
            norm_m = normalize_name(m.name)
            if norm_m == norm_tag or norm_tag in norm_m or norm_m in norm_tag:
                return m.id
    nearest = min(
        municipalities,
        key=lambda m: haversine_km(lat, lng, m.center_lat, m.center_lng),
    )
    return nearest.id


def import_osm_payload(
    db: Session,
    payload: dict,
    dry_run: bool = False,
) -> dict[str, int]:
    """Validates, deduplicates, and upserts OSM elements into the places table."""
    elements = payload.get("elements", [])
    municipalities = list(db.scalars(select(Municipality)).all())

    seen_source_ids: set[str] = set()
    validated_records: list[dict] = []
    skipped_out_of_bounds = 0
    skipped_unmapped = 0

    for el in elements:
        tags = el.get("tags") or {}
        name = (tags.get("name") or tags.get("name:en") or "").strip()
        lat = el.get("lat") if el.get("lat") is not None else (el.get("center") or {}).get("lat")
        lng = el.get("lon") if el.get("lon") is not None else (el.get("center") or {}).get("lon")
        el_type = el.get("type", "node")
        el_id = el.get("id")

        if not name or lat is None or lng is None or el_id is None:
            skipped_unmapped += 1
            continue

        lat_f, lng_f = float(lat), float(lng)
        if not is_within_nueva_ecija(lat_f, lng_f):
            skipped_out_of_bounds += 1
            continue

        category = map_osm_tags_to_category(tags)
        if not category:
            skipped_unmapped += 1
            continue

        source_record_id = f"{el_type}/{el_id}"
        if source_record_id in seen_source_ids:
            continue
        seen_source_ids.add(source_record_id)

        municipality_id = resolve_municipality_id(tags, lat_f, lng_f, municipalities)
        address_parts = [
            p
            for p in (
                tags.get("addr:housenumber"),
                tags.get("addr:street"),
                tags.get("addr:barangay"),
                tags.get("addr:city"),
            )
            if p
        ]
        address_text = ", ".join(address_parts) if address_parts else tags.get("addr:full")

        validated_records.append(
            {
                "name": name,
                "category": category,
                "latitude": lat_f,
                "longitude": lng_f,
                "municipality_id": municipality_id,
                "address_text": address_text,
                "description": tags.get("description"),
                "phone": tags.get("phone") or tags.get("contact:phone"),
                "website": tags.get("website") or tags.get("contact:website"),
                "opening_hours": tags.get("opening_hours"),
                "source_name": "OpenStreetMap",
                "source_record_id": source_record_id,
                "source_url": f"https://www.openstreetmap.org/{source_record_id}",
                "imported_at": datetime.now(timezone.utc),
                "is_active": True,
                "tags": [category],
            }
        )

    inserted = 0
    updated = 0
    if not dry_run:
        for rec in validated_records:
            existing = db.scalar(
                select(Place).where(
                    Place.source_name == rec["source_name"],
                    Place.source_record_id == rec["source_record_id"],
                )
            )
            if existing:
                existing.name = rec["name"]
                existing.category = rec["category"]
                existing.latitude = rec["latitude"]
                existing.longitude = rec["longitude"]
                existing.municipality_id = rec["municipality_id"]
                existing.address_text = rec["address_text"] or existing.address_text
                existing.phone = rec["phone"] or existing.phone
                existing.website = rec["website"] or existing.website
                existing.opening_hours = rec["opening_hours"] or existing.opening_hours
                existing.imported_at = rec["imported_at"]
                updated += 1
            else:
                db.add(Place(**rec))
                inserted += 1
        db.commit()

    return {
        "validated": len(validated_records),
        "inserted": inserted,
        "updated": updated,
        "skipped_out_of_bounds": skipped_out_of_bounds,
        "skipped_unmapped": skipped_unmapped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Nueva Ecija OSM POIs into PostgreSQL.")
    parser.add_argument("filepath", help="Path to Overpass JSON export file")
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing to DB")
    args = parser.parse_args()

    with open(args.filepath, "r", encoding="utf-8") as f:
        payload = json.load(f)

    with SessionLocal() as db:
        stats = import_osm_payload(db, payload, dry_run=args.dry_run)

    mode = "DRY-RUN" if args.dry_run else "COMMITTED"
    print(f"[{mode}] Nueva Ecija OSM Import Summary: {stats}")


if __name__ == "__main__":
    main()
'''

FILES["scripts/seed_featured_places.py"] = '''#!/usr/bin/env python3
"""Step 2 — Seeds Nueva Ecija cities/municipalities and curated featured destinations.

Includes all key destinations showcased across the Figma UI references:
- Cabanatuan, Gapan, Pantabangan, General Tinio, and Bongabon Day 1 stops.

Usage:
    python3 scripts/seed_featured_places.py
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.entities import Municipality, Place

# Key Nueva Ecija Cities and Municipalities with center coordinates
NUEVA_ECIJA_MUNICIPALITIES = [
    {"name": "Cabanatuan City", "slug": "cabanatuan-city", "is_city": True, "center_lat": 15.4865, "center_lng": 120.9734},
    {"name": "Gapan City", "slug": "gapan-city", "is_city": True, "center_lat": 15.3072, "center_lng": 120.9464},
    {"name": "Science City of Muñoz", "slug": "science-city-of-munoz", "is_city": True, "center_lat": 15.7161, "center_lng": 120.9031},
    {"name": "Palayan City", "slug": "palayan-city", "is_city": True, "center_lat": 15.5415, "center_lng": 121.0848},
    {"name": "San Jose City", "slug": "san-jose-city", "is_city": True, "center_lat": 15.7917, "center_lng": 120.9959},
    {"name": "General Tinio", "slug": "general-tinio", "is_city": False, "center_lat": 15.3490, "center_lng": 121.0490},
    {"name": "Gabaldon", "slug": "gabaldon", "is_city": False, "center_lat": 15.4550, "center_lng": 121.3364},
    {"name": "Pantabangan", "slug": "pantabangan", "is_city": False, "center_lat": 15.8239, "center_lng": 121.1444},
    {"name": "Bongabon", "slug": "bongabon", "is_city": False, "center_lat": 15.6322, "center_lng": 121.1447},
    {"name": "Laur", "slug": "laur", "is_city": False, "center_lat": 15.5869, "center_lng": 121.1833},
    {"name": "Santa Rosa", "slug": "santa-rosa", "is_city": False, "center_lat": 15.4247, "center_lng": 120.9386},
    {"name": "Talavera", "slug": "talavera", "is_city": False, "center_lat": 15.5842, "center_lng": 120.9189},
]

# Curated Featured Destinations across Nueva Ecija aligned with Figma designs
CURATED_FEATURED_PLACES = [
    {
        "name": "Minalungao National Park",
        "category": "nature_park",
        "municipality_slug": "general-tinio",
        "latitude": 15.2981,
        "longitude": 121.1223,
        "address_text": "Brgy. Pias, General Tinio, Nueva Ecija",
        "description": (
            "Protected limestone canyon along the Peñaranda River featuring emerald waters, "
            "bamboo rafting, cave formations, and scenic hanging bridge viewpoints."
        ),
        "opening_hours": "07:00-17:00",
        "estimated_cost_min": 100.0,
        "estimated_cost_max": 500.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/minalungao-national-park",
        "source_url": "https://www.openstreetmap.org/way/238471920",
        "is_featured": True,
        "tags": ["nature_park", "Nature & Parks", "Family-Friendly", "Resort/Swimming"],
    },
    {
        "name": "Pantabangan Dam and Lake Viewpoint",
        "category": "tourist_attraction",
        "municipality_slug": "pantabangan",
        "latitude": 15.8126,
        "longitude": 121.1098,
        "address_text": "Pantabangan, Nueva Ecija",
        "description": (
            "Major reservoir and hydroelectric dam overlooking the Sierra Madre foothills, "
            "popular for sunrise viewing, lakeside sightseeing, and photography."
        ),
        "opening_hours": "06:00-18:00",
        "estimated_cost_min": None,
        "estimated_cost_max": None,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/pantabangan-dam-viewpoint",
        "source_url": "https://www.openstreetmap.org/way/139284711",
        "is_featured": True,
        "tags": ["tourist_attraction", "Nature & Parks", "Family-Friendly"],
    },
    {
        "name": "Saint Nicholas of Tolentine Cathedral & Plaza Lucero",
        "category": "church_religious",
        "municipality_slug": "cabanatuan-city",
        "latitude": 15.4898,
        "longitude": 120.9679,
        "address_text": "Burgos Avenue, Cabanatuan City, Nueva Ecija",
        "description": (
            "Historic seat of the Roman Catholic Diocese of Cabanatuan adjacent to Plaza Lucero, "
            "site of General Antonio Luna's historical marker."
        ),
        "opening_hours": "06:00-19:00",
        "estimated_cost_min": None,
        "estimated_cost_max": None,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/cabanatuan-cathedral-plaza-lucero",
        "source_url": "https://www.openstreetmap.org/way/159283741",
        "is_featured": True,
        "tags": ["church_religious", "Culture & History", "Religious/Cultural Sites", "Family-Friendly"],
    },
    {
        "name": "Dupinga River Eco-Tourism Area",
        "category": "nature_park",
        "municipality_slug": "gabaldon",
        "latitude": 15.4892,
        "longitude": 121.3204,
        "address_text": "Gabaldon, Nueva Ecija",
        "description": (
            "Freshwater mountain river bordered by the Sierra Madre range, known for shallow "
            "picnic rapids and riverside cottages."
        ),
        "opening_hours": "07:00-17:00",
        "estimated_cost_min": 50.0,
        "estimated_cost_max": 350.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/dupinga-river-gabaldon",
        "source_url": "https://www.openstreetmap.org/node/482910384",
        "is_featured": True,
        "tags": ["nature_park", "Nature & Parks", "Resort/Swimming", "Family-Friendly"],
    },
    {
        "name": "CLSU Agricultural Museum & Philippine Carabao Center",
        "category": "museum_cultural",
        "municipality_slug": "science-city-of-munoz",
        "latitude": 15.7325,
        "longitude": 120.9288,
        "address_text": "Central Luzon State University Compound, Science City of Muñoz, Nueva Ecija",
        "description": (
            "Educational agricultural heritage center and dairy showcase highlighting Nueva Ecija's "
            "role as the Rice Granary of the Philippines and fresh carabao milk products."
        ),
        "opening_hours": "08:00-17:00",
        "estimated_cost_min": 50.0,
        "estimated_cost_max": 250.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/clsu-agricultural-museum-pcc",
        "source_url": "https://www.openstreetmap.org/way/301928374",
        "is_featured": True,
        "tags": ["museum_cultural", "Culture & History", "Food Trip", "Family-Friendly"],
    },
    {
        "name": "Lumang Gapan Heritage Street & National Shrine of La Virgen Divina Pastora",
        "category": "church_religious",
        "municipality_slug": "gapan-city",
        "latitude": 15.3065,
        "longitude": 120.9461,
        "address_text": "Gapan City, Nueva Ecija",
        "description": (
            "Brick-and-adobe heritage district and Marian pilgrimage shrine dating back to the "
            "Spanish colonial period."
        ),
        "opening_hours": "06:00-20:00",
        "estimated_cost_min": None,
        "estimated_cost_max": None,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/gapan-divina-pastora-shrine",
        "source_url": "https://www.openstreetmap.org/way/210394857",
        "is_featured": True,
        "tags": ["church_religious", "Culture & History", "Religious/Cultural Sites"],
    },
    {
        "name": "Camp Pangatian War Memorial Shrine",
        "category": "museum_cultural",
        "municipality_slug": "cabanatuan-city",
        "latitude": 15.5122,
        "longitude": 121.0419,
        "address_text": "Brgy. Pangatian, Cabanatuan City, Nueva Ecija",
        "description": (
            "World War II historical memorial commemorating the January 1945 Great Raid that "
            "liberated Allied prisoners of war in Cabanatuan."
        ),
        "opening_hours": "08:00-17:00",
        "estimated_cost_min": 50.0,
        "estimated_cost_max": 100.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/camp-pangatian-memorial-shrine",
        "source_url": "https://www.openstreetmap.org/way/192837465",
        "is_featured": True,
        "tags": ["museum_cultural", "Culture & History", "Family-Friendly"],
    },
    {
        "name": "Edna's Cakeland & Cafe Kapitan",
        "category": "cafe",
        "municipality_slug": "cabanatuan-city",
        "latitude": 15.4884,
        "longitude": 120.9692,
        "address_text": "Don Manuel B. Tinio St., Cabanatuan City, Nueva Ecija",
        "description": (
            "Well-known homegrown Cabanatuan bakery and cafe serving local pastries, cakes, "
            "and kapeng barako blends."
        ),
        "opening_hours": "08:00-20:00",
        "estimated_cost_min": 150.0,
        "estimated_cost_max": 450.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/ednas-cakeland-cabanatuan",
        "source_url": "https://www.openstreetmap.org/node/592837461",
        "is_featured": True,
        "tags": ["cafe", "Cafes", "Food Trip", "Family-Friendly"],
    },
    # --- Figma-Showcased Featured Venues ---
    {
        "name": "Rohi Paperflower Cafe",
        "category": "cafe",
        "municipality_slug": "bongabon",
        "latitude": 15.6315,
        "longitude": 121.1438,
        "address_text": "Bongabon, Nueva Ecija",
        "description": (
            "Popular botanical cafe in Bongabon known for picturesque paperflower decor, "
            "artisanal handcrafted coffee, and Filipino pasta dishes."
        ),
        "opening_hours": "09:00-20:00",
        "estimated_cost_min": 150.0,
        "estimated_cost_max": 400.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/rohi-paperflower-cafe",
        "source_url": "https://www.openstreetmap.org/node/998273641",
        "is_featured": True,
        "tags": ["cafe", "Cafes", "Food Trip"],
    },
    {
        "name": "Museo de Bongabon",
        "category": "museum_cultural",
        "municipality_slug": "bongabon",
        "latitude": 15.6330,
        "longitude": 121.1455,
        "address_text": "Town Hall Compound, Bongabon, Nueva Ecija",
        "description": (
            "Town cultural museum showcasing Bongabon's onion-capital agricultural history, "
            "colonial artifacts, and local heritage."
        ),
        "opening_hours": "08:00-17:00",
        "estimated_cost_min": None,
        "estimated_cost_max": None,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/museo-de-bongabon",
        "source_url": "https://www.openstreetmap.org/way/882736412",
        "is_featured": True,
        "tags": ["museum_cultural", "Culture & History", "Family-Friendly"],
    },
    {
        "name": "La Casa Prime Cabins",
        "category": "hotel_accommodation",
        "municipality_slug": "bongabon",
        "latitude": 15.6280,
        "longitude": 121.1520,
        "address_text": "Brgy. Vega, Bongabon, Nueva Ecija",
        "description": (
            "Peaceful mountain-view A-frame cabins and staycation retreat situated at the foot "
            "of the Sierra Madre mountain range."
        ),
        "opening_hours": "24/7",
        "estimated_cost_min": 2500.0,
        "estimated_cost_max": 5500.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/la-casa-prime-cabins",
        "source_url": "https://www.openstreetmap.org/way/882736415",
        "is_featured": True,
        "tags": ["hotel_accommodation", "Resort/Swimming", "Family-Friendly"],
    },
    {
        "name": "Thornes Samgyupsal House",
        "category": "restaurant",
        "municipality_slug": "bongabon",
        "latitude": 15.6328,
        "longitude": 121.1460,
        "address_text": "Poblacion, Bongabon, Nueva Ecija",
        "description": (
            "Popular casual grill restaurant in Bongabon offering Korean-style BBQ, unlimited pork, "
            "and traditional side dishes."
        ),
        "opening_hours": "11:00-21:00",
        "estimated_cost_min": 299.0,
        "estimated_cost_max": 499.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/thornes-samgyupsal-house",
        "source_url": "https://www.openstreetmap.org/node/998273645",
        "is_featured": True,
        "tags": ["restaurant", "Food Trip"],
    },
    {
        "name": "George Point Viewdeck & Resto",
        "category": "tourist_attraction",
        "municipality_slug": "pantabangan",
        "latitude": 15.8205,
        "longitude": 121.1350,
        "address_text": "Pantabangan Lake Overlook, Pantabangan, Nueva Ecija",
        "description": (
            "Elevated lakeside scenic viewpoint and open-air restaurant offering 360-degree vistas "
            "of Pantabangan Lake and surrounding rolling mountains."
        ),
        "opening_hours": "07:00-19:00",
        "estimated_cost_min": 200.0,
        "estimated_cost_max": 600.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/george-point-pantabangan",
        "source_url": "https://www.openstreetmap.org/node/998273648",
        "is_featured": True,
        "tags": ["tourist_attraction", "Nature & Parks", "Food Trip"],
    },
    {
        "name": "Highland Bali Villas Resort and Spa",
        "category": "resort_swimming",
        "municipality_slug": "pantabangan",
        "latitude": 15.8270,
        "longitude": 121.1415,
        "address_text": "Pantabangan, Nueva Ecija",
        "description": (
            "Bali-inspired luxury hillside resort featuring infinity pools, water sports on Pantabangan Lake, "
            "spas, and Balinese architecture."
        ),
        "opening_hours": "24/7",
        "estimated_cost_min": 3500.0,
        "estimated_cost_max": 9500.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/highland-bali-villas-pantabangan",
        "source_url": "https://www.openstreetmap.org/way/882736420",
        "is_featured": True,
        "tags": ["resort_swimming", "hotel_accommodation", "Family-Friendly"],
    },
    {
        "name": "Farm Villaronte",
        "category": "tourist_attraction",
        "municipality_slug": "cabanatuan-city",
        "latitude": 15.5020,
        "longitude": 121.0150,
        "address_text": "Cabanatuan City, Nueva Ecija",
        "description": (
            "Eco-tourism and family farm destination featuring lush outdoor picnic spaces, gardens, "
            "and nature recreation."
        ),
        "opening_hours": "08:00-17:00",
        "estimated_cost_min": 100.0,
        "estimated_cost_max": 300.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/farm-villaronte-cabanatuan",
        "source_url": "https://www.openstreetmap.org/node/998273650",
        "is_featured": True,
        "tags": ["tourist_attraction", "Nature & Parks", "Family-Friendly"],
    },
    {
        "name": "Casa Batik",
        "category": "restaurant",
        "municipality_slug": "cabanatuan-city",
        "latitude": 15.4850,
        "longitude": 120.9710,
        "address_text": "Cabanatuan City, Nueva Ecija",
        "description": (
            "Artisan garden restaurant and cafe serving signature regional Central Luzon dishes "
            "and specialty refreshments."
        ),
        "opening_hours": "10:00-21:00",
        "estimated_cost_min": 250.0,
        "estimated_cost_max": 650.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/casa-batik-cabanatuan",
        "source_url": "https://www.openstreetmap.org/node/998273652",
        "is_featured": True,
        "tags": ["restaurant", "Food Trip"],
    },
    {
        "name": "Lake Farm De La Marre",
        "category": "resort_swimming",
        "municipality_slug": "pantabangan",
        "latitude": 15.8310,
        "longitude": 121.1380,
        "address_text": "Pantabangan, Nueva Ecija",
        "description": (
            "Lakeside agri-resort and glamping grounds offering water activities, mountain views, "
            "and sustainable farm visits."
        ),
        "opening_hours": "08:00-18:00",
        "estimated_cost_min": 500.0,
        "estimated_cost_max": 2500.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/lake-farm-de-la-marre",
        "source_url": "https://www.openstreetmap.org/node/998273655",
        "is_featured": True,
        "tags": ["resort_swimming", "nature_park", "Family-Friendly"],
    },
]


def seed_municipalities_and_featured(db: Session) -> dict[str, int]:
    """Idempotently upserts Nueva Ecija municipalities and curated featured POIs."""
    muni_map: dict[str, Municipality] = {}
    muni_created = 0

    for m in NUEVA_ECIJA_MUNICIPALITIES:
        existing = db.scalar(select(Municipality).where(Municipality.slug == m["slug"]))
        if existing:
            existing.name = m["name"]
            existing.is_city = m["is_city"]
            existing.center_lat = m["center_lat"]
            existing.center_lng = m["center_lng"]
            muni_map[m["slug"]] = existing
        else:
            obj = Municipality(**m)
            db.add(obj)
            db.flush()
            muni_map[m["slug"]] = obj
            muni_created += 1

    now = datetime.now(timezone.utc)
    places_created = 0
    places_updated = 0

    for item in CURATED_FEATURED_PLACES:
        muni = muni_map.get(item["municipality_slug"])
        existing_place = db.scalar(
            select(Place).where(
                Place.source_name == item["source_name"],
                Place.source_record_id == item["source_record_id"],
            )
        )
        payload = {
            "name": item["name"],
            "category": item["category"],
            "latitude": item["latitude"],
            "longitude": item["longitude"],
            "municipality_id": muni.id if muni else None,
            "address_text": item["address_text"],
            "description": item["description"],
            "opening_hours": item["opening_hours"],
            "estimated_cost_min": item["estimated_cost_min"],
            "estimated_cost_max": item["estimated_cost_max"],
            "cost_currency": "PHP",
            "source_name": item["source_name"],
            "source_record_id": item["source_record_id"],
            "source_url": item["source_url"],
            "imported_at": now,
            "verified_at": now,
            "is_featured": item["is_featured"],
            "is_active": True,
            "tags": item["tags"],
        }
        if existing_place:
            for k, v in payload.items():
                setattr(existing_place, k, v)
            places_updated += 1
        else:
            db.add(Place(**payload))
            places_created += 1

    db.commit()
    return {
        "municipalities_total": len(muni_map),
        "municipalities_created": muni_created,
        "featured_places_created": places_created,
        "featured_places_updated": places_updated,
    }


def main() -> None:
    with SessionLocal() as db:
        summary = seed_municipalities_and_featured(db)
    print(f"[SEED COMPLETE] {summary}")


if __name__ == "__main__":
    main()
'''

FILES["backend/tests/test_foundation.py"] = '''"""Automated test suite for Steps 1 and 2 (Database, Health, Seeding, and OSM Import)."""

import sys
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
for d in [str(BACKEND_DIR), str(ROOT_DIR)]:
    if d not in sys.path:
        sys.path.insert(0, d)

from app.core.database import Base, get_db
from app.main import app
from app.models.entities import Municipality, Place
from scripts.import_osm import import_osm_payload
from scripts.seed_featured_places import seed_municipalities_and_featured


def make_test_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_health_and_featured_places_pipeline():
    TestingSessionLocal = make_test_session()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # 1. Verify /api/v1/health
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.json()["province_scope"] == "Nueva Ecija"

    # 2. Verify idempotent seeding of municipalities and featured places (12 municipalities, 17 featured places)
    with TestingSessionLocal() as db:
        first_seed = seed_municipalities_and_featured(db)
        assert first_seed["municipalities_created"] == 12
        assert first_seed["featured_places_created"] == 17

        second_seed = seed_municipalities_and_featured(db)
        assert second_seed["municipalities_created"] == 0
        assert second_seed["featured_places_created"] == 0
        assert second_seed["featured_places_updated"] == 17

    # 3. Verify GET /api/v1/municipalities search
    muni_res = client.get("/api/v1/municipalities?q=Cabanatuan")
    assert muni_res.status_code == 200
    assert len(muni_res.json()) == 1
    assert muni_res.json()[0]["slug"] == "cabanatuan-city"

    # 4. Verify GET /api/v1/places featured filter & honest null costs
    places_res = client.get("/api/v1/places?featured=true")
    assert places_res.status_code == 200
    payload = places_res.json()
    assert payload["total"] == 17
    pantabangan = next(p for p in payload["items"] if "Pantabangan Dam" in p["name"])
    assert pantabangan["estimated_cost_min"] is None
    assert pantabangan["estimated_cost_max"] is None
    assert "google.com/maps/dir/" in pantabangan["directions_url"]

    # 5. Verify Figma-featured Bongabon stops exist
    bongabon_res = client.get("/api/v1/places?q=Bongabon")
    assert bongabon_res.status_code == 200
    bongabon_names = [p["name"] for p in bongabon_res.json()["items"]]
    assert any("Rohi Paperflower" in n for n in bongabon_names)
    assert any("La Casa Prime Cabins" in n for n in bongabon_names)
    assert any("Museo de Bongabon" in n for n in bongabon_names)
    assert any("Thornes Samgyupsal" in n for n in bongabon_names)

    # 6. Verify comma-separated and multi-value category query parameter handling
    cat_res = client.get("/api/v1/places?categories=cafe,restaurant")
    assert cat_res.status_code == 200
    for place in cat_res.json()["items"]:
        assert place["category"] in {"cafe", "restaurant"}

    # 7. Verify idempotent OSM import & out-of-province rejection
    sample_osm = {
        "elements": [
            {
                "type": "node",
                "id": 1001,
                "lat": 15.4872,
                "lon": 120.9711,
                "tags": {"name": "Cabanatuan Roastery Cafe", "amenity": "cafe", "addr:city": "Cabanatuan City"},
            },
            {
                "type": "node",
                "id": 1002,
                "lat": 14.5995,  # Manila (outside Nueva Ecija bounds -> must be rejected!)
                "lon": 120.9842,
                "tags": {"name": "Manila Cafe Outside NE", "amenity": "cafe"},
            },
        ]
    }
    with TestingSessionLocal() as db:
        stats1 = import_osm_payload(db, sample_osm, dry_run=False)
        assert stats1["validated"] == 1
        assert stats1["inserted"] == 1
        assert stats1["skipped_out_of_bounds"] == 1

        stats2 = import_osm_payload(db, sample_osm, dry_run=False)
        assert stats2["inserted"] == 0
        assert stats2["updated"] == 1
        total_places = len(db.scalars(select(Place)).all())
        assert total_places == 18  # 17 curated + 1 valid OSM import
'''

for rel_path, content in FILES.items():
    full_path = os.path.join(BASE_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Successfully generated ./ project structure (Steps 0-2)!")
