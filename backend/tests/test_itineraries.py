"""Automated tests for Itinerary Builder CRUD, Stop Reordering, and BOLA Protection."""

import sys
import uuid
from datetime import date, timedelta
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


def make_test_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_itinerary_lifecycle_and_bola_protection():
    TestingSessionLocal = make_test_session()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # Seed a place into the test database
    db = TestingSessionLocal()
    muni = Municipality(
        name="General Tinio",
        slug="general-tinio",
        is_city=False,
        center_lat=15.34,
        center_lng=121.05,
    )
    db.add(muni)
    db.flush()

    test_place = Place(
        name="Minalungao National Park",
        category="nature_park",
        latitude=15.2981,
        longitude=121.1223,
        municipality_id=muni.id,
        address_text="General Tinio, Nueva Ecija",
        source_name="TestSeeder",
        source_record_id="test/minalungao",
        is_featured=True,
        tags=["nature_park", "Adventure"],
    )
    db.add(test_place)
    db.commit()
    place_id = str(test_place.id)
    db.close()

    # 1. Register User A (Itinerary Owner)
    res_a = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Maria",
            "last_name": "Santos",
            "username": "mariasantos",
            "email": "maria.santos@example.ph",
            "password": "Password123!",
        },
    )
    assert res_a.status_code == 201
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B (Attacker / Different Traveler)
    res_b = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Pedro",
            "last_name": "Penduko",
            "username": "pedropenduko",
            "email": "pedro.penduko@example.ph",
            "password": "Password123!",
        },
    )
    assert res_b.status_code == 201
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A creates a 2-day custom itinerary
    start_d = date.today() + timedelta(days=7)
    end_d = start_d + timedelta(days=1)

    create_payload = {
        "title": "Bongabon & Minalungao Weekend",
        "destination": "Nueva Ecija",
        "start_date": start_d.isoformat(),
        "end_date": end_d.isoformat(),
        "daily_budget": 2500.0,
        "preferences": ["nature_park", "cafe"],
        "type": "custom",
        "assumptions": ["Travel by private vehicle"],
        "days": [
            {
                "day_number": 1,
                "travel_date": start_d.isoformat(),
                "title": "Day 1 - Canyons & Adventure",
                "items": [
                    {
                        "place_id": place_id,
                        "sort_order": 1,
                        "duration_minutes": 180,
                        "notes": "Bring swimwear and water shoes",
                        "estimated_cost_min": 100.0,
                        "estimated_cost_max": 500.0,
                    }
                ],
            },
            {
                "day_number": 2,
                "travel_date": end_d.isoformat(),
                "title": "Day 2 - Relaxed Cafe Hop",
                "items": [],
            },
        ],
    }

    res_create = client.post(
        "/api/v1/itineraries", json=create_payload, headers=headers_a
    )
    assert res_create.status_code == 201, res_create.text
    itin_data = res_create.json()
    itinerary_id = itin_data["id"]
    assert itin_data["title"] == "Bongabon & Minalungao Weekend"
    assert len(itin_data["days"]) == 2
    day_1_id = itin_data["days"][0]["id"]
    day_2_id = itin_data["days"][1]["id"]
    assert len(itin_data["days"][0]["items"]) == 1
    assert itin_data["days"][0]["items"][0]["place"]["name"] == "Minalungao National Park"

    # 4. Strict BOLA Protection (OWASP API1:2023)
    # User B tries to GET User A's itinerary -> 404
    res_bola_get = client.get(
        f"/api/v1/itineraries/{itinerary_id}", headers=headers_b
    )
    assert res_bola_get.status_code == 404

    # User B tries to PATCH User A's itinerary -> 404
    res_bola_patch = client.patch(
        f"/api/v1/itineraries/{itinerary_id}",
        json={"title": "Hacked Title"},
        headers=headers_b,
    )
    assert res_bola_patch.status_code == 404

    # User B tries to DELETE User A's itinerary -> 404
    res_bola_del = client.delete(
        f"/api/v1/itineraries/{itinerary_id}", headers=headers_b
    )
    assert res_bola_del.status_code == 404

    # User B list itineraries -> returns empty list
    res_list_b = client.get("/api/v1/itineraries", headers=headers_b)
    assert res_list_b.status_code == 200
    assert len(res_list_b.json()) == 0

    # User A list itineraries -> returns User A's itinerary
    res_list_a = client.get("/api/v1/itineraries", headers=headers_a)
    assert res_list_a.status_code == 200
    assert len(res_list_a.json()) == 1

    # 5. Same-Day Duplicate Stop Guard
    # Adding Minalungao to Day 1 again must fail with 409 Conflict
    dup_res = client.post(
        f"/api/v1/itineraries/{itinerary_id}/days/{day_1_id}/items",
        json={"place_id": place_id, "sort_order": 2},
        headers=headers_a,
    )
    assert dup_res.status_code == 409
    assert "already been scheduled" in dup_res.json()["detail"]

    # 6. Add Custom Off-Grid Stop
    custom_stop_res = client.post(
        f"/api/v1/itineraries/{itinerary_id}/days/{day_1_id}/items",
        json={
            "custom_title": "Local Sari-Sari Store & View Deck",
            "custom_lat": 15.3100,
            "custom_lng": 121.1100,
            "sort_order": 2,
            "duration_minutes": 30,
            "notes": "Quick snack break",
            "estimated_cost_min": 50.0,
            "estimated_cost_max": 150.0,
        },
        headers=headers_a,
    )
    assert custom_stop_res.status_code == 200
    updated_itin = custom_stop_res.json()
    assert len(updated_itin["days"][0]["items"]) == 2
    item_1_id = updated_itin["days"][0]["items"][0]["id"]
    item_2_id = updated_itin["days"][0]["items"][1]["id"]

    # 7. Reorder Stops Within/Across Days
    reorder_res = client.post(
        f"/api/v1/itineraries/{itinerary_id}/reorder",
        json={
            "items": [
                {"id": item_1_id, "day_id": day_1_id, "sort_order": 2},
                {"id": item_2_id, "day_id": day_1_id, "sort_order": 1},
            ]
        },
        headers=headers_a,
    )
    assert reorder_res.status_code == 200
    reordered_items = reorder_res.json()["days"][0]["items"]
    assert reordered_items[0]["id"] == item_2_id
    assert reordered_items[0]["sort_order"] == 1
    assert reordered_items[1]["id"] == item_1_id
    assert reordered_items[1]["sort_order"] == 2

    # 8. Delete a stop and verify order re-compaction
    del_stop_res = client.delete(
        f"/api/v1/itineraries/{itinerary_id}/days/{day_1_id}/items/{item_2_id}",
        headers=headers_a,
    )
    assert del_stop_res.status_code == 200
    remaining_stops = del_stop_res.json()["days"][0]["items"]
    assert len(remaining_stops) == 1
    assert remaining_stops[0]["sort_order"] == 1

    # 9. Delete itinerary and verify cascade
    del_itin_res = client.delete(
        f"/api/v1/itineraries/{itinerary_id}", headers=headers_a
    )
    assert del_itin_res.status_code == 204

    # Verify GET now returns 404
    assert (
        client.get(
            f"/api/v1/itineraries/{itinerary_id}", headers=headers_a
        ).status_code
        == 404
    )
