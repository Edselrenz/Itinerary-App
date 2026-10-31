"""Pydantic v2 schemas for multi-day itineraries, days, stops, and reordering."""

import uuid
from datetime import date, datetime, time
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.schemas.place import PlaceOut


class ItineraryItemBase(BaseModel):
    """Common properties for a scheduled itinerary stop."""

    place_id: uuid.UUID | None = None
    custom_title: str | None = Field(None, max_length=200)
    custom_lat: float | None = Field(None, ge=-90.0, le=90.0)
    custom_lng: float | None = Field(None, ge=-180.0, le=180.0)
    sort_order: int = Field(1, ge=1)
    planned_time: time | None = None
    duration_minutes: int = Field(90, ge=5, le=1440)
    notes: str | None = None
    estimated_cost_min: float | None = Field(None, ge=0.0)
    estimated_cost_max: float | None = Field(None, ge=0.0)


class ItineraryItemCreate(ItineraryItemBase):
    """Payload to add a new stop to an itinerary day."""

    @model_validator(mode="after")
    def validate_place_or_custom(self) -> "ItineraryItemCreate":
        if not self.place_id and not (self.custom_title and self.custom_title.strip()):
            raise ValueError("Either place_id or custom_title must be provided for a stop.")
        if self.estimated_cost_min is not None and self.estimated_cost_max is not None:
            if self.estimated_cost_max < self.estimated_cost_min:
                raise ValueError("estimated_cost_max cannot be less than estimated_cost_min.")
        return self


class ItineraryItemUpdate(BaseModel):
    """Payload to partially update an itinerary stop."""

    custom_title: str | None = Field(None, max_length=200)
    custom_lat: float | None = Field(None, ge=-90.0, le=90.0)
    custom_lng: float | None = Field(None, ge=-180.0, le=180.0)
    sort_order: int | None = Field(None, ge=1)
    planned_time: time | None = None
    duration_minutes: int | None = Field(None, ge=5, le=1440)
    notes: str | None = None
    estimated_cost_min: float | None = Field(None, ge=0.0)
    estimated_cost_max: float | None = Field(None, ge=0.0)


class ItineraryItemOut(ItineraryItemBase):
    """Serialized itinerary stop with linked POI details."""

    id: uuid.UUID
    day_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    place: PlaceOut | None = None

    model_config = ConfigDict(from_attributes=True)


class ItineraryDayCreate(BaseModel):
    """Payload to add a day to an itinerary."""

    day_number: int = Field(..., ge=1)
    travel_date: date
    title: str | None = Field(None, max_length=120)
    items: list[ItineraryItemCreate] = []


class ItineraryDayOut(BaseModel):
    """Serialized itinerary day with chronological stops."""

    id: uuid.UUID
    itinerary_id: uuid.UUID
    day_number: int
    travel_date: date
    title: str | None = None
    items: list[ItineraryItemOut] = []

    model_config = ConfigDict(from_attributes=True)


class ItineraryCreate(BaseModel):
    """Payload to create a new multi-day itinerary."""

    title: str = Field(..., min_length=1, max_length=160)
    destination: str = Field("Nueva Ecija", max_length=120)
    start_date: date
    end_date: date
    daily_budget: float = Field(0.0, ge=0.0)
    preferences: list[str] = []
    type: str = Field("custom", pattern="^(custom|suggested)$")
    assumptions: list[str] = []
    days: list[ItineraryDayCreate] = []

    @model_validator(mode="after")
    def validate_dates(self) -> "ItineraryCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date.")
        return self


class ItineraryUpdate(BaseModel):
    """Payload to partially update itinerary metadata."""

    title: str | None = Field(None, min_length=1, max_length=160)
    destination: str | None = Field(None, max_length=120)
    start_date: date | None = None
    end_date: date | None = None
    daily_budget: float | None = Field(None, ge=0.0)
    preferences: list[str] | None = None
    assumptions: list[str] | None = None


class ItineraryOut(BaseModel):
    """Serialized itinerary with days and stops."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    destination: str
    start_date: date
    end_date: date
    daily_budget: float
    preferences: list[str]
    type: str
    assumptions: list[str]
    created_at: datetime
    updated_at: datetime
    days: list[ItineraryDayOut] = []

    model_config = ConfigDict(from_attributes=True)


class ItineraryReorderItem(BaseModel):
    """Specifies new ordering and day assignment for a stop."""

    id: uuid.UUID
    day_id: uuid.UUID
    sort_order: int = Field(..., ge=1)


class ItineraryReorderIn(BaseModel):
    """Batch reorder request payload."""

    items: list[ItineraryReorderItem]
