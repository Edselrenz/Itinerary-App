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

    # 8b. CR-001 & CR-002: BOLA / IDOR Protection for Reorder and Delete
    # User B creates an itinerary
    res_b_itin = client.post(
        "/api/v1/itineraries",
        json={
            "title": "User B Trip",
            "destination": "Nueva Ecija",
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "daily_budget": 1000.0,
            "days": [
                {
                    "day_number": 1,
                    "travel_date": start_d.isoformat(),
                    "title": "User B Day 1",
                    "items": [],
                }
            ],
        },
        headers=headers_b,
    )
    assert res_b_itin.status_code == 201
    itin_b_id = res_b_itin.json()["id"]
    day_b_id = res_b_itin.json()["days"][0]["id"]

    # CR-001: User B tries to reorder stop item_1_id (belonging to User A) into User B's itinerary -> 400 Bad Request
    res_reorder_bola = client.post(
        f"/api/v1/itineraries/{itin_b_id}/reorder",
        json={
            "items": [
                {"id": item_1_id, "day_id": day_b_id, "sort_order": 1}
            ]
        },
        headers=headers_b,
    )
    assert res_reorder_bola.status_code == 400
    assert "does not belong to this itinerary" in res_reorder_bola.json()["detail"]

    # CR-002: User B tries to delete User A's stop using User B's itinerary -> 404 Not Found
    res_del_idor = client.delete(
        f"/api/v1/itineraries/{itin_b_id}/days/{day_1_id}/items/{item_1_id}",
        headers=headers_b,
    )
    assert res_del_idor.status_code == 404
    assert "Day not found in this itinerary" in res_del_idor.json()["detail"]

    # 8c. CR-003: User A composite PATCH itinerary including days and stops
    patch_payload = {
        "title": "Updated Weekend Adventure",
        "daily_budget": 4000.0,
        "days": [
            {
                "day_number": 1,
                "travel_date": start_d.isoformat(),
                "title": "Day 1 Updated",
                "items": [
                    {
                        "place_id": place_id,
                        "sort_order": 1,
                        "duration_minutes": 240,
                        "notes": "Updated note",
                    }
                ],
            },
            {
                "day_number": 2,
                "travel_date": end_d.isoformat(),
                "title": "Day 2 With New Stop",
                "items": [
                    {
                        "custom_title": "Day 2 Custom Stop",
                        "sort_order": 1,
                        "duration_minutes": 60,
                    }
                ],
            },
        ],
    }
    patch_res = client.patch(
        f"/api/v1/itineraries/{itinerary_id}",
        json=patch_payload,
        headers=headers_a,
    )
    assert patch_res.status_code == 200
    patched_data = patch_res.json()
    assert patched_data["title"] == "Updated Weekend Adventure"
    assert patched_data["daily_budget"] == 4000.0
    assert len(patched_data["days"]) == 2
    assert patched_data["days"][0]["title"] == "Day 1 Updated"
    assert len(patched_data["days"][0]["items"]) == 1
    assert patched_data["days"][0]["items"][0]["notes"] == "Updated note"
    assert patched_data["days"][1]["title"] == "Day 2 With New Stop"
    assert len(patched_data["days"][1]["items"]) == 1
    assert patched_data["days"][1]["items"][0]["custom_title"] == "Day 2 Custom Stop"

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


def test_suggested_itinerary_engine():
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
    # Seed municipalities
    muni_bongabon = Municipality(
        name="Bongabon", slug="bongabon", is_city=False, center_lat=15.6322, center_lng=121.1447
    )
    muni_pantabangan = Municipality(
        name="Pantabangan", slug="pantabangan", is_city=False, center_lat=15.8239, center_lng=121.1444
    )
    db.add_all([muni_bongabon, muni_pantabangan])
    db.flush()

    # Seed places in Bongabon
    p1 = Place(
        name="Rohi Paperflower Cafe",
        category="cafe",
        municipality_id=muni_bongabon.id,
        latitude=15.6315,
        longitude=121.1438,
        is_featured=True,
        estimated_cost_min=150.0,
        estimated_cost_max=400.0,
        source_record_id="test/rohi-paperflower",
        tags=["cafe", "food"],
    )
    p2 = Place(
        name="Museo de Bongabon",
        category="museum_cultural",
        municipality_id=muni_bongabon.id,
        latitude=15.6330,
        longitude=121.1455,
        is_featured=True,
        estimated_cost_min=None,
        estimated_cost_max=None,
        source_record_id="test/museo-bongabon",
        tags=["museum", "heritage"],
    )
    p3 = Place(
        name="Thornes Samgyupsal House",
        category="restaurant",
        municipality_id=muni_bongabon.id,
        latitude=15.6328,
        longitude=121.1460,
        is_featured=True,
        estimated_cost_min=299.0,
        estimated_cost_max=499.0,
        source_record_id="test/thornes-samgyup",
        tags=["restaurant", "food"],
    )
    # Seed places in Pantabangan
    p4 = Place(
        name="Pantabangan Dam Viewpoint",
        category="tourist_attraction",
        municipality_id=muni_pantabangan.id,
        latitude=15.8126,
        longitude=121.1098,
        is_featured=True,
        estimated_cost_min=None,
        estimated_cost_max=None,
        source_record_id="test/pantabangan-dam",
        tags=["scenic", "nature"],
    )
    p5 = Place(
        name="George Point Viewdeck & Resto",
        category="restaurant",
        municipality_id=muni_pantabangan.id,
        latitude=15.8205,
        longitude=121.1350,
        is_featured=True,
        estimated_cost_min=200.0,
        estimated_cost_max=600.0,
        source_record_id="test/george-point",
        tags=["restaurant", "scenic"],
    )
    p6 = Place(
        name="Highland Bali Villas Resort",
        category="resort_swimming",
        municipality_id=muni_pantabangan.id,
        latitude=15.8270,
        longitude=121.1415,
        is_featured=True,
        estimated_cost_min=3500.0,
        estimated_cost_max=8500.0,
        source_record_id="test/highland-bali",
        tags=["resort", "swimming"],
    )
    db.add_all([p1, p2, p3, p4, p5, p6])
    db.commit()

    # 1. Anonymous / Guest suggested itinerary request (no Bearer token)
    guest_req = {
        "title": "Bongabon Weekend Escape",
        "destination": "Bongabon",
        "start_date": "2026-11-01",
        "end_date": "2026-11-02",
        "daily_budget": 2500.0,
        "preferences": ["nature", "food"],
        "save_immediately": False,
    }
    res = client.post("/api/v1/itineraries/suggest", json=guest_req)
    assert res.status_code == 200
    plan = res.json()

    assert plan["title"] == "Bongabon Weekend Escape"
    assert plan["destination"] == "Bongabon"
    assert plan["type"] == "suggested"
    assert plan["user_id"] is None  # Guest mode unpersisted draft
    assert len(plan["days"]) == 2

    # Check Day 1 stops
    day_1 = plan["days"][0]
    assert day_1["day_number"] == 1
    assert len(day_1["items"]) >= 2
    # Verify chronological sort order
    for idx, item in enumerate(day_1["items"]):
        assert item["sort_order"] == idx + 1
        assert item["place"] is not None

    # Check transparent assumptions
    assumptions = plan["assumptions"]
    assert len(assumptions) >= 4
    assert any("Pacing" in a for a in assumptions)
    assert any("Geographic clustering" in a for a in assumptions)
    assert any("Pricing Notice" in a for a in assumptions)

    # 2. Date validation (end date before start date -> 422)
    invalid_req = {
        "title": "Invalid Trip",
        "destination": "Bongabon",
        "start_date": "2026-11-05",
        "end_date": "2026-11-01",
        "daily_budget": 1000.0,
    }
    invalid_res = client.post("/api/v1/itineraries/suggest", json=invalid_req)
    assert invalid_res.status_code == 422

    # 3. Authenticated user with save_immediately=True
    auth_user_req = {
        "first_name": "Maria",
        "last_name": "Santos",
        "username": "mariasantos",
        "email": "maria@example.ph",
        "password": "Password123!",
    }
    user_res = client.post("/api/v1/auth/register", json=auth_user_req)
    assert user_res.status_code == 201
    auth_headers = {"Authorization": f"Bearer {user_res.json()['access_token']}"}

    save_req = {
        "title": "Bongabon Saved Tour",
        "destination": "Bongabon",
        "start_date": "2026-11-01",
        "end_date": "2026-11-01",
        "daily_budget": 3000.0,
        "preferences": ["food"],
        "save_immediately": True,
    }
    save_res = client.post("/api/v1/itineraries/suggest", json=save_req, headers=auth_headers)
    assert save_res.status_code == 200
    saved_plan = save_res.json()
    assert saved_plan["user_id"] is not None
    saved_id = saved_plan["id"]

    # Verify that the itinerary is now in the user's saved list
    list_res = client.get("/api/v1/itineraries", headers=auth_headers)
    assert list_res.status_code == 200
    user_itins = list_res.json()
    assert any(i["id"] == saved_id for i in user_itins)




def test_single_stop_patch_and_place_validation():
    TestingSessionLocal = make_test_session()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # Seed place
    db = TestingSessionLocal()
    muni = Municipality(
        name="Cabanatuan City",
        slug="cabanatuan-city",
        is_city=True,
        center_lat=15.4858,
        center_lng=120.9667,
    )
    db.add(muni)
    db.flush()

    p = Place(
        name="Plaza Lucero",
        category="tourist_attraction",
        latitude=15.4860,
        longitude=120.9670,
        municipality_id=muni.id,
        source_name="TestSeeder",
        source_record_id="test/plaza-lucero",
    )
    db.add(p)
    db.commit()
    place_id = str(p.id)
    db.close()

    # Register user
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Juan",
            "last_name": "Dela Cruz",
            "username": "juandelacruz",
            "email": "juan@example.ph",
            "password": "Password123!",
        },
    )
    assert reg.status_code == 201
    auth_headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    # 1. Test create_itinerary with nonexistent place_id -> 404
    fake_place_id = str(uuid.uuid4())
    bad_itin_res = client.post(
        "/api/v1/itineraries",
        headers=auth_headers,
        json={
            "title": "Bad Itinerary",
            "destination": "Cabanatuan City",
            "start_date": "2026-11-10",
            "end_date": "2026-11-10",
            "days": [
                {
                    "day_number": 1,
                    "travel_date": "2026-11-10",
                    "title": "Day 1",
                    "items": [
                        {
                            "place_id": fake_place_id,
                            "sort_order": 1,
                        }
                    ],
                }
            ],
        },
    )
    assert bad_itin_res.status_code == 404
    assert "do not exist" in bad_itin_res.json()["detail"]

    # 2. Test create valid itinerary
    good_itin_res = client.post(
        "/api/v1/itineraries",
        headers=auth_headers,
        json={
            "title": "Good Itinerary",
            "destination": "Cabanatuan City",
            "start_date": "2026-11-10",
            "end_date": "2026-11-10",
            "days": [
                {
                    "day_number": 1,
                    "travel_date": "2026-11-10",
                    "title": "Day 1",
                    "items": [
                        {
                            "place_id": place_id,
                            "sort_order": 1,
                            "duration_minutes": 60,
                            "notes": "Initial note",
                        }
                    ],
                }
            ],
        },
    )
    assert good_itin_res.status_code == 201
    itin = good_itin_res.json()
    itin_id = itin["id"]
    day_id = itin["days"][0]["id"]
    item_id = itin["days"][0]["items"][0]["id"]

    # 3. Test add_itinerary_item with nonexistent place_id -> 404
    bad_add_res = client.post(
        f"/api/v1/itineraries/{itin_id}/days/{day_id}/items",
        headers=auth_headers,
        json={"place_id": fake_place_id, "sort_order": 2},
    )
    assert bad_add_res.status_code == 404

    # 4. Test single-stop PATCH /api/v1/itineraries/{id}/days/{day_id}/items/{item_id}
    patch_res = client.patch(
        f"/api/v1/itineraries/{itin_id}/days/{day_id}/items/{item_id}",
        headers=auth_headers,
        json={
            "notes": "Updated historical notes",
            "duration_minutes": 120,
            "estimated_cost_min": 150.0,
            "estimated_cost_max": 300.0,
        },
    )
    assert patch_res.status_code == 200
    updated_itin = patch_res.json()
    updated_item = updated_itin["days"][0]["items"][0]
    assert updated_item["notes"] == "Updated historical notes"
    assert updated_item["duration_minutes"] == 120
    assert updated_item["estimated_cost_min"] == 150.0
    assert updated_item["estimated_cost_max"] == 300.0

    # 5. Test single-stop PATCH BOLA protection (foreign user)
    reg2 = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Attacker",
            "last_name": "Bob",
            "username": "attackerbob",
            "email": "attacker@example.ph",
            "password": "Password123!",
        },
    )
    assert reg2.status_code == 201
    attacker_headers = {"Authorization": f"Bearer {reg2.json()['access_token']}"}

    attacker_patch = client.patch(
        f"/api/v1/itineraries/{itin_id}/days/{day_id}/items/{item_id}",
        headers=attacker_headers,
        json={"notes": "Hacked note"},
    )
    assert attacker_patch.status_code == 404


def test_suggested_generator_radius_and_budget_clustering():
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
    # Municipality in Bongabon (Eastern Nueva Ecija)
    muni_bongabon = Municipality(
        name="Bongabon",
        slug="bongabon",
        is_city=False,
        center_lat=15.6319,
        center_lng=121.1444,
    )
    # Distant Municipality in Cuyapo (Northwestern Nueva Ecija ~60km away)
    muni_cuyapo = Municipality(
        name="Cuyapo",
        slug="cuyapo",
        is_city=False,
        center_lat=15.7761,
        center_lng=120.6669,
    )
    db.add_all([muni_bongabon, muni_cuyapo])
    db.flush()

    # Seed 3 places in Bongabon within 5km radius
    p_b1 = Place(
        name="Mount Labi Viewpoint",
        category="nature_park",
        latitude=15.6350,
        longitude=121.1460,
        municipality_id=muni_bongabon.id,
        source_name="Seed",
        source_record_id="b1",
        is_featured=True,
        estimated_cost_min=50.0,
        estimated_cost_max=100.0,
    )
    p_b2 = Place(
        name="Bongabon Onion Cafe",
        category="restaurant",
        latitude=15.6300,
        longitude=121.1420,
        municipality_id=muni_bongabon.id,
        source_name="Seed",
        source_record_id="b2",
        is_featured=False,
        estimated_cost_min=150.0,
        estimated_cost_max=250.0,
    )
    p_b3 = Place(
        name="Sierra Madre Nature Trail",
        category="tourist_attraction",
        latitude=15.6400,
        longitude=121.1500,
        municipality_id=muni_bongabon.id,
        source_name="Seed",
        source_record_id="b3",
        is_featured=True,
        estimated_cost_min=80.0,
        estimated_cost_max=120.0,
    )

    # Seed distant places in Cuyapo (60+ km away)
    p_c1 = Place(
        name="Cuyapo Far Heritage House",
        category="museum_cultural",
        latitude=15.7770,
        longitude=120.6680,
        municipality_id=muni_cuyapo.id,
        source_name="Seed",
        source_record_id="c1",
        is_featured=True,
        estimated_cost_min=2000.0,
        estimated_cost_max=3000.0,
    )
    p_c2 = Place(
        name="Cuyapo Distant Restaurant",
        category="restaurant",
        latitude=15.7780,
        longitude=120.6690,
        municipality_id=muni_cuyapo.id,
        source_name="Seed",
        source_record_id="c2",
        is_featured=True,
        estimated_cost_min=1500.0,
        estimated_cost_max=2000.0,
    )
    db.add_all([p_b1, p_b2, p_b3, p_c1, p_c2])
    db.commit()
    db.close()

    # Request suggested itinerary for Bongabon
    res = client.post(
        "/api/v1/itineraries/suggest",
        json={
            "title": "Bongabon Radius Test",
            "destination": "Bongabon",
            "start_date": "2026-11-20",
            "end_date": "2026-11-20",
            "daily_budget": 500.0,
            "preferences": ["nature", "food"],
            "save_immediately": False,
        },
    )
    assert res.status_code == 200
    plan = res.json()
    day_items = plan["days"][0]["items"]
    assert len(day_items) >= 2

    # Verify all scheduled stops belong to Bongabon and NOT distant Cuyapo
    scheduled_names = [it["place"]["name"] for it in day_items]
    assert "Mount Labi Viewpoint" in scheduled_names
    assert "Bongabon Onion Cafe" in scheduled_names
    assert "Cuyapo Far Heritage House" not in scheduled_names
    assert "Cuyapo Distant Restaurant" not in scheduled_names


def test_generator_sql_bounding_box_pre_filtering():
    """CR-013: Verifies candidate POIs are pre-filtered via SQL bounding box."""
    from datetime import date
    from app.algorithms.itinerary_generator import generate_suggested_itinerary_data
    from app.schemas.itinerary import SuggestedItineraryRequest

    TestingSessionLocal = make_test_session()
    db = TestingSessionLocal()
    try:
        # Create Bongabon municipality and 3 local POIs
        muni = Municipality(
            name="Bongabon",
            slug="bongabon",
            is_city=False,
            center_lat=15.6319,
            center_lng=121.1444,
        )
        db.add(muni)
        db.flush()

        p1 = Place(
            name="Bongabon Mountain Peak",
            category="nature_park",
            latitude=15.6350,
            longitude=121.1450,
            municipality_id=muni.id,
            source_name="BBoxTest",
            source_record_id="bbt1",
            is_active=True,
            is_featured=True,
            estimated_cost_min=50.0,
            estimated_cost_max=100.0,
        )
        p2 = Place(
            name="Bongabon Cozy Cafe",
            category="cafe",
            latitude=15.6325,
            longitude=121.1440,
            municipality_id=muni.id,
            source_name="BBoxTest",
            source_record_id="bbt2",
            is_active=True,
            is_featured=True,
            estimated_cost_min=100.0,
            estimated_cost_max=200.0,
        )
        p3 = Place(
            name="Bongabon Local Grill",
            category="restaurant",
            latitude=15.6310,
            longitude=121.1460,
            municipality_id=muni.id,
            source_name="BBoxTest",
            source_record_id="bbt3",
            is_active=True,
            is_featured=True,
            estimated_cost_min=150.0,
            estimated_cost_max=300.0,
        )
        # Distant place in Lupao (>50km away)
        p_far = Place(
            name="Lupao Distant Falls",
            category="nature_park",
            latitude=15.8750,
            longitude=120.8980,
            source_name="BBoxTest",
            source_record_id="bbt_far",
            is_active=True,
            is_featured=True,
        )
        db.add_all([p1, p2, p3, p_far])
        db.commit()

        req = SuggestedItineraryRequest(
            title="Bongabon BBox Clustered Tour",
            destination="Bongabon",
            start_date=date(2026, 12, 1),
            end_date=date(2026, 12, 1),
            daily_budget=2000.0,
            preferences=["nature_park", "restaurant", "cafe"],
            save_immediately=False,
        )
        data = generate_suggested_itinerary_data(db, req)
        assert len(data["days"]) == 1
        items = data["days"][0]["items"]
        assert len(items) >= 2
        for it in items:
            p = it["place"]
            assert "Lupao" not in p.name
            assert "Bongabon" in p.name
    finally:
        db.close()

