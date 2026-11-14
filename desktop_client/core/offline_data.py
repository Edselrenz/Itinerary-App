"""Canonical offline datasets, 2,673 OSM places, and 32-LGU metadata for Nueva Ecija MVP.

Ported from Project/src/app/core/data/offline-places.data.ts.
Provides seamless 3-tier offline fallback across Home tab, PlaceService, MapView, and ItineraryService.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Optional, Sequence

from desktop_client.config.settings import get_settings


@dataclass
class CanonicalOfflinePlace:
    id: str
    name: str
    category: str
    category_name: str
    municipality: str
    address_text: str
    latitude: float
    longitude: float
    description: str
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[str] = None
    estimated_cost_min: Optional[float] = None
    estimated_cost_max: Optional[float] = None
    cost_currency: str = "PHP"
    image: str = ""
    tags: list[str] = field(default_factory=list)
    directions_url: str = ""
    default_time: str = ""
    default_duration_minutes: int = 120
    is_featured: bool = True
    rating: float = 4.6
    user_rating_count: int = 150

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "category_name": self.category_name,
            "municipality_name": self.municipality,
            "address": self.address_text,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "description": self.description,
            "phone": self.phone,
            "website": self.website,
            "opening_hours": self.opening_hours,
            "estimated_cost_min": self.estimated_cost_min,
            "estimated_cost_max": self.estimated_cost_max,
            "cost_currency": self.cost_currency,
            "photos": [self.image] if self.image else [],
            "rating": self.rating,
            "user_rating_count": self.user_rating_count,
            "is_featured": self.is_featured,
            "tags": self.tags,
            "directions_url": self.directions_url,
            "default_time": self.default_time,
            "default_duration_minutes": self.default_duration_minutes,
        }


CANONICAL_OFFLINE_PLACES: list[CanonicalOfflinePlace] = [
    CanonicalOfflinePlace(
        id="dest-rohi-paperflower",
        name="Rohi Paperflower Cafe",
        category="cafe",
        category_name="Cafe & Dining",
        municipality="Bongabon",
        address_text="Bongabon, Nueva Ecija",
        latitude=15.6315,
        longitude=121.1440,
        description="Charming artisanal cafe adorned with vibrant paper flower crafts, signature coffee blends, and baked pastries.",
        opening_hours="10:00-21:00",
        estimated_cost_min=150.0,
        estimated_cost_max=350.0,
        image="popular_destinations/rohi_paperflower.png",
        tags=["Cafe", "Artisan Coffee", "Crafts"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.6315,121.1440",
        default_time="12:00 PM - 02:00 PM",
        default_duration_minutes=120,
        rating=4.7,
        user_rating_count=210,
    ),
    CanonicalOfflinePlace(
        id="dest-museo-bongabon",
        name="Museo de Bongabon",
        category="museum_cultural",
        category_name="Culture & Museum",
        municipality="Bongabon",
        address_text="Bongabon, Nueva Ecija",
        latitude=15.6300,
        longitude=121.1430,
        description="Community heritage museum chronicling the agricultural identity, historic revolution roots, and onion industry of Bongabon.",
        opening_hours="08:00-17:00",
        estimated_cost_min=None,
        estimated_cost_max=None,
        image="popular_destinations/museo_bongabon.png",
        tags=["Museum", "Culture", "History"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.6300,121.1430",
        default_time="02:00 PM - 05:00 PM",
        default_duration_minutes=180,
        rating=4.6,
        user_rating_count=135,
    ),
    CanonicalOfflinePlace(
        id="dest-thornes-samgyupsal",
        name="Thornes Samgyupsal House",
        category="restaurant",
        category_name="Restaurant",
        municipality="Bongabon",
        address_text="Bongabon, Nueva Ecija",
        latitude=15.6330,
        longitude=121.1460,
        description="Beloved dining spot serving unlimited Korean samgyupsal BBQ, savory side dishes, and fresh lettuce wraps.",
        opening_hours="11:00-22:00",
        estimated_cost_min=399.0,
        estimated_cost_max=599.0,
        image="popular_destinations/thornes_samgyupsal.png",
        tags=["Korean BBQ", "Samgyupsal", "Dinner"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.6330,121.1460",
        default_time="05:00 PM - 07:00 PM",
        default_duration_minutes=120,
        rating=4.5,
        user_rating_count=180,
    ),
    CanonicalOfflinePlace(
        id="dest-la-casa-prime",
        name="La Casa Prime Cabins",
        category="hotel_accommodation",
        category_name="Resort & Stay",
        municipality="Bongabon",
        address_text="Bongabon, Nueva Ecija",
        latitude=15.6280,
        longitude=121.1520,
        description="Serene mountain cabin sanctuary with overlooking views of Pantabangan Lake and modern glamping amenities.",
        opening_hours="24 Hours",
        estimated_cost_min=2500.0,
        estimated_cost_max=6000.0,
        image="popular_destinations/Lasa Casa Prime Cabins.jpg",
        tags=["Mountain Cabins", "Lake View", "Glamping"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.6280,121.1520",
        default_time="02:00 PM - 12:00 PM",
        default_duration_minutes=360,
        rating=4.8,
        user_rating_count=190,
    ),
    CanonicalOfflinePlace(
        id="dest-minalungao",
        name="Minalungao National Park",
        category="nature_park",
        category_name="Nature & Adventure",
        municipality="General Tinio",
        address_text="General Tinio, Nueva Ecija",
        latitude=15.2981,
        longitude=121.1223,
        description="Towering 16-meter limestone cliffs along emerald Peñaranda River with bamboo rafting, cliff diving, and cave exploration.",
        opening_hours="07:00-17:00",
        estimated_cost_min=100.0,
        estimated_cost_max=500.0,
        image="popular_destinations/minalungao.png",
        tags=["Balsa Rafting", "Cliff Diving", "Caving"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.2981,121.1223",
        default_time="09:00 AM - 01:00 PM",
        default_duration_minutes=240,
        rating=4.8,
        user_rating_count=890,
    ),
    CanonicalOfflinePlace(
        id="dest-tagpuan-gapan",
        name="Tagpuan sa Lumang Gapan",
        category="church_religious",
        category_name="Heritage & Faith",
        municipality="Gapan City",
        address_text="Gapan City, Nueva Ecija",
        latitude=15.3065,
        longitude=120.9461,
        description="The 'Little Vigan' of Nueva Ecija featuring restored Spanish colonial street lamps, historic brick facades, and night food stalls.",
        opening_hours="06:00-20:00",
        estimated_cost_min=None,
        estimated_cost_max=150.0,
        image="popular_destinations/tagpuan_gapan.png",
        tags=["Colonial Walk", "Night Market", "Historic Street"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.3065,120.9461",
        default_time="05:30 PM - 09:00 PM",
        default_duration_minutes=180,
        rating=4.7,
        user_rating_count=740,
    ),
    CanonicalOfflinePlace(
        id="dest-pantabangan-lake",
        name="Pantabangan Dam and Lake Viewpoint",
        category="tourist_attraction",
        category_name="Tourist Attraction",
        municipality="Pantabangan",
        address_text="Pantabangan, Nueva Ecija",
        latitude=15.8126,
        longitude=121.1098,
        description="One of Southeast Asia's largest human-made water reservoirs, celebrated for mountain vistas, clean air, and largemouth bass sportfishing.",
        opening_hours="06:00-18:00",
        estimated_cost_min=None,
        estimated_cost_max=200.0,
        image="popular_destinations/pantabangan_lake.png",
        tags=["Bass Fishing", "Scenic View", "Dam Site"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.8126,121.1098",
        default_time="08:00 AM - 12:00 PM",
        default_duration_minutes=240,
        rating=4.7,
        user_rating_count=420,
    ),
    CanonicalOfflinePlace(
        id="dest-george-point",
        name="George Point",
        category="cafe",
        category_name="Cafe & Dining",
        municipality="Pantabangan",
        address_text="Pantabangan, Nueva Ecija",
        latitude=15.8200,
        longitude=121.1150,
        description="Scenic panoramic hilltop overlooking Pantabangan Lake, ideal for sunset views, relaxing lakeside dining, and coffee.",
        opening_hours="08:00-20:00",
        estimated_cost_min=150.0,
        estimated_cost_max=450.0,
        image="popular_destinations/george_point.png",
        tags=["Sunset View", "Lakeside Coffee", "Photography"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.8200,121.1150",
        default_time="04:30 PM - 06:30 PM",
        default_duration_minutes=120,
        rating=4.6,
        user_rating_count=195,
    ),
    CanonicalOfflinePlace(
        id="dest-highland-bali",
        name="Highland Bali Villas Resort and Spa",
        category="hotel_accommodation",
        category_name="Resort & Stay",
        municipality="Pantabangan",
        address_text="Pantabangan, Nueva Ecija",
        latitude=15.8180,
        longitude=121.1210,
        description="Balinese-inspired lakefront retreat with water sports, exotic villas, and breathtaking vistas across the water.",
        opening_hours="24 Hours",
        estimated_cost_min=3500.0,
        estimated_cost_max=8000.0,
        image="popular_destinations/highland_bali.png",
        tags=["Water Sports", "Resort Villas", "Spa"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.8180,121.1210",
        default_time="02:00 PM - 12:00 PM",
        default_duration_minutes=360,
        rating=4.8,
        user_rating_count=650,
    ),
    CanonicalOfflinePlace(
        id="dest-farm-villaronte",
        name="Farm Villaronte",
        category="tourist_attraction",
        category_name="Tourist Attraction",
        municipality="San Jose City",
        address_text="San Jose City, Nueva Ecija",
        latitude=15.7850,
        longitude=120.9980,
        description="Vibrant flower farm, organic produce picking, rustic pavilions, and family-friendly agro-tourism trails.",
        opening_hours="08:00-17:00",
        estimated_cost_min=50.0,
        estimated_cost_max=200.0,
        image="popular_destinations/farm_villaronte.png",
        tags=["Sunflower Fields", "Organic Produce", "Agri-Tour"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.7850,120.9980",
        default_time="09:00 AM - 11:30 AM",
        default_duration_minutes=150,
        rating=4.7,
        user_rating_count=520,
    ),
    CanonicalOfflinePlace(
        id="dest-casa-batik",
        name="Casa Batik",
        category="museum_cultural",
        category_name="Culture & Museum",
        municipality="Cabanatuan City",
        address_text="Cabanatuan City, Nueva Ecija",
        latitude=15.4850,
        longitude=120.9680,
        description="Artisan craft space celebrating Philippine textile traditions, local handcrafted coffee, and homegrown culinary heritage.",
        opening_hours="09:00-19:00",
        estimated_cost_min=100.0,
        estimated_cost_max=300.0,
        image="popular_destinations/casa_batik.png",
        tags=["Handcrafted Goods", "Art Cafe", "Local Heritage"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.4850,120.9680",
        default_time="11:00 AM - 01:00 PM",
        default_duration_minutes=90,
        rating=4.7,
        user_rating_count=180,
    ),
    CanonicalOfflinePlace(
        id="dest-pavillion-farm",
        name="D' Pavilion Farm and Resort",
        category="resort_swimming",
        category_name="Resort & Swimming",
        municipality="Bongabon",
        address_text="Bongabon, Nueva Ecija",
        latitude=15.6322,
        longitude=121.1447,
        description="Sprawling eco-tourism estate in the Onion Capital with open lawns, fresh mountain breezes, and native dining.",
        opening_hours="08:00-18:00",
        estimated_cost_min=150.0,
        estimated_cost_max=400.0,
        image="popular_destinations/D_ Pavilion Farm and Resort.jpg",
        tags=["Mountain View", "Onion Capital", "Eco Camp"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.6322,121.1447",
        default_time="01:00 PM - 03:00 PM",
        default_duration_minutes=120,
        rating=4.6,
        user_rating_count=160,
    ),
    CanonicalOfflinePlace(
        id="dest-lake-farm-marre",
        name="Lake Farm de La Marre",
        category="hotel_accommodation",
        category_name="Resort & Stay",
        municipality="San Jose City",
        address_text="San Jose City, Nueva Ecija",
        latitude=15.7720,
        longitude=120.9850,
        description="Tranquil countryside lakefront farm estate with boating, peaceful nature retreats, and farm-to-table culinary dining.",
        opening_hours="08:00-20:00",
        estimated_cost_min=500.0,
        estimated_cost_max=2500.0,
        image="popular_destinations/Lake Farm de La Marre.jpg",
        tags=["Lakeside Retreat", "Nature Farm", "Boating"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.7720,120.9850",
        default_time="02:00 PM - 04:00 PM",
        default_duration_minutes=120,
        rating=4.7,
        user_rating_count=230,
    ),
]


ALL_32_LGUS_METADATA: dict[str, dict[str, Any]] = {
    "Aliaga": {"district": "Central", "is_city": False, "poi_count": 48, "highlights": ["Taong Putik Festival", "Bibingka Delicacies"]},
    "Bongabon": {"district": "East", "is_city": False, "poi_count": 64, "highlights": ["Onion Capital", "Museo de Bongabon", "Rohi Cafe"]},
    "Cabanatuan City": {"district": "Central", "is_city": True, "poi_count": 412, "highlights": ["Camp Pangatian Shrine", "Plaza Lucero", "Central Terminal"]},
    "Cabiao": {"district": "South", "is_city": False, "poi_count": 52, "highlights": ["Nabao Lake", "Mt. Arayat Foothills"]},
    "Carranglan": {"district": "North", "is_city": False, "poi_count": 39, "highlights": ["General Luna Falls", "Dalton Pass Highway"]},
    "Cuyapo": {"district": "North", "is_city": False, "poi_count": 45, "highlights": ["Apolinario Mabini Sites", "Colosboa Hills"]},
    "Gabaldon": {"district": "East", "is_city": False, "poi_count": 72, "highlights": ["Dupinga River", "Sierra Madre Ecotourism"]},
    "Gapan City": {"district": "South", "is_city": True, "poi_count": 184, "highlights": ["Tagpuan sa Lumang Gapan", "Three Kings Parish"]},
    "General Mamerto Natividad": {"district": "Central", "is_city": False, "poi_count": 36, "highlights": ["General Natividad Shrine"]},
    "General Tinio": {"district": "South", "is_city": False, "poi_count": 92, "highlights": ["Minalungao National Park", "Papaya River"]},
    "Guimba": {"district": "North", "is_city": False, "poi_count": 88, "highlights": ["San Juan Nepomuceno Church", "Rice Plains"]},
    "Jaen": {"district": "South", "is_city": False, "poi_count": 42, "highlights": ["San Agustin Parish", "Rice Fields"]},
    "Laur": {"district": "East", "is_city": False, "poi_count": 34, "highlights": ["Pinagtampakan Falls", "Fort Magsaysay"]},
    "Licab": {"district": "Central", "is_city": False, "poi_count": 28, "highlights": ["Don Dalmacio Esguerra Shrine", "Kariton Festival"]},
    "Llanera": {"district": "Central", "is_city": False, "poi_count": 31, "highlights": ["Katubusan Festival"]},
    "Lupao": {"district": "North", "is_city": False, "poi_count": 38, "highlights": ["Lupao Dam", "Rice and Corn Agriculture"]},
    "Nampicuan": {"district": "North", "is_city": False, "poi_count": 24, "highlights": ["Holy Face of Manoppello Sanctuary"]},
    "Palayan City": {"district": "Central", "is_city": True, "poi_count": 115, "highlights": ["Provincial Capitol", "Government Center"]},
    "Pantabangan": {"district": "North", "is_city": False, "poi_count": 78, "highlights": ["Pantabangan Dam & Lake", "Highland Bali", "George Point"]},
    "Peñaranda": {"district": "South", "is_city": False, "poi_count": 35, "highlights": ["St. Francis of Assisi Church", "Peñaranda River"]},
    "Quezon": {"district": "Central", "is_city": False, "poi_count": 33, "highlights": ["Patimyas Festival"]},
    "Rizal": {"district": "East", "is_city": False, "poi_count": 41, "highlights": ["General Luna Memorial", "Mt. Williams"]},
    "San Antonio": {"district": "South", "is_city": False, "poi_count": 56, "highlights": ["Cuyapo River", "St. Anthony Abbot Parish"]},
    "San Isidro": {"district": "South", "is_city": False, "poi_count": 49, "highlights": ["Historic Revolutionary House", "Wright Institute"]},
    "San Jose City": {"district": "North", "is_city": True, "poi_count": 210, "highlights": ["St. Joseph Cathedral", "Diamond Park", "Gateway to North"]},
    "San Leonardo": {"district": "South", "is_city": False, "poi_count": 47, "highlights": ["San Bartolome Parish", "Maharlika Highway Food"]},
    "Santa Rosa": {"district": "Central", "is_city": False, "poi_count": 68, "highlights": ["Holy Cross Parish", "Rose Town Markets"]},
    "Santo Domingo": {"district": "Central", "is_city": False, "poi_count": 44, "highlights": ["Pulong Bato Ecopark"]},
    "Science City of Muñoz": {"district": "Central", "is_city": True, "poi_count": 165, "highlights": ["CLSU Agri Campus", "Philippine Carabao Center", "PhilRice"]},
    "Talavera": {"district": "Central", "is_city": False, "poi_count": 96, "highlights": ["Talavera Municipal Plaza", "Rice Granary"]},
    "Talugtug": {"district": "North", "is_city": False, "poi_count": 26, "highlights": ["Talugtug Rolling Hills"]},
    "Zaragoza": {"district": "South", "is_city": False, "poi_count": 37, "highlights": ["San Vicente Ferrer Parish", "Scenic Countryside"]},
}


_CACHED_ALL_PLACES: Optional[list[dict[str, Any]]] = None


def load_osm_places() -> list[dict[str, Any]]:
    """Loads curated OpenStreetMap places from bundled or local assets."""
    global _CACHED_ALL_PLACES
    if _CACHED_ALL_PLACES is not None:
        return _CACHED_ALL_PLACES

    settings = get_settings()
    asset_file = settings.assets_dir / "data" / "osm_places.json"
    if not asset_file.is_file():
        proj_file = settings.base_dir.parent / "Project" / "src" / "assets" / "data" / "osm_places.json"
        if proj_file.is_file():
            asset_file = proj_file

    raw_osm: list[dict[str, Any]] = []
    if asset_file.is_file():
        try:
            with open(asset_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    raw_osm = data
                elif isinstance(data, dict) and "places" in data:
                    raw_osm = data["places"]
        except Exception:
            raw_osm = []

    # Merge: Put canonical curated places at top
    merged: list[dict[str, Any]] = [p.to_dict() for p in CANONICAL_OFFLINE_PLACES]
    seen_ids = {p["id"] for p in merged}
    seen_names = {p["name"].lower().strip() for p in merged}

    for item in raw_osm:
        item_id = str(item.get("id", ""))
        item_name = str(item.get("name", "")).lower().strip()
        if item_id in seen_ids or item_name in seen_names:
            continue
        seen_ids.add(item_id)
        seen_names.add(item_name)
        merged.append(item)

    _CACHED_ALL_PLACES = merged
    return _CACHED_ALL_PLACES


def get_all_offline_places() -> list[dict[str, Any]]:
    """Returns the consolidated 2,673+ offline places list."""
    return load_osm_places()


def get_filtered_local_places(
    q: Optional[str] = None,
    category: Optional[str] = None,
    categories: Optional[Sequence[str]] = None,
    municipality_name: Optional[str] = None,
    municipality_id: Optional[str] = None,
    is_featured: Optional[bool] = None,
    price_tier: Optional[str] = None,
    min_rating: Optional[float] = None,
    bounds: Optional[tuple[float, float, float, float]] = None,  # (min_lat, max_lat, min_lng, max_lng)
    sort: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Filters offline places in-memory with full parity to backend query params."""
    all_places = get_all_offline_places()
    filtered: list[dict[str, Any]] = []

    # Category normalization
    active_cats = set()
    if category:
        for c in category.split(","):
            if c.strip():
                active_cats.add(c.strip().lower())
    if categories:
        for c in categories:
            if c and c.strip():
                active_cats.add(c.strip().lower())

    target_muni = (municipality_name or municipality_id or "").lower().strip()
    query_str = (q or "").lower().strip()

    for p in all_places:
        # Search query
        if query_str:
            name = str(p.get("name", "")).lower()
            desc = str(p.get("description", "")).lower()
            muni = str(p.get("municipality_name", "")).lower()
            cat = str(p.get("category", "")).lower()
            if not (query_str in name or query_str in desc or query_str in muni or query_str in cat):
                continue

        # Category match
        if active_cats:
            p_cat = str(p.get("category", "")).lower()
            if p_cat not in active_cats and "all" not in active_cats:
                continue

        # Municipality match
        if target_muni and target_muni not in ("all", "all municipalities", "nueva ecija"):
            p_muni = str(p.get("municipality_name", "")).lower()
            if target_muni not in p_muni and p_muni not in target_muni:
                continue

        # Featured match
        if is_featured is not None:
            if bool(p.get("is_featured")) != is_featured:
                continue

        # Minimum rating
        if min_rating is not None and min_rating > 0:
            rating = float(p.get("rating") or 0.0)
            if rating < min_rating:
                continue

        # Bounding box filter (min_lat, max_lat, min_lng, max_lng)
        if bounds:
            min_lat, max_lat, min_lng, max_lng = bounds
            lat = float(p.get("latitude") or 0.0)
            lng = float(p.get("longitude") or 0.0)
            if not (min_lat <= lat <= max_lat and min_lng <= lng <= max_lng):
                continue

        # Price tier filter
        if price_tier:
            pt = price_tier.lower().strip()
            min_cost = p.get("estimated_cost_min")
            max_cost = p.get("estimated_cost_max")
            c_val = min_cost if min_cost is not None else max_cost

            if pt == "free":
                if c_val is not None and c_val > 0:
                    continue
            elif pt == "budget":
                if c_val is not None and c_val > 500.0:
                    continue
            elif pt == "mid":
                if c_val is not None and (c_val <= 500.0 or c_val > 1500.0):
                    continue
            elif pt == "luxury":
                if c_val is not None and c_val <= 1500.0:
                    continue

        filtered.append(p)

    # Sort
    if sort == "rating":
        filtered.sort(key=lambda x: float(x.get("rating") or 0.0), reverse=True)
    elif sort == "name":
        filtered.sort(key=lambda x: str(x.get("name", "")).lower())
    elif sort == "cost_asc":
        filtered.sort(key=lambda x: float(x.get("estimated_cost_min") or 0.0))
    elif sort == "cost_desc":
        filtered.sort(key=lambda x: float(x.get("estimated_cost_max") or 0.0), reverse=True)

    total_count = len(filtered)
    paginated = filtered[offset : offset + limit]
    return paginated, total_count
