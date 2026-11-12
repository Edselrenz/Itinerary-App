"""Pydantic v2 schemas for multi-day itineraries, days, stops, and reordering."""

import uuid
from datetime import date, datetime, time
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
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

    # GIS & Turn-by-Turn routing extensions
    google_place_id: str | None = None
    travel_mode_from_prev: str | None = "DRIVE"
    travel_distance_meters: int | None = None
    travel_duration_seconds: int | None = None
    route_polyline_from_prev: str | None = None

    @field_validator("planned_time", mode="before")
    @classmethod
    def parse_planned_time(cls, v: Any) -> time | None:
        if v is None or v == "":
            return None
        if isinstance(v, time):
            return v
        if isinstance(v, str):
            v_clean = v.strip()
            if not v_clean:
                return None
            if "-" in v_clean:
                v_clean = v_clean.split("-")[0].strip()
            for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M:%S", "%H:%M"):
                try:
                    return datetime.strptime(v_clean, fmt).time()
                except ValueError:
                    continue
        return v


class ItineraryItemCreate(ItineraryItemBase):
    """Payload to add a new stop to an itinerary day."""

    place_payload: dict | None = None

    @model_validator(mode="after")
    def validate_place_or_custom(self) -> "ItineraryItemCreate":
        if (
            not self.place_id
            and not self.google_place_id
            and not (self.custom_title and self.custom_title.strip())
            and not (self.place_payload and self.place_payload.get("name"))
        ):
            raise ValueError(
                "A stop must specify place_id, google_place_id, place_payload, or custom_title."
            )
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
    travel_mode_from_prev: str | None = None
    travel_distance_meters: int | None = None
    travel_duration_seconds: int | None = None
    route_polyline_from_prev: str | None = None

    @field_validator("planned_time", mode="before")
    @classmethod
    def parse_planned_time(cls, v: Any) -> time | None:
        if v is None or v == "":
            return None
        if isinstance(v, time):
            return v
        if isinstance(v, str):
            v_clean = v.strip()
            if not v_clean:
                return None
            if "-" in v_clean:
                v_clean = v_clean.split("-")[0].strip()
            for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M:%S", "%H:%M"):
                try:
                    return datetime.strptime(v_clean, fmt).time()
                except ValueError:
                    continue
        return v


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
    """Serialized itinerary day with chronological stops and computed route overview."""

    id: uuid.UUID
    itinerary_id: uuid.UUID
    day_number: int
    travel_date: date
    title: str | None = None
    items: list[ItineraryItemOut] = []

    # Day routing overview
    day_overview_polyline: str | None = None
    total_distance_meters: int | None = None
    total_travel_duration_seconds: int | None = None
    route_legs: list[dict] = []

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
    days: list[ItineraryDayCreate] | None = None


class ItineraryOut(BaseModel):
    """Serialized itinerary with days and stops."""

    id: uuid.UUID
    user_id: uuid.UUID | None = None
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


class SuggestedItineraryRequest(BaseModel):
    """Payload to request an automated, geographically clustered suggested itinerary."""

    title: str = Field("Suggested Nueva Ecija Itinerary", max_length=160)
    destination: str = Field("Nueva Ecija", max_length=120)
    start_date: date
    end_date: date
    daily_budget: float = Field(2500.0, ge=0.0)
    preferences: list[str] = Field(default_factory=list)
    save_immediately: bool = Field(
        False, description="If True and authenticated, persists directly to database."
    )
    origin_lat: float | None = None
    origin_lng: float | None = None
    travel_mode: str = "DRIVE"
    min_rating: float | None = None
    pacing: str = "moderate"
    include_live_places: bool = False

    @model_validator(mode="after")
    def validate_dates(self) -> "SuggestedItineraryRequest":
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date.")
        return self



class ItineraryReorderItem(BaseModel):
    """Specifies new ordering and day assignment for a stop."""

    id: uuid.UUID
    day_id: uuid.UUID
    sort_order: int = Field(..., ge=1)


class ItineraryReorderIn(BaseModel):
    """Batch reorder request payload."""

    items: list[ItineraryReorderItem]


class RouteStepOut(BaseModel):
    """Step-by-step turn instructions for active navigation."""

    instruction: str
    distance_meters: int
    duration_seconds: int
    polyline: str | None = None
    start_location: dict | None = None
    end_location: dict | None = None
    maneuver: str | None = None


class RouteLegOut(BaseModel):
    """Single leg connecting consecutive stops."""

    start_location: dict
    end_location: dict
    distance_meters: int
    duration_seconds: int
    polyline: str | None = None
    steps: list[RouteStepOut] = []


class RouteComputeRequest(BaseModel):
    """Stateless request to calculate driving/walking routes between stops."""

    origin: dict  # {"latitude": float, "longitude": float}
    destination: dict  # {"latitude": float, "longitude": float}
    intermediates: list[dict] = []
    travel_mode: str = "DRIVE"


class RouteComputeResponse(BaseModel):
    """Computed route with turn-by-turn legs and polyline."""

    overview_polyline: str
    total_distance_meters: int
    total_duration_seconds: int
    legs: list[RouteLegOut] = []
    source: str = "google_routes"  # "google_routes" | "osrm" | "haversine_direct"


