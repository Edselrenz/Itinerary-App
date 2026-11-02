#!/usr/bin/env python3
"""Step 2 — Seeds Nueva Ecija cities/municipalities and curated featured destinations.

Includes all key destinations showcased across the Figma UI references:
- Cabanatuan, Gapan, Pantabangan, General Tinio, and Bongabon Day 1 stops.

Usage:
    python3 scripts/seed_featured_places.py
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import Base, SessionLocal, engine
from app.models.entities import Municipality, Place

# Key Nueva Ecija Cities and Municipalities with center coordinates
NUEVA_ECIJA_MUNICIPALITIES = [
    {"name": "Cabanatuan City", "slug": "cabanatuan-city", "is_city": True, "center_lat": 15.4865, "center_lng": 120.9734},
    {"name": "Gapan City", "slug": "gapan-city", "is_city": True, "center_lat": 15.3072, "center_lng": 120.9464},
    {"name": "Science City of Muñoz", "slug": "science-city-of-munoz", "is_city": True, "center_lat": 15.7161, "center_lng": 120.9031},
    {"name": "Palayan City", "slug": "palayan-city", "is_city": True, "center_lat": 15.5415, "center_lng": 121.0848},
    {"name": "San Jose City", "slug": "san-jose-city", "is_city": True, "center_lat": 15.7917, "center_lng": 120.9959},
    {"name": "General Tinio", "slug": "general-tinio", "is_city": False, "center_lat": 15.3490, "center_lng": 121.0490},
    {"name": "Gabaldon", "slug": "gabaldon", "is_city": False, "center_lat": 15.4550, "center_lng": 121.3364},
    {"name": "Pantabangan", "slug": "pantabangan", "is_city": False, "center_lat": 15.8239, "center_lng": 121.1444},
    {"name": "Bongabon", "slug": "bongabon", "is_city": False, "center_lat": 15.6322, "center_lng": 121.1447},
    {"name": "Laur", "slug": "laur", "is_city": False, "center_lat": 15.5869, "center_lng": 121.1833},
    {"name": "Santa Rosa", "slug": "santa-rosa", "is_city": False, "center_lat": 15.4247, "center_lng": 120.9386},
    {"name": "Talavera", "slug": "talavera", "is_city": False, "center_lat": 15.5842, "center_lng": 120.9189},
]

# Curated Featured Destinations across Nueva Ecija aligned with Figma designs
CURATED_FEATURED_PLACES = [
    {
        "name": "Minalungao National Park",
        "category": "nature_park",
        "municipality_slug": "general-tinio",
        "latitude": 15.2981,
        "longitude": 121.1223,
        "address_text": "Brgy. Pias, General Tinio, Nueva Ecija",
        "description": (
            "Protected limestone canyon along the Peñaranda River featuring emerald waters, "
            "bamboo rafting, cave formations, and scenic hanging bridge viewpoints."
        ),
        "opening_hours": "07:00-17:00",
        "estimated_cost_min": 100.0,
        "estimated_cost_max": 500.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/minalungao-national-park",
        "source_url": "https://www.openstreetmap.org/way/238471920",
        "is_featured": True,
        "tags": ["nature_park", "Nature & Parks", "Family-Friendly", "Resort/Swimming"],
    },
    {
        "name": "Pantabangan Dam and Lake Viewpoint",
        "category": "tourist_attraction",
        "municipality_slug": "pantabangan",
        "latitude": 15.8126,
        "longitude": 121.1098,
        "address_text": "Pantabangan, Nueva Ecija",
        "description": (
            "Major reservoir and hydroelectric dam overlooking the Sierra Madre foothills, "
            "popular for sunrise viewing, lakeside sightseeing, and photography."
        ),
        "opening_hours": "06:00-18:00",
        "estimated_cost_min": None,
        "estimated_cost_max": None,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/pantabangan-dam-viewpoint",
        "source_url": "https://www.openstreetmap.org/way/139284711",
        "is_featured": True,
        "tags": ["tourist_attraction", "Nature & Parks", "Family-Friendly"],
    },
    {
        "name": "Saint Nicholas of Tolentine Cathedral & Plaza Lucero",
        "category": "church_religious",
        "municipality_slug": "cabanatuan-city",
        "latitude": 15.4898,
        "longitude": 120.9679,
        "address_text": "Burgos Avenue, Cabanatuan City, Nueva Ecija",
        "description": (
            "Historic seat of the Roman Catholic Diocese of Cabanatuan adjacent to Plaza Lucero, "
            "site of General Antonio Luna's historical marker."
        ),
        "opening_hours": "06:00-19:00",
        "estimated_cost_min": None,
        "estimated_cost_max": None,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/cabanatuan-cathedral-plaza-lucero",
        "source_url": "https://www.openstreetmap.org/way/159283741",
        "is_featured": True,
        "tags": ["church_religious", "Culture & History", "Religious/Cultural Sites", "Family-Friendly"],
    },
    {
        "name": "Dupinga River Eco-Tourism Area",
        "category": "nature_park",
        "municipality_slug": "gabaldon",
        "latitude": 15.4892,
        "longitude": 121.3204,
        "address_text": "Gabaldon, Nueva Ecija",
        "description": (
            "Freshwater mountain river bordered by the Sierra Madre range, known for shallow "
            "picnic rapids and riverside cottages."
        ),
        "opening_hours": "07:00-17:00",
        "estimated_cost_min": 50.0,
        "estimated_cost_max": 350.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/dupinga-river-gabaldon",
        "source_url": "https://www.openstreetmap.org/node/482910384",
        "is_featured": True,
        "tags": ["nature_park", "Nature & Parks", "Resort/Swimming", "Family-Friendly"],
    },
    {
        "name": "CLSU Agricultural Museum & Philippine Carabao Center",
        "category": "museum_cultural",
        "municipality_slug": "science-city-of-munoz",
        "latitude": 15.7325,
        "longitude": 120.9288,
        "address_text": "Central Luzon State University Compound, Science City of Muñoz, Nueva Ecija",
        "description": (
            "Educational agricultural heritage center and dairy showcase highlighting Nueva Ecija's "
            "role as the Rice Granary of the Philippines and fresh carabao milk products."
        ),
        "opening_hours": "08:00-17:00",
        "estimated_cost_min": 50.0,
        "estimated_cost_max": 250.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/clsu-agricultural-museum-pcc",
        "source_url": "https://www.openstreetmap.org/way/301928374",
        "is_featured": True,
        "tags": ["museum_cultural", "Culture & History", "Food Trip", "Family-Friendly"],
    },
    {
        "name": "Lumang Gapan Heritage Street & National Shrine of La Virgen Divina Pastora",
        "category": "church_religious",
        "municipality_slug": "gapan-city",
        "latitude": 15.3065,
        "longitude": 120.9461,
        "address_text": "Gapan City, Nueva Ecija",
        "description": (
            "Brick-and-adobe heritage district and Marian pilgrimage shrine dating back to the "
            "Spanish colonial period."
        ),
        "opening_hours": "06:00-20:00",
        "estimated_cost_min": None,
        "estimated_cost_max": None,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/gapan-divina-pastora-shrine",
        "source_url": "https://www.openstreetmap.org/way/210394857",
        "is_featured": True,
        "tags": ["church_religious", "Culture & History", "Religious/Cultural Sites"],
    },
    {
        "name": "Camp Pangatian War Memorial Shrine",
        "category": "museum_cultural",
        "municipality_slug": "cabanatuan-city",
        "latitude": 15.5122,
        "longitude": 121.0419,
        "address_text": "Brgy. Pangatian, Cabanatuan City, Nueva Ecija",
        "description": (
            "World War II historical memorial commemorating the January 1945 Great Raid that "
            "liberated Allied prisoners of war in Cabanatuan."
        ),
        "opening_hours": "08:00-17:00",
        "estimated_cost_min": 50.0,
        "estimated_cost_max": 100.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/camp-pangatian-memorial-shrine",
        "source_url": "https://www.openstreetmap.org/way/192837465",
        "is_featured": True,
        "tags": ["museum_cultural", "Culture & History", "Family-Friendly"],
    },
    {
        "name": "Edna's Cakeland & Cafe Kapitan",
        "category": "cafe",
        "municipality_slug": "cabanatuan-city",
        "latitude": 15.4884,
        "longitude": 120.9692,
        "address_text": "Don Manuel B. Tinio St., Cabanatuan City, Nueva Ecija",
        "description": (
            "Well-known homegrown Cabanatuan bakery and cafe serving local pastries, cakes, "
            "and kapeng barako blends."
        ),
        "opening_hours": "08:00-20:00",
        "estimated_cost_min": 150.0,
        "estimated_cost_max": 450.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/ednas-cakeland-cabanatuan",
        "source_url": "https://www.openstreetmap.org/node/592837461",
        "is_featured": True,
        "tags": ["cafe", "Cafes", "Food Trip", "Family-Friendly"],
    },
    # --- Figma-Showcased Featured Venues ---
    {
        "name": "Rohi Paperflower Cafe",
        "category": "cafe",
        "municipality_slug": "bongabon",
        "latitude": 15.6315,
        "longitude": 121.1438,
        "address_text": "Bongabon, Nueva Ecija",
        "description": (
            "Popular botanical cafe in Bongabon known for picturesque paperflower decor, "
            "artisanal handcrafted coffee, and Filipino pasta dishes."
        ),
        "opening_hours": "09:00-20:00",
        "estimated_cost_min": 150.0,
        "estimated_cost_max": 400.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/rohi-paperflower-cafe",
        "source_url": "https://www.openstreetmap.org/node/998273641",
        "is_featured": True,
        "tags": ["cafe", "Cafes", "Food Trip"],
    },
    {
        "name": "Museo de Bongabon",
        "category": "museum_cultural",
        "municipality_slug": "bongabon",
        "latitude": 15.6330,
        "longitude": 121.1455,
        "address_text": "Town Hall Compound, Bongabon, Nueva Ecija",
        "description": (
            "Town cultural museum showcasing Bongabon's onion-capital agricultural history, "
            "colonial artifacts, and local heritage."
        ),
        "opening_hours": "08:00-17:00",
        "estimated_cost_min": None,
        "estimated_cost_max": None,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/museo-de-bongabon",
        "source_url": "https://www.openstreetmap.org/way/882736412",
        "is_featured": True,
        "tags": ["museum_cultural", "Culture & History", "Family-Friendly"],
    },
    {
        "name": "La Casa Prime Cabins",
        "category": "hotel_accommodation",
        "municipality_slug": "bongabon",
        "latitude": 15.6280,
        "longitude": 121.1520,
        "address_text": "Brgy. Vega, Bongabon, Nueva Ecija",
        "description": (
            "Peaceful mountain-view A-frame cabins and staycation retreat situated at the foot "
            "of the Sierra Madre mountain range."
        ),
        "opening_hours": "24/7",
        "estimated_cost_min": 2500.0,
        "estimated_cost_max": 5500.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/la-casa-prime-cabins",
        "source_url": "https://www.openstreetmap.org/way/882736415",
        "is_featured": True,
        "tags": ["hotel_accommodation", "Resort/Swimming", "Family-Friendly"],
    },
    {
        "name": "Thornes Samgyupsal House",
        "category": "restaurant",
        "municipality_slug": "bongabon",
        "latitude": 15.6328,
        "longitude": 121.1460,
        "address_text": "Poblacion, Bongabon, Nueva Ecija",
        "description": (
            "Popular casual grill restaurant in Bongabon offering Korean-style BBQ, unlimited pork, "
            "and traditional side dishes."
        ),
        "opening_hours": "11:00-21:00",
        "estimated_cost_min": 299.0,
        "estimated_cost_max": 499.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/thornes-samgyupsal-house",
        "source_url": "https://www.openstreetmap.org/node/998273645",
        "is_featured": True,
        "tags": ["restaurant", "Food Trip"],
    },
    {
        "name": "George Point Viewdeck & Resto",
        "category": "tourist_attraction",
        "municipality_slug": "pantabangan",
        "latitude": 15.8205,
        "longitude": 121.1350,
        "address_text": "Pantabangan Lake Overlook, Pantabangan, Nueva Ecija",
        "description": (
            "Elevated lakeside scenic viewpoint and open-air restaurant offering 360-degree vistas "
            "of Pantabangan Lake and surrounding rolling mountains."
        ),
        "opening_hours": "07:00-19:00",
        "estimated_cost_min": 200.0,
        "estimated_cost_max": 600.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/george-point-pantabangan",
        "source_url": "https://www.openstreetmap.org/node/998273648",
        "is_featured": True,
        "tags": ["tourist_attraction", "Nature & Parks", "Food Trip"],
    },
    {
        "name": "Highland Bali Villas Resort and Spa",
        "category": "resort_swimming",
        "municipality_slug": "pantabangan",
        "latitude": 15.8270,
        "longitude": 121.1415,
        "address_text": "Pantabangan, Nueva Ecija",
        "description": (
            "Bali-inspired luxury hillside resort featuring infinity pools, water sports on Pantabangan Lake, "
            "spas, and Balinese architecture."
        ),
        "opening_hours": "24/7",
        "estimated_cost_min": 3500.0,
        "estimated_cost_max": 9500.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/highland-bali-villas-pantabangan",
        "source_url": "https://www.openstreetmap.org/way/882736420",
        "is_featured": True,
        "tags": ["resort_swimming", "hotel_accommodation", "Family-Friendly"],
    },
    {
        "name": "Farm Villaronte",
        "category": "tourist_attraction",
        "municipality_slug": "cabanatuan-city",
        "latitude": 15.5020,
        "longitude": 121.0150,
        "address_text": "Cabanatuan City, Nueva Ecija",
        "description": (
            "Eco-tourism and family farm destination featuring lush outdoor picnic spaces, gardens, "
            "and nature recreation."
        ),
        "opening_hours": "08:00-17:00",
        "estimated_cost_min": 100.0,
        "estimated_cost_max": 300.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/farm-villaronte-cabanatuan",
        "source_url": "https://www.openstreetmap.org/node/998273650",
        "is_featured": True,
        "tags": ["tourist_attraction", "Nature & Parks", "Family-Friendly"],
    },
    {
        "name": "Casa Batik",
        "category": "restaurant",
        "municipality_slug": "cabanatuan-city",
        "latitude": 15.4850,
        "longitude": 120.9710,
        "address_text": "Cabanatuan City, Nueva Ecija",
        "description": (
            "Artisan garden restaurant and cafe serving signature regional Central Luzon dishes "
            "and specialty refreshments."
        ),
        "opening_hours": "10:00-21:00",
        "estimated_cost_min": 250.0,
        "estimated_cost_max": 650.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/casa-batik-cabanatuan",
        "source_url": "https://www.openstreetmap.org/node/998273652",
        "is_featured": True,
        "tags": ["restaurant", "Food Trip"],
    },
    {
        "name": "Lake Farm De La Marre",
        "category": "resort_swimming",
        "municipality_slug": "pantabangan",
        "latitude": 15.8310,
        "longitude": 121.1380,
        "address_text": "Pantabangan, Nueva Ecija",
        "description": (
            "Lakeside agri-resort and glamping grounds offering water activities, mountain views, "
            "and sustainable farm visits."
        ),
        "opening_hours": "08:00-18:00",
        "estimated_cost_min": 500.0,
        "estimated_cost_max": 2500.0,
        "source_name": "CuratedNuevaEcijaMVP",
        "source_record_id": "curated/lake-farm-de-la-marre",
        "source_url": "https://www.openstreetmap.org/node/998273655",
        "is_featured": True,
        "tags": ["resort_swimming", "nature_park", "Family-Friendly"],
    },
]


def seed_municipalities_and_featured(db: Session) -> dict[str, int]:
    """Idempotently upserts Nueva Ecija municipalities and curated featured POIs."""
    muni_map: dict[str, Municipality] = {}
    muni_created = 0

    # CR-013: Batch fetch existing municipalities to avoid per-row SELECT queries
    existing_munis = {
        m.slug: m
        for m in db.scalars(
            select(Municipality).where(
                Municipality.slug.in_([m["slug"] for m in NUEVA_ECIJA_MUNICIPALITIES])
            )
        ).all()
    }

    for m in NUEVA_ECIJA_MUNICIPALITIES:
        existing = existing_munis.get(m["slug"])
        if existing:
            existing.name = m["name"]
            existing.is_city = m["is_city"]
            existing.center_lat = m["center_lat"]
            existing.center_lng = m["center_lng"]
            muni_map[m["slug"]] = existing
        else:
            obj = Municipality(**m)
            db.add(obj)
            db.flush()
            muni_map[m["slug"]] = obj
            muni_created += 1

    now = datetime.now(timezone.utc)
    places_created = 0
    places_updated = 0

    # CR-013: Batch fetch existing curated places using source_record_id in_()
    curated_source_ids = [item["source_record_id"] for item in CURATED_FEATURED_PLACES]
    existing_places_map = {
        p.source_record_id: p
        for p in db.scalars(
            select(Place).where(
                Place.source_name == "CuratedNuevaEcijaMVP",
                Place.source_record_id.in_(curated_source_ids),
            )
        ).all()
    }

    for item in CURATED_FEATURED_PLACES:
        muni = muni_map.get(item["municipality_slug"])
        existing_place = existing_places_map.get(item["source_record_id"])
        payload = {
            "name": item["name"],
            "category": item["category"],
            "latitude": item["latitude"],
            "longitude": item["longitude"],
            "municipality_id": muni.id if muni else None,
            "address_text": item["address_text"],
            "description": item["description"],
            "opening_hours": item["opening_hours"],
            "estimated_cost_min": item["estimated_cost_min"],
            "estimated_cost_max": item["estimated_cost_max"],
            "cost_currency": "PHP",
            "source_name": item["source_name"],
            "source_record_id": item["source_record_id"],
            "source_url": item["source_url"],
            "imported_at": now,
            "verified_at": now,
            "is_featured": item["is_featured"],
            "is_active": True,
            "tags": item["tags"],
        }
        if existing_place:
            for k, v in payload.items():
                setattr(existing_place, k, v)
            places_updated += 1
        else:
            db.add(Place(**payload))
            places_created += 1

    db.commit()
    return {
        "municipalities_total": len(muni_map),
        "municipalities_created": muni_created,
        "featured_places_created": places_created,
        "featured_places_updated": places_updated,
    }


def main() -> None:
    # Ensure all tables exist before seeding (supports SQLite and PostgreSQL)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        summary = seed_municipalities_and_featured(db)
    print(f"[SEED COMPLETE] {summary}")


if __name__ == "__main__":
    main()
