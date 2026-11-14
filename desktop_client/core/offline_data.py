"""Canonical offline datasets and 32-LGU metadata for Nueva Ecija MVP.

Provides offline fallback across Home tab, PlaceService, and ItineraryService.
"""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Optional

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
            "photos": [self.image] if self.image else [],
            "rating": self.rating,
            "user_rating_count": self.user_rating_count,
            "is_featured": self.is_featured,
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
        opening_hours="10:00 AM - 09:00 PM",
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
        opening_hours="08:00 AM - 05:00 PM",
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
        opening_hours="11:00 AM - 10:00 PM",
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
        id="dest-minalungao",
        name="Minalungao National Park",
        category="nature_park",
        category_name="Nature & Parks",
        municipality="General Tinio",
        address_text="General Tinio, Nueva Ecija",
        latitude=15.3025,
        longitude=121.1411,
        description="Pristine limestone canyon along the Peñaranda River featuring emerald waters, balsa raft cruising, cave exploration, and zip-lining.",
        opening_hours="07:00 AM - 05:00 PM",
        estimated_cost_min=100.0,
        estimated_cost_max=250.0,
        image="popular_destinations/minalungao.png",
        tags=["Limestone", "River Rafting", "Ecotourism"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.3025,121.1411",
        default_time="09:00 AM - 01:00 PM",
        default_duration_minutes=240,
        rating=4.8,
        user_rating_count=890,
    ),
    CanonicalOfflinePlace(
        id="dest-pantabangan-lake",
        name="Pantabangan Lake",
        category="nature_park",
        category_name="Nature & Parks",
        municipality="Pantabangan",
        address_text="Pantabangan, Nueva Ecija",
        latitude=15.8167,
        longitude=121.1500,
        description="One of Southeast Asia's largest human-made reservoirs, celebrated for world-class largemouth bass sportfishing and panoramic mountain vistas.",
        opening_hours="06:00 AM - 06:00 PM",
        estimated_cost_min=50.0,
        estimated_cost_max=200.0,
        image="popular_destinations/pantabangan_lake.png",
        tags=["Lake", "Fishing", "Mountain View"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.8167,121.1500",
        default_time="08:00 AM - 12:00 PM",
        default_duration_minutes=240,
        rating=4.7,
        user_rating_count=420,
    ),
    CanonicalOfflinePlace(
        id="dest-highland-bali",
        name="Highland Bali Villas Resort and Spa",
        category="resort_swimming",
        category_name="Resorts & Stays",
        municipality="Pantabangan",
        address_text="Pantabangan, Nueva Ecija",
        latitude=15.8050,
        longitude=121.1380,
        description="Luxury Balinese-inspired mountain retreat overlooking Lake Pantabangan with infinity pools, spa pavilions, and water sports.",
        opening_hours="24 Hours Open",
        estimated_cost_min=3500.0,
        estimated_cost_max=7500.0,
        image="popular_destinations/highland_bali.png",
        tags=["Resort", "Spa", "Luxury", "Infinity Pool"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.8050,121.1380",
        default_time="02:00 PM - 12:00 PM",
        default_duration_minutes=360,
        rating=4.8,
        user_rating_count=650,
    ),
    CanonicalOfflinePlace(
        id="dest-george-point",
        name="George Point",
        category="tourist_attraction",
        category_name="Scenic Viewpoint",
        municipality="Pantabangan",
        address_text="Pantabangan, Nueva Ecija",
        latitude=15.8200,
        longitude=121.1450,
        description="Elevated viewing promontory offering uninterrupted 360-degree vistas across Pantabangan Dam, Sierra Madre peaks, and sunset horizons.",
        opening_hours="06:00 AM - 07:00 PM",
        estimated_cost_min=20.0,
        estimated_cost_max=50.0,
        image="popular_destinations/george_point.png",
        tags=["Viewpoint", "Sunset", "Photography"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.8200,121.1450",
        default_time="04:30 PM - 06:30 PM",
        default_duration_minutes=120,
        rating=4.6,
        user_rating_count=195,
    ),
    CanonicalOfflinePlace(
        id="dest-tagpuan-gapan",
        name="Tagpuan sa Lumang Gapan",
        category="tourist_attraction",
        category_name="Heritage & Promenade",
        municipality="Gapan City",
        address_text="Gapan City, Nueva Ecija",
        latitude=15.3080,
        longitude=120.9470,
        description="Atmospheric riverside heritage street lined with restored ancestral houses, ambient lampposts, local street food stalls, and cultural strolls.",
        opening_hours="04:00 PM - 11:00 PM",
        estimated_cost_min=None,
        estimated_cost_max=150.0,
        image="popular_destinations/tagpuan_gapan.png",
        tags=["Heritage", "Street Food", "Ancestral Houses"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.3080,120.9470",
        default_time="05:30 PM - 09:00 PM",
        default_duration_minutes=180,
        rating=4.7,
        user_rating_count=740,
    ),
    CanonicalOfflinePlace(
        id="dest-casa-batik",
        name="Casa Batik",
        category="hotel_accommodation",
        category_name="Boutique Stay",
        municipality="Pantabangan",
        address_text="Pantabangan, Nueva Ecija",
        latitude=15.8110,
        longitude=121.1420,
        description="Bohemian boutique lakeside sanctuary featuring handcrafted textiles, open-air sun decks, and bespoke farm-to-table dining.",
        opening_hours="24 Hours Open",
        estimated_cost_min=2800.0,
        estimated_cost_max=5500.0,
        image="popular_destinations/casa_batik.png",
        tags=["Boutique", "Lakeside", "Farm-to-Table"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.8110,121.1420",
        default_time="02:00 PM - 11:00 AM",
        default_duration_minutes=360,
        rating=4.7,
        user_rating_count=180,
    ),
    CanonicalOfflinePlace(
        id="dest-clsu-carabao",
        name="Philippine Carabao Center & Dairy Outlet",
        category="tourist_attraction",
        category_name="Agri-Tourism",
        municipality="Science City of Muñoz",
        address_text="CLSU Campus, Science City of Muñoz, Nueva Ecija",
        latitude=15.7360,
        longitude=120.9320,
        description="Premier national biotechnology institute showcasing water buffalo breeding, fresh carabaos milk, pastillas de leche, and artisanal dairy cheeses.",
        opening_hours="08:00 AM - 05:00 PM",
        estimated_cost_min=50.0,
        estimated_cost_max=200.0,
        image="popular_destinations/farm_villaronte.png",
        tags=["Agri-Tourism", "Dairy", "Milka Krem"],
        directions_url="https://www.google.com/maps/dir/?api=1&destination=15.7360,120.9320",
        default_time="09:00 AM - 11:30 AM",
        default_duration_minutes=150,
        rating=4.7,
        user_rating_count=520,
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


def load_osm_places() -> list[dict[str, Any]]:
    """Loads curated OpenStreetMap places from bundled or local assets."""
    settings = get_settings()
    asset_file = settings.assets_dir / "data" / "osm_places.json"
    if not asset_file.is_file():
        # Fallback to Project static asset
        proj_file = settings.base_dir.parent / "Project" / "src" / "assets" / "data" / "osm_places.json"
        if proj_file.is_file():
            asset_file = proj_file

    if asset_file.is_file():
        try:
            with open(asset_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                if isinstance(data, dict) and "places" in data:
                    return data["places"]
        except Exception:
            pass

    # Fallback to canonical offline places
    return [p.to_dict() for p in CANONICAL_OFFLINE_PLACES]
