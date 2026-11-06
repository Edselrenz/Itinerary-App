"""Deterministic Suggested Itinerary Generator using Haversine distance clustering, Bayesian scoring, and 2-Opt road pacing."""

import itertools
import logging
import math
import re
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.entities import Municipality, Place, Itinerary, ItineraryDay, ItineraryItem
from app.schemas.itinerary import SuggestedItineraryRequest
from app.services.google_maps_service import google_maps_service

logger = logging.getLogger("app.algorithms.itinerary_generator")


# Earth radius in kilometers for spherical great-circle calculation
EARTH_RADIUS_KM = 6371.0

# Canonical category mapping from user preferences
PREFERENCE_CATEGORY_MAP: dict[str, list[str]] = {
    "nature": ["nature_park", "tourist_attraction"],
    "heritage": ["church_religious", "museum_cultural"],
    "culture": ["museum_cultural", "church_religious"],
    "history": ["museum_cultural", "church_religious"],
    "food": ["restaurant", "cafe"],
    "dining": ["restaurant", "cafe"],
    "cafes": ["cafe", "restaurant"],
    "relaxation": ["resort_swimming", "hotel_accommodation"],
    "resort": ["resort_swimming", "hotel_accommodation"],
    "adventure": ["nature_park", "tourist_attraction"],
    "shopping": ["shopping_market", "convenience_store"],
}

# Standard time slots for a balanced 3-stop day
DAILY_TIME_SLOTS = [
    {"planned_time": time(9, 0), "duration_minutes": 120, "slot_type": "morning_activity"},
    {"planned_time": time(12, 0), "duration_minutes": 90, "slot_type": "lunch_dining"},
    {"planned_time": time(14, 30), "duration_minutes": 120, "slot_type": "afternoon_activity"},
    {"planned_time": time(17, 30), "duration_minutes": 90, "slot_type": "evening_relaxation"},
]


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes the great-circle distance between two points in kilometers."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c


def resolve_preference_categories(preferences: list[str]) -> set[str]:
    """Expands user-selected preference keywords into canonical category keys."""
    categories: set[str] = set()
    for pref in preferences:
        clean = pref.strip().lower()
        if clean in PREFERENCE_CATEGORY_MAP:
            categories.update(PREFERENCE_CATEGORY_MAP[clean])
        else:
            categories.add(clean)
    return categories


def resolve_geographic_anchor(db: Session, destination: str) -> tuple[float, float, str]:
    """Resolves target destination coordinates to serve as the initial geographic anchor."""
    clean_dest = destination.strip()
    safe_dest = clean_dest.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    
    # 1. Match Municipality by name or slug
    muni = db.scalar(
        select(Municipality).where(
            (Municipality.name.ilike(f"%{safe_dest}%"))
            | (Municipality.slug.ilike(f"%{safe_dest.replace(' ', '-')}%"))
        )
    )
    if muni and muni.center_lat is not None and muni.center_lng is not None:
        return muni.center_lat, muni.center_lng, muni.name

    # 2. Match Place by name
    place = db.scalar(select(Place).where(Place.name.ilike(f"%{safe_dest}%")))
    if place:
        muni_name = place.municipality.name if place.municipality else clean_dest
        return place.latitude, place.longitude, muni_name

    # 3. Default to Nueva Ecija provincial center (Cabanatuan / Palayan axis)
    return 15.5800, 121.0000, "Nueva Ecija"


def is_accommodation_place(place: Place) -> bool:
    """Checks whether a place represents an overnight accommodation or lodging resort (DEF-03)."""
    cat = (place.category or "").lower()
    tags = [t.lower() for t in (place.tags or [])]
    if cat == "hotel_accommodation":
        return True
    if any(
        kw in t
        for kw in ("cabin", "glamping", "hotel", "overnight", "stay", "resort villas")
        for t in tags
    ):
        return True
    return False


def bayesian_quality_score(
    rating: float | None,
    user_rating_count: int | None,
    c_baseline: float = 3.8,
    m_threshold: int = 15,
) -> float:
    """Calculates Bayesian weighted average rating to normalize sparse vs established ratings."""
    if rating is None or rating <= 0:
        return c_baseline
    v = user_rating_count or 0
    if v <= 0:
        return c_baseline
    m = m_threshold
    r = rating
    return (v / (v + m)) * r + (m / (v + m)) * c_baseline


def is_open_during_slot(
    regular_opening_hours: dict | None,
    opening_hours_text: str | None,
    planned_time: time | None,
    target_weekday: int = 0,
) -> bool:
    """Checks whether a venue is open during the scheduled stop time."""
    if planned_time is None:
        return True

    # 1. Structured Google Places regular_opening_hours
    if regular_opening_hours and isinstance(regular_opening_hours, dict):
        periods = regular_opening_hours.get("periods", [])
        if periods:
            # Google Places: 0=Sunday, 1=Monday ... 6=Saturday
            google_day = (target_weekday + 1) % 7
            target_min = planned_time.hour * 60 + planned_time.minute

            for p in periods:
                o = p.get("open", {})
                c = p.get("close")
                # 24/7 indicator: open on Sunday at 00:00 with no close
                if not c and o.get("day") == 0 and o.get("hour") == 0:
                    return True

                if o.get("day") == google_day:
                    o_min = o.get("hour", 0) * 60 + o.get("minute", 0)
                    if c:
                        c_min = c.get("hour", 0) * 60 + c.get("minute", 0)
                        if c_min >= o_min:
                            if o_min <= target_min < c_min:
                                return True
                        else:
                            # Crosses midnight
                            if target_min >= o_min or target_min < c_min:
                                return True
                    else:
                        if target_min >= o_min:
                            return True
            return False

    # 2. String OSM opening_hours fallback
    if opening_hours_text and isinstance(opening_hours_text, str):
        cleaned = opening_hours_text.strip().lower()
        if "24/7" in cleaned:
            return True
        m = re.search(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})", cleaned)
        if m:
            start_min = int(m.group(1)) * 60 + int(m.group(2))
            end_min = int(m.group(3)) * 60 + int(m.group(4))
            target_min = planned_time.hour * 60 + planned_time.minute
            return start_min <= target_min < end_min

    # Default to True when schedule is unlisted to avoid penalizing unverified open places
    return True


def score_place(
    place: Place,
    anchor_lat: float,
    anchor_lng: float,
    preferred_categories: set[str],
    current_day_categories: list[str],
    remaining_daily_budget: float,
    require_dining: bool = False,
    max_radius_km: float = 25.0,
    planned_time: time | None = None,
    target_weekday: int = 0,
) -> float:
    """Scores a candidate place based on preferences, proximity, Bayesian quality rating, hours, and diversity."""
    # Hard boost or filter for dining slots
    if require_dining:
        if place.category in ("restaurant", "cafe"):
            score = 80.0
        else:
            score = 10.0
    else:
        score = 50.0

    # Morning slot penalty for overnight accommodation (DEF-03)
    if not require_dining and is_accommodation_place(place):
        if len(current_day_categories) == 0:
            score -= 40.0
        else:
            score += 20.0

    # 1. Category / Preference match (+40)
    if place.category in preferred_categories:
        score += 40.0
    for tag in place.tags or []:
        if any(p in tag.lower() for p in preferred_categories):
            score += 15.0
            break

    # 2. Curated & Featured quality (+20)
    if place.is_featured:
        score += 20.0

    # 3. Bayesian Quality Rating score (+20 max based on weighted rating)
    bayesian_score = bayesian_quality_score(place.rating, place.user_rating_count)
    score += (bayesian_score / 5.0) * 20.0

    # 4. Proximity to current anchor (+30 max, decaying by distance)
    dist = haversine_distance_km(anchor_lat, anchor_lng, place.latitude, place.longitude)
    if dist <= max_radius_km:
        score += max(0.0, 30.0 - (dist * 1.2))
    else:
        # Distance penalty for places exceeding default cluster radius
        score -= (dist - max_radius_km) * 2.0

    # 5. Operating hours gate (-50 if closed during planned visit)
    if planned_time is not None:
        if not is_open_during_slot(
            place.regular_opening_hours, place.opening_hours, planned_time, target_weekday
        ):
            score -= 50.0

    # 6. Same-day Category Diversity penalty (-25)
    if place.category in current_day_categories:
        score -= 25.0

    # 7. Cumulative Daily Budget fit
    if remaining_daily_budget > 0:
        raw_cost = (
            place.estimated_cost_min
            if place.estimated_cost_min is not None
            else place.estimated_cost_max
        )
        if raw_cost is not None:
            place_cost = float(raw_cost)
            if place_cost <= remaining_daily_budget:
                score += 10.0
            else:
                score -= 30.0

    return score


def generate_suggested_itinerary_data(
    db: Session,
    request: SuggestedItineraryRequest,
    user_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Generates an editable, geographically clustered itinerary draft with transparent assumptions."""
    # 1. Compute day dates
    travel_dates: list[date] = []
    curr_date = request.start_date
    while curr_date <= request.end_date:
        travel_dates.append(curr_date)
        curr_date += timedelta(days=1)

    total_days = len(travel_dates)
    if total_days > 14:
        raise ValueError("Suggested itineraries are currently supported up to 14 days.")

    # 2. Determine initial geographic anchor
    anchor_lat, anchor_lng, resolved_area = resolve_geographic_anchor(db, request.destination)
    preferred_categories = resolve_preference_categories(request.preferences)

    # 3. Fetch candidate POIs (CR-013: SQL bounding-box pre-filtering)
    cluster_radius_km = settings.default_dest_radius_km
    candidate_places: list[Place] = []

    if resolved_area != "Nueva Ecija":
        # Pre-filter candidates in SQL using coordinate bounding box around target anchor
        lat_buffer = (cluster_radius_km + 10.0) / 111.0
        lng_cos = max(0.1, math.cos(math.radians(anchor_lat)))
        lng_buffer = (cluster_radius_km + 10.0) / (111.0 * lng_cos)

        bbox_query = (
            select(Place)
            .where(
                Place.is_active == True,
                Place.latitude.between(anchor_lat - lat_buffer, anchor_lat + lat_buffer),
                Place.longitude.between(anchor_lng - lng_buffer, anchor_lng + lng_buffer),
            )
            .options(selectinload(Place.municipality))
        )
        candidates = list(db.scalars(bbox_query).all())

        # Refine candidates with exact haversine distance within cluster radius
        within_radius = [
            p
            for p in candidates
            if haversine_distance_km(anchor_lat, anchor_lng, p.latitude, p.longitude)
            <= cluster_radius_km
        ]
        if len(within_radius) >= min(total_days * 2, 3):
            candidate_places = within_radius
        elif len(candidates) >= min(total_days * 2, 3):
            candidate_places = candidates

    # Live discovery integration: fetch and upsert nearby Google Places if requested or catalog is sparse
    if getattr(request, "include_live_places", False) or len(candidate_places) < total_days * 3:
        if settings.google_maps_api_key:
            try:
                live_places, _ = google_maps_service.search_places_nearby(
                    db=db,
                    lat=anchor_lat,
                    lng=anchor_lng,
                    radius_meters=cluster_radius_km * 1000.0,
                )
                existing_ids = {p.id for p in candidate_places}
                for lp in live_places:
                    upserted = google_maps_service.upsert_google_place_to_db(db, lp)
                    if upserted.id not in existing_ids:
                        candidate_places.append(upserted)
                        existing_ids.add(upserted.id)
            except Exception as e:
                logger.warning("Could not fetch live Google Places for itinerary generation: %s", e)

    # Fall back to loading full active catalog if province-wide or insufficient bounding box matches
    if not candidate_places:
        candidate_places = list(
            db.scalars(
                select(Place)
                .where(Place.is_active == True)
                .options(selectinload(Place.municipality))
            ).all()
        )

    if not candidate_places:
        raise ValueError("No active destinations found in Nueva Ecija database.")

    # Track already scheduled places across the entire trip
    scheduled_place_ids: set[uuid.UUID] = set()

    # Track unverified stops for honest budget reporting
    unverified_cost_count = 0

    days_data: list[dict[str, Any]] = []
    current_anchor_lat = anchor_lat
    current_anchor_lng = anchor_lng

    # 4. Schedule each travel day
    for day_idx, travel_date in enumerate(travel_dates):
        day_number = day_idx + 1
        day_categories: list[str] = []
        day_items: list[dict[str, Any]] = []
        current_day_cost = 0.0

        # Target 3 stops per day: Morning, Lunch, Afternoon
        available_slots = DAILY_TIME_SLOTS[:3]

        for slot_idx, slot in enumerate(available_slots):
            is_dining_slot = slot["slot_type"] == "lunch_dining"

            # Filter remaining candidates
            eligible = [p for p in candidate_places if p.id not in scheduled_place_ids]
            if not eligible:
                # If we exhausted places, allow non-duplicate re-use only if strictly necessary
                eligible = [
                    p for p in candidate_places 
                    if p.id not in [it["place_id"] for it in day_items]
                ]

            if not eligible:
                break

            remaining_daily_budget = (
                max(0.0, request.daily_budget - current_day_cost)
                if request.daily_budget > 0
                else 0.0
            )

            # Score each candidate relative to current day anchor
            scored_candidates = []
            for p in eligible:
                s = score_place(
                    place=p,
                    anchor_lat=current_anchor_lat,
                    anchor_lng=current_anchor_lng,
                    preferred_categories=preferred_categories,
                    current_day_categories=day_categories,
                    remaining_daily_budget=remaining_daily_budget,
                    require_dining=is_dining_slot,
                    max_radius_km=cluster_radius_km,
                    planned_time=slot["planned_time"],
                    target_weekday=travel_date.weekday(),
                )
                scored_candidates.append((s, p))

            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            best_score, chosen_place = scored_candidates[0]

            scheduled_place_ids.add(chosen_place.id)
            day_categories.append(chosen_place.category)

            # Track cumulative daily expenditure
            raw_item_cost = (
                chosen_place.estimated_cost_min
                if chosen_place.estimated_cost_min is not None
                else (chosen_place.estimated_cost_max or 0.0)
            )
            item_cost = float(raw_item_cost) if raw_item_cost is not None else 0.0
            current_day_cost += item_cost

            # Move day anchor toward chosen place for localized proximity chaining
            current_anchor_lat = chosen_place.latitude
            current_anchor_lng = chosen_place.longitude

            if chosen_place.estimated_cost_min is None and chosen_place.estimated_cost_max is None:
                unverified_cost_count += 1

            day_items.append({
                "id": uuid.uuid4(),
                "place_id": chosen_place.id,
                "google_place_id": chosen_place.google_place_id,
                "custom_title": None,
                "custom_lat": None,
                "custom_lng": None,
                "sort_order": slot_idx + 1,
                "planned_time": slot["planned_time"],
                "duration_minutes": slot["duration_minutes"],
                "notes": f"Recommended for {slot['slot_type'].replace('_', ' ')} based on local proximity and quality.",
                "estimated_cost_min": chosen_place.estimated_cost_min,
                "estimated_cost_max": chosen_place.estimated_cost_max,
                "travel_mode_from_prev": getattr(request, "travel_mode", "DRIVE") or "DRIVE",
                "travel_distance_meters": None,
                "travel_duration_seconds": None,
                "route_polyline_from_prev": None,
                "place": chosen_place,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            })

        # 2-Opt TSP Permutation Optimization & Dynamic Road Pacing
        non_acc = [it for it in day_items if not is_accommodation_place(it["place"])]
        acc = [it for it in day_items if is_accommodation_place(it["place"])]

        if len(non_acc) > 1:
            best_perm = None
            best_dist = float("inf")
            day_start_coord = (anchor_lat, anchor_lng)
            for perm in itertools.permutations(non_acc):
                total_d = haversine_distance_km(
                    day_start_coord[0], day_start_coord[1], perm[0]["place"].latitude, perm[0]["place"].longitude
                )
                for i in range(len(perm) - 1):
                    total_d += haversine_distance_km(
                        perm[i]["place"].latitude, perm[i]["place"].longitude, perm[i + 1]["place"].latitude, perm[i + 1]["place"].longitude
                    )
                if acc:
                    total_d += haversine_distance_km(
                        perm[-1]["place"].latitude, perm[-1]["place"].longitude, acc[0]["place"].latitude, acc[0]["place"].longitude
                    )
                if total_d < best_dist:
                    best_dist = total_d
                    best_perm = perm
            ordered_items = list(best_perm) + acc
        else:
            ordered_items = non_acc + acc

        # Calculate dynamic travel arrival times and leg routes
        curr_dt = datetime.combine(travel_date, time(9, 0))
        travel_mode = getattr(request, "travel_mode", "DRIVE") or "DRIVE"

        for idx, it in enumerate(ordered_items):
            it["sort_order"] = idx + 1
            it["google_place_id"] = it["place"].google_place_id

            if is_accommodation_place(it["place"]):
                dur = 120
            elif it["place"].category in ("restaurant", "cafe"):
                dur = 75
            else:
                dur = 90
            it["duration_minutes"] = dur

            if idx == 0:
                it["planned_time"] = time(curr_dt.hour, curr_dt.minute)
                it["travel_distance_meters"] = None
                it["travel_duration_seconds"] = None
                it["route_polyline_from_prev"] = None
                it["travel_mode_from_prev"] = travel_mode
                curr_dt += timedelta(minutes=dur)
            else:
                prev_place = ordered_items[idx - 1]["place"]
                curr_place = it["place"]
                leg_route = google_maps_service.compute_route(
                    db=db,
                    origin={"latitude": prev_place.latitude, "longitude": prev_place.longitude},
                    destination={"latitude": curr_place.latitude, "longitude": curr_place.longitude},
                    intermediates=[],
                    travel_mode=travel_mode,
                )
                leg_dist = leg_route.get("total_distance_meters", 0)
                leg_dur = leg_route.get("total_duration_seconds", 0)
                leg_poly = leg_route.get("overview_polyline")

                if (not leg_dist or leg_dist <= 0) and (prev_place.latitude != curr_place.latitude or prev_place.longitude != curr_place.longitude):
                    straight_km = haversine_distance_km(prev_place.latitude, prev_place.longitude, curr_place.latitude, curr_place.longitude)
                    road_km = max(0.5, straight_km * 1.28)
                    leg_dist = int(round(road_km * 1000))
                    leg_dur = max(180, int(round((road_km / 32.0) * 3600)))

                curr_dt += timedelta(seconds=leg_dur)
                rounded_m = int(round(curr_dt.minute / 5.0) * 5)
                if rounded_m >= 60:
                    curr_dt = (curr_dt + timedelta(hours=1)).replace(minute=0)
                else:
                    curr_dt = curr_dt.replace(minute=rounded_m)

                it["planned_time"] = time(curr_dt.hour, curr_dt.minute)
                it["travel_distance_meters"] = leg_dist
                it["travel_duration_seconds"] = leg_dur
                it["route_polyline_from_prev"] = leg_poly
                it["travel_mode_from_prev"] = travel_mode
                curr_dt += timedelta(minutes=dur)

        day_items = ordered_items

        # Set title reflecting the primary destination of the day
        first_place = day_items[0]["place"] if day_items else None
        day_muni = (
            first_place.municipality.name
            if first_place and first_place.municipality
            else resolved_area
        )
        day_title = f"Day {day_number}: {day_muni} Tour"

        # Compute full day overview route
        if len(day_items) >= 2:
            day_origin = {"latitude": day_items[0]["place"].latitude, "longitude": day_items[0]["place"].longitude}
            day_dest = {"latitude": day_items[-1]["place"].latitude, "longitude": day_items[-1]["place"].longitude}
            day_intermediates = [
                {"latitude": it["place"].latitude, "longitude": it["place"].longitude}
                for it in day_items[1:-1]
            ]
            day_route_data = google_maps_service.compute_route(
                db=db,
                origin=day_origin,
                destination=day_dest,
                intermediates=day_intermediates,
                travel_mode=travel_mode,
            )
            day_overview_poly = day_route_data.get("overview_polyline")
            day_total_dist = day_route_data.get("total_distance_meters", 0)
            day_total_dur = day_route_data.get("total_duration_seconds", 0)
            day_legs = day_route_data.get("legs", [])

            if (not day_total_dist or day_total_dist <= 0) and len(day_items) >= 2:
                day_total_dist = sum(it.get("travel_distance_meters", 0) for it in day_items if it.get("travel_distance_meters"))
                day_total_dur = sum(it.get("travel_duration_seconds", 0) for it in day_items if it.get("travel_duration_seconds"))
        else:
            day_overview_poly = None
            day_total_dist = 0
            day_total_dur = 0
            day_legs = []

        day_id = uuid.uuid4()
        for it in day_items:
            it["day_id"] = day_id

        days_data.append({
            "id": day_id,
            "day_number": day_number,
            "travel_date": travel_date,
            "title": day_title,
            "items": day_items,
            "day_overview_polyline": day_overview_poly,
            "total_distance_meters": day_total_dist,
            "total_travel_duration_seconds": day_total_dur,
            "route_legs": day_legs,
        })

    # 5. Generate transparent, human-readable assumptions
    assumptions = [
        "Pacing: 2 to 3 stops scheduled per day to allow relaxed travel along provincial roads.",
        f"Geographic clustering: Stops on each day are clustered around {resolved_area} to prevent cross-province backtracking.",
        "Budget & Expenses: Estimates reflect entrance, activities, and dining where available. Inter-town tricycle, jeepney fares, and private vehicle fuel are not included.",
        "Operating Hours: Hours reflect verified public records; travelers are encouraged to verify schedules locally for holidays.",
    ]
    if unverified_cost_count > 0:
        assumptions.append(
            f"Pricing Notice: {unverified_cost_count} stop(s) do not list verified admission/dining costs in open records and are not counted as ₱0."
        )

    now = datetime.now(timezone.utc)
    itinerary_id = uuid.uuid4()

    for d in days_data:
        d["itinerary_id"] = itinerary_id

    return {
        "id": itinerary_id,
        "user_id": user_id,
        "title": request.title,
        "destination": resolved_area,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "daily_budget": request.daily_budget,
        "preferences": request.preferences,
        "type": "suggested",
        "assumptions": assumptions,
        "created_at": now,
        "updated_at": now,
        "days": days_data,
    }


def persist_generated_itinerary(db: Session, data: dict[str, Any], user_id: uuid.UUID) -> Itinerary:
    """Persists an algorithmically generated itinerary into the database."""
    itinerary = Itinerary(
        id=data["id"],
        user_id=user_id,
        title=data["title"],
        destination=data["destination"],
        start_date=data["start_date"],
        end_date=data["end_date"],
        daily_budget=data["daily_budget"],
        preferences=data["preferences"],
        type="suggested",
        assumptions=data["assumptions"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )
    db.add(itinerary)
    db.flush()

    for d_data in data["days"]:
        day = ItineraryDay(
            id=d_data["id"],
            itinerary_id=itinerary.id,
            day_number=d_data["day_number"],
            travel_date=d_data["travel_date"],
            title=d_data["title"],
            day_overview_polyline=d_data.get("day_overview_polyline"),
            total_distance_meters=d_data.get("total_distance_meters"),
            total_travel_duration_seconds=d_data.get("total_travel_duration_seconds"),
            route_legs=d_data.get("route_legs", []),
        )
        db.add(day)
        db.flush()

        for it_data in d_data["items"]:
            item = ItineraryItem(
                id=it_data["id"],
                day_id=day.id,
                place_id=it_data["place_id"],
                google_place_id=it_data.get("google_place_id"),
                custom_title=it_data.get("custom_title"),
                custom_lat=it_data.get("custom_lat"),
                custom_lng=it_data.get("custom_lng"),
                sort_order=it_data["sort_order"],
                planned_time=it_data["planned_time"],
                duration_minutes=it_data["duration_minutes"],
                notes=it_data["notes"],
                estimated_cost_min=it_data["estimated_cost_min"],
                estimated_cost_max=it_data["estimated_cost_max"],
                travel_mode_from_prev=it_data.get("travel_mode_from_prev", "DRIVE"),
                travel_distance_meters=it_data.get("travel_distance_meters"),
                travel_duration_seconds=it_data.get("travel_duration_seconds"),
                route_polyline_from_prev=it_data.get("route_polyline_from_prev"),
            )
            db.add(item)

    db.commit()

    # Re-query with eager relationships
    stmt = (
        select(Itinerary)
        .where(Itinerary.id == itinerary.id)
        .options(
            selectinload(Itinerary.days)
            .selectinload(ItineraryDay.items)
            .selectinload(ItineraryItem.place)
        )
    )
    return db.scalar(stmt)
