"""Itinerary Service managing generation, custom building, days, stops, and cloud/local synchronization."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import logging
import uuid

from desktop_client.config.settings import get_settings
from desktop_client.core.api_client import ApiClient, ApiClientError, get_api_client
from desktop_client.core.session import SessionManager, get_session_manager

logger = logging.getLogger(__name__)
from desktop_client.core.storage import GuestStorageManager, get_guest_storage
from desktop_client.models.itinerary import (
    Itinerary,
    ItineraryCreatePayload,
    ItineraryDay,
    ItineraryItem,
    ItineraryItemCreatePayload,
    SuggestedItineraryRequest,
)
from desktop_client.models.place import Place


class ItineraryService:
    """Orchestrates multi-day itineraries, stops, and sync between cloud and local guest storage."""

    def __init__(
        self,
        api_client: Optional[ApiClient] = None,
        session_manager: Optional[SessionManager] = None,
        guest_storage: Optional[GuestStorageManager] = None,
    ):
        self.api_client = api_client or get_api_client()
        self.session_manager = session_manager or get_session_manager()
        self.guest_storage = guest_storage or get_guest_storage()
        self.settings = get_settings()

    async def generate_suggested_itinerary(
        self,
        request: SuggestedItineraryRequest,
    ) -> Itinerary:
        """Invokes the backend greedy clustering algorithm to produce an optimized multi-day travel schedule."""
        payload = request.to_dict()
        
        # Extended timeout for GIS/routing calculations
        try:
            data = await self.api_client.post(
                "itineraries/suggest",
                json_data=payload,
                timeout=self.settings.itinerary_gen_timeout_seconds,
            )
        except ApiClientError as err:
            if err.status_code == 404 or err.status_code == 405:
                # Fallback to generate if legacy route
                data = await self.api_client.post(
                    "itineraries/generate",
                    json_data=payload,
                    timeout=self.settings.itinerary_gen_timeout_seconds,
                )
            else:
                raise
        
        itinerary = Itinerary.from_dict(data)
        
        # If traveler is guest, save to local desktop storage
        if not self.session_manager.is_authenticated:
            itinerary.is_guest = True
            self.guest_storage.save_itinerary(itinerary)

        return itinerary

    async def list_itineraries(self) -> list[Itinerary]:
        """Lists itineraries: cloud itineraries if logged in, plus local guest itineraries."""
        results: list[Itinerary] = []

        if self.session_manager.is_authenticated:
            try:
                data = await self.api_client.get("itineraries")
                if isinstance(data, list):
                    for item in data:
                        itin = Itinerary.from_dict(item)
                        itin.is_guest = False
                        results.append(itin)
            except Exception:
                pass

        # Always include guest itineraries
        guest_items = self.guest_storage.list_itineraries()
        results.extend(guest_items)

        return results

    async def get_itinerary(self, itinerary_id: str) -> Optional[Itinerary]:
        """Retrieves an itinerary by UUID from cloud or local guest storage."""
        # Check local guest storage first
        local = self.guest_storage.get_itinerary(itinerary_id)
        if local:
            return local

        if self.session_manager.is_authenticated:
            try:
                data = await self.api_client.get(f"itineraries/{itinerary_id}")
                return Itinerary.from_dict(data)
            except Exception:
                return None

        return None

    async def create_itinerary(self, payload: ItineraryCreatePayload) -> Itinerary:
        """Creates a new itinerary in the cloud or in local guest storage."""
        if self.session_manager.is_authenticated:
            data = await self.api_client.post("itineraries", json_data=payload.to_dict())
            return Itinerary.from_dict(data)

        # Local guest creation
        itin_id = str(uuid.uuid4())
        days: list[ItineraryDay] = []
        for d in payload.days:
            day_id = str(uuid.uuid4())
            raw_items = d.get("items") or []
            items = []
            for item_idx, itm in enumerate(raw_items, 1):
                item_id = str(uuid.uuid4())
                place_obj = Place.from_dict(itm["place"]) if itm.get("place") else None
                items.append(
                    ItineraryItem(
                        id=item_id,
                        day_id=day_id,
                        place_id=itm.get("place_id"),
                        custom_title=itm.get("custom_title"),
                        custom_lat=itm.get("custom_lat"),
                        custom_lng=itm.get("custom_lng"),
                        sort_order=item_idx,
                        planned_time=itm.get("planned_time"),
                        duration_minutes=itm.get("duration_minutes", 90),
                        notes=itm.get("notes"),
                        estimated_cost_min=itm.get("estimated_cost_min"),
                        estimated_cost_max=itm.get("estimated_cost_max"),
                        place=place_obj,
                    )
                )
            days.append(
                ItineraryDay(
                    id=day_id,
                    itinerary_id=itin_id,
                    day_number=d.get("day_number", len(days) + 1),
                    travel_date=d.get("travel_date", payload.start_date),
                    title=d.get("title"),
                    items=items,
                )
            )

        new_itin = Itinerary(
            id=itin_id,
            title=payload.title,
            destination=payload.destination,
            start_date=payload.start_date,
            end_date=payload.end_date,
            daily_budget=payload.daily_budget,
            preferences=payload.preferences,
            type=payload.type,
            assumptions=payload.assumptions,
            days=days,
            is_guest=True,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return self.guest_storage.save_itinerary(new_itin)

    async def update_itinerary(self, itinerary: Itinerary) -> Itinerary:
        """Saves changes to an itinerary."""
        if itinerary.is_guest or not self.session_manager.is_authenticated:
            return self.guest_storage.save_itinerary(itinerary)

        # Update in cloud via PATCH
        update_data = {
            "title": itinerary.title,
            "destination": itinerary.destination,
            "start_date": itinerary.start_date,
            "end_date": itinerary.end_date,
            "daily_budget": itinerary.daily_budget,
            "preferences": itinerary.preferences,
            "assumptions": itinerary.assumptions,
        }
        data = await self.api_client.patch(f"itineraries/{itinerary.id}", json_data=update_data)
        return Itinerary.from_dict(data)

    async def delete_itinerary(self, itinerary_id: str, is_guest: bool = False) -> bool:
        """Deletes an itinerary from cloud or local guest storage."""
        if is_guest or not self.session_manager.is_authenticated:
            return self.guest_storage.delete_itinerary(itinerary_id)

        try:
            await self.api_client.delete(f"itineraries/{itinerary_id}")
            return True
        except Exception:
            # Fallback check if it was locally stored
            return self.guest_storage.delete_itinerary(itinerary_id)

    async def add_stop(
        self,
        itinerary: Itinerary,
        day_id: str,
        payload: ItineraryItemCreatePayload,
        place: Optional[Place] = None,
    ) -> Itinerary:
        """Adds a scheduled stop to a specific day."""
        target_day = next((d for d in itinerary.days if d.id == day_id), None)
        if not target_day:
            return itinerary

        new_order = len(target_day.items) + 1
        payload.sort_order = new_order

        if not itinerary.is_guest and self.session_manager.is_authenticated:
            try:
                data = await self.api_client.post(
                    f"itineraries/{itinerary.id}/days/{day_id}/items",
                    json_data=payload.to_dict(),
                )
                new_item = ItineraryItem.from_dict(data)
                target_day.items.append(new_item)
                return itinerary
            except Exception:
                pass

        # Local guest handling
        new_item = ItineraryItem(
            id=str(uuid.uuid4()),
            day_id=day_id,
            place_id=payload.place_id,
            custom_title=payload.custom_title,
            custom_lat=payload.custom_lat,
            custom_lng=payload.custom_lng,
            sort_order=new_order,
            planned_time=payload.planned_time,
            duration_minutes=payload.duration_minutes,
            notes=payload.notes,
            estimated_cost_min=payload.estimated_cost_min,
            estimated_cost_max=payload.estimated_cost_max,
            place=place,
        )
        target_day.items.append(new_item)
        return self.guest_storage.save_itinerary(itinerary)

    async def delete_stop(self, itinerary: Itinerary, day_id: str, stop_id: str) -> Itinerary:
        """Removes a stop from an itinerary day."""
        target_day = next((d for d in itinerary.days if d.id == day_id), None)
        if not target_day:
            return itinerary

        if not itinerary.is_guest and self.session_manager.is_authenticated:
            try:
                await self.api_client.delete(
                    f"itineraries/{itinerary.id}/days/{day_id}/items/{stop_id}"
                )
            except Exception:
                pass

        target_day.items = [i for i in target_day.items if i.id != stop_id]
        # Recalculate sort_order
        for idx, item in enumerate(target_day.items, 1):
            item.sort_order = idx

        if itinerary.is_guest or not self.session_manager.is_authenticated:
            self.guest_storage.save_itinerary(itinerary)

        return itinerary

    async def reorder_stops(
        self,
        itinerary: Itinerary,
        day_id: str,
        ordered_item_ids: list[str],
    ) -> Itinerary:
        """Reorders stops within an itinerary day."""
        target_day = next((d for d in itinerary.days if d.id == day_id), None)
        if not target_day:
            return itinerary

        # Re-sort local array
        id_to_item = {item.id: item for item in target_day.items}
        reordered: list[ItineraryItem] = []
        for idx, item_id in enumerate(ordered_item_ids, 1):
            if item_id in id_to_item:
                item = id_to_item[item_id]
                item.sort_order = idx
                reordered.append(item)
        target_day.items = reordered

        if not itinerary.is_guest and self.session_manager.is_authenticated:
            try:
                reorder_items = [
                    {"id": item_id, "day_id": day_id, "sort_order": idx}
                    for idx, item_id in enumerate(ordered_item_ids, 1)
                ]
                await self.api_client.post(
                    f"itineraries/{itinerary.id}/reorder",
                    json_data={"items": reorder_items},
                )
            except Exception as err:
                logger.warning(f"Failed to persist stop reordering to backend: {err}")
        else:
            self.guest_storage.save_itinerary(itinerary)

        return itinerary


_itinerary_service_instance: Optional[ItineraryService] = None


def get_itinerary_service() -> ItineraryService:
    """Singleton getter for ItineraryService."""
    global _itinerary_service_instance
    if _itinerary_service_instance is None:
        _itinerary_service_instance = ItineraryService()
    return _itinerary_service_instance
