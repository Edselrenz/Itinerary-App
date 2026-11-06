"""REST endpoints for Nueva Ecija municipalities and POI search/filtering."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload
from app.core.config import settings
from app.core.database import get_db
from app.models.entities import Municipality, Place
from app.schemas.place import (
    LivePlaceSearchRequest,
    LivePlaceSearchResponse,
    MunicipalityOut,
    PaginatedPlacesOut,
    PlaceOut,
)
from app.services.google_maps_service import google_maps_service

router = APIRouter(tags=["places"])

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


def escape_like(query: str) -> str:
    """Escapes SQL LIKE / ILIKE wildcard characters (% and _) as well as backslashes."""
    return query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def serialize_place(place: Place) -> PlaceOut:
    """Converts a Place ORM instance into a PlaceOut response with external Google Maps URL and GIS fields."""
    return PlaceOut(
        id=place.id,
        name=place.name,
        category=place.category,
        latitude=place.latitude,
        longitude=place.longitude,
        municipality_id=place.municipality_id,
        municipality_name=place.municipality.name if place.municipality else None,
        address_text=place.address_text,
        description=place.description,
        phone=place.phone,
        website=place.website,
        opening_hours=place.opening_hours,
        estimated_cost_min=(
            float(place.estimated_cost_min) if place.estimated_cost_min is not None else None
        ),
        estimated_cost_max=(
            float(place.estimated_cost_max) if place.estimated_cost_max is not None else None
        ),
        cost_currency=place.cost_currency,
        image_url=place.image_url,
        image_license=place.image_license,
        source_name=place.source_name,
        source_record_id=place.source_record_id,
        source_url=place.source_url,
        imported_at=place.imported_at,
        verified_at=place.verified_at,
        is_featured=place.is_featured,
        tags=place.tags or [],
        directions_url=(
            place.google_maps_uri
            or f"https://www.google.com/maps/dir/?api=1&destination={place.latitude},{place.longitude}"
        ),
        google_place_id=place.google_place_id,
        google_types=place.google_types or [],
        editorial_summary=place.editorial_summary,
        regular_opening_hours=place.regular_opening_hours,
        rating=place.rating,
        user_rating_count=place.user_rating_count,
        price_level=place.price_level,
        photos=place.photos or [],
        reviews=place.reviews or [],
        business_status=place.business_status,
        google_maps_uri=place.google_maps_uri,
        details_cached_at=place.details_cached_at,
    )


@router.get("/municipalities", response_model=list[MunicipalityOut])
def list_municipalities(
    q: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
) -> list[Municipality]:
    """Returns searchable Nueva Ecija cities and municipalities."""
    stmt = select(Municipality)
    if q and q.strip():
        safe_q = escape_like(q.strip())
        stmt = stmt.where(Municipality.name.ilike(f"%{safe_q}%"))
    stmt = stmt.order_by(Municipality.is_city.desc(), Municipality.name.asc())
    return list(db.scalars(stmt).all())


@router.get("/places", response_model=PaginatedPlacesOut)
def list_places(
    q: str | None = Query(default=None, max_length=100),
    categories: list[str] | None = Query(default=None),
    municipality_id: uuid.UUID | None = Query(default=None),
    featured: bool | None = Query(default=None),
    min_lat: float | None = Query(default=None),
    max_lat: float | None = Query(default=None),
    min_lng: float | None = Query(default=None),
    max_lng: float | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PaginatedPlacesOut:
    """Searches and filters active Nueva Ecija POIs for Home search and Map bounds."""
    stmt = (
        select(Place)
        .outerjoin(Municipality, Place.municipality_id == Municipality.id)
        .options(joinedload(Place.municipality))
        .where(Place.is_active.is_(True))
    )

    if q and q.strip():
        safe_q = escape_like(q.strip())
        pattern = f"%{safe_q}%"
        stmt = stmt.where(
            or_(
                Place.name.ilike(pattern),
                Place.address_text.ilike(pattern),
                Place.category.ilike(pattern),
                Municipality.name.ilike(pattern),
            )
        )

    if categories:
        # Support both repeated params (?categories=a&categories=b) and comma-separated (?categories=a,b)
        flat_categories: list[str] = []
        for item in categories:
            flat_categories.extend([c.strip() for c in item.split(",") if c.strip()])

        invalid = [c for c in flat_categories if c not in CANONICAL_CATEGORIES]
        if invalid:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported category filter(s): {', '.join(invalid)}",
            )
        stmt = stmt.where(Place.category.in_(flat_categories))

    if municipality_id is not None:
        stmt = stmt.where(Place.municipality_id == municipality_id)

    if featured is not None:
        stmt = stmt.where(Place.is_featured.is_(featured))

    if None not in (min_lat, max_lat, min_lng, max_lng):
        stmt = stmt.where(
            Place.latitude.between(min_lat, max_lat),
            Place.longitude.between(min_lng, max_lng),
        )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    rows = (
        db.scalars(
            stmt.order_by(Place.is_featured.desc(), Place.name.asc())
            .limit(limit)
            .offset(offset)
        )
        .unique()
        .all()
    )

    return PaginatedPlacesOut(
        total=total,
        limit=limit,
        offset=offset,
        items=[serialize_place(p) for p in rows],
    )


@router.get("/places/{place_id}", response_model=PlaceOut)
def get_place_detail(
    place_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> PlaceOut:
    """Returns full details and verification provenance for one Nueva Ecija POI."""
    stmt = (
        select(Place)
        .options(joinedload(Place.municipality))
        .where(Place.id == place_id, Place.is_active.is_(True))
    )
    place = db.scalar(stmt)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return serialize_place(place)


@router.post("/places/discover", response_model=LivePlaceSearchResponse)
def discover_places(
    payload: LivePlaceSearchRequest,
    db: Session = Depends(get_db),
) -> LivePlaceSearchResponse:
    """Performs live Google Places (New) or cached/local POI discovery for Nueva Ecija."""
    bias = None
    if payload.latitude is not None and payload.longitude is not None:
        bias = {
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "radius_meters": payload.radius_meters or 50000.0,
        }

    places_dict, source = google_maps_service.search_places_text(
        db=db,
        query=payload.query,
        location_bias=bias,
        included_types=payload.included_types,
        min_rating=payload.min_rating,
        open_now=payload.open_now,
    )

    return LivePlaceSearchResponse(
        places=[PlaceOut.model_validate(p) for p in places_dict],
        source=source,
        total=len(places_dict),
    )


@router.get("/places/google/{google_place_id}", response_model=PlaceOut)
def get_google_place_detail(
    google_place_id: str,
    db: Session = Depends(get_db),
) -> PlaceOut:
    """Fetches rich Atmosphere details for a Google Place, caching per Google ToS."""
    data = google_maps_service.fetch_place_details(db, google_place_id)
    if not data:
        raise HTTPException(status_code=404, detail="Google Place details not found")
    return PlaceOut.model_validate(data)


@router.get("/places/photos/{photo_name:path}")
def get_place_photo(photo_name: str) -> Response:
    """Proxies Google Places photo media to protect Google Maps API key from frontend leakage."""
    api_key = settings.google_maps_api_key
    if not api_key:
        return Response(
            content='<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>',
            media_type="image/svg+xml",
        )

    url = f"https://places.googleapis.com/v1/{photo_name}/media?maxHeightPx=800&maxWidthPx=1200&key={api_key}"
    try:
        import httpx

        resp = httpx.get(url, timeout=6.0)
        if resp.status_code == 200:
            return Response(
                content=resp.content,
                media_type=resp.headers.get("content-type", "image/jpeg"),
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception:
        pass

    return Response(
        content='<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>',
        media_type="image/svg+xml",
    )
