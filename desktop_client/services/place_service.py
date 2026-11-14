"""Place Service managing POI queries, 2,673-POI cache merging, filtering, search, and municipality catalogs."""

import logging
from typing import Any, Optional
import uuid
import httpx

from desktop_client.config.settings import CANONICAL_CATEGORIES
from desktop_client.core.api_client import ApiClient, get_api_client
from desktop_client.core.offline_data import (
    ALL_32_LGUS_METADATA,
    get_all_offline_places,
    get_filtered_local_places,
)
from desktop_client.models.place import Municipality, PaginatedPlaces, Place

logger = logging.getLogger(__name__)


def _is_valid_uuid(val: Any) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except Exception:
        return False


class PlaceService:
    """Interacts with backend Places and Municipalities endpoints with 2,673-POI in-memory cache merging."""

    def __init__(self, api_client: Optional[ApiClient] = None):
        self.api_client = api_client or get_api_client()
        self._municipalities_cache: Optional[list[Municipality]] = None
        self._categories_cache: Optional[list[str]] = None
        self._osm_places_cache: list[Place] = []

    def get_loaded_places(self, municipality: Optional[str] = None) -> list[Place]:
        """Synchronously returns all 2,673+ places (merged online + offline OSM dataset)."""
        if not self._osm_places_cache:
            self._osm_places_cache = [Place.from_dict(p) for p in get_all_offline_places()]
        if not municipality or municipality.lower().strip() in ("all", "nueva ecija", "all 32 municipalities"):
            return list(self._osm_places_cache)
        m_low = municipality.lower().strip()
        return [
            p for p in self._osm_places_cache
            if m_low in (p.municipality_name or "").lower() or m_low == (p.municipality_id or "").lower()
        ]

    def merge_places_into_cache(self, new_places: list[Place]) -> None:
        """Merges online API places into the 2,673-POI cache by ID and name without duplicating places (QA-02)."""
        if not new_places:
            return
        if not self._osm_places_cache:
            self._osm_places_cache = [Place.from_dict(p) for p in get_all_offline_places()]
        by_id = {p.id: p for p in self._osm_places_cache}
        by_name = {p.name.lower().strip(): p.id for p in self._osm_places_cache}
        for np in new_places:
            norm_name = np.name.lower().strip()
            if np.id in by_id:
                by_id[np.id] = np
            elif norm_name in by_name:
                existing_id = by_name[norm_name]
                by_id[existing_id] = np
            else:
                by_id[np.id] = np
        self._osm_places_cache = list(by_id.values())

    async def get_municipalities(self, force_refresh: bool = False) -> list[Municipality]:
        """Fetches all 32 Nueva Ecija municipalities and cities with offline fallback."""
        if self._municipalities_cache is not None and not force_refresh:
            return self._municipalities_cache

        try:
            data = await self.api_client.get("municipalities")
            if isinstance(data, list) and data:
                by_name = {str(m.get("name", "")).lower(): Municipality.from_dict(m) for m in data}
                merged: list[Municipality] = []
                for name, meta in ALL_32_LGUS_METADATA.items():
                    found = by_name.get(name.lower())
                    if found:
                        if not found.place_count:
                            found.place_count = meta.get("poi_count", 0)
                        merged.append(found)
                    else:
                        merged.append(
                            Municipality(
                                id=name,
                                name=name,
                                place_count=meta.get("poi_count", 0),
                            )
                        )
                self._municipalities_cache = merged
                return self._municipalities_cache
        except Exception as err:
            logger.info(f"Could not load municipalities from backend, using offline dataset: {err}")

        fallback: list[Municipality] = []
        for name, meta in ALL_32_LGUS_METADATA.items():
            fallback.append(
                Municipality(
                    id=name,
                    name=name,
                    place_count=meta.get("poi_count", 0),
                )
            )
        self._municipalities_cache = fallback
        return self._municipalities_cache

    async def get_categories(self, force_refresh: bool = False) -> list[str]:
        """Returns the 16 canonical categories conforming to the Nueva Ecija schema."""
        if self._categories_cache is None or force_refresh:
            self._categories_cache = [c["key"] for c in CANONICAL_CATEGORIES]
        return self._categories_cache

    async def get_places(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None,
        categories: Optional[list[str]] = None,
        municipality_id: Optional[str] = None,
        municipality_name: Optional[str] = None,
        price_tier: Optional[str] = None,
        is_featured: Optional[bool] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lng: Optional[float] = None,
        max_lng: Optional[float] = None,
        sort: Optional[str] = None,
    ) -> PaginatedPlaces:
        """Queries places via GET /api/v1/places with full parameter parity and 2,673-POI offline fallback."""
        limit = max(1, page_size)
        offset = max(0, (page - 1) * limit)
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }
        if search and search.strip():
            params["q"] = search.strip()
        if categories:
            valid_cats = [c.strip() for c in categories if c and c.strip() and c != "all"]
            if valid_cats:
                params["categories"] = valid_cats
        elif category and category.strip() and category != "all":
            params["categories"] = [category.strip()]

        # Resolve municipality_id vs municipality_name safely (prevents FastAPI 422 on non-UUID town names)
        muni_name_resolved = municipality_name
        if municipality_id and municipality_id.strip() and municipality_id != "all":
            raw_m = municipality_id.strip()
            # If a town name was passed (e.g. "Bongabon", "Pantabangan"), route to municipality_name
            is_known_town_name = (
                raw_m in ALL_32_LGUS_METADATA
                or any(raw_m.lower() == k.lower() for k in ALL_32_LGUS_METADATA)
            )
            if is_known_town_name:
                muni_name_resolved = raw_m
            else:
                params["municipality_id"] = raw_m

        if muni_name_resolved and muni_name_resolved.strip() and muni_name_resolved.lower() != "all":
            params["municipality_name"] = muni_name_resolved.strip()

        if price_tier and price_tier.strip() and price_tier != "all":
            params["price_tier"] = price_tier.strip().lower()

        if is_featured is not None:
            params["featured"] = is_featured

        if None not in (min_lat, max_lat, min_lng, max_lng):
            params["min_lat"] = min_lat
            params["max_lat"] = max_lat
            params["min_lng"] = min_lng
            params["max_lng"] = max_lng

        if sort:
            params["sort"] = sort

        try:
            data = await self.api_client.get("places", params=params)
            paginated = PaginatedPlaces.from_dict(data)
            self.merge_places_into_cache(paginated.items)
            return paginated
        except Exception as err:
            logger.info(f"Using offline 2,673-POI catalog fallback: {err}")
            bounds = (min_lat, max_lat, min_lng, max_lng) if None not in (min_lat, max_lat, min_lng, max_lng) else None
            items, total = get_filtered_local_places(
                q=search,
                category=category,
                categories=categories,
                municipality_name=muni_name_resolved,
                municipality_id=municipality_id if (municipality_id and _is_valid_uuid(municipality_id)) else None,
                is_featured=is_featured,
                price_tier=price_tier,
                bounds=bounds,
                sort=sort,
                limit=limit,
                offset=offset,
            )
            place_objs = [Place.from_dict(it) for it in items]
            return PaginatedPlaces(
                items=place_objs,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=max(1, (total + limit - 1) // limit),
            )

    async def get_featured_places(self, limit: int = 12) -> list[Place]:
        """Retrieves top curated destinations for the dashboard."""
        try:
            paginated = await self.get_places(page=1, page_size=limit, is_featured=True)
            if paginated.items:
                return paginated.items
            fallback = await self.get_places(page=1, page_size=limit)
            return fallback.items
        except Exception:
            return self.get_loaded_places()[:limit]

    async def get_place_by_id(self, place_id: str) -> Optional[Place]:
        """Fetches full place details with offline lookup across all 2,673 places."""
        try:
            data = await self.api_client.get(f"places/{place_id}")
            if data:
                return Place.from_dict(data)
        except Exception:
            pass

        for p in self.get_loaded_places():
            if str(p.id) == str(place_id):
                return p
        return None

    @staticmethod
    def map_osm_tags_to_category(tags: dict[str, Any]) -> str:
        """Maps OpenStreetMap amenity/tourism/historic/leisure tags to canonical categories."""
        amenity = str(tags.get("amenity", "")).lower()
        tourism = str(tags.get("tourism", "")).lower()
        leisure = str(tags.get("leisure", "")).lower()
        shop = str(tags.get("shop", "")).lower()
        historic = str(tags.get("historic", "")).lower()

        if amenity == "cafe":
            return "cafe"
        if amenity in ("restaurant", "fast_food", "food_court"):
            return "restaurant"
        if tourism in ("hotel", "motel", "guest_house", "hostel"):
            return "hotel_accommodation"
        if tourism in ("attraction", "viewpoint") or historic in ("monument", "memorial"):
            return "tourist_attraction"
        if tourism == "museum" or historic == "archaeological_site":
            return "museum_cultural"
        if amenity == "place_of_worship":
            return "church_religious"
        if leisure in ("park", "nature_reserve", "garden"):
            return "nature_park"
        if leisure in ("water_park", "swimming_pool") or tourism == "resort":
            return "resort_swimming"
        if amenity in ("hospital", "clinic", "doctors"):
            return "hospital_clinic"
        if amenity == "pharmacy":
            return "pharmacy"
        if amenity in ("bank", "atm"):
            return "bank_atm"
        if amenity == "fuel":
            return "fuel_station"
        if amenity in ("bus_station", "taxi") or str(tags.get("railway", "")).lower() == "station":
            return "transport_terminal"
        if shop in ("supermarket", "convenience"):
            return "convenience_store"
        if shop or amenity == "marketplace":
            return "shopping_market"
        if amenity in ("townhall", "police", "post_office"):
            return "public_facility"
        return "tourist_attraction"

    async def fetch_live_osm_places(
        self,
        min_lat: float = 15.15,
        max_lat: float = 16.15,
        min_lng: float = 120.70,
        max_lng: float = 121.40,
    ) -> list[Place]:
        """Queries backend /places and live OpenStreetMap Overpass API within bounds and merges into cache."""
        discovered: list[Place] = []
        # 1. Try backend bbox query first
        try:
            res = await self.get_places(
                page=1,
                page_size=500,
                min_lat=min_lat,
                max_lat=max_lat,
                min_lng=min_lng,
                max_lng=max_lng,
            )
            if res.items:
                discovered.extend(res.items)
        except Exception:
            pass

        # 2. Query live Overpass API for viewport bbox
        bbox = f"{min_lat},{min_lng},{max_lat},{max_lng}"
        overpass_query = f"""
        [out:json][timeout:12];
        (
          node["amenity"~"cafe|restaurant|fast_food|bank|atm|pharmacy|hospital|clinic|fuel|place_of_worship|bus_station|townhall"]({bbox});
          node["tourism"~"attraction|hotel|motel|guest_house|museum|viewpoint|resort"]({bbox});
          node["leisure"~"park|resort|water_park|nature_reserve|swimming_pool"]({bbox});
          way["tourism"~"attraction|hotel|resort|museum"]({bbox});
        );
        out center body;
        """
        endpoints = [
            "https://overpass-api.de/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
        ]
        for ep in endpoints:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(ep, params={"data": overpass_query})
                    if resp.status_code == 200:
                        payload = resp.json()
                        for el in payload.get("elements", []):
                            tags = el.get("tags") or {}
                            name = tags.get("name") or tags.get("name:en") or tags.get("alt_name")
                            if not name:
                                continue
                            lat = el.get("lat") or (el.get("center") or {}).get("lat")
                            lng = el.get("lon") or (el.get("center") or {}).get("lon")
                            if lat is None or lng is None:
                                continue
                            cat = self.map_osm_tags_to_category(tags)
                            city = tags.get("addr:city") or tags.get("addr:municipality") or "Nueva Ecija"
                            street = tags.get("addr:street") or ""
                            address = f"{street}, {city}" if street else city
                            osm_id = f"{el.get('type', 'node')}-{el.get('id')}"
                            discovered.append(
                                Place(
                                    id=f"osm-{osm_id}",
                                    name=str(name).strip(),
                                    category=cat,
                                    latitude=float(lat),
                                    longitude=float(lng),
                                    municipality_name=city,
                                    address_text=address,
                                    description=tags.get("description") or tags.get("tourism:description") or "",
                                    phone=tags.get("phone") or tags.get("contact:phone"),
                                    website=tags.get("website") or tags.get("contact:website"),
                                    opening_hours=tags.get("opening_hours"),
                                    directions_url=f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}",
                                )
                            )
                        break
            except Exception:
                continue

        if discovered:
            self.merge_places_into_cache(discovered)
        return discovered

    def get_nearby_places(
        self,
        municipality: Optional[str] = None,
        category_tab: str = "restaurant",
    ) -> list[Place]:
        """Filters cached places for nearby amenities by municipality and category tab matching Web app."""
        group_map = {
            "restaurant": {"restaurant", "cafe"},
            "restaurants": {"restaurant", "cafe"},
            "hospital": {"hospital_clinic", "pharmacy"},
            "hospitals": {"hospital_clinic", "pharmacy"},
            "store": {"convenience_store", "shopping_market", "fuel_station", "bank_atm"},
            "stores": {"convenience_store", "shopping_market", "fuel_station", "bank_atm"},
        }
        allowed_cats = group_map.get(category_tab.lower(), {"restaurant", "cafe"})
        muni_places = self.get_loaded_places(municipality)
        if len(muni_places) < 3 and municipality and municipality.lower().strip() not in ("all", "nueva ecija"):
            muni_places = self.get_loaded_places()

        res: list[Place] = []
        for p in muni_places:
            if p.category in allowed_cats:
                res.append(p)
        return res


_place_service_instance: Optional[PlaceService] = None


def get_place_service() -> PlaceService:
    """Singleton getter for PlaceService."""
    global _place_service_instance
    if _place_service_instance is None:
        _place_service_instance = PlaceService()
    return _place_service_instance
