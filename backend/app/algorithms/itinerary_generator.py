"""Deterministic Suggested Itinerary Generator using Haversine distance clustering and preference scoring."""

import math
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import Municipality, Place, Itinerary, ItineraryDay, ItineraryItem
from app.schemas.itinerary import SuggestedItineraryRequest


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
    
    # 1. Match Municipality by name or slug
    muni = db.scalar(
        select(Municipality).where(
            (Municipality.name.ilike(f"%{clean_dest}%"))
            | (Municipality.slug.ilike(f"%{clean_dest.replace(' ', '-')}%"))
        )
    )
    if muni and muni.center_lat is not None and muni.center_lng is not None:
        return muni.center_lat, muni.center_lng, muni.name

    # 2. Match Place by name
    place = db.scalar(select(Place).where(Place.name.ilike(f"%{clean_dest}%")))
    if place:
        muni_name = place.municipality.name if place.municipality else clean_dest
        return place.latitude, place.longitude, muni_name

    # 3. Default to Nueva Ecija provincial center (Cabanatuan / Palayan axis)
    return 15.5800, 121.0000, "Nueva Ecija"


def score_place(
    place: Place,
    anchor_lat: float,
    anchor_lng: float,
    preferred_categories: set[str],
    current_day_categories: list[str],
    daily_budget: float,
    require_dining: bool = False,
) -> float:
    """Scores a candidate place based on preferences, proximity, quality, and diversity."""
    # Hard boost or filter for dining slots
    if require_dining:
        if place.category in ("restaurant", "cafe"):
            score = 80.0
        else:
            score = 10.0
    else:
        score = 50.0

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

    # 3. Proximity to current anchor (+30 max, decaying by distance)
    dist = haversine_distance_km(anchor_lat, anchor_lng, place.latitude, place.longitude)
    score += max(0.0, 30.0 - (dist * 1.2))

    # 4. Same-day Category Diversity penalty (-25)
    if place.category in current_day_categories:
        score -= 25.0

    # 5. Cost fit (+10)
    if daily_budget > 0 and place.estimated_cost_max is not None:
        if place.estimated_cost_max <= daily_budget:
            score += 10.0

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

    # 3. Fetch all active POIs within Nueva Ecija
    candidate_places: list[Place] = list(
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

            # Score each candidate relative to current day anchor
            scored_candidates = []
            for p in eligible:
                s = score_place(
                    place=p,
                    anchor_lat=current_anchor_lat,
                    anchor_lng=current_anchor_lng,
                    preferred_categories=preferred_categories,
                    current_day_categories=day_categories,
                    daily_budget=request.daily_budget,
                    require_dining=is_dining_slot,
                )
                scored_candidates.append((s, p))

            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            best_score, chosen_place = scored_candidates[0]

            scheduled_place_ids.add(chosen_place.id)
            day_categories.append(chosen_place.category)

            # Move day anchor toward chosen place for localized proximity chaining
            current_anchor_lat = chosen_place.latitude
            current_anchor_lng = chosen_place.longitude

            if chosen_place.estimated_cost_min is None and chosen_place.estimated_cost_max is None:
                unverified_cost_count += 1

            day_items.append({
                "id": uuid.uuid4(),
                "place_id": chosen_place.id,
                "custom_title": None,
                "custom_lat": None,
                "custom_lng": None,
                "sort_order": slot_idx + 1,
                "planned_time": slot["planned_time"],
                "duration_minutes": slot["duration_minutes"],
                "notes": f"Recommended for {slot['slot_type'].replace('_', ' ')} based on local proximity.",
                "estimated_cost_min": chosen_place.estimated_cost_min,
                "estimated_cost_max": chosen_place.estimated_cost_max,
                "place": chosen_place,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            })

        # Set title reflecting the primary destination of the day
        first_place = day_items[0]["place"] if day_items else None
        day_muni = (
            first_place.municipality.name
            if first_place and first_place.municipality
            else resolved_area
        )
        day_title = f"Day {day_number}: {day_muni} Tour"

        day_id = uuid.uuid4()
        for it in day_items:
            it["day_id"] = day_id

        days_data.append({
            "id": day_id,
            "day_number": day_number,
            "travel_date": travel_date,
            "title": day_title,
            "items": day_items,
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
        )
        db.add(day)
        db.flush()

        for it_data in d_data["items"]:
            item = ItineraryItem(
                id=it_data["id"],
                day_id=day.id,
                place_id=it_data["place_id"],
                custom_title=it_data.get("custom_title"),
                custom_lat=it_data.get("custom_lat"),
                custom_lng=it_data.get("custom_lng"),
                sort_order=it_data["sort_order"],
                planned_time=it_data["planned_time"],
                duration_minutes=it_data["duration_minutes"],
                notes=it_data["notes"],
                estimated_cost_min=it_data["estimated_cost_min"],
                estimated_cost_max=it_data["estimated_cost_max"],
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
