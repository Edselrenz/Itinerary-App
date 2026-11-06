"""Google Maps Platform Service with Resilient Fallbacks, Caching, and Polyline Utilities.

Provides:
1. Google Places API (New) Text & Nearby Search with Basic Tier FieldMask.
2. Google Places Details with Rich Atmosphere Tier FieldMask.
3. Google Routes API (Directions v2) with turn-by-turn navigation steps.
4. Resilient Fallbacks: OSRM Public Routing & Offline Haversine Calculation.
5. In-database Geospatial Caching (GeospatialCache) adhering to Google Terms of Service.
6. Local Nueva Ecija Place upserting and resolution.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import GeospatialCache, Municipality, Place

logger = logging.getLogger("app.services.google_maps_service")

# Google API URLs
PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
PLACES_NEARBY_SEARCH_URL = "https://places.googleapis.com/v1/places:searchNearby"
PLACES_DETAILS_BASE_URL = "https://places.googleapis.com/v1/places"
ROUTES_COMPUTE_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
OSRM_DRIVING_BASE_URL = "https://router.project-osrm.org/route/v1/driving"

# FieldMask Definitions
# Search/Discovery tier: only basic fields to protect billing
DISCOVERY_FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,places.location,"
    "places.types,places.rating,places.userRatingCount,places.priceLevel,places.primaryType"
)

# Rich Details tier: requested only on explicit place details lookup
DETAILS_FIELD_MASK = (
    "id,displayName,formattedAddress,location,types,rating,userRatingCount,priceLevel,"
    "primaryType,editorialSummary,regularOpeningHours,photos,reviews,websiteUri,"
    "internationalPhoneNumber,businessStatus,googleMapsUri"
)

ROUTES_FIELD_MASK = "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs"

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


# ============================================================================
# Polyline & Distance Utilities
# ============================================================================


def encode_polyline(coords: list[tuple[float, float]]) -> str:
    """Encodes a list of (lat, lng) tuples into Google Encoded Polyline format (precision 5)."""
    result: list[str] = []
    prev_lat = 0
    prev_lng = 0

    for lat, lng in coords:
        lat_int = round(lat * 1e5)
        lng_int = round(lng * 1e5)

        d_lat = lat_int - prev_lat
        d_lng = lng_int - prev_lng

        prev_lat = lat_int
        prev_lng = lng_int

        for d in (d_lat, d_lng):
            val = ~(d << 1) if d < 0 else (d << 1)
            while val >= 0x20:
                result.append(chr((0x20 | (val & 0x1F)) + 63))
                val >>= 5
            result.append(chr(val + 63))

    return "".join(result)


def decode_polyline(encoded: str) -> list[tuple[float, float]]:
    """Decodes Google Encoded Polyline string into a list of (lat, lng) tuples."""
    coords: list[tuple[float, float]] = []
    index = 0
    length = len(encoded)
    lat = 0
    lng = 0

    while index < length:
        # Latitude
        shift = 0
        result = 0
        while True:
            if index >= length:
                break
            byte = ord(encoded[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat

        # Longitude
        shift = 0
        result = 0
        while True:
            if index >= length:
                break
            byte = ord(encoded[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng

        coords.append((lat / 1e5, lng / 1e5))

    return coords


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the Great Circle distance between two points in meters using Haversine formula."""
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def parse_duration_seconds(duration_str: str | int | float | None) -> int:
    """Parses Google / OSRM duration strings (e.g. '1234s' or float seconds) to integer seconds."""
    if duration_str is None:
        return 0
    if isinstance(duration_str, (int, float)):
        return int(duration_str)
    cleaned = str(duration_str).strip()
    if cleaned.endswith("s"):
        cleaned = cleaned[:-1]
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return 0


def map_google_type_to_category(types: list[str] | None, primary_type: str | None = None) -> str:
    """Maps Google Places types to the application's canonical categories."""
    type_set = set(types or [])
    if primary_type:
        type_set.add(primary_type)

    if type_set & {"coffee_shop", "cafe", "tea_house"}:
        return "cafe"
    if type_set & {"restaurant", "fast_food_restaurant", "meal_takeaway", "food", "bakery", "bar"}:
        return "restaurant"
    if type_set & {
        "lodging",
        "hotel",
        "motel",
        "resort_hotel",
        "bed_and_breakfast",
        "guest_house",
    }:
        return "hotel_accommodation"
    if type_set & {"swimming_pool", "water_park"}:
        return "resort_swimming"
    if type_set & {"national_park", "park", "natural_feature", "campground", "hiking_area"}:
        return "nature_park"
    if type_set & {"church", "place_of_worship", "hindu_temple", "mosque", "synagogue"}:
        return "church_religious"
    if type_set & {"museum", "art_gallery", "historical_landmark", "cultural_center"}:
        return "museum_cultural"
    if type_set & {"shopping_mall", "supermarket", "market", "grocery_store", "store"}:
        return "shopping_market"
    if type_set & {"gas_station"}:
        return "fuel_station"
    if type_set & {"bus_station", "transit_station", "train_station"}:
        return "transport_terminal"
    if type_set & {"hospital", "doctor", "health"}:
        return "hospital_clinic"
    if type_set & {"pharmacy", "drugstore"}:
        return "pharmacy"
    if type_set & {"bank", "atm"}:
        return "bank_atm"
    if type_set & {"convenience_store"}:
        return "convenience_store"
    if type_set & {"city_hall", "local_government_office", "courthouse", "police"}:
        return "public_facility"

    return "tourist_attraction"


# ============================================================================
# Cache Helpers
# ============================================================================


def get_cached_payload(db: Session, cache_key: str) -> dict | None:
    """Retrieves an unexpired cached geospatial JSON payload."""
    try:
        now = datetime.now(timezone.utc)
        stmt = select(GeospatialCache).where(
            GeospatialCache.cache_key == cache_key,
            GeospatialCache.expires_at > now,
        )
        entry = db.scalar(stmt)
        if entry and isinstance(entry.payload, dict):
            return entry.payload
    except Exception as e:
        logger.warning("Failed to read geospatial cache for key %s: %s", cache_key, e)
    return None


def set_cached_payload(
    db: Session,
    cache_key: str,
    cache_type: str,
    payload: dict,
    ttl_hours: int,
) -> None:
    """Saves or updates a cached geospatial JSON payload with an expiration timestamp."""
    try:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=ttl_hours)
        entry = db.get(GeospatialCache, cache_key)
        if entry:
            entry.cache_type = cache_type
            entry.payload = payload
            entry.expires_at = expires_at
        else:
            entry = GeospatialCache(
                cache_key=cache_key,
                cache_type=cache_type,
                payload=payload,
                created_at=now,
                expires_at=expires_at,
            )
            db.add(entry)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning("Failed to write geospatial cache for key %s: %s", cache_key, e)


# ============================================================================
# Normalization Helper
# ============================================================================


def normalize_google_place(place_data: dict) -> dict:
    """Normalizes raw Google Places v1 payload into the unified PlaceOut dictionary schema."""
    place_id = place_data.get("id") or place_data.get("placeId") or ""
    display_name = place_data.get("displayName", {})
    name = (
        display_name.get("text")
        if isinstance(display_name, dict)
        else str(display_name or "")
    )
    if not name and "name" in place_data and not str(place_data["name"]).startswith("places/"):
        name = place_data["name"]

    location = place_data.get("location", {})
    lat = float(location.get("latitude", 0.0))
    lng = float(location.get("longitude", 0.0))
    address = place_data.get("formattedAddress", "")
    types = place_data.get("types", [])
    primary_type = place_data.get("primaryType")
    category = map_google_type_to_category(types, primary_type)

    editorial = place_data.get("editorialSummary", {})
    editorial_summary = (
        editorial.get("text")
        if isinstance(editorial, dict)
        else (str(editorial) if editorial else None)
    )

    rating = (
        float(place_data["rating"])
        if "rating" in place_data and place_data["rating"] is not None
        else None
    )
    user_rating_count = (
        int(place_data["userRatingCount"])
        if "userRatingCount" in place_data and place_data["userRatingCount"] is not None
        else None
    )

    price_level_val = place_data.get("priceLevel")
    price_level: int | None = None
    if isinstance(price_level_val, int):
        price_level = price_level_val
    elif isinstance(price_level_val, str):
        price_map = {
            "PRICE_LEVEL_FREE": 0,
            "PRICE_LEVEL_INEXPENSIVE": 1,
            "PRICE_LEVEL_MODERATE": 2,
            "PRICE_LEVEL_EXPENSIVE": 3,
            "PRICE_LEVEL_VERY_EXPENSIVE": 4,
        }
        price_level = price_map.get(price_level_val)

    # Photos
    photos: list[dict] = []
    for p in place_data.get("photos", []):
        p_name = p.get("name")
        photos.append(
            {
                "name": p_name,
                "width_px": p.get("widthPx"),
                "height_px": p.get("heightPx"),
                "author_attributions": p.get("authorAttributions", []),
                "photo_uri": f"/api/v1/places/photos/{p_name}" if p_name else None,
            }
        )

    # Reviews
    reviews: list[dict] = []
    for r in place_data.get("reviews", []):
        r_text = r.get("text")
        reviews.append(
            {
                "name": r.get("name"),
                "author_name": r.get("authorAttribution", {}).get("displayName"),
                "author_photo_uri": r.get("authorAttribution", {}).get("photoUri"),
                "rating": r.get("rating"),
                "text": (
                    r_text.get("text") if isinstance(r_text, dict) else (str(r_text) if r_text else None)
                ),
                "publish_time": r.get("publishTime"),
                "relative_publish_time_description": r.get("relativePublishTimeDescription"),
            }
        )

    regular_hours = place_data.get("regularOpeningHours")
    maps_uri = (
        place_data.get("googleMapsUri")
        or f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
    )

    stable_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"google:{place_id}"))

    return {
        "id": stable_uuid,
        "name": name or "Unnamed Location",
        "category": category,
        "latitude": lat,
        "longitude": lng,
        "municipality_id": None,
        "municipality_name": None,
        "address_text": address,
        "description": editorial_summary or (f"{name} in Nueva Ecija." if name else None),
        "phone": place_data.get("internationalPhoneNumber") or place_data.get("nationalPhoneNumber"),
        "website": place_data.get("websiteUri"),
        "opening_hours": None,
        "estimated_cost_min": None,
        "estimated_cost_max": None,
        "cost_currency": "PHP",
        "image_url": photos[0]["photo_uri"] if photos else None,
        "image_license": "Google Maps Platform",
        "source_name": "google_places",
        "source_record_id": place_id,
        "source_url": maps_uri,
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "is_featured": False,
        "tags": types,
        "directions_url": maps_uri,
        "google_place_id": place_id,
        "google_types": types,
        "editorial_summary": editorial_summary,
        "regular_opening_hours": regular_hours,
        "rating": rating,
        "user_rating_count": user_rating_count,
        "price_level": price_level,
        "photos": photos,
        "reviews": reviews,
        "business_status": place_data.get("businessStatus"),
        "google_maps_uri": maps_uri,
        "details_cached_at": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# GoogleMapsService Class
# ============================================================================


class GoogleMapsService:
    """High-level service wrapping Google Places (New) and Google Routes v2."""

    def __init__(self, http_client: httpx.Client | None = None) -> None:
        self.client = http_client or httpx.Client(timeout=10.0)

    # ------------------------------------------------------------------------
    # Places Search (Text & Nearby)
    # ------------------------------------------------------------------------

    def search_places_text(
        self,
        db: Session,
        query: str,
        location_bias: dict | None = None,
        included_types: list[str] | None = None,
        min_rating: float | None = None,
        open_now: bool | None = None,
    ) -> tuple[list[dict], str]:
        """Searches places using Google Places (New) searchText, cached data, or local DB fallback."""
        norm_query = query.strip()
        if not norm_query:
            return [], "local_db"

        # Check Cache
        bias_str = (
            f"{location_bias.get('latitude')},{location_bias.get('longitude')}"
            if location_bias
            else "none"
        )
        types_str = ",".join(sorted(included_types or []))
        cache_key = f"places:text:{hashlib.sha256(f'{norm_query}:{bias_str}:{types_str}:{min_rating}'.encode()).hexdigest()}"

        cached = get_cached_payload(db, cache_key)
        if cached and "places" in cached:
            return cached["places"], "cache"

        # Check if Google Maps API key is configured
        api_key = settings.google_maps_api_key
        if not api_key:
            return self._search_places_local(db, norm_query, location_bias, min_rating), "local_db"

        # Call Google Places v1 Text Search
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": DISCOVERY_FIELD_MASK,
        }
        body: dict[str, Any] = {"textQuery": norm_query}

        if location_bias and "latitude" in location_bias and "longitude" in location_bias:
            body["locationBias"] = {
                "circle": {
                    "center": {
                        "latitude": float(location_bias["latitude"]),
                        "longitude": float(location_bias["longitude"]),
                    },
                    "radius": float(location_bias.get("radius_meters", 50000.0)),
                }
            }
        else:
            # Default bias to Nueva Ecija center
            body["locationBias"] = {
                "circle": {
                    "center": {"latitude": 15.4859, "longitude": 120.9669},
                    "radius": 55000.0,
                }
            }

        if included_types and len(included_types) > 0:
            body["includedType"] = included_types[0]
        if min_rating is not None:
            body["minRating"] = float(min_rating)
        if open_now:
            body["openNow"] = True

        try:
            resp = self.client.post(PLACES_TEXT_SEARCH_URL, headers=headers, json=body)
            if resp.status_code == 200:
                data = resp.json()
                raw_places = data.get("places", [])
                normalized = [normalize_google_place(p) for p in raw_places]

                set_cached_payload(
                    db,
                    cache_key,
                    "places_search",
                    {"places": normalized},
                    settings.google_places_cache_ttl_hours,
                )
                return normalized, "google_live"
            else:
                logger.warning(
                    "Google Places searchText returned HTTP %d: %s. Falling back to local search.",
                    resp.status_code,
                    resp.text,
                )
        except Exception as e:
            logger.warning(
                "Error calling Google Places searchText: %s. Falling back to local search.", e
            )

        return self._search_places_local(db, norm_query, location_bias, min_rating), "local_db"

    def search_places_nearby(
        self,
        db: Session,
        lat: float,
        lng: float,
        radius_meters: float = 10000.0,
        included_types: list[str] | None = None,
        max_results: int = 20,
    ) -> tuple[list[dict], str]:
        """Searches places near coordinates using Google Places (New) searchNearby or fallback."""
        cache_key = f"places:nearby:{lat:.4f}_{lng:.4f}_{radius_meters:.0f}_{','.join(sorted(included_types or []))}"
        cached = get_cached_payload(db, cache_key)
        if cached and "places" in cached:
            return cached["places"], "cache"

        api_key = settings.google_maps_api_key
        if not api_key:
            return self._search_places_local_nearby(db, lat, lng, radius_meters), "local_db"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": DISCOVERY_FIELD_MASK,
        }
        body: dict[str, Any] = {
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": radius_meters,
                }
            },
            "maxResultCount": max(1, min(max_results, 20)),
        }
        if included_types:
            body["includedTypes"] = included_types

        try:
            resp = self.client.post(PLACES_NEARBY_SEARCH_URL, headers=headers, json=body)
            if resp.status_code == 200:
                data = resp.json()
                raw_places = data.get("places", [])
                normalized = [normalize_google_place(p) for p in raw_places]

                set_cached_payload(
                    db,
                    cache_key,
                    "places_nearby",
                    {"places": normalized},
                    settings.google_places_cache_ttl_hours,
                )
                return normalized, "google_live"
            else:
                logger.warning(
                    "Google Places searchNearby returned HTTP %d: %s. Falling back to local search.",
                    resp.status_code,
                    resp.text,
                )
        except Exception as e:
            logger.warning(
                "Error calling Google Places searchNearby: %s. Falling back to local search.", e
            )

        return self._search_places_local_nearby(db, lat, lng, radius_meters), "local_db"

    # ------------------------------------------------------------------------
    # Place Details
    # ------------------------------------------------------------------------

    def fetch_place_details(self, db: Session, google_place_id: str) -> dict | None:
        """Fetches rich Atmosphere/Advanced details for a single place."""
        clean_id = google_place_id.strip()
        if not clean_id:
            return None

        cache_key = f"places:details:{clean_id}"
        cached = get_cached_payload(db, cache_key)
        if cached:
            return cached

        api_key = settings.google_maps_api_key
        if not api_key:
            # Check if place is already saved in local DB
            stmt = select(Place).where(
                or_(
                    Place.google_place_id == clean_id,
                    Place.source_record_id == clean_id,
                )
            )
            place_orm = db.scalar(stmt)
            if place_orm:
                return self._serialize_orm_place_dict(place_orm)
            return None

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": DETAILS_FIELD_MASK,
        }
        url = f"{PLACES_DETAILS_BASE_URL}/{clean_id}"

        try:
            resp = self.client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                normalized = normalize_google_place(data)
                set_cached_payload(
                    db,
                    cache_key,
                    "place_details",
                    normalized,
                    settings.google_details_cache_ttl_hours,
                )
                return normalized
            else:
                logger.warning(
                    "Google Places details returned HTTP %d: %s", resp.status_code, resp.text
                )
        except Exception as e:
            logger.warning("Error calling Google Places details for %s: %s", clean_id, e)

        return None

    # ------------------------------------------------------------------------
    # Turn-by-Turn Route Computation
    # ------------------------------------------------------------------------

    def compute_route(
        self,
        db: Session,
        origin: dict,
        destination: dict,
        intermediates: list[dict] | None = None,
        travel_mode: str = "DRIVE",
    ) -> dict:
        """Computes navigation routes with overview polyline and turn legs, falling back gracefully."""
        intermediates = intermediates or []
        mode = travel_mode.upper() if travel_mode else "DRIVE"

        # Unique cache key
        inter_str = "_".join(f"{p['latitude']:.4f},{p['longitude']:.4f}" for p in intermediates)
        cache_key = (
            f"routes:{mode}:{origin['latitude']:.4f},{origin['longitude']:.4f}:"
            f"{destination['latitude']:.4f},{destination['longitude']:.4f}:{inter_str}"
        )

        cached = get_cached_payload(db, cache_key)
        if cached and "overview_polyline" in cached:
            cached_copy = dict(cached)
            cached_copy["source"] = "cache"
            return cached_copy

        api_key = settings.google_maps_api_key
        if api_key:
            # Attempt Google Routes v2
            google_route = self._compute_google_route(
                api_key, origin, destination, intermediates, mode
            )
            if google_route:
                set_cached_payload(
                    db,
                    cache_key,
                    "route",
                    google_route,
                    settings.google_routes_cache_ttl_hours,
                )
                return google_route

        # Fallback 1: OSRM Public Routing
        osrm_route = self._compute_osrm_route(origin, destination, intermediates, mode)
        if osrm_route:
            set_cached_payload(
                db,
                cache_key,
                "route",
                osrm_route,
                settings.google_routes_cache_ttl_hours,
            )
            return osrm_route

        # Fallback 2: Offline Haversine Calculation
        haversine_route = self._compute_haversine_route(origin, destination, intermediates, mode)
        return haversine_route

    # ------------------------------------------------------------------------
    # Place Upsert Helper
    # ------------------------------------------------------------------------

    def upsert_google_place_to_db(self, db: Session, place_data: dict) -> Place:
        """Persists or links a Google Place into the local PostgreSQL/SQLite places database."""
        google_place_id = (
            place_data.get("google_place_id")
            or place_data.get("source_record_id")
            or place_data.get("id")
        )

        # 1. Match by google_place_id
        if google_place_id:
            stmt = select(Place).where(Place.google_place_id == str(google_place_id))
            existing = db.scalar(stmt)
            if existing:
                return existing

            # 2. Match by source_record_id & source_name
            stmt_src = select(Place).where(
                Place.source_name == "google_places",
                Place.source_record_id == str(google_place_id),
            )
            existing_src = db.scalar(stmt_src)
            if existing_src:
                return existing_src

        # 3. Match by name & approximate coordinates
        lat = float(place_data.get("latitude", 0.0))
        lng = float(place_data.get("longitude", 0.0))
        name = place_data.get("name") or "Unnamed Place"

        stmt_near = select(Place).where(
            Place.name == name,
            Place.latitude.between(lat - 0.001, lat + 0.001),
            Place.longitude.between(lng - 0.001, lng + 0.001),
        )
        existing_near = db.scalar(stmt_near)
        if existing_near:
            return existing_near

        # 4. Resolve closest Municipality
        municipality_id = None
        all_municipalities = list(db.scalars(select(Municipality)).all())
        if all_municipalities and lat != 0.0 and lng != 0.0:
            closest_muni = min(
                all_municipalities,
                key=lambda m: haversine_distance_meters(lat, lng, m.center_lat, m.center_lng),
            )
            municipality_id = closest_muni.id

        category = place_data.get("category")
        if not category or category not in CANONICAL_CATEGORIES:
            category = map_google_type_to_category(
                place_data.get("google_types") or place_data.get("tags")
            )

        new_place = Place(
            id=uuid.uuid4(),
            name=name,
            category=category,
            latitude=lat,
            longitude=lng,
            municipality_id=municipality_id,
            address_text=place_data.get("address_text"),
            description=place_data.get("description") or place_data.get("editorial_summary"),
            phone=place_data.get("phone"),
            website=place_data.get("website"),
            opening_hours=place_data.get("opening_hours"),
            cost_currency=place_data.get("cost_currency", "PHP"),
            image_url=place_data.get("image_url"),
            image_license=place_data.get("image_license", "Google Maps Platform"),
            source_name="google_places",
            source_record_id=str(google_place_id or uuid.uuid4()),
            source_url=place_data.get("google_maps_uri") or place_data.get("directions_url"),
            is_featured=False,
            is_active=True,
            tags=place_data.get("tags") or place_data.get("google_types") or [],
            google_place_id=str(google_place_id) if google_place_id else None,
            google_types=place_data.get("google_types") or [],
            editorial_summary=place_data.get("editorial_summary"),
            regular_opening_hours=place_data.get("regular_opening_hours"),
            rating=place_data.get("rating"),
            user_rating_count=place_data.get("user_rating_count"),
            price_level=place_data.get("price_level"),
            photos=place_data.get("photos") or [],
            reviews=place_data.get("reviews") or [],
            business_status=place_data.get("business_status"),
            google_maps_uri=place_data.get("google_maps_uri") or place_data.get("directions_url"),
            details_cached_at=datetime.now(timezone.utc),
        )
        db.add(new_place)
        db.flush()
        return new_place

    # ------------------------------------------------------------------------
    # Private Fallback & Routing Implementations
    # ------------------------------------------------------------------------

    def _compute_google_route(
        self,
        api_key: str,
        origin: dict,
        destination: dict,
        intermediates: list[dict],
        travel_mode: str,
    ) -> dict | None:
        """Invokes Google Routes API Directions v2."""
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": ROUTES_FIELD_MASK,
        }
        body: dict[str, Any] = {
            "origin": {
                "location": {
                    "latLng": {
                        "latitude": float(origin["latitude"]),
                        "longitude": float(origin["longitude"]),
                    }
                }
            },
            "destination": {
                "location": {
                    "latLng": {
                        "latitude": float(destination["latitude"]),
                        "longitude": float(destination["longitude"]),
                    }
                }
            },
            "intermediates": [
                {
                    "location": {
                        "latLng": {
                            "latitude": float(p["latitude"]),
                            "longitude": float(p["longitude"]),
                        }
                    }
                }
                for p in intermediates
            ],
            "travelMode": travel_mode if travel_mode in {"DRIVE", "WALK", "BICYCLE", "TRANSIT"} else "DRIVE",
        }
        if travel_mode == "DRIVE":
            body["routingPreference"] = "TRAFFIC_AWARE"

        try:
            resp = self.client.post(ROUTES_COMPUTE_URL, headers=headers, json=body)
            if resp.status_code == 200:
                data = resp.json()
                routes = data.get("routes", [])
                if routes:
                    r = routes[0]
                    overview_polyline = r.get("polyline", {}).get("encodedPolyline", "")
                    total_dist = r.get("distanceMeters", 0)
                    total_dur = parse_duration_seconds(r.get("duration", "0s"))

                    legs = []
                    for leg in r.get("legs", []):
                        start_loc = leg.get("startLocation", {}).get("latLng", {})
                        end_loc = leg.get("endLocation", {}).get("latLng", {})
                        steps = []
                        for step in leg.get("steps", []):
                            nav = step.get("navigationInstruction", {})
                            s_start = step.get("startLocation", {}).get("latLng")
                            s_end = step.get("endLocation", {}).get("latLng")
                            steps.append(
                                {
                                    "instruction": nav.get("instructions", "Continue straight"),
                                    "distance_meters": step.get("distanceMeters", 0),
                                    "duration_seconds": parse_duration_seconds(step.get("duration")),
                                    "polyline": step.get("polyline", {}).get("encodedPolyline"),
                                    "start_location": s_start,
                                    "end_location": s_end,
                                    "maneuver": nav.get("maneuver"),
                                }
                            )

                        legs.append(
                            {
                                "start_location": start_loc,
                                "end_location": end_loc,
                                "distance_meters": leg.get("distanceMeters", 0),
                                "duration_seconds": parse_duration_seconds(leg.get("duration")),
                                "polyline": leg.get("polyline", {}).get("encodedPolyline"),
                                "steps": steps,
                            }
                        )

                    return {
                        "overview_polyline": overview_polyline,
                        "total_distance_meters": total_dist,
                        "total_duration_seconds": total_dur,
                        "legs": legs,
                        "source": "google_routes",
                    }
            else:
                logger.warning("Google Routes API failed with HTTP %d: %s", resp.status_code, resp.text)
        except Exception as e:
            logger.warning("Google Routes API call failed: %s", e)

        return None

    def _compute_osrm_route(
        self,
        origin: dict,
        destination: dict,
        intermediates: list[dict],
        travel_mode: str,
    ) -> dict | None:
        """Invokes public OpenStreetMap OSRM routing service."""
        points = [origin] + intermediates + [destination]
        coords_str = ";".join(f"{p['longitude']:.5f},{p['latitude']:.5f}" for p in points)
        url = f"{OSRM_DRIVING_BASE_URL}/{coords_str}?overview=full&geometries=polyline&steps=true"

        try:
            resp = self.client.get(url, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "Ok" and data.get("routes"):
                    r = data["routes"][0]
                    overview_polyline = r.get("geometry", "")
                    total_dist = int(round(r.get("distance", 0.0)))
                    total_dur = int(round(r.get("duration", 0.0)))

                    legs = []
                    for leg in r.get("legs", []):
                        steps = []
                        for s in leg.get("steps", []):
                            man = s.get("maneuver", {})
                            instr = s.get("name") or man.get("type", "Proceed")
                            steps.append(
                                {
                                    "instruction": instr,
                                    "distance_meters": int(round(s.get("distance", 0.0))),
                                    "duration_seconds": int(round(s.get("duration", 0.0))),
                                    "polyline": s.get("geometry"),
                                    "start_location": (
                                        {"latitude": man["location"][1], "longitude": man["location"][0]}
                                        if "location" in man
                                        else None
                                    ),
                                    "end_location": None,
                                    "maneuver": man.get("modifier") or man.get("type"),
                                }
                            )

                        legs.append(
                            {
                                "start_location": {
                                    "latitude": leg["steps"][0]["maneuver"]["location"][1],
                                    "longitude": leg["steps"][0]["maneuver"]["location"][0],
                                } if leg.get("steps") else origin,
                                "end_location": {
                                    "latitude": leg["steps"][-1]["maneuver"]["location"][1],
                                    "longitude": leg["steps"][-1]["maneuver"]["location"][0],
                                } if leg.get("steps") else destination,
                                "distance_meters": int(round(leg.get("distance", 0.0))),
                                "duration_seconds": int(round(leg.get("duration", 0.0))),
                                "polyline": None,
                                "steps": steps,
                            }
                        )

                    return {
                        "overview_polyline": overview_polyline,
                        "total_distance_meters": total_dist,
                        "total_duration_seconds": total_dur,
                        "legs": legs,
                        "source": "osrm",
                    }
        except Exception as e:
            logger.info("OSRM public routing unavailable: %s. Using Haversine direct.", e)

        return None

    def _compute_haversine_route(
        self,
        origin: dict,
        destination: dict,
        intermediates: list[dict],
        travel_mode: str,
    ) -> dict:
        """Calculates direct point-to-point legs using Haversine formula and encoded polyline."""
        points = [origin] + intermediates + [destination]
        coords = [(float(p["latitude"]), float(p["longitude"])) for p in points]
        overview_polyline = encode_polyline(coords)

        # Assumed average speed in m/s (40 km/h for drive, 4.5 km/h for walk)
        speed_mps = 11.11 if travel_mode != "WALK" else 1.25

        total_distance = 0
        total_duration = 0
        legs = []

        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            dist = int(
                round(
                    haversine_distance_meters(
                        float(p1["latitude"]),
                        float(p1["longitude"]),
                        float(p2["latitude"]),
                        float(p2["longitude"]),
                    )
                )
            )
            dur = int(round(dist / speed_mps))
            leg_polyline = encode_polyline(
                [
                    (float(p1["latitude"]), float(p1["longitude"])),
                    (float(p2["latitude"]), float(p2["longitude"])),
                ]
            )

            total_distance += dist
            total_duration += dur

            legs.append(
                {
                    "start_location": {"latitude": p1["latitude"], "longitude": p1["longitude"]},
                    "end_location": {"latitude": p2["latitude"], "longitude": p2["longitude"]},
                    "distance_meters": dist,
                    "duration_seconds": dur,
                    "polyline": leg_polyline,
                    "steps": [
                        {
                            "instruction": f"Head toward destination ({dist}m)",
                            "distance_meters": dist,
                            "duration_seconds": dur,
                            "polyline": leg_polyline,
                            "start_location": {"latitude": p1["latitude"], "longitude": p1["longitude"]},
                            "end_location": {"latitude": p2["latitude"], "longitude": p2["longitude"]},
                            "maneuver": "straight",
                        }
                    ],
                }
            )

        return {
            "overview_polyline": overview_polyline,
            "total_distance_meters": total_distance,
            "total_duration_seconds": total_duration,
            "legs": legs,
            "source": "haversine_direct",
        }

    def _search_places_local(
        self,
        db: Session,
        query: str,
        location_bias: dict | None = None,
        min_rating: float | None = None,
    ) -> list[dict]:
        """Local database fallback search."""
        safe_q = query.replace("%", "").replace("_", "")
        stmt = (
            select(Place)
            .where(
                Place.is_active == True,
                or_(
                    Place.name.ilike(f"%{safe_q}%"),
                    Place.description.ilike(f"%{safe_q}%"),
                    Place.category.ilike(f"%{safe_q}%"),
                ),
            )
            .limit(20)
        )
        places = list(db.scalars(stmt).all())
        results = [self._serialize_orm_place_dict(p) for p in places]

        if location_bias and "latitude" in location_bias and "longitude" in location_bias:
            bias_lat = float(location_bias["latitude"])
            bias_lng = float(location_bias["longitude"])
            results.sort(
                key=lambda p: haversine_distance_meters(
                    bias_lat, bias_lng, p["latitude"], p["longitude"]
                )
            )

        return results

    def _search_places_local_nearby(
        self,
        db: Session,
        lat: float,
        lng: float,
        radius_meters: float,
    ) -> list[dict]:
        """Local database fallback nearby search."""
        stmt = select(Place).where(Place.is_active == True).limit(50)
        places = list(db.scalars(stmt).all())
        within_radius = []
        for p in places:
            dist = haversine_distance_meters(lat, lng, p.latitude, p.longitude)
            if dist <= radius_meters:
                serialized = self._serialize_orm_place_dict(p)
                within_radius.append((dist, serialized))

        within_radius.sort(key=lambda x: x[0])
        return [item[1] for item in within_radius[:20]]

    def _serialize_orm_place_dict(self, place: Place) -> dict:
        """Serializes an ORM Place to the PlaceOut dictionary representation."""
        return {
            "id": str(place.id),
            "name": place.name,
            "category": place.category,
            "latitude": place.latitude,
            "longitude": place.longitude,
            "municipality_id": str(place.municipality_id) if place.municipality_id else None,
            "municipality_name": place.municipality.name if place.municipality else None,
            "address_text": place.address_text,
            "description": place.description,
            "phone": place.phone,
            "website": place.website,
            "opening_hours": place.opening_hours,
            "estimated_cost_min": float(place.estimated_cost_min) if place.estimated_cost_min is not None else None,
            "estimated_cost_max": float(place.estimated_cost_max) if place.estimated_cost_max is not None else None,
            "cost_currency": place.cost_currency,
            "image_url": place.image_url,
            "image_license": place.image_license,
            "source_name": place.source_name,
            "source_record_id": place.source_record_id,
            "source_url": place.source_url,
            "imported_at": place.imported_at.isoformat() if place.imported_at else None,
            "verified_at": place.verified_at.isoformat() if place.verified_at else None,
            "is_featured": place.is_featured,
            "tags": place.tags or [],
            "directions_url": (
                place.google_maps_uri
                or f"https://www.google.com/maps/dir/?api=1&destination={place.latitude},{place.longitude}"
            ),
            "google_place_id": place.google_place_id,
            "google_types": place.google_types or [],
            "editorial_summary": place.editorial_summary,
            "regular_opening_hours": place.regular_opening_hours,
            "rating": place.rating,
            "user_rating_count": place.user_rating_count,
            "price_level": place.price_level,
            "photos": place.photos or [],
            "reviews": place.reviews or [],
            "business_status": place.business_status,
            "google_maps_uri": place.google_maps_uri,
            "details_cached_at": place.details_cached_at.isoformat() if place.details_cached_at else None,
        }


# Global singleton instance
google_maps_service = GoogleMapsService()

