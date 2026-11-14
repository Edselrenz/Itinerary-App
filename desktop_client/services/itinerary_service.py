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
    _is_valid_uuid,
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
        self.active_draft_itinerary: Optional[Itinerary] = None

    async def generate_suggested_itinerary(
        self,
        request: SuggestedItineraryRequest,
    ) -> Itinerary:
        """Invokes the backend clustering algorithm to produce an optimized multi-day travel schedule, falling back offline."""
        from desktop_client.core.connectivity_service import get_connectivity_service
        conn = get_connectivity_service()

        if not conn.is_host_offline_raw:
            payload = request.to_dict()
            try:
                data = await self.api_client.post(
                    "itineraries/suggest",
                    json_data=payload,
                    timeout=self.settings.itinerary_gen_timeout_seconds,
                )
                itinerary = Itinerary.from_dict(data)
                if request.save_immediately and not self.session_manager.is_authenticated:
                    itinerary.is_guest = True
                    self.guest_storage.save_itinerary(itinerary)
                self.active_draft_itinerary = itinerary
                return itinerary
            except Exception as err:
                logger.info(f"Backend itinerary suggestion failed ({err}), using offline clustering engine fallback")

        # Offline clustering fallback
        itinerary = await self.generate_offline_suggested_itinerary(request)
        if request.save_immediately:
            if not self.session_manager.is_authenticated:
                itinerary.is_guest = True
            self.guest_storage.save_itinerary(itinerary)
        self.active_draft_itinerary = itinerary
        return itinerary

    def set_active_draft_itinerary(self, itinerary: Optional[Itinerary]) -> None:
        """Stores the active draft preview itinerary in memory."""
        self.active_draft_itinerary = itinerary

    def get_active_draft_itinerary(self) -> Optional[Itinerary]:
        """Returns the active draft preview itinerary if present."""
        return self.active_draft_itinerary

    def generate_suggested_itinerary_sync(
        self,
        destination: str,
        days: int = 2,
        pacing: str = "moderate",
        preferences: Optional[list[str]] = None,
        daily_budget: Optional[float] = None,
        anchor_place_id: Optional[str] = None,
    ) -> Itinerary:
        """Synchronously runs offline clustering engine to generate a suggested itinerary."""
        import asyncio
        s_date = datetime.now().strftime("%Y-%m-%d")
        e_date = (datetime.now() + timedelta(days=days - 1)).strftime("%Y-%m-%d")
        req = SuggestedItineraryRequest(
            destination=destination,
            start_date=s_date,
            end_date=e_date,
            pacing=pacing,
            preferences=preferences or ["food", "culture"],
            daily_budget=daily_budget,
            anchor_place_id=anchor_place_id,
        )
        try:
            return asyncio.run(self.generate_offline_suggested_itinerary(req))
        except RuntimeError:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                return ex.submit(lambda: asyncio.run(self.generate_offline_suggested_itinerary(req))).result()

    async def generate_offline_suggested_itinerary(
        self,
        request: SuggestedItineraryRequest,
    ) -> Itinerary:
        """Deterministic offline clustering engine matching canonical Project algorithm."""
        from desktop_client.core.offline_data import CANONICAL_OFFLINE_PLACES, get_all_offline_places
        from desktop_client.core.polyline import haversine_distance_meters, encode_polyline, generate_geodesic_arc

        def _parse_d(s: str) -> datetime:
            try:
                return datetime.strptime(s, "%Y-%m-%d")
            except Exception:
                return datetime.now()

        s_dt = _parse_d(request.start_date)
        e_dt = _parse_d(request.end_date)
        if e_dt < s_dt:
            e_dt = s_dt
        total_days = max(1, (e_dt - s_dt).days + 1)
        is_single_day = total_days == 1

        pacing = (request.pacing or "moderate").lower()
        target_stops = 2 if pacing == "relaxed" else (4 if pacing in ("fast", "packed") else 3)

        UTILITY_CATEGORIES = {
            "bank_atm", "fuel_station", "hospital_clinic", "pharmacy",
            "convenience_store", "transport_terminal", "public_facility"
        }

        # Build candidate pool excluding utility/amenity POIs from tourist slots
        curated_pool = [
            p.to_dict() for p in CANONICAL_OFFLINE_PLACES
            if str(p.category or "").lower() not in UTILITY_CATEGORIES
        ]
        all_places = [
            p for p in get_all_offline_places()
            if str(p.get("category", "")).lower() not in UTILITY_CATEGORIES
        ]
        curated_ids = {p["id"] for p in curated_pool}
        for p in all_places:
            if p.get("id") not in curated_ids:
                curated_pool.append(p)

        target_dest = (request.destination or "").lower().strip()
        is_targeting_muni = bool(target_dest and "nueva ecija" not in target_dest and "province" not in target_dest)

        prefs = [p.lower() for p in (request.preferences or [])]
        PREF_MAP = {
            "nature": {"nature_park", "tourist_attraction"},
            "nature & parks": {"nature_park", "tourist_attraction"},
            "food": {"restaurant", "cafe"},
            "food trip": {"restaurant", "cafe"},
            "culture": {"museum_cultural", "church_religious"},
            "culture & history": {"museum_cultural", "church_religious"},
            "shopping": {"shopping_market", "convenience_store"},
            "resort": {"resort_swimming", "hotel_accommodation"},
        }
        pref_cats: set[str] = set()
        for pr in prefs:
            for k, cats in PREF_MAP.items():
                if k in pr:
                    pref_cats.update(cats)

        daily_budget = request.daily_budget if request.daily_budget and request.daily_budget > 0 else None

        # Filter by destination municipality if specific
        matched_pool = list(curated_pool)
        if is_targeting_muni:
            muni_matches = [p for p in curated_pool if target_dest in str(p.get("municipality_name", "")).lower()]
            if muni_matches:
                matched_pool = muni_matches

        # Filter by min_rating if requested
        min_r = float(request.min_rating or 0.0)
        if min_r > 0:
            filtered_by_r = [p for p in matched_pool if float(p.get("rating") or 4.5) >= min_r]
            if filtered_by_r:
                matched_pool = filtered_by_r

        # Score candidates
        def score_place(p: dict[str, Any]) -> float:
            score = 0.0
            p_muni = str(p.get("municipality_name", "")).lower()
            p_cat = str(p.get("category", "")).lower()
            p_tags = [str(t).lower() for t in p.get("tags", [])]

            if p.get("is_featured") or str(p.get("id", "")).startswith("dest-"):
                score += 20.0

            if is_targeting_muni and target_dest in p_muni:
                score += 15.0

            if pref_cats:
                if p_cat in pref_cats:
                    score += 25.0
            elif prefs:
                for pr in prefs:
                    if pr in p_cat:
                        score += 25.0
                    if any(pr in t for t in p_tags):
                        score += 10.0

            if daily_budget:
                c_min = p.get("estimated_cost_min") or 0.0
                if c_min <= daily_budget:
                    score += 5.0

            if p.get("rating") is not None:
                score += float(p["rating"]) * 2.0
            return score

        matched_pool.sort(key=score_place, reverse=True)

        itinerary_id = str(uuid.uuid4())
        days: list[ItineraryDay] = []
        used_ids: set[str] = set()
        used_names: set[str] = set()
        used_coords: list[tuple[float, float]] = []

        def _clean_name(name: str) -> str:
            n = (name or "").lower()
            for w in ("viewdeck", "viewpoint", "resort", "park", "hotel", "cafe", "restaurant", "farm", "lake", "de", "the"):
                n = n.replace(w, "")
            return "".join(c for c in n if c.isalnum())

        def is_mountain_hike(p: dict[str, Any]) -> bool:
            nm = str(p.get("name", "")).lower()
            tags = " ".join(str(t).lower() for t in p.get("tags", []))
            return ("mt." in nm or "mount " in nm or "hike" in nm or "trail" in nm or "peak" in nm or "mountain" in tags)

        def is_dup(p: dict[str, Any]) -> bool:
            p_id = str(p.get("id", ""))
            if p_id in used_ids:
                return True
            c_name = _clean_name(str(p.get("name", "")))
            if len(c_name) >= 4 and c_name in used_names:
                return True
            lat = float(p.get("latitude") or 0.0)
            lng = float(p.get("longitude") or 0.0)
            for u_lat, u_lng in used_coords:
                if haversine_distance_meters(lat, lng, u_lat, u_lng) < 200:
                    return True
            return False

        def mark_used(p: dict[str, Any]):
            used_ids.add(str(p.get("id", "")))
            c_name = _clean_name(str(p.get("name", "")))
            if len(c_name) >= 4:
                used_names.add(c_name)
            lat = float(p.get("latitude") or 0.0)
            lng = float(p.get("longitude") or 0.0)
            if lat != 0.0 and lng != 0.0:
                used_coords.append((lat, lng))

        def is_dining(cat: str) -> bool:
            return cat in ("restaurant", "cafe", "food", "dining")

        def is_lodging(cat: str) -> bool:
            return cat in ("hotel_accommodation", "resort_swimming", "lodging")

        for d_idx in range(total_days):
            current_date = s_dt + timedelta(days=d_idx)
            date_str = current_date.strftime("%Y-%m-%d")
            day_id = str(uuid.uuid4())

            day_places: list[dict[str, Any]] = []

            # Lock anchor place as Stop 1 of Day 1 (UC-S1)
            if d_idx == 0 and request.anchor_place_id:
                anchor_match = next((p for p in curated_pool if str(p.get("id")) == str(request.anchor_place_id)), None)
                if anchor_match:
                    day_places.append(anchor_match)
                    mark_used(anchor_match)

            candidates = [p for p in matched_pool if not is_dup(p)]
            if is_single_day:
                candidates = [p for p in candidates if not is_lodging(str(p.get("category", "")).lower())]

            if len(candidates) < target_stops:
                extra = [p for p in curated_pool if not is_dup(p) and p.get("id") not in [c.get("id") for c in candidates]]
                if is_single_day:
                    extra = [p for p in extra if not is_lodging(str(p.get("category", "")).lower())]
                candidates.extend(extra)

            hike_count = sum(1 for dp in day_places if is_mountain_hike(dp))

            while len(day_places) < target_stops and candidates:
                slot = len(day_places)
                # Geographic clustering: if day_places has an anchor, prioritize candidates within 25km radius
                if day_places:
                    a_lat = float(day_places[0].get("latitude") or 0.0)
                    a_lng = float(day_places[0].get("longitude") or 0.0)
                    if a_lat and a_lng:
                        def cand_cluster_score(c: dict[str, Any]) -> float:
                            base = score_place(c)
                            c_lat = float(c.get("latitude") or 0.0)
                            c_lng = float(c.get("longitude") or 0.0)
                            if c_lat and c_lng:
                                d_km = haversine_distance_meters(a_lat, a_lng, c_lat, c_lng) / 1000.0
                                if d_km <= 25.0:
                                    base += max(0.0, 25.0 - d_km)
                                else:
                                    base -= (d_km - 25.0) * 1.5
                            return base
                        candidates.sort(key=cand_cluster_score, reverse=True)

                # Slot #1 around noon: prioritize dining
                if slot == 1:
                    dining_cands = [c for c in candidates if is_dining(str(c.get("category", "")).lower())]
                    if dining_cands:
                        selected = dining_cands[0]
                        candidates.remove(selected)
                        day_places.append(selected)
                        mark_used(selected)
                        continue

                # Max 1 mountain hike per day
                selected = None
                for idx, c in enumerate(candidates):
                    if is_mountain_hike(c) and hike_count >= 1:
                        continue
                    selected = candidates.pop(idx)
                    break

                if selected is None:
                    if candidates:
                        selected = candidates.pop(0)
                    else:
                        break

                if not any(dp.get("id") == selected.get("id") for dp in day_places):
                    if is_mountain_hike(selected):
                        hike_count += 1
                    day_places.append(selected)
                    mark_used(selected)

            # 2-Opt nearest-neighbor stop ordering with lodging at day end
            lodging = [p for p in day_places if is_lodging(str(p.get("category", "")).lower())]
            non_lodging = [p for p in day_places if not is_lodging(str(p.get("category", "")).lower())]
            if len(non_lodging) > 2:
                ordered = [non_lodging[0]]
                rem = list(non_lodging[1:])
                while rem:
                    curr_lat = float(ordered[-1].get("latitude") or 0.0)
                    curr_lng = float(ordered[-1].get("longitude") or 0.0)
                    best_idx = 0
                    best_d = float("inf")
                    for idx, r in enumerate(rem):
                        r_lat = float(r.get("latitude") or 0.0)
                        r_lng = float(r.get("longitude") or 0.0)
                        if curr_lat and curr_lng and r_lat and r_lng:
                            d = haversine_distance_meters(curr_lat, curr_lng, r_lat, r_lng)
                        else:
                            d = 999999
                        if d < best_d:
                            best_d = d
                            best_idx = idx
                    ordered.append(rem.pop(best_idx))
                day_places = ordered + lodging
            else:
                day_places = non_lodging + lodging

            items: list[ItineraryItem] = []
            cur_time = datetime.strptime("09:30 AM", "%I:%M %p")
            primary_muni = None

            for s_idx, p_data in enumerate(day_places):
                item_id = str(uuid.uuid4())
                place_obj = Place.from_dict(p_data)
                if not primary_muni and p_data.get("municipality_name"):
                    primary_muni = p_data.get("municipality_name")

                dur_mins = int(p_data.get("default_duration_minutes") or (90 if is_dining(str(p_data.get("category", "")).lower()) else 120))
                end_time = cur_time + timedelta(minutes=dur_mins)
                planned_time = f"{cur_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"

                dist_m = None
                dur_s = None
                if s_idx > 0:
                    prev_p = day_places[s_idx - 1]
                    p_lat, p_lng = float(prev_p.get("latitude") or 0.0), float(prev_p.get("longitude") or 0.0)
                    c_lat, c_lng = float(p_data.get("latitude") or 0.0), float(p_data.get("longitude") or 0.0)
                    if p_lat and p_lng and c_lat and c_lng:
                        raw_dist = haversine_distance_meters(p_lat, p_lng, c_lat, c_lng)
                        dist_m = int(raw_dist * 1.28)
                        dur_s = max(15 * 60, min(120 * 60, int(dist_m / 11.11)))

                items.append(
                    ItineraryItem(
                        id=item_id,
                        day_id=day_id,
                        place_id=p_data.get("id"),
                        custom_title=p_data.get("name"),
                        sort_order=s_idx + 1,
                        planned_time=planned_time,
                        duration_minutes=dur_mins,
                        notes=f"Recommended based on local popularity and cluster proximity in {p_data.get('municipality_name', 'Nueva Ecija')}.",
                        estimated_cost_min=p_data.get("estimated_cost_min"),
                        estimated_cost_max=p_data.get("estimated_cost_max"),
                        place=place_obj,
                        travel_distance_meters=dist_m,
                        travel_duration_seconds=dur_s,
                    )
                )

                transit_mins = int((dur_s or (30 * 60)) / 60)
                cur_time = end_time + timedelta(minutes=transit_mins)

            # Calculate day polylines and leg metrics
            coords: list[tuple[float, float]] = [
                (float(it.place.latitude), float(it.place.longitude))
                for it in items
                if it.place and it.place.latitude and it.place.longitude
            ]
            day_polyline = encode_polyline(coords) if len(coords) >= 2 else None

            muni_title = primary_muni or (request.destination or "Nueva Ecija")
            days.append(
                ItineraryDay(
                    id=day_id,
                    itinerary_id=itinerary_id,
                    day_number=d_idx + 1,
                    travel_date=date_str,
                    title=f"Day {d_idx + 1}: {muni_title}",
                    items=items,
                    day_overview_polyline=day_polyline,
                )
            )

        assumptions = [
            "Travel times between destinations are estimated and subject to local traffic and weather conditions.",
            "Inter-stop transit times and transfers are excluded from activity duration totals.",
            "Budget estimates exclude optional activities, souvenirs, and personal incidentals.",
            "Stops with unverified admission fees are marked as Cost Not Provided or Free Admission where applicable.",
            "Tricycle fares and jeepney schedules conform to municipal terminal guidelines and may vary by time of day.",
        ]

        return Itinerary(
            id=itinerary_id,
            title=request.title or f"{request.destination or 'Nueva Ecija'} Journey",
            destination=request.destination or "Nueva Ecija",
            start_date=request.start_date,
            end_date=request.end_date,
            daily_budget=request.daily_budget,
            preferences=request.preferences or [],
            type="suggested",
            assumptions=assumptions,
            days=days,
            is_guest=True,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

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
        """Creates a new itinerary in the cloud or in local guest storage on network failure."""
        if self.session_manager.is_authenticated:
            try:
                data = await self.api_client.post("itineraries", json_data=payload.to_dict())
                return Itinerary.from_dict(data)
            except Exception as err:
                logger.info(f"Failed to create cloud itinerary ({err}), falling back to local guest storage")

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

    def get_itinerary_or_draft(self, itinerary_id: str) -> Optional[Itinerary]:
        """Resolves an itinerary by ID from draft memory or guest storage."""
        if itinerary_id == "draft" or (self.active_draft_itinerary and self.active_draft_itinerary.id == itinerary_id):
            return self.active_draft_itinerary
        return self.guest_storage.get_itinerary(itinerary_id)

    async def update_itinerary(self, itinerary: Itinerary) -> Itinerary:
        """Saves changes to an itinerary, falling back to local storage on network failure."""
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
            "days": itinerary.to_create_payload().days,
        }
        try:
            data = await self.api_client.patch(f"itineraries/{itinerary.id}", json_data=update_data)
            return Itinerary.from_dict(data)
        except Exception as err:
            logger.info(f"Failed to patch cloud itinerary ({err}), saving to local storage fallback")
            return self.guest_storage.save_itinerary(itinerary)

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

    def calculate_budget_summary(self, itinerary: Itinerary) -> dict[str, Any]:
        """Transparently calculates verified min/max stop costs and unpriced stop count."""
        verified_min = 0.0
        verified_max = 0.0
        unverified_count = 0

        for day in itinerary.days or []:
            for item in day.items or []:
                c_min = item.estimated_cost_min
                c_max = item.estimated_cost_max
                if c_min is None and c_max is None and item.place:
                    c_min = item.place.estimated_cost_min
                    c_max = item.place.estimated_cost_max
                if c_min is not None or c_max is not None:
                    verified_min += float(c_min if c_min is not None else c_max or 0.0)
                    verified_max += float(c_max if c_max is not None else c_min or 0.0)
                else:
                    unverified_count += 1

        if verified_min > 0 or verified_max > 0:
            if abs(verified_min - verified_max) < 0.01:
                formatted_range = f"₱{verified_min:,.0f}"
            else:
                formatted_range = f"₱{verified_min:,.0f} - ₱{verified_max:,.0f}"
            display_text = (
                f"{formatted_range} (+ {unverified_count} unpriced)"
                if unverified_count > 0
                else formatted_range
            )
        elif unverified_count > 0:
            display_text = f"{unverified_count} unpriced stops"
        else:
            display_text = "No stops added"

        return {
            "verified_min": verified_min,
            "verified_max": verified_max,
            "unverified_count": unverified_count,
            "display_text": display_text,
        }

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
                req_dict = payload.to_dict()
                if not _is_valid_uuid(req_dict.get("place_id")):
                    req_dict["place_id"] = None
                    if place:
                        req_dict["place_payload"] = place.to_dict()
                data = await self.api_client.post(
                    f"itineraries/{itinerary.id}/days/{day_id}/items",
                    json_data=req_dict,
                )
                if isinstance(data, dict) and "days" in data:
                    return Itinerary.from_dict(data)
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

    async def update_stop(
        self,
        itinerary: Itinerary,
        day_id: str,
        stop_id: str,
        patch_data: dict[str, Any],
    ) -> Itinerary:
        """Partially updates a stop via PATCH /api/v1/itineraries/{id}/days/{day_id}/items/{stop_id}."""
        if not itinerary.is_guest and self.session_manager.is_authenticated:
            try:
                data = await self.api_client.patch(
                    f"itineraries/{itinerary.id}/days/{day_id}/items/{stop_id}",
                    json_data=patch_data,
                )
                if isinstance(data, dict) and "days" in data:
                    return Itinerary.from_dict(data)
            except Exception:
                pass

        target_day = next((d for d in itinerary.days if d.id == day_id), None)
        if target_day:
            target_item = next((i for i in target_day.items if i.id == stop_id), None)
            if target_item:
                for k, v in patch_data.items():
                    if hasattr(target_item, k):
                        setattr(target_item, k, v)
        if itinerary.is_guest or not self.session_manager.is_authenticated:
            self.guest_storage.save_itinerary(itinerary)
        return itinerary

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
