"""Unit and integration tests for GoogleMapsService, GIS routing, and place discovery."""

import sys
import uuid
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
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
from app.services.google_maps_service import (
    decode_polyline,
    encode_polyline,
    google_maps_service,
    haversine_distance_meters,
    map_google_type_to_category,
    normalize_google_place,
    parse_duration_seconds,
)


def make_test_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_polyline_utilities():
    coords = [
        (15.4859, 120.9669),
        (15.5414, 121.0844),
        (15.7167, 121.0500),
    ]
    encoded = encode_polyline(coords)
    assert isinstance(encoded, str)
    assert len(encoded) > 0

    decoded = decode_polyline(encoded)
    assert len(decoded) == 3
    for orig, dec in zip(coords, decoded):
        assert abs(orig[0] - dec[0]) < 1e-4
        assert abs(orig[1] - dec[1]) < 1e-4


def test_haversine_and_duration_helpers():
    # Cabanatuan to Palayan is approx 14km
    dist = haversine_distance_meters(15.4859, 120.9669, 15.5414, 121.0844)
    assert 13000 < dist < 16000

    # Same coordinates should return 0
    assert haversine_distance_meters(15.0, 120.0, 15.0, 120.0) == 0.0

    # Duration parsing
    assert parse_duration_seconds("3600s") == 3600
    assert parse_duration_seconds(120) == 120
    assert parse_duration_seconds("45.5s") == 45
    assert parse_duration_seconds(None) == 0


def test_map_google_type_to_category():
    assert map_google_type_to_category(["cafe", "food"]) == "cafe"
    assert map_google_type_to_category(["hotel", "lodging"]) == "hotel_accommodation"
    assert map_google_type_to_category(["national_park"]) == "nature_park"
    assert map_google_type_to_category(["church", "place_of_worship"]) == "church_religious"
    assert map_google_type_to_category(["museum"]) == "museum_cultural"
    assert map_google_type_to_category(["shopping_mall"]) == "shopping_market"
    assert map_google_type_to_category(["unknown_xyz"]) == "tourist_attraction"


def test_normalize_google_place():
    raw = {
        "id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
        "displayName": {"text": "Googleplex"},
        "formattedAddress": "1600 Amphitheatre Pkwy, Mountain View, CA 94043",
        "location": {"latitude": 37.422, "longitude": -122.084},
        "types": ["tourist_attraction", "point_of_interest"],
        "rating": 4.5,
        "userRatingCount": 1200,
        "editorialSummary": {"text": "Headquarters of Google."},
    }
    normalized = normalize_google_place(raw)
    assert normalized["name"] == "Googleplex"
    assert normalized["latitude"] == 37.422
    assert normalized["longitude"] == -122.084
    assert normalized["category"] == "tourist_attraction"
    assert normalized["rating"] == 4.5
    assert normalized["google_place_id"] == "ChIJN1t_tDeuEmsRUsoyG83frY4"
    assert normalized["editorial_summary"] == "Headquarters of Google."


def test_google_maps_service_db_integration():
    TestingSessionLocal = make_test_session()
    db = TestingSessionLocal()

    # Seed Municipality
    muni = Municipality(
        name="Cabanatuan City",
        slug="cabanatuan-city",
        is_city=True,
        center_lat=15.4859,
        center_lng=120.9669,
    )
    db.add(muni)
    db.commit()

    # Seed Place
    place = Place(
        name="Plaza Lucero Park",
        category="nature_park",
        latitude=15.4880,
        longitude=120.9690,
        municipality_id=muni.id,
        source_name="OpenStreetMap",
        source_record_id="node/12345",
        is_active=True,
    )
    db.add(place)
    db.commit()

    # Test local DB search fallback when no key is set
    results, source = google_maps_service.search_places_text(db=db, query="Plaza")
    assert len(results) >= 1
    assert results[0]["name"] == "Plaza Lucero Park"
    assert source == "local_db"

    # Test place upsert helper
    place_payload = {
        "google_place_id": "google-test-id-999",
        "name": "Live Cafe Nueva Ecija",
        "category": "cafe",
        "latitude": 15.4900,
        "longitude": 120.9700,
        "address_text": "Cabanatuan Highway",
        "rating": 4.8,
        "google_types": ["cafe", "food"],
    }
    upserted = google_maps_service.upsert_google_place_to_db(db, place_payload)
    assert upserted.id is not None
    assert upserted.name == "Live Cafe Nueva Ecija"
    assert upserted.municipality_id == muni.id
    assert upserted.google_place_id == "google-test-id-999"

    # Test route computation fallback
    origin = {"latitude": 15.4859, "longitude": 120.9669}
    destination = {"latitude": 15.5414, "longitude": 121.0844}
    route = google_maps_service.compute_route(
        db=db,
        origin=origin,
        destination=destination,
        intermediates=[],
        travel_mode="DRIVE",
    )
    assert "overview_polyline" in route
    assert route["total_distance_meters"] > 0
    assert route["total_duration_seconds"] > 0
    assert len(route["legs"]) == 1
    assert route["source"] in {"haversine_direct", "osrm"}
    db.close()


def test_endpoints_discover_and_route():
    TestingSessionLocal = make_test_session()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    db = TestingSessionLocal()
    muni = Municipality(
        name="Cabanatuan City",
        slug="cabanatuan-city",
        is_city=True,
        center_lat=15.4859,
        center_lng=120.9669,
    )
    db.add(muni)
    db.commit()

    place = Place(
        name="Historical Church",
        category="church_religious",
        latitude=15.4860,
        longitude=120.9670,
        municipality_id=muni.id,
        source_name="OpenStreetMap",
        source_record_id="node/9988",
        is_active=True,
    )
    db.add(place)
    db.commit()
    db.close()

    # 1. Test POST /places/discover
    disc_res = client.post(
        "/api/v1/places/discover",
        json={"query": "Church", "latitude": 15.4859, "longitude": 120.9669},
    )
    assert disc_res.status_code == 200
    disc_data = disc_res.json()
    assert disc_data["total"] >= 1
    assert disc_data["places"][0]["name"] == "Historical Church"

    # 2. Test POST /itineraries/compute-day-route
    route_res = client.post(
        "/api/v1/itineraries/compute-day-route",
        json={
            "origin": {"latitude": 15.4859, "longitude": 120.9669},
            "destination": {"latitude": 15.5414, "longitude": 121.0844},
            "intermediates": [],
            "travel_mode": "DRIVE",
        },
    )
    assert route_res.status_code == 200
    route_data = route_res.json()
    assert "overview_polyline" in route_data
    assert route_data["total_distance_meters"] > 0
    assert len(route_data["legs"]) == 1

    app.dependency_overrides.clear()


def test_bayesian_quality_score_and_hours_gate():
    from datetime import time
    from app.algorithms.itinerary_generator import bayesian_quality_score, is_open_during_slot

    # 1. Bayesian Score: high rating with high count should beat high rating with low count
    score_high_vol = bayesian_quality_score(4.6, 300)
    score_low_vol = bayesian_quality_score(5.0, 2)
    assert score_high_vol > score_low_vol
    assert 4.5 < score_high_vol < 4.7
    assert 3.8 < score_low_vol < 4.1

    # Missing rating defaults to baseline 3.8
    assert bayesian_quality_score(None, None) == 3.8

    # 2. Operating Hours Gate
    g_hours = {
        "periods": [
            {
                "open": {"day": 1, "hour": 9, "minute": 0},
                "close": {"day": 1, "hour": 17, "minute": 0},
            }
        ]
    }
    # Monday is weekday 0, which corresponds to Google day 1
    assert is_open_during_slot(g_hours, None, time(11, 0), target_weekday=0) is True
    assert is_open_during_slot(g_hours, None, time(20, 0), target_weekday=0) is False

    # OSM string format
    osm_hours = "08:00-18:00"
    assert is_open_during_slot(None, osm_hours, time(14, 0), target_weekday=2) is True
    assert is_open_during_slot(None, osm_hours, time(19, 0), target_weekday=2) is False


