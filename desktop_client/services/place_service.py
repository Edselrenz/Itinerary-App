"""Place Service managing POI queries, filtering, search, and municipality catalogs."""

from typing import Any, Optional

from desktop_client.core.api_client import ApiClient, get_api_client
from desktop_client.models.place import Municipality, PaginatedPlaces, Place


class PlaceService:
    """Interacts with backend Places and Municipalities endpoints."""

    def __init__(self, api_client: Optional[ApiClient] = None):
        self.api_client = api_client or get_api_client()
        self._municipalities_cache: Optional[list[Municipality]] = None
        self._categories_cache: Optional[list[str]] = None

    async def get_municipalities(self, force_refresh: bool = False) -> list[Municipality]:
        """Fetches all 32 Nueva Ecija municipalities and cities."""
        if self._municipalities_cache is not None and not force_refresh:
            return self._municipalities_cache

        try:
            data = await self.api_client.get("municipalities")
            if isinstance(data, list):
                self._municipalities_cache = [Municipality.from_dict(m) for m in data]
                return self._municipalities_cache
        except Exception:
            pass

        return self._municipalities_cache or []

    async def get_categories(self, force_refresh: bool = False) -> list[str]:
        """Fetches the 16 canonical categories from backend."""
        if self._categories_cache is not None and not force_refresh:
            return self._categories_cache

        try:
            data = await self.api_client.get("places/categories")
            if isinstance(data, list):
                self._categories_cache = data
                return self._categories_cache
        except Exception:
            pass

        return self._categories_cache or []

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
        """Queries places with multi-criteria filtering."""
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }
        if search and search.strip():
            params["search"] = search.strip()
        if category and category.strip() and category != "all":
            params["category"] = category.strip()
        if municipality_id and municipality_id.strip() and municipality_id != "all":
            params["municipality_id"] = municipality_id.strip()
        if is_featured is not None:
            params["is_featured"] = is_featured
        if sort:
            params["sort"] = sort

        data = await self.api_client.get("places", params=params)
        return PaginatedPlaces.from_dict(data)

    async def get_featured_places(self, limit: int = 6) -> list[Place]:
        """Retrieves top curated destinations for the dashboard."""
        try:
            paginated = await self.get_places(page=1, page_size=limit, is_featured=True)
            if paginated.items:
                return paginated.items
            # Fallback to general places if no featured flags
            fallback = await self.get_places(page=1, page_size=limit)
            return fallback.items
        except Exception:
            return []

    async def get_place_by_id(self, place_id: str) -> Optional[Place]:
        """Fetches full place details including editorial summary and GIS data."""
        try:
            data = await self.api_client.get(f"places/{place_id}")
            return Place.from_dict(data)
        except Exception:
            return None


_place_service_instance: Optional[PlaceService] = None


def get_place_service() -> PlaceService:
    """Singleton getter for PlaceService."""
    global _place_service_instance
    if _place_service_instance is None:
        _place_service_instance = PlaceService()
    return _place_service_instance
