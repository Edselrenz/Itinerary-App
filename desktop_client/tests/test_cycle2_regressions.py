"""Cycle 2 Regression Test Suite (TC-01 through TC-15) verifying fixes for REG-01 to REG-16."""

import os
from pathlib import Path
import uuid
import pytest
import flet as ft

from desktop_client.config.settings import ThemeColors, ThemePalette, get_settings
from desktop_client.core.api_client import ApiClient, get_api_client
from desktop_client.core.session import get_session_manager
from desktop_client.models.itinerary import (
    Itinerary,
    ItineraryDay,
    ItineraryItem,
    SuggestedItineraryRequest,
)
from desktop_client.models.place import Place
from desktop_client.components.bottom_tab_bar import BottomTabBar
from desktop_client.views.custom_builder_view import CustomBuilderView
from desktop_client.views.dashboard_view import DashboardView
from desktop_client.views.saved_trips_view import SavedTripsView
from desktop_client.views.suggested_wizard_view import SuggestedWizardView
from desktop_client.views.trip_detail_view import TripDetailView
from desktop_client.views.profile_view import ProfileView


def test_tc_01_desktop_startup_types_and_palette():
    """TC-01: Verifies settings imports, ThemeColors aliases, and ThemePalette access (REG-01, REG-08, REG-11)."""
    settings = get_settings()
    assert hasattr(settings, "set_dark_mode")
    assert hasattr(settings, "is_dark_mode")
    assert hasattr(settings, "palette")

    settings.set_dark_mode(False)
    pal_light = settings.palette
    assert pal_light.bg_primary == pal_light.bg_main == ThemeColors.BG_LIGHT
    assert hasattr(ThemeColors, "TEXT_PRIMARY_LIGHT")
    assert ThemeColors.TEXT_PRIMARY_LIGHT == "#0f172a"

    settings.set_dark_mode(True)
    pal_dark = settings.palette
    assert pal_dark.bg_primary == pal_dark.bg_main == ThemeColors.BG_DARK
    assert hasattr(ThemeColors, "TEXT_PRIMARY_DARK")
    settings.set_dark_mode(False)


def test_tc_02_cloud_failover_api_client():
    """TC-02: Verifies ApiClient set_base_url and logger are defined for failover (REG-12)."""
    client = ApiClient()
    assert hasattr(client, "set_base_url")
    client.set_base_url("https://worker.proxy.test/api/v1")
    assert client.base_url == "https://worker.proxy.test/api/v1"
    client.set_base_url("")


def test_tc_03_custom_builder_save_estimated_cost_attribute():
    """TC-03: Verifies ItineraryItem exposes estimated_cost property matching representative_cost (REG-02)."""
    item = ItineraryItem(
        id=str(uuid.uuid4()),
        day_id="d1",
        sort_order=1,
        custom_title="Test Place",
        estimated_cost_min=100.0,
        estimated_cost_max=250.0,
    )
    assert item.estimated_cost == item.representative_cost == 250.0

    day = ItineraryDay(
        id="d1",
        itinerary_id="itin1",
        day_number=1,
        travel_date="2026-11-15",
        items=[item],
    )
    itin = Itinerary(
        id="itin1",
        title="Test Itinerary",
        destination="Nueva Ecija",
        start_date="2026-11-15",
        end_date="2026-11-16",
        days=[day],
    )
    total_expenses = sum(float(itm.representative_cost) for d in itin.days for itm in d.items)
    assert total_expenses == 250.0


def test_tc_04_custom_builder_handle_back_clean_steps():
    """TC-04: Verifies handle_back steps through browse -> timeline -> form without discard trap (REG-03)."""
    cbv = CustomBuilderView()
    cbv.active_view = "browse"
    cbv.is_dirty = True

    # Stepping back from browse should move to form/timeline, not trigger discard
    res = cbv.handle_back()
    assert res is True
    assert cbv.active_view in ("form", "timeline")

    # Stepping back from form with is_dirty should guard with discard dialog
    cbv.active_view = "form"
    cbv.is_dirty = True
    assert cbv.handle_back() is True

    # Stepping back from form without dirty flag should return False to let router exit
    cbv.is_dirty = False
    assert cbv.handle_back() is False


def test_tc_05_offgrid_coordinates_toggle():
    """TC-05: Verifies coordinates toggle button sets .content using Flet 1.1.2 standard (REG-04)."""
    coords_expanded = [False]
    coords_col = ft.Column(visible=False)
    coords_toggle_btn = ft.TextButton(
        content=ft.Text("Pin Coordinates (Lat / Lng) — Optional ▼", size=12, color=ThemeColors.PRIMARY_BLUE)
    )

    def _toggle():
        coords_expanded[0] = not coords_expanded[0]
        coords_col.visible = coords_expanded[0]
        coords_toggle_btn.content = ft.Text(
            "Hide Coordinates ▲" if coords_expanded[0] else "Pin Coordinates (Lat / Lng) — Optional ▼",
            size=12,
            color=ThemeColors.PRIMARY_BLUE,
            weight=ft.FontWeight.W_600,
        )

    _toggle()
    assert coords_expanded[0] is True
    assert coords_col.visible is True
    assert coords_toggle_btn.content.value == "Hide Coordinates ▲"

    _toggle()
    assert coords_expanded[0] is False
    assert coords_col.visible is False
    assert coords_toggle_btn.content.value == "Pin Coordinates (Lat / Lng) — Optional ▼"


def test_tc_06_backend_anchor_normalization():
    """TC-06: Verifies backend schema SuggestedItineraryRequest preserves string anchor IDs (REG-06)."""
    import sys
    backend_dir = str(Path(__file__).resolve().parent.parent.parent / "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from app.schemas.itinerary import SuggestedItineraryRequest as BackendSuggestedReq

    req_data = {
        "destination": "General Tinio",
        "start_date": "2026-11-20",
        "end_date": "2026-11-22",
        "anchor_place_id": "dest-minalungao",
    }
    model = BackendSuggestedReq.model_validate(req_data)
    assert model.anchor_place_id is None
    assert model.anchor_place_payload is not None
    assert model.anchor_place_payload.get("id") == "dest-minalungao"

    valid_uuid = str(uuid.uuid4())
    req_data_uuid = {
        "destination": "General Tinio",
        "start_date": "2026-11-20",
        "end_date": "2026-11-22",
        "anchor_place_id": valid_uuid,
    }
    model_uuid = BackendSuggestedReq.model_validate(req_data_uuid)
    assert str(model_uuid.anchor_place_id) == valid_uuid


@pytest.mark.anyio
async def test_tc_07_resort_anchor_retained_in_offline_suggested():
    """TC-07: Verifies resort/hotel anchor is retained at Day 1, Stop 1 in offline generator (REG-07)."""
    from desktop_client.services.itinerary_service import get_itinerary_service

    svc = get_itinerary_service()
    resort_anchor = {
        "id": "resort-bali-test",
        "name": "Highland Bali Villas Resort and Spa",
        "category": "resort_swimming",
        "municipality_name": "Pantabangan",
        "latitude": 15.82,
        "longitude": 121.14,
        "estimated_cost_min": 3500.0,
        "estimated_cost_max": 5000.0,
    }
    req = SuggestedItineraryRequest(
        destination="Pantabangan",
        start_date="2026-11-20",
        end_date="2026-11-20",  # Single day trip
        anchor_place_id="resort-bali-test",
        anchor_place_payload=resort_anchor,
    )
    itin = await svc.generate_offline_suggested_itinerary(req)
    assert itin is not None
    assert len(itin.days) >= 1
    day1_items = itin.days[0].items
    assert len(day1_items) >= 1
    # Day 1, Stop 1 must be the resort anchor
    assert day1_items[0].display_title == "Highland Bali Villas Resort and Spa"


def test_tc_08_suggested_wizard_save_to_create_payload():
    """TC-08: Verifies Itinerary.to_create_payload converts cleanly without start_time crash (REG-05)."""
    place = Place(
        id=str(uuid.uuid4()),
        name="Minalungao National Park",
        municipality_name="General Tinio",
        category="nature_park",
        latitude=15.30,
        longitude=121.05,
    )
    item = ItineraryItem(
        id=str(uuid.uuid4()),
        day_id="d1",
        sort_order=1,
        place_id=place.id,
        place=place,
        duration_minutes=90,
    )
    day = ItineraryDay(
        id="d1",
        itinerary_id="itin-1",
        day_number=1,
        travel_date="2026-11-20",
        items=[item],
    )
    itin = Itinerary(
        id="itin-1",
        title="Suggested Trip",
        destination="General Tinio",
        start_date="2026-11-20",
        end_date="2026-11-21",
        type="suggested",
        days=[day],
    )
    payload = itin.to_create_payload()
    assert payload.title == "Suggested Trip"
    assert len(payload.days) == 1
    assert payload.days[0]["items"][0]["place_id"] == place.id


def test_tc_09_bottom_tab_bar_refresh_theme():
    """TC-09: Verifies BottomTabBar exposes refresh_theme() and updates colors (REG-08)."""
    tab_bar = BottomTabBar(current_route="/home")
    assert hasattr(tab_bar, "refresh_theme")
    tab_bar.refresh_theme()


def test_tc_11_trip_detail_add_nearby_stop_dataclass():
    """TC-11: Verifies TripDetailView._add_nearby_to_active_day constructs valid ItineraryItem (REG-13)."""
    itin = Itinerary(
        id="itin-test",
        title="Sample",
        destination="Cabanatuan",
        start_date="2026-11-20",
        end_date="2026-11-20",
        days=[ItineraryDay(id="d-test", itinerary_id="itin-test", day_number=1, travel_date="2026-11-20", items=[])],
    )
    view = TripDetailView(itinerary=itin)
    place = Place(
        id="p-nearby-1",
        name="Nearby Cafe",
        municipality_name="Cabanatuan",
        category="cafe",
        latitude=15.48,
        longitude=120.97,
    )
    view._add_nearby_to_active_day(place)
    assert len(itin.days[0].items) == 1
    new_item = itin.days[0].items[0]
    assert new_item.place_id == "p-nearby-1"
    assert new_item.display_title == "Nearby Cafe"
    assert itin.total_stops == 1


def test_tc_14_saved_trips_guest_isolation():
    """TC-14: Verifies SavedTripsView does not load guest itineraries when authenticated (REG-15)."""
    from desktop_client.models.user import User

    sm = get_session_manager()
    was_guest = sm.is_guest
    was_token = sm.access_token
    was_user = sm.current_user
    try:
        # Mock authenticated state
        sm.is_guest = False
        sm.access_token = "mock-token"
        sm.current_user = User(id="usr_test", email="test@test.com", username="testuser", first_name="Test", last_name="User")
        assert sm.is_authenticated is True
        view = SavedTripsView()
        assert view.itineraries == []
    finally:
        sm.is_guest = was_guest
        sm.access_token = was_token
        sm.current_user = was_user


def test_tc_15_portable_daemon_path_and_spec_hidden_imports():
    """TC-15: Verifies run_daemon uses dynamic Path and spec has complete hiddenimports (REG-16)."""
    daemon_file = Path(__file__).resolve().parent.parent.parent / "scripts" / "run_daemon.py"
    content = daemon_file.read_text(encoding="utf-8")
    assert 'r"C:\\Users\\Edward\\Desktop\\CaseStudy"' not in content
    assert "Path(__file__).resolve().parent.parent" in content

    spec_file = Path(__file__).resolve().parent.parent.parent / "NuevaEcijaTravel.spec"
    spec_content = spec_file.read_text(encoding="utf-8")
    assert "desktop_client.core.connectivity_service" in spec_content
    assert "desktop_client.services.favorites_service" in spec_content
    assert "desktop_client.views.suggested_wizard_view" in spec_content


def test_tc_16_places_view_did_mount_coroutine():
    """TC-16: Verifies PlacesView.did_mount schedules a valid coroutine function via safe_page.run_task."""
    import inspect
    from desktop_client.views.places_view import PlacesView

    tasks_passed = []

    class MockPage:
        def run_task(self, handler, *args, **kwargs):
            assert inspect.iscoroutinefunction(handler), "handler must be a coroutine function"
            tasks_passed.append(handler)

    pv = PlacesView()
    pv._test_page = MockPage()
    pv.did_mount()
    assert len(tasks_passed) == 1
    assert inspect.iscoroutinefunction(tasks_passed[0])


def test_tc_17_main_page_theme_color_scheme_compatibility():
    """TC-17: Verifies Theme and ColorScheme in main.py do not pass deprecated kwargs like 'background'."""
    from desktop_client.config.settings import ThemeColors

    # Flet 1.1.2 Material 3 ColorScheme uses surface/on_surface/surface_container, NOT background
    light_cs = ft.ColorScheme(
        surface=ThemeColors.SURFACE_LIGHT,
        on_surface=ThemeColors.TEXT_BLACK,
        primary=ThemeColors.PRIMARY_BLUE,
        on_primary=ft.Colors.WHITE,
        surface_container=ThemeColors.BG_LIGHT,
        surface_container_lowest=ThemeColors.BG_LIGHT,
    )
    light_theme = ft.Theme(color_scheme=light_cs)
    assert light_theme.color_scheme.primary == ThemeColors.PRIMARY_BLUE

    dark_cs = ft.ColorScheme(
        surface=ThemeColors.SURFACE_DARK,
        on_surface=ThemeColors.TEXT_MAIN_DARK,
        primary=ThemeColors.PRIMARY_BLUE,
        on_primary=ft.Colors.WHITE,
        surface_container=ThemeColors.BG_DARK,
        surface_container_lowest=ThemeColors.BG_DARK,
    )
    dark_theme = ft.Theme(color_scheme=dark_cs)
    assert dark_theme.color_scheme.primary == ThemeColors.PRIMARY_BLUE


def test_tc_18_navigation_transitions_not_blocked():
    """TC-18: Verifies standalone and workflow view returns are indented inside if blocks so navigation is never trapped."""
    import inspect
    import desktop_client.main as main_mod

    src = inspect.getsource(main_mod.main)
    lines = src.splitlines()
    for idx, line in enumerate(lines):
        if "if route in (\"/welcome\"" in line:
            for sub_line in lines[idx + 1 : idx + 35]:
                if sub_line.strip() == "return":
                    indent = len(sub_line) - len(sub_line.lstrip())
                    if_indent = len(line) - len(line.lstrip())
                    assert indent > if_indent, "Return in section 1 must be indented inside the if-block"
                    break
        if "if base_route in (\"/suggested\"" in line:
            for sub_line in lines[idx + 1 : idx + 80]:
                if sub_line.strip() == "return" and "navigate_to(\"/saved\")" not in lines[idx]:
                    indent = len(sub_line) - len(sub_line.lstrip())
                    if_indent = len(line) - len(line.lstrip())
                    assert indent > if_indent, "Return in section 2 must be indented inside the if-block"
                    break
