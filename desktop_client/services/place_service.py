"""Place Service managing POI queries, filtering, search, and municipality catalogs."""

import logging
from typing import Any, Optional

from desktop_client.config.settings import CANONICAL_CATEGORIES
from desktop_client.core.api_client import ApiClient, get_api_client
from desktop_client.models.place import Municipality, PaginatedPlaces, Place

logger = logging.getLogger(__name__)


class PlaceService:
    """Interacts with backend Places and Municipalities endpoints."""

    def __init__(self, api_client: Optional[ApiClient] = None):
        self.api_client = api_client or get_api_client()
        self._municipalities_cache: Optional[list[Municipality]] = None
        self._categories_cache: Optional[list[str]] = None

    async def get_municipalities(self, force_refresh: bool = False) -> list[Municipality]:
        """Fetches all 32 Nueva Ecija municipalities and cities with offline fallback."""
        if self._municipalities_cache is not None and not force_refresh:
            return self._municipalities_cache

        try:
            data = await self.api_client.get("municipalities")
            if isinstance(data, list) and data:
                self._municipalities_cache = [Municipality.from_dict(m) for m in data]
                return self._municipalities_cache
        except Exception as err:
            logger.info(f"Could not load municipalities from backend, using offline dataset: {err}")

        from desktop_client.core.offline_data import ALL_32_LGUS_METADATA
        fallback: list[Municipality] = []
        for name, meta in ALL_32_LGUS_METADATA.items():
            fallback.append(
                Municipality(
                    id=f"muni-{name.lower().replace(' ', '-')}",
                    name=name,
                    district=meta.get("district", "Central"),
                    is_city=meta.get("is_city", False),
                    poi_count=meta.get("poi_count", 0),
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
        municipality_id: Optional[str] = None,
        is_featured: Optional[bool] = None,
        sort: Optional[str] = None,
    ) -> PaginatedPlaces:
        """Queries places with multi-criteria filtering mapped to backend parameters, falling back offline."""
        limit = max(1, page_size)
        offset = max(0, (page - 1) * limit)
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }
        if search and search.strip():
            params["q"] = search.strip()
        if category and category.strip() and category != "all":
            params["categories"] = [category.strip()]
        if municipality_id and municipality_id.strip() and municipality_id != "all":
            params["municipality_id"] = municipality_id.strip()
        if is_featured is not None:
            params["featured"] = is_featured
        if sort:
            params["sort"] = sort

        try:
            data = await self.api_client.get("places", params=params)
            return PaginatedPlaces.from_dict(data)
        except Exception as err:
            logger.info(f"Using offline place catalog fallback: {err}")
            from desktop_client.core.offline_data import get_filtered_local_places
            items, total = get_filtered_local_places(
                q=search,
                category=category,
                municipality_id=municipality_id,
                is_featured=is_featured,
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
                pages=max(1, (total + limit - 1) // limit),
            )

    async def get_featured_places(self, limit: int = 6) -> list[Place]:
        """Retrieves top curated destinations for the dashboard."""
        try:
            paginated = await self.get_places(page=1, page_size=limit, is_featured=True)
            if paginated.items:
                return paginated.items
            fallback = await self.get_places(page=1, page_size=limit)
            return fallback.items
        except Exception:
            return []

    async def get_place_by_id(self, place_id: str) -> Optional[Place]:
        """Fetches full place details including editorial summary and GIS data with offline lookup."""
        try:
            data = await self.api_client.get(f"places/{place_id}")
            if data:
                return Place.from_dict(data)
        except Exception:
            pass

        from desktop_client.core.offline_data import get_all_offline_places
        for p in get_all_offline_places():
            if str(p.get("id")) == str(place_id):
                return Place.from_dict(p)
        return None


_place_service_instance: Optional[PlaceService] = None


def get_place_service() -> PlaceService:
    """Singleton getter for PlaceService."""
    global _place_service_instance
    if _place_service_instance is None:
        _place_service_instance = PlaceService()
    return _place_service_instance
