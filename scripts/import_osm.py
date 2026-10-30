#!/usr/bin/env python3
"""Step 2 — Idempotent OpenStreetMap / Overpass POI importer for Nueva Ecija.

Usage:
    python3 scripts/import_osm.py data/raw/nueva_ecija_osm.json --dry-run
    python3 scripts/import_osm.py data/raw/nueva_ecija_osm.json
"""

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend directory to sys.path so scripts can import app.*
BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.entities import Municipality, Place

# Nueva Ecija province bounding box
NE_BOUNDS = {
    "min_lat": 15.15,
    "max_lat": 16.15,
    "min_lng": 120.70,
    "max_lng": 121.40,
}


def is_within_nueva_ecija(lat: float, lng: float) -> bool:
    """Returns True if coordinates fall within Nueva Ecija's bounding box."""
    return (
        NE_BOUNDS["min_lat"] <= lat <= NE_BOUNDS["max_lat"]
        and NE_BOUNDS["min_lng"] <= lng <= NE_BOUNDS["max_lng"]
    )


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Computes great-circle distance in kilometers between two coordinates."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def normalize_name(s: str) -> str:
    """Normalizes municipality and city names for robust fuzzy matching."""
    return (
        s.lower()
        .replace("ñ", "n")
        .replace("city", "")
        .replace("science", "")
        .replace("of", "")
        .replace(".", "")
        .replace("-", " ")
        .strip()
    )


def map_osm_tags_to_category(tags: dict[str, str]) -> str | None:
    """Maps raw OpenStreetMap element tags to one of the 16 canonical MVP categories."""
    amenity = tags.get("amenity")
    tourism = tags.get("tourism")
    leisure = tags.get("leisure")
    historic = tags.get("historic")
    shop = tags.get("shop")
    waterway = tags.get("waterway")
    natural = tags.get("natural")
    public_transport = tags.get("public_transport")

    if amenity == "cafe":
        return "cafe"
    if amenity in {"restaurant", "fast_food", "food_court"}:
        return "restaurant"
    if tourism in {"hotel", "guest_house", "hostel", "motel", "chalet"}:
        return "hotel_accommodation"
    if tourism in {"attraction", "viewpoint"} or historic in {"monument", "memorial", "ruins"}:
        return "tourist_attraction"
    if (
        leisure in {"park", "nature_reserve", "garden"}
        or waterway == "waterfall"
        or natural in {"peak", "spring"}
    ):
        return "nature_park"
    if tourism == "resort" or leisure in {"water_park", "swimming_pool"}:
        return "resort_swimming"
    if amenity == "place_of_worship":
        return "church_religious"
    if tourism in {"museum", "gallery"} or historic == "heritage" or amenity == "arts_centre":
        return "museum_cultural"
    if shop in {"mall", "supermarket", "department_store"} or amenity == "marketplace":
        return "shopping_market"
    if amenity in {"bus_station", "ferry_terminal"} or public_transport in {"station", "stop_area"}:
        return "transport_terminal"
    if amenity in {"hospital", "clinic", "doctors"}:
        return "hospital_clinic"
    if amenity == "pharmacy":
        return "pharmacy"
    if amenity in {"bank", "atm"}:
        return "bank_atm"
    if amenity == "fuel":
        return "fuel_station"
    if shop == "convenience":
        return "convenience_store"
    if amenity in {"townhall", "police", "fire_station", "community_centre", "library"}:
        return "public_facility"
    return None


def resolve_municipality_id(
    tags: dict[str, str],
    lat: float,
    lng: float,
    municipalities: list[Municipality],
) -> object | None:
    """Matches a POI to a seeded Nueva Ecija municipality by addr:city tag or nearest center."""
    if not municipalities:
        return None
    city_tag = (tags.get("addr:city") or tags.get("addr:municipality") or "").strip()
    if city_tag:
        norm_tag = normalize_name(city_tag)
        for m in municipalities:
            norm_m = normalize_name(m.name)
            if norm_m == norm_tag or norm_tag in norm_m or norm_m in norm_tag:
                return m.id
    nearest = min(
        municipalities,
        key=lambda m: haversine_km(lat, lng, m.center_lat, m.center_lng),
    )
    return nearest.id


def import_osm_payload(
    db: Session,
    payload: dict,
    dry_run: bool = False,
) -> dict[str, int]:
    """Validates, deduplicates, and upserts OSM elements into the places table."""
    elements = payload.get("elements", [])
    municipalities = list(db.scalars(select(Municipality)).all())

    seen_source_ids: set[str] = set()
    validated_records: list[dict] = []
    skipped_out_of_bounds = 0
    skipped_unmapped = 0

    for el in elements:
        tags = el.get("tags") or {}
        name = (tags.get("name") or tags.get("name:en") or "").strip()
        lat = el.get("lat") if el.get("lat") is not None else (el.get("center") or {}).get("lat")
        lng = el.get("lon") if el.get("lon") is not None else (el.get("center") or {}).get("lon")
        el_type = el.get("type", "node")
        el_id = el.get("id")

        if not name or lat is None or lng is None or el_id is None:
            skipped_unmapped += 1
            continue

        lat_f, lng_f = float(lat), float(lng)
        if not is_within_nueva_ecija(lat_f, lng_f):
            skipped_out_of_bounds += 1
            continue

        category = map_osm_tags_to_category(tags)
        if not category:
            skipped_unmapped += 1
            continue

        source_record_id = f"{el_type}/{el_id}"
        if source_record_id in seen_source_ids:
            continue
        seen_source_ids.add(source_record_id)

        municipality_id = resolve_municipality_id(tags, lat_f, lng_f, municipalities)
        address_parts = [
            p
            for p in (
                tags.get("addr:housenumber"),
                tags.get("addr:street"),
                tags.get("addr:barangay"),
                tags.get("addr:city"),
            )
            if p
        ]
        address_text = ", ".join(address_parts) if address_parts else tags.get("addr:full")

        validated_records.append(
            {
                "name": name,
                "category": category,
                "latitude": lat_f,
                "longitude": lng_f,
                "municipality_id": municipality_id,
                "address_text": address_text,
                "description": tags.get("description"),
                "phone": tags.get("phone") or tags.get("contact:phone"),
                "website": tags.get("website") or tags.get("contact:website"),
                "opening_hours": tags.get("opening_hours"),
                "source_name": "OpenStreetMap",
                "source_record_id": source_record_id,
                "source_url": f"https://www.openstreetmap.org/{source_record_id}",
                "imported_at": datetime.now(timezone.utc),
                "is_active": True,
                "tags": [category],
            }
        )

    inserted = 0
    updated = 0
    if not dry_run:
        for rec in validated_records:
            existing = db.scalar(
                select(Place).where(
                    Place.source_name == rec["source_name"],
                    Place.source_record_id == rec["source_record_id"],
                )
            )
            if existing:
                existing.name = rec["name"]
                existing.category = rec["category"]
                existing.latitude = rec["latitude"]
                existing.longitude = rec["longitude"]
                existing.municipality_id = rec["municipality_id"]
                existing.address_text = rec["address_text"] or existing.address_text
                existing.phone = rec["phone"] or existing.phone
                existing.website = rec["website"] or existing.website
                existing.opening_hours = rec["opening_hours"] or existing.opening_hours
                existing.imported_at = rec["imported_at"]
                updated += 1
            else:
                db.add(Place(**rec))
                inserted += 1
        db.commit()

    return {
        "validated": len(validated_records),
        "inserted": inserted,
        "updated": updated,
        "skipped_out_of_bounds": skipped_out_of_bounds,
        "skipped_unmapped": skipped_unmapped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Nueva Ecija OSM POIs into PostgreSQL.")
    parser.add_argument("filepath", help="Path to Overpass JSON export file")
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing to DB")
    args = parser.parse_args()

    with open(args.filepath, "r", encoding="utf-8") as f:
        payload = json.load(f)

    with SessionLocal() as db:
        stats = import_osm_payload(db, payload, dry_run=args.dry_run)

    mode = "DRY-RUN" if args.dry_run else "COMMITTED"
    print(f"[{mode}] Nueva Ecija OSM Import Summary: {stats}")


if __name__ == "__main__":
    main()
