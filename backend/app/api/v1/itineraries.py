"""REST endpoints for Traveler Custom Itinerary Builder, Days, Stops, and Reordering.

All endpoints strictly enforce Broken Object Level Authorization (BOLA), ensuring
users can only read, update, delete, or reorder their own itineraries.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.v1.places import serialize_place
from app.core.database import get_db
from app.models.entities import Itinerary, ItineraryDay, ItineraryItem, Place, User
from app.schemas.itinerary import (
    ItineraryCreate,
    ItineraryDayCreate,
    ItineraryDayOut,
    ItineraryItemCreate,
    ItineraryItemOut,
    ItineraryItemUpdate,
    ItineraryOut,
    ItineraryReorderIn,
    ItineraryUpdate,
    RouteComputeRequest,
    RouteComputeResponse,
    SuggestedItineraryRequest,
)
from app.services.auth_service import get_current_user, get_current_user_optional
from app.services.google_maps_service import google_maps_service
from app.algorithms.itinerary_generator import (
    generate_suggested_itinerary_data,
    persist_generated_itinerary,
)

router = APIRouter(prefix="/itineraries", tags=["itineraries"])


def get_eager_itinerary_stmt(itinerary_id: uuid.UUID, user_id: uuid.UUID):
    """Constructs a select query with eager-loaded days, items, and linked POIs."""
    return (
        select(Itinerary)
        .where(Itinerary.id == itinerary_id, Itinerary.user_id == user_id)
        .options(
            selectinload(Itinerary.days)
            .selectinload(ItineraryDay.items)
            .selectinload(ItineraryItem.place)
        )
    )


def serialize_itinerary(itinerary: Itinerary) -> ItineraryOut:
    """Converts an Itinerary ORM entity into a serialized ItineraryOut schema with GIS routing fields."""
    sorted_days = sorted(itinerary.days, key=lambda d: d.day_number)
    days_out: list[ItineraryDayOut] = []

    for day in sorted_days:
        sorted_items = sorted(day.items, key=lambda i: i.sort_order)
        items_out: list[ItineraryItemOut] = []

        for item in sorted_items:
            items_out.append(
                ItineraryItemOut(
                    id=item.id,
                    day_id=item.day_id,
                    place_id=item.place_id,
                    custom_title=item.custom_title,
                    custom_lat=item.custom_lat,
                    custom_lng=item.custom_lng,
                    sort_order=item.sort_order,
                    planned_time=item.planned_time,
                    duration_minutes=item.duration_minutes,
                    notes=item.notes,
                    estimated_cost_min=(
                        float(item.estimated_cost_min)
                        if item.estimated_cost_min is not None
                        else None
                    ),
                    estimated_cost_max=(
                        float(item.estimated_cost_max)
                        if item.estimated_cost_max is not None
                        else None
                    ),
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    place=serialize_place(item.place) if item.place else None,
                    google_place_id=item.google_place_id,
                    travel_mode_from_prev=item.travel_mode_from_prev,
                    travel_distance_meters=item.travel_distance_meters,
                    travel_duration_seconds=item.travel_duration_seconds,
                    route_polyline_from_prev=item.route_polyline_from_prev,
                )
            )

        days_out.append(
            ItineraryDayOut(
                id=day.id,
                itinerary_id=day.itinerary_id,
                day_number=day.day_number,
                travel_date=day.travel_date,
                title=day.title,
                items=items_out,
                day_overview_polyline=day.day_overview_polyline,
                total_distance_meters=day.total_distance_meters,
                total_travel_duration_seconds=day.total_travel_duration_seconds,
                route_legs=day.route_legs or [],
            )
        )

    return ItineraryOut(
        id=itinerary.id,
        user_id=itinerary.user_id,
        title=itinerary.title,
        destination=itinerary.destination,
        start_date=itinerary.start_date,
        end_date=itinerary.end_date,
        daily_budget=float(itinerary.daily_budget),
        preferences=itinerary.preferences,
        type=itinerary.type,
        assumptions=itinerary.assumptions,
        created_at=itinerary.created_at,
        updated_at=itinerary.updated_at,
        days=days_out,
    )


@router.post("/suggest", response_model=ItineraryOut, status_code=status.HTTP_200_OK)
def suggest_itinerary(
    payload: SuggestedItineraryRequest,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> ItineraryOut:
    """Generates an algorithmic, geographically clustered suggested itinerary draft with transparent assumptions."""
    try:
        user_id = current_user.id if current_user else None
        data = generate_suggested_itinerary_data(db=db, request=payload, user_id=user_id)

        if payload.save_immediately and current_user:
            persisted = persist_generated_itinerary(db=db, data=data, user_id=current_user.id)
            return serialize_itinerary(persisted)

        days_out: list[ItineraryDayOut] = []
        for d in data["days"]:
            items_out: list[ItineraryItemOut] = []
            for item in d["items"]:
                items_out.append(
                    ItineraryItemOut(
                        id=item["id"],
                        day_id=d["id"],
                        place_id=item["place_id"],
                        custom_title=item.get("custom_title"),
                        custom_lat=item.get("custom_lat"),
                        custom_lng=item.get("custom_lng"),
                        sort_order=item["sort_order"],
                        planned_time=item["planned_time"],
                        duration_minutes=item["duration_minutes"],
                        notes=item["notes"],
                        estimated_cost_min=item["estimated_cost_min"],
                        estimated_cost_max=item["estimated_cost_max"],
                        created_at=item["created_at"],
                        updated_at=item["updated_at"],
                        place=serialize_place(item["place"]) if item.get("place") else None,
                        google_place_id=item.get("google_place_id"),
                        travel_mode_from_prev=item.get("travel_mode_from_prev", "DRIVE"),
                        travel_distance_meters=item.get("travel_distance_meters"),
                        travel_duration_seconds=item.get("travel_duration_seconds"),
                        route_polyline_from_prev=item.get("route_polyline_from_prev"),
                    )
                )
            days_out.append(
                ItineraryDayOut(
                    id=d["id"],
                    itinerary_id=data["id"],
                    day_number=d["day_number"],
                    travel_date=d["travel_date"],
                    title=d["title"],
                    items=items_out,
                    day_overview_polyline=d.get("day_overview_polyline"),
                    total_distance_meters=d.get("total_distance_meters"),
                    total_travel_duration_seconds=d.get("total_travel_duration_seconds"),
                    route_legs=d.get("route_legs", []),
                )
            )

        return ItineraryOut(
            id=data["id"],
            user_id=user_id,
            title=data["title"],
            destination=data["destination"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            daily_budget=float(data["daily_budget"]),
            preferences=data["preferences"],
            type="suggested",
            assumptions=data["assumptions"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            days=days_out,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


def resolve_or_upsert_item_place(
    db: Session, item_payload: ItineraryItemCreate
) -> tuple[uuid.UUID | None, str | None]:
    """Safely resolves place_id and google_place_id for an item, upserting when appropriate."""
    place_id = item_payload.place_id
    google_place_id = item_payload.google_place_id

    # 1. Existing place by UUID
    if place_id:
        existing = db.get(Place, place_id)
        if existing:
            return existing.id, existing.google_place_id or (str(google_place_id) if google_place_id else None)

    # 2. Existing place by google_place_id
    if google_place_id:
        existing_g = db.scalar(select(Place).where(Place.google_place_id == str(google_place_id)))
        if existing_g:
            return existing_g.id, str(google_place_id)

    # 3. Payload provided
    if item_payload.place_payload:
        upserted = google_maps_service.upsert_google_place_to_db(db, item_payload.place_payload)
        return upserted.id, upserted.google_place_id or (str(google_place_id) if google_place_id else None)

    # 4. google_place_id provided without payload -> fetch details and upsert
    if google_place_id:
        details = google_maps_service.fetch_place_details(db, str(google_place_id))
        if details:
            upserted = google_maps_service.upsert_google_place_to_db(db, details)
            return upserted.id, str(google_place_id)

    return None, str(google_place_id) if google_place_id else None


@router.post("", response_model=ItineraryOut, status_code=status.HTTP_201_CREATED)
def create_itinerary(
    payload: ItineraryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItineraryOut:
    """Creates a new multi-day custom travel itinerary owned by the authenticated traveler."""
    # Validate place_id existence for explicit UUIDs that do not provide fallback google_place_id or place_payload
    missing_place_ids: list[str] = []
    for day in payload.days:
        for item in day.items:
            if item.place_id is not None and not item.google_place_id and not item.place_payload:
                existing = db.get(Place, item.place_id)
                if not existing:
                    missing_place_ids.append(str(item.place_id))
    if missing_place_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The following place IDs do not exist: {missing_place_ids}",
        )

    itinerary = Itinerary(
        user_id=current_user.id,
        title=payload.title,
        destination=payload.destination,
        start_date=payload.start_date,
        end_date=payload.end_date,
        daily_budget=payload.daily_budget,
        preferences=payload.preferences,
        type=payload.type,
        assumptions=payload.assumptions,
    )
    db.add(itinerary)
    db.flush()

    for day_payload in payload.days:
        day = ItineraryDay(
            itinerary_id=itinerary.id,
            day_number=day_payload.day_number,
            travel_date=day_payload.travel_date,
            title=day_payload.title,
        )
        db.add(day)
        db.flush()

        for item_payload in day_payload.items:
            resolved_pid, resolved_gid = resolve_or_upsert_item_place(db, item_payload)
            item = ItineraryItem(
                day_id=day.id,
                place_id=resolved_pid,
                google_place_id=resolved_gid,
                custom_title=item_payload.custom_title,
                custom_lat=item_payload.custom_lat,
                custom_lng=item_payload.custom_lng,
                sort_order=item_payload.sort_order,
                planned_time=item_payload.planned_time,
                duration_minutes=item_payload.duration_minutes,
                notes=item_payload.notes,
                estimated_cost_min=item_payload.estimated_cost_min,
                estimated_cost_max=item_payload.estimated_cost_max,
                travel_mode_from_prev=item_payload.travel_mode_from_prev or "DRIVE",
                travel_distance_meters=item_payload.travel_distance_meters,
                travel_duration_seconds=item_payload.travel_duration_seconds,
                route_polyline_from_prev=item_payload.route_polyline_from_prev,
            )
            db.add(item)

    db.commit()

    loaded = db.scalar(get_eager_itinerary_stmt(itinerary.id, current_user.id))
    return serialize_itinerary(loaded)


@router.get("", response_model=list[ItineraryOut])
def list_itineraries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ItineraryOut]:
    """Lists all travel itineraries owned by the current traveler, sorted by newest first."""
    stmt = (
        select(Itinerary)
        .where(Itinerary.user_id == current_user.id)
        .order_by(Itinerary.created_at.desc())
        .options(
            selectinload(Itinerary.days)
            .selectinload(ItineraryDay.items)
            .selectinload(ItineraryItem.place)
        )
    )
    itineraries = db.scalars(stmt).all()
    return [serialize_itinerary(i) for i in itineraries]


@router.get("/{itinerary_id}", response_model=ItineraryOut)
def get_itinerary(
    itinerary_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItineraryOut:
    """Retrieves full details for an itinerary. Enforces strict BOLA protection."""
    itinerary = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Itinerary not found",
        )
    return serialize_itinerary(itinerary)


@router.patch("/{itinerary_id}", response_model=ItineraryOut)
def update_itinerary(
    itinerary_id: uuid.UUID,
    payload: ItineraryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItineraryOut:
    """Updates itinerary metadata (title, dates, budget). Enforces strict BOLA protection."""
    itinerary = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Itinerary not found",
        )

    if payload.title is not None:
        itinerary.title = payload.title
    if payload.destination is not None:
        itinerary.destination = payload.destination
    if payload.start_date is not None:
        itinerary.start_date = payload.start_date
    if payload.end_date is not None:
        itinerary.end_date = payload.end_date
    if payload.daily_budget is not None:
        itinerary.daily_budget = payload.daily_budget
    if payload.preferences is not None:
        itinerary.preferences = payload.preferences
    if payload.assumptions is not None:
        itinerary.assumptions = payload.assumptions

    if itinerary.end_date < itinerary.start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date cannot be earlier than start_date",
        )

    if payload.days is not None:
        # Clear existing days (cascade will delete orphan days and items)
        itinerary.days.clear()
        db.flush()

        for day_payload in payload.days:
            day = ItineraryDay(
                itinerary_id=itinerary.id,
                day_number=day_payload.day_number,
                travel_date=day_payload.travel_date,
                title=day_payload.title,
            )
            db.add(day)
            db.flush()

            for item_payload in day_payload.items:
                resolved_pid, resolved_gid = resolve_or_upsert_item_place(db, item_payload)
                item = ItineraryItem(
                    day_id=day.id,
                    place_id=resolved_pid,
                    google_place_id=resolved_gid,
                    custom_title=item_payload.custom_title,
                    custom_lat=item_payload.custom_lat,
                    custom_lng=item_payload.custom_lng,
                    sort_order=item_payload.sort_order,
                    planned_time=item_payload.planned_time,
                    duration_minutes=item_payload.duration_minutes,
                    notes=item_payload.notes,
                    estimated_cost_min=item_payload.estimated_cost_min,
                    estimated_cost_max=item_payload.estimated_cost_max,
                    travel_mode_from_prev=item_payload.travel_mode_from_prev or "DRIVE",
                    travel_distance_meters=item_payload.travel_distance_meters,
                    travel_duration_seconds=item_payload.travel_duration_seconds,
                    route_polyline_from_prev=item_payload.route_polyline_from_prev,
                )
                db.add(item)

    db.commit()
    loaded = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
    return serialize_itinerary(loaded)



@router.delete("/{itinerary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_itinerary(
    itinerary_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Deletes an itinerary with all associated days and stops. Enforces strict BOLA protection."""
    itinerary = db.scalar(
        select(Itinerary).where(
            Itinerary.id == itinerary_id, Itinerary.user_id == current_user.id
        )
    )
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Itinerary not found",
        )
    db.delete(itinerary)
    db.commit()


@router.post("/{itinerary_id}/days", response_model=ItineraryOut)
def add_itinerary_day(
    itinerary_id: uuid.UUID,
    payload: ItineraryDayCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItineraryOut:
    """Adds a new calendar day to an itinerary."""
    itinerary = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Itinerary not found",
        )

    existing_day = db.scalar(
        select(ItineraryDay).where(
            ItineraryDay.itinerary_id == itinerary_id,
            ItineraryDay.day_number == payload.day_number,
        )
    )
    if existing_day:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Day {payload.day_number} already exists in this itinerary.",
        )

    day = ItineraryDay(
        itinerary_id=itinerary.id,
        day_number=payload.day_number,
        travel_date=payload.travel_date,
        title=payload.title,
    )
    db.add(day)
    db.commit()

    loaded = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
    return serialize_itinerary(loaded)


@router.post("/{itinerary_id}/days/{day_id}/items", response_model=ItineraryOut)
def add_itinerary_item(
    itinerary_id: uuid.UUID,
    day_id: uuid.UUID,
    payload: ItineraryItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItineraryOut:
    """Adds a stop (POI from database or custom venue) to a scheduled day."""
    itinerary = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Itinerary not found",
        )

    day = db.scalar(
        select(ItineraryDay).where(
            ItineraryDay.id == day_id,
            ItineraryDay.itinerary_id == itinerary_id,
        )
    )
    if not day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Itinerary day not found in this itinerary",
        )

    # Resolve or upsert place
    resolved_pid, resolved_gid = resolve_or_upsert_item_place(db, payload)
    if payload.place_id and not resolved_pid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Place with id '{payload.place_id}' not found.",
        )

    if resolved_pid:
        duplicate = db.scalar(
            select(ItineraryItem).where(
                ItineraryItem.day_id == day_id,
                ItineraryItem.place_id == resolved_pid,
            )
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This destination has already been scheduled for this day.",
            )

    # Automatically compute next sort order if not specified
    max_order = db.scalar(
        select(func.max(ItineraryItem.sort_order)).where(
            ItineraryItem.day_id == day_id
        )
    )
    if max_order is None:
        next_order = 1
    elif payload.sort_order <= 1:
        next_order = max_order + 1
    else:
        next_order = payload.sort_order

    item = ItineraryItem(
        day_id=day.id,
        place_id=resolved_pid,
        google_place_id=resolved_gid,
        custom_title=payload.custom_title,
        custom_lat=payload.custom_lat,
        custom_lng=payload.custom_lng,
        sort_order=next_order,
        planned_time=payload.planned_time,
        duration_minutes=payload.duration_minutes,
        notes=payload.notes,
        estimated_cost_min=payload.estimated_cost_min,
        estimated_cost_max=payload.estimated_cost_max,
        travel_mode_from_prev=payload.travel_mode_from_prev or "DRIVE",
        travel_distance_meters=payload.travel_distance_meters,
        travel_duration_seconds=payload.travel_duration_seconds,
        route_polyline_from_prev=payload.route_polyline_from_prev,
    )
    db.add(item)
    db.commit()

    loaded = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
    return serialize_itinerary(loaded)


@router.patch(
    "/{itinerary_id}/days/{day_id}/items/{item_id}", response_model=ItineraryOut
)
def update_itinerary_item(
    itinerary_id: uuid.UUID,
    day_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: ItineraryItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItineraryOut:
    """Partially updates a specific itinerary stop (notes, planned time, duration, cost, etc.)."""
    itinerary = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Itinerary not found",
        )

    valid_day_ids = {day.id for day in itinerary.days}
    if day_id not in valid_day_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Day not found in this itinerary",
        )

    item = db.scalar(
        select(ItineraryItem).where(
            ItineraryItem.id == item_id,
            ItineraryItem.day_id == day_id,
        )
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Itinerary stop not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(item, field, val)

    from datetime import datetime, timezone
    item.updated_at = datetime.now(timezone.utc)
    itinerary.updated_at = datetime.now(timezone.utc)
    db.commit()

    loaded = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
    return serialize_itinerary(loaded)


@router.delete(
    "/{itinerary_id}/days/{day_id}/items/{item_id}", response_model=ItineraryOut
)
def delete_itinerary_item(
    itinerary_id: uuid.UUID,
    day_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItineraryOut:
    """Removes a stop from an itinerary day and re-compacts sort order."""
    itinerary = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Itinerary not found",
        )

    valid_day_ids = {day.id for day in itinerary.days}
    if day_id not in valid_day_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Day not found in this itinerary",
        )

    item = db.scalar(
        select(ItineraryItem).where(
            ItineraryItem.id == item_id,
            ItineraryItem.day_id == day_id,
        )
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Itinerary stop not found",
        )

    db.delete(item)
    db.flush()

    # Re-compact sort orders for remaining items
    remaining_items = db.scalars(
        select(ItineraryItem)
        .where(ItineraryItem.day_id == day_id)
        .order_by(ItineraryItem.sort_order.asc())
    ).all()

    for idx, rem in enumerate(remaining_items, start=1):
        rem.sort_order = idx

    db.commit()

    loaded = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
    return serialize_itinerary(loaded)


@router.post("/{itinerary_id}/reorder", response_model=ItineraryOut)
def reorder_itinerary_items(
    itinerary_id: uuid.UUID,
    payload: ItineraryReorderIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItineraryOut:
    """Batch reorders stops within or across days. Enforces strict BOLA protection."""
    itinerary = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Itinerary not found",
        )

    valid_day_ids = {day.id for day in itinerary.days}

    for reorder_entry in payload.items:
        if reorder_entry.day_id not in valid_day_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target day {reorder_entry.day_id} does not belong to this itinerary.",
            )

        item = db.scalar(
            select(ItineraryItem).where(ItineraryItem.id == reorder_entry.id)
        )
        if not item or item.day_id not in valid_day_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stop {reorder_entry.id} does not belong to this itinerary.",
            )

        item.day_id = reorder_entry.day_id
        item.sort_order = reorder_entry.sort_order

    db.commit()

    loaded = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
    return serialize_itinerary(loaded)


@router.post("/compute-day-route", response_model=RouteComputeResponse)
def compute_day_route(
    payload: RouteComputeRequest,
    db: Session = Depends(get_db),
) -> RouteComputeResponse:
    """Calculates turn-by-turn route, legs, and encoded polyline for real-time itinerary route preview."""
    route_result = google_maps_service.compute_route(
        db=db,
        origin=payload.origin,
        destination=payload.destination,
        intermediates=payload.intermediates,
        travel_mode=payload.travel_mode,
    )
    return RouteComputeResponse.model_validate(route_result)


@router.post("/{itinerary_id}/days/{day_id}/compute-route", response_model=ItineraryOut)
def compute_and_save_day_route(
    itinerary_id: uuid.UUID,
    day_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItineraryOut:
    """Computes and persists driving routes, overview polyline, and turn legs for all stops in an itinerary day."""
    itinerary = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
    if not itinerary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary not found")

    day = next((d for d in itinerary.days if d.id == day_id), None)
    if not day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Day not found in this itinerary",
        )

    sorted_items = sorted(day.items, key=lambda i: i.sort_order)
    if len(sorted_items) < 2:
        day.day_overview_polyline = None
        day.total_distance_meters = 0
        day.total_travel_duration_seconds = 0
        day.route_legs = []
        db.commit()
        loaded = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
        return serialize_itinerary(loaded)

    def get_stop_coords(item: ItineraryItem) -> tuple[float, float] | None:
        if item.place:
            return float(item.place.latitude), float(item.place.longitude)
        if item.custom_lat is not None and item.custom_lng is not None:
            return float(item.custom_lat), float(item.custom_lng)
        return None

    coords_list = [get_stop_coords(it) for it in sorted_items]
    valid_pairs = [(it, c) for it, c in zip(sorted_items, coords_list) if c is not None]

    if len(valid_pairs) < 2:
        db.commit()
        loaded = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
        return serialize_itinerary(loaded)

    origin = {"latitude": valid_pairs[0][1][0], "longitude": valid_pairs[0][1][1]}
    destination = {"latitude": valid_pairs[-1][1][0], "longitude": valid_pairs[-1][1][1]}
    intermediates = [
        {"latitude": c[0], "longitude": c[1]}
        for _, c in valid_pairs[1:-1]
    ]

    travel_mode = valid_pairs[1][0].travel_mode_from_prev or "DRIVE"
    route_data = google_maps_service.compute_route(
        db=db,
        origin=origin,
        destination=destination,
        intermediates=intermediates,
        travel_mode=travel_mode,
    )

    day.day_overview_polyline = route_data.get("overview_polyline")
    day.total_distance_meters = route_data.get("total_distance_meters", 0)
    day.total_travel_duration_seconds = route_data.get("total_duration_seconds", 0)
    day.route_legs = route_data.get("legs", [])

    legs = route_data.get("legs", [])
    for idx, (item, _) in enumerate(valid_pairs[1:], start=0):
        if idx < len(legs):
            item.travel_distance_meters = legs[idx].get("distance_meters")
            item.travel_duration_seconds = legs[idx].get("duration_seconds")
            item.route_polyline_from_prev = legs[idx].get("polyline")

    from datetime import datetime, timezone
    day.updated_at = datetime.now(timezone.utc)
    itinerary.updated_at = datetime.now(timezone.utc)

    db.commit()
    loaded = db.scalar(get_eager_itinerary_stmt(itinerary_id, current_user.id))
    return serialize_itinerary(loaded)

