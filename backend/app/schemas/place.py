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


class PlacePhotoOut(BaseModel):
    """Serialized photo attribution from Google Places."""

    name: str | None = None
    width_px: int | None = None
    height_px: int | None = None
    author_attributions: list[dict] = []
    photo_uri: str | None = None


class PlaceReviewOut(BaseModel):
    """Serialized user review from Google Places."""

    name: str | None = None
    author_name: str | None = None
    author_photo_uri: str | None = None
    rating: int | None = None
    text: str | None = None
    publish_time: str | None = None
    relative_publish_time_description: str | None = None


class PlaceRegularOpeningHoursOut(BaseModel):
    """Structured opening hours schedule from Google Places."""

    open_now: bool | None = None
    periods: list[dict] = []
    weekday_descriptions: list[str] = []


class PlaceOut(BaseModel):
    """Serialized Point of Interest (POI) with provenance, verification, and GIS details."""

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

    # Google Places v1 GIS extensions
    google_place_id: str | None = None
    google_types: list[str] = []
    editorial_summary: str | None = None
    regular_opening_hours: dict | None = None
    rating: float | None = None
    user_rating_count: int | None = None
    price_level: int | None = None
    photos: list[dict] = []
    reviews: list[dict] = []
    business_status: str | None = None
    google_maps_uri: str | None = None
    details_cached_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class LivePlaceSearchRequest(BaseModel):
    """Request payload for live Google Places text/nearby search."""

    query: str
    latitude: float | None = None
    longitude: float | None = None
    radius_meters: float | None = 50000.0
    included_types: list[str] | None = None
    min_rating: float | None = None
    open_now: bool | None = None


class LivePlaceSearchResponse(BaseModel):
    """Response payload wrapping discovered Google or cached places."""

    places: list[PlaceOut]
    source: str  # "google_live" | "cache" | "local_db"
    total: int


class PaginatedPlacesOut(BaseModel):
    """Paginated response wrapper for GET /api/v1/places."""

    total: int
    limit: int
    offset: int
    items: list[PlaceOut]
