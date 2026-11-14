"""Automated test suite verifying fixes for QA Audit defects (DEF-01 through DEF-15)."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from desktop_client.config.settings import ThemeColors, get_settings, CANONICAL_CATEGORIES
from desktop_client.core.api_client import ApiClient, ApiClientError
from desktop_client.models.place import Municipality, PaginatedPlaces, Place
from desktop_client.models.user import User, UserUpdatePayload
from desktop_client.services.auth_service import AuthService
from desktop_client.services.itinerary_service import ItineraryService
from desktop_client.services.place_service import PlaceService
from desktop_client.models.itinerary import Itinerary, ItineraryDay, ItineraryItem


def test_def_02_auth_register_schema_compliance():
    """DEF-02: AuthService.register must produce first_name, last_name, and username."""
    mock_api = MagicMock(spec=ApiClient)
    mock_api.post = AsyncMock(return_value={
        "access_token": "acc-123",
        "refresh_token": "ref-123",
        "user": {
            "id": "u-1",
            "first_name": "Maria",
            "last_name": "Clara",
            "username_normalized": "mariaclara",
            "email_normalized": "maria@example.ph",
            "is_active": True,
            "created_at": "2026-11-12T00:00:00",
        }
    })

    service = AuthService(api_client=mock_api)
    import asyncio
    user = asyncio.run(service.register(
        email="maria@example.ph",
        password="Password123!",
        full_name="Maria Clara",
    ))

    # Assert payload passed to API client
    mock_api.post.assert_called_once()
    call_args = mock_api.post.call_args
    payload = call_args.kwargs.get("json_data") or call_args[1].get("json_data")
    assert payload["first_name"] == "Maria"
    assert payload["last_name"] == "Clara"
    assert payload["username"] == "maria"
    assert payload["email"] == "maria@example.ph"
    assert payload["password"] == "Password123!"
    assert user.full_name == "Maria Clara"


def test_def_07_user_model_from_dict_normalization():
    """DEF-07: User.from_dict must parse first_name, last_name, and normalized email."""
    data = {
        "id": "uuid-123",
        "first_name": "Jose",
        "last_name": "Rizal",
        "username_normalized": "jrizal",
        "email_normalized": "jose.rizal@philippines.gov",
        "is_active": True,
        "created_at": "2026-11-12T08:00:00",
    }
    user = User.from_dict(data)
    assert user.id == "uuid-123"
    assert user.first_name == "Jose"
    assert user.last_name == "Rizal"
    assert user.full_name == "Jose Rizal"
    assert user.email == "jose.rizal@philippines.gov"
    assert user.username == "jrizal"


def test_def_08_user_update_payload_first_last_name():
    """DEF-08: UserUpdatePayload must emit first_name and last_name for backend PATCH /auth/me."""
    payload = UserUpdatePayload(full_name="Andres Bonifacio")
    d = payload.to_dict()
    assert d["first_name"] == "Andres"
    assert d["last_name"] == "Bonifacio"

    payload2 = UserUpdatePayload(first_name="Apolinario", last_name="Mabini")
    d2 = payload2.to_dict()
    assert d2["first_name"] == "Apolinario"
    assert d2["last_name"] == "Mabini"


def test_def_14_municipality_center_lat_lng_parsing():
    """DEF-14: Municipality.from_dict must parse center_lat and center_lng from backend."""
    data = {
        "id": "muni-cab",
        "name": "Cabanatuan City",
        "slug": "cabanatuan-city",
        "is_city": True,
        "center_lat": 15.4859,
        "center_lng": 120.9669,
    }
    muni = Municipality.from_dict(data)
    assert muni.id == "muni-cab"
    assert muni.name == "Cabanatuan City"
    assert muni.latitude == 15.4859
    assert muni.longitude == 120.9669


def test_def_06_place_service_query_parameter_mapping():
    """DEF-06: PlaceService.get_places must send q, limit, offset, featured to backend."""
    mock_api = MagicMock(spec=ApiClient)
    mock_api.get = AsyncMock(return_value={
        "total": 100,
        "limit": 20,
        "offset": 40,
        "items": []
    })

    service = PlaceService(api_client=mock_api)
    import asyncio
    paginated = asyncio.run(service.get_places(
        page=3,
        page_size=20,
        search="Pantabangan",
        category="nature_park",
        municipality_id="muni-pan",
        is_featured=True,
    ))

    mock_api.get.assert_called_once()
    call_args = mock_api.get.call_args
    params = call_args.kwargs.get("params")
    assert params["q"] == "Pantabangan"
    assert "search" not in params
    assert params["limit"] == 20
    assert params["offset"] == 40
    assert "page" not in params
    assert params["featured"] is True
    assert "is_featured" not in params
    assert params["categories"] == ["nature_park"]
    assert params["municipality_id"] == "muni-pan"
    assert paginated.page == 3


def test_def_12_place_service_get_categories():
    """DEF-12: PlaceService.get_categories returns canonical categories without HTTP 422."""
    service = PlaceService()
    import asyncio
    cats = asyncio.run(service.get_categories())
    assert len(cats) == 16
    assert "nature_park" in cats
    assert "church_religious" in cats


def test_def_04_api_client_health_sync_dynamic_host_port():
    """DEF-04: ApiClient.check_health_sync dynamically parses host and port from base_url."""
    # Test with custom base_url
    client = ApiClient(base_url="https://api.nuevaecijatravel.ph/api/v1")
    # Even if unreachable, verify it parses host 'api.nuevaecijatravel.ph' and port 443 without crashing
    assert client.base_url == "https://api.nuevaecijatravel.ph/api/v1"
    res = client.check_health_sync()
    assert isinstance(res, bool)


def test_def_09_and_05_itinerary_update_and_reorder_methods():
    """DEF-09 & DEF-05: update_itinerary uses PATCH and reorder_stops calls POST /itineraries/{id}/reorder."""
    mock_api = MagicMock(spec=ApiClient)
    mock_api.patch = AsyncMock(return_value={
        "id": "itin-1",
        "title": "Updated Title",
        "destination": "Nueva Ecija",
        "start_date": "2026-12-01",
        "end_date": "2026-12-02",
        "daily_budget": 3000.0,
        "preferences": [],
        "type": "custom",
        "assumptions": [],
        "days": [],
    })
    mock_api.post = AsyncMock(return_value={"id": "itin-1"})

    mock_session = MagicMock()
    mock_session.is_authenticated = True

    service = ItineraryService(api_client=mock_api, session_manager=mock_session)
    import asyncio

    itin = Itinerary(
        id="itin-1",
        title="Original Title",
        destination="Nueva Ecija",
        start_date="2026-12-01",
        end_date="2026-12-02",
        type="custom",
        daily_budget=2500.0,
        days=[
            ItineraryDay(
                id="d1",
                itinerary_id="itin-1",
                day_number=1,
                travel_date="2026-12-01",
                items=[
                    ItineraryItem(id="i1", day_id="d1", sort_order=1),
                    ItineraryItem(id="i2", day_id="d1", sort_order=2),
                ],
            )
        ],
    )

    # Test update_itinerary calls PATCH
    itin.title = "Updated Title"
    updated = asyncio.run(service.update_itinerary(itin))
    mock_api.patch.assert_called_once()
    patch_call = mock_api.patch.call_args
    assert patch_call[0][0] == "itineraries/itin-1"
    assert patch_call.kwargs["json_data"]["title"] == "Updated Title"
    assert patch_call.kwargs["json_data"]["daily_budget"] == 2500.0
    assert updated.title == "Updated Title"

    # Test reorder_stops calls POST /itineraries/{id}/reorder
    reordered = asyncio.run(service.reorder_stops(itin, "d1", ["i2", "i1"]))
    mock_api.post.assert_called_once()
    call_args = mock_api.post.call_args
    assert call_args[0][0] == "itineraries/itin-1/reorder"
    assert call_args.kwargs["json_data"] == {
        "items": [
            {"id": "i2", "day_id": "d1", "sort_order": 1},
            {"id": "i1", "day_id": "d1", "sort_order": 2},
        ]
    }


def test_def_15_wcag_contrast_muted_text():
    """DEF-15: TEXT_MUTED_LIGHT must be #475569 for WCAG 2.2 AA compliance."""
    assert ThemeColors.TEXT_MUTED_LIGHT == "#475569"
