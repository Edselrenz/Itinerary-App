"""Itinerary, Days, and Stops data models."""

from dataclasses import dataclass, field
from datetime import date, datetime
import re
from typing import Any, Optional
import uuid

from desktop_client.models.place import Place


def _is_valid_uuid(val: Any) -> bool:
    """Checks whether a string or object is a valid UUID."""
    if not val:
        return False
    try:
        uuid.UUID(str(val))
        return True
    except Exception:
        return False


def to_backend_iso_time(time_str: Optional[str]) -> Optional[str]:
    """Normalizes user-facing time strings ('09:30 AM - 11:30 AM', '2:00 PM', '14:30') into 'HH:MM:00' for FastAPI."""
    if not time_str:
        return None
    clean = str(time_str).strip()
    if not clean:
        return None
    first_part = clean.split("-")[0].strip() if "-" in clean else clean
    if re.match(r"^\d{2}:\d{2}:\d{2}$", first_part):
        return first_part
    if re.match(r"^\d{2}:\d{2}$", first_part):
        return f"{first_part}:00"
    m = re.match(r"^(\d{1,2}):(\d{2})(?::\d{2})?\s*(AM|PM)?$", first_part, re.IGNORECASE)
    if m:
        h = int(m.group(1))
        mins = m.group(2)
        meridiem = (m.group(3) or "").upper()
        if meridiem == "PM" and h < 12:
            h += 12
        elif meridiem == "AM" and h == 12:
            h = 0
        return f"{h:02d}:{mins}:00"
    return None


@dataclass
class ItineraryItem:
    """Individual scheduled stop or venue within an itinerary day."""
    
    id: str
    day_id: str
    sort_order: int
    place_id: Optional[str] = None
    custom_title: Optional[str] = None
    custom_lat: Optional[float] = None
    custom_lng: Optional[float] = None
    planned_time: Optional[str] = None
    duration_minutes: int = 90
    notes: Optional[str] = None
    estimated_cost_min: Optional[float] = None
    estimated_cost_max: Optional[float] = None
    place: Optional[Place] = None
    google_place_id: Optional[str] = None
    travel_mode_from_prev: Optional[str] = "DRIVE"
    travel_distance_meters: Optional[int] = None
    travel_duration_seconds: Optional[int] = None
    route_polyline_from_prev: Optional[str] = None

    @property
    def display_title(self) -> str:
        """Resolves venue name: linked POI name or custom off-grid venue title."""
        if self.place and self.place.name:
            return self.place.name
        if self.custom_title:
            return self.custom_title
        return "Scheduled Stop"

    @property
    def display_cost(self) -> str:
        """Formatted stop estimated cost."""
        if self.estimated_cost_min is None and self.estimated_cost_max is None:
            if self.place:
                return self.place.formatted_cost
            return "Free / Unspecified"
        if self.estimated_cost_min == 0 and (self.estimated_cost_max is None or self.estimated_cost_max == 0):
            return "Free"
        if self.estimated_cost_min is not None and self.estimated_cost_max is not None:
            if self.estimated_cost_min == self.estimated_cost_max:
                return f"₱{self.estimated_cost_min:,.0f}"
            return f"₱{self.estimated_cost_min:,.0f} - ₱{self.estimated_cost_max:,.0f}"
        if self.estimated_cost_min is not None:
            return f"₱{self.estimated_cost_min:,.0f}"
        return f"₱{self.estimated_cost_max:,.0f}"

    @property
    def representative_cost(self) -> float:
        """Numerical cost estimate for day & trip budgeting."""
        if self.estimated_cost_max is not None:
            return float(self.estimated_cost_max)
        if self.estimated_cost_min is not None:
            return float(self.estimated_cost_min)
        if self.place and self.place.estimated_cost_max is not None:
            return float(self.place.estimated_cost_max)
        if self.place and self.place.estimated_cost_min is not None:
            return float(self.place.estimated_cost_min)
        return 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ItineraryItem":
        place_obj = None
        if data.get("place") and isinstance(data["place"], dict):
            place_obj = Place.from_dict(data["place"])
        return cls(
            id=str(data.get("id", uuid.uuid4())),
            day_id=str(data.get("day_id", "")),
            place_id=str(data["place_id"]) if data.get("place_id") else None,
            custom_title=data.get("custom_title"),
            custom_lat=float(data["custom_lat"]) if data.get("custom_lat") is not None else None,
            custom_lng=float(data["custom_lng"]) if data.get("custom_lng") is not None else None,
            sort_order=int(data.get("sort_order", 1)),
            planned_time=str(data["planned_time"]) if data.get("planned_time") else None,
            duration_minutes=int(data.get("duration_minutes", 90)),
            notes=data.get("notes"),
            estimated_cost_min=(
                float(data["estimated_cost_min"])
                if data.get("estimated_cost_min") is not None
                else None
            ),
            estimated_cost_max=(
                float(data["estimated_cost_max"])
                if data.get("estimated_cost_max") is not None
                else None
            ),
            place=place_obj,
            google_place_id=data.get("google_place_id"),
            travel_mode_from_prev=data.get("travel_mode_from_prev", "DRIVE"),
            travel_distance_meters=data.get("travel_distance_meters"),
            travel_duration_seconds=data.get("travel_duration_seconds"),
            route_polyline_from_prev=data.get("route_polyline_from_prev"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "day_id": self.day_id,
            "place_id": self.place_id,
            "custom_title": self.custom_title,
            "custom_lat": self.custom_lat,
            "custom_lng": self.custom_lng,
            "sort_order": self.sort_order,
            "planned_time": self.planned_time,
            "duration_minutes": self.duration_minutes,
            "notes": self.notes,
            "estimated_cost_min": self.estimated_cost_min,
            "estimated_cost_max": self.estimated_cost_max,
            "place": self.place.to_dict() if self.place else None,
            "google_place_id": self.google_place_id,
            "travel_mode_from_prev": self.travel_mode_from_prev,
            "travel_distance_meters": self.travel_distance_meters,
            "travel_duration_seconds": self.travel_duration_seconds,
            "route_polyline_from_prev": self.route_polyline_from_prev,
        }


@dataclass
class ItineraryDay:
    """A single day within a travel itinerary."""
    
    id: str
    itinerary_id: str
    day_number: int
    travel_date: str
    title: Optional[str] = None
    items: list[ItineraryItem] = field(default_factory=list)
    day_overview_polyline: Optional[str] = None
    total_distance_meters: Optional[int] = None
    total_travel_duration_seconds: Optional[int] = None

    @property
    def display_title(self) -> str:
        if self.title and self.title.strip():
            return f"Day {self.day_number}: {self.title}"
        return f"Day {self.day_number}"

    @property
    def total_day_cost(self) -> float:
        return sum(item.representative_cost for item in self.items)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ItineraryDay":
        raw_items = data.get("items") or []
        items = [ItineraryItem.from_dict(item) for item in raw_items]
        items.sort(key=lambda i: i.sort_order)
        return cls(
            id=str(data.get("id", uuid.uuid4())),
            itinerary_id=str(data.get("itinerary_id", "")),
            day_number=int(data.get("day_number", 1)),
            travel_date=str(data.get("travel_date", "")),
            title=data.get("title"),
            items=items,
            day_overview_polyline=data.get("day_overview_polyline"),
            total_distance_meters=data.get("total_distance_meters"),
            total_travel_duration_seconds=data.get("total_travel_duration_seconds"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "itinerary_id": self.itinerary_id,
            "day_number": self.day_number,
            "travel_date": self.travel_date,
            "title": self.title,
            "items": [item.to_dict() for item in self.items],
            "day_overview_polyline": self.day_overview_polyline,
            "total_distance_meters": self.total_distance_meters,
            "total_travel_duration_seconds": self.total_travel_duration_seconds,
        }


@dataclass
class Itinerary:
    """Full travel itinerary with multi-day schedule and stops."""
    
    id: str
    title: str
    destination: str
    start_date: str
    end_date: str
    daily_budget: float = 2500.0
    preferences: list[str] = field(default_factory=list)
    type: str = "custom"  # "custom" | "suggested"
    assumptions: list[str] = field(default_factory=list)
    days: list[ItineraryDay] = field(default_factory=list)
    user_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_guest: bool = False

    @property
    def total_stops(self) -> int:
        return sum(len(day.items) for day in self.days)

    @property
    def total_days(self) -> int:
        return max(1, len(self.days))

    @property
    def total_estimated_cost(self) -> float:
        return sum(day.total_day_cost for day in self.days)

    @property
    def date_range_display(self) -> str:
        return f"{self.start_date} to {self.end_date}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Itinerary":
        raw_days = data.get("days") or []
        days = [ItineraryDay.from_dict(d) for d in raw_days]
        days.sort(key=lambda d: d.day_number)
        return cls(
            id=str(data.get("id", uuid.uuid4())),
            title=str(data.get("title", "Untitled Itinerary")),
            destination=str(data.get("destination", "Nueva Ecija")),
            start_date=str(data.get("start_date", "")),
            end_date=str(data.get("end_date", "")),
            daily_budget=float(data.get("daily_budget", 2500.0)),
            preferences=list(data.get("preferences") or []),
            type=str(data.get("type", "custom")),
            assumptions=list(data.get("assumptions") or []),
            days=days,
            user_id=str(data["user_id"]) if data.get("user_id") else None,
            created_at=str(data.get("created_at")) if data.get("created_at") else None,
            updated_at=str(data.get("updated_at")) if data.get("updated_at") else None,
            is_guest=bool(data.get("is_guest", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "destination": self.destination,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "daily_budget": self.daily_budget,
            "preferences": self.preferences,
            "type": self.type,
            "assumptions": self.assumptions,
            "days": [day.to_dict() for day in self.days],
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_guest": self.is_guest,
        }

    def to_create_payload(self) -> "ItineraryCreatePayload":
        days_data = []
        for d in self.days:
            items_data = []
            for it in d.items:
                valid_uuid = _is_valid_uuid(it.place_id)
                place_dict = it.place.to_dict() if it.place else None
                items_data.append({
                    "place_id": it.place_id if valid_uuid else None,
                    "custom_title": it.custom_title or it.display_title,
                    "custom_lat": it.custom_lat if it.custom_lat is not None else (it.place.latitude if it.place else None),
                    "custom_lng": it.custom_lng if it.custom_lng is not None else (it.place.longitude if it.place else None),
                    "sort_order": it.sort_order,
                    "planned_time": to_backend_iso_time(it.planned_time) or it.planned_time,
                    "duration_minutes": it.duration_minutes or 90,
                    "notes": it.notes,
                    "estimated_cost_min": it.estimated_cost_min,
                    "estimated_cost_max": it.estimated_cost_max,
                    "place_payload": place_dict,
                    "place": place_dict,
                })
            days_data.append({
                "day_number": d.day_number,
                "travel_date": d.travel_date or self.start_date,
                "title": d.title or f"Day {d.day_number}",
                "items": items_data,
            })
        return ItineraryCreatePayload(
            title=self.title,
            destination=self.destination,
            start_date=self.start_date,
            end_date=self.end_date,
            daily_budget=self.daily_budget,
            preferences=self.preferences,
            type=self.type,
            assumptions=self.assumptions,
            days=days_data,
        )


@dataclass
class SuggestedItineraryRequest:
    """Request payload for automated clustered itinerary generation."""
    
    title: str = "Suggested Nueva Ecija Itinerary"
    destination: str = "Nueva Ecija"
    start_date: str = ""
    end_date: str = ""
    daily_budget: float = 2500.0
    preferences: list[str] = field(default_factory=list)
    pacing: str = "moderate"
    travel_mode: str = "DRIVE"
    save_immediately: bool = False
    min_rating: Optional[float] = None
    include_live_places: bool = True
    anchor_place_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "title": self.title,
            "destination": self.destination,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "daily_budget": self.daily_budget,
            "preferences": self.preferences,
            "pacing": self.pacing,
            "travel_mode": self.travel_mode,
            "save_immediately": self.save_immediately,
            "include_live_places": self.include_live_places,
        }
        if self.min_rating is not None:
            res["min_rating"] = self.min_rating
        if self.anchor_place_id is not None:
            res["anchor_place_id"] = self.anchor_place_id
        return res


@dataclass
class ItineraryItemCreatePayload:
    """Payload to add a stop to an itinerary day."""
    
    day_id: str
    place_id: Optional[str] = None
    custom_title: Optional[str] = None
    custom_lat: Optional[float] = None
    custom_lng: Optional[float] = None
    sort_order: int = 1
    planned_time: Optional[str] = None
    duration_minutes: int = 90
    notes: Optional[str] = None
    estimated_cost_min: Optional[float] = None
    estimated_cost_max: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "sort_order": self.sort_order,
            "duration_minutes": self.duration_minutes,
        }
        if self.place_id:
            res["place_id"] = self.place_id
        if self.custom_title:
            res["custom_title"] = self.custom_title
        if self.custom_lat is not None:
            res["custom_lat"] = self.custom_lat
        if self.custom_lng is not None:
            res["custom_lng"] = self.custom_lng
        if self.planned_time:
            res["planned_time"] = self.planned_time
        if self.notes:
            res["notes"] = self.notes
        if self.estimated_cost_min is not None:
            res["estimated_cost_min"] = self.estimated_cost_min
        if self.estimated_cost_max is not None:
            res["estimated_cost_max"] = self.estimated_cost_max
        return res


@dataclass
class ItineraryCreatePayload:
    """Payload to create a new multi-day itinerary in backend."""
    
    title: str
    destination: str
    start_date: str
    end_date: str
    daily_budget: float
    preferences: list[str] = field(default_factory=list)
    type: str = "custom"
    assumptions: list[str] = field(default_factory=list)
    days: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "destination": self.destination,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "daily_budget": self.daily_budget,
            "preferences": self.preferences,
            "type": self.type,
            "assumptions": self.assumptions,
            "days": self.days,
        }
