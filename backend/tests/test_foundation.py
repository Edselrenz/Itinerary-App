"""Automated test suite for Steps 1 and 2 (Database, Health, Seeding, and OSM Import)."""

import sys
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
for d in [str(BACKEND_DIR), str(ROOT_DIR)]:
    if d not in sys.path:
        sys.path.insert(0, d)

from app.core.database import Base, get_db
from app.main import app
from app.models.entities import Municipality, Place
from scripts.import_osm import import_osm_payload
from scripts.seed_featured_places import seed_municipalities_and_featured


def make_test_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_health_and_featured_places_pipeline():
    TestingSessionLocal = make_test_session()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # 1. Verify /api/v1/health
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.json()["province_scope"] == "Nueva Ecija"

    # 2. Verify idempotent seeding of municipalities and featured places (12 municipalities, 17 featured places)
    with TestingSessionLocal() as db:
        first_seed = seed_municipalities_and_featured(db)
        assert first_seed["municipalities_created"] == 12
        assert first_seed["featured_places_created"] == 17

        second_seed = seed_municipalities_and_featured(db)
        assert second_seed["municipalities_created"] == 0
        assert second_seed["featured_places_created"] == 0
        assert second_seed["featured_places_updated"] == 17

    # 3. Verify GET /api/v1/municipalities search
    muni_res = client.get("/api/v1/municipalities?q=Cabanatuan")
    assert muni_res.status_code == 200
    assert len(muni_res.json()) == 1
    assert muni_res.json()[0]["slug"] == "cabanatuan-city"

    # 4. Verify GET /api/v1/places featured filter & honest null costs
    places_res = client.get("/api/v1/places?featured=true")
    assert places_res.status_code == 200
    payload = places_res.json()
    assert payload["total"] == 17
    pantabangan = next(p for p in payload["items"] if "Pantabangan Dam" in p["name"])
    assert pantabangan["estimated_cost_min"] is None
    assert pantabangan["estimated_cost_max"] is None
    assert "google.com/maps/dir/" in pantabangan["directions_url"]

    # 5. Verify Figma-featured Bongabon stops exist
    bongabon_res = client.get("/api/v1/places?q=Bongabon")
    assert bongabon_res.status_code == 200
    bongabon_names = [p["name"] for p in bongabon_res.json()["items"]]
    assert any("Rohi Paperflower" in n for n in bongabon_names)
    assert any("La Casa Prime Cabins" in n for n in bongabon_names)
    assert any("Museo de Bongabon" in n for n in bongabon_names)
    assert any("Thornes Samgyupsal" in n for n in bongabon_names)

    # 6. Verify comma-separated and multi-value category query parameter handling
    cat_res = client.get("/api/v1/places?categories=cafe,restaurant")
    assert cat_res.status_code == 200
    for place in cat_res.json()["items"]:
        assert place["category"] in {"cafe", "restaurant"}

    # 7. Verify idempotent OSM import & out-of-province rejection
    sample_osm = {
        "elements": [
            {
                "type": "node",
                "id": 1001,
                "lat": 15.4872,
                "lon": 120.9711,
                "tags": {"name": "Cabanatuan Roastery Cafe", "amenity": "cafe", "addr:city": "Cabanatuan City"},
            },
            {
                "type": "node",
                "id": 1002,
                "lat": 14.5995,  # Manila (outside Nueva Ecija bounds -> must be rejected!)
                "lon": 120.9842,
                "tags": {"name": "Manila Cafe Outside NE", "amenity": "cafe"},
            },
        ]
    }
    with TestingSessionLocal() as db:
        stats1 = import_osm_payload(db, sample_osm, dry_run=False)
        assert stats1["validated"] == 1
        assert stats1["inserted"] == 1
        assert stats1["skipped_out_of_bounds"] == 1

        stats2 = import_osm_payload(db, sample_osm, dry_run=False)
        assert stats2["inserted"] == 0
        assert stats2["updated"] == 1
        total_places = len(db.scalars(select(Place)).all())
        assert total_places == 18  # 17 curated + 1 valid OSM import
