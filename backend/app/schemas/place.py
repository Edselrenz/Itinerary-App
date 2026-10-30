"""Pydantic v2 response schemas for Municipalities and Places."""

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
