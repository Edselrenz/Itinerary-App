"""Places, Municipalities, and Geospatial POI data models."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PlaceCategory:
    """Category classification."""
    
    key: str
    label: str
    icon: str


@dataclass
class Municipality:
    """Nueva Ecija LGU municipality or city."""
    
    id: str
    name: str
    zip_code: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_count: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Municipality":
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            zip_code=data.get("zip_code"),
            description=data.get("description"),
            latitude=float(data["latitude"]) if data.get("latitude") is not None else None,
            longitude=float(data["longitude"]) if data.get("longitude") is not None else None,
            place_count=data.get("place_count"),
        )


@dataclass
class Place:
    """Destination, point-of-interest, or venue in Nueva Ecija."""
    
    id: str
    name: str
    category: str
    latitude: float
    longitude: float
    municipality_id: Optional[str] = None
    municipality_name: Optional[str] = None
    address_text: Optional[str] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[str] = None
    estimated_cost_min: Optional[float] = None
    estimated_cost_max: Optional[float] = None
    cost_currency: str = "PHP"
    image_url: Optional[str] = None
    is_featured: bool = False
    tags: list[str] = field(default_factory=list)
    directions_url: Optional[str] = None
    rating: Optional[float] = None
    user_rating_count: Optional[int] = None
    price_level: Optional[int] = None
    photos: list[dict[str, Any]] = field(default_factory=list)
    editorial_summary: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Place":
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            category=str(data.get("category", "tourist_attraction")),
            latitude=float(data.get("latitude", 15.4865)),
            longitude=float(data.get("longitude", 120.9734)),
            municipality_id=str(data["municipality_id"]) if data.get("municipality_id") else None,
            municipality_name=data.get("municipality_name"),
            address_text=data.get("address_text"),
            description=data.get("description"),
            phone=data.get("phone"),
            website=data.get("website"),
            opening_hours=data.get("opening_hours"),
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
            cost_currency=str(data.get("cost_currency", "PHP")),
            image_url=data.get("image_url"),
            is_featured=bool(data.get("is_featured", False)),
            tags=list(data.get("tags") or []),
            directions_url=data.get("directions_url"),
            rating=float(data["rating"]) if data.get("rating") is not None else None,
            user_rating_count=data.get("user_rating_count"),
            price_level=data.get("price_level"),
            photos=list(data.get("photos") or []),
            editorial_summary=data.get("editorial_summary"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "municipality_id": self.municipality_id,
            "municipality_name": self.municipality_name,
            "address_text": self.address_text,
            "description": self.description,
            "phone": self.phone,
            "website": self.website,
            "opening_hours": self.opening_hours,
            "estimated_cost_min": self.estimated_cost_min,
            "estimated_cost_max": self.estimated_cost_max,
            "cost_currency": self.cost_currency,
            "image_url": self.image_url,
            "is_featured": self.is_featured,
            "tags": self.tags,
            "directions_url": self.directions_url,
            "rating": self.rating,
            "user_rating_count": self.user_rating_count,
            "price_level": self.price_level,
        }

    @property
    def formatted_cost(self) -> str:
        """Honest pricing display conforming to Nueva Ecija requirements."""
        if self.estimated_cost_min is None and self.estimated_cost_max is None:
            return "Estimated Cost: Free / Varies"
        if self.estimated_cost_min == 0 and (self.estimated_cost_max is None or self.estimated_cost_max == 0):
            return "Free Admission"
        if self.estimated_cost_min is not None and self.estimated_cost_max is not None:
            if self.estimated_cost_min == self.estimated_cost_max:
                return f"₱{self.estimated_cost_min:,.0f}"
            return f"₱{self.estimated_cost_min:,.0f} - ₱{self.estimated_cost_max:,.0f}"
        if self.estimated_cost_min is not None:
            return f"From ₱{self.estimated_cost_min:,.0f}"
        return f"Up to ₱{self.estimated_cost_max:,.0f}"

    @property
    def formatted_category(self) -> str:
        """User-friendly category display."""
        mapping = {
            "nature_park": "Nature & Parks",
            "tourist_attraction": "Tourist Attraction",
            "museum_cultural": "Museum & Cultural",
            "church_religious": "Church & Historic",
            "resort_swimming": "Resort & Swimming",
            "restaurant": "Restaurant & Dining",
            "cafe": "Cafe & Coffee",
            "hotel_accommodation": "Hotel & Accommodation",
            "shopping_market": "Market & Shopping",
            "transport_terminal": "Transport Terminal",
            "hospital_clinic": "Hospital & Health",
            "pharmacy": "Pharmacy",
            "bank_atm": "Bank & ATM",
            "fuel_station": "Fuel Station",
            "convenience_store": "Convenience Store",
            "public_facility": "Public Facility",
        }
        return mapping.get(self.category, self.category.replace("_", " ").title())


@dataclass
class PaginatedPlaces:
    """Paginated collection of places."""
    
    items: list[Place]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PaginatedPlaces":
        items = [Place.from_dict(item) for item in data.get("items", [])]
        return cls(
            items=items,
            total=int(data.get("total", len(items))),
            page=int(data.get("page", 1)),
            page_size=int(data.get("page_size", len(items))),
            total_pages=int(data.get("total_pages", 1)),
        )
