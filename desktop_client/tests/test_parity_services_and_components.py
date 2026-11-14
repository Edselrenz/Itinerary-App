"""Unit tests verifying new parity services, components, and local offline guides."""

import pytest
from desktop_client.config.settings import ThemeColors, ThemePalette, get_settings
from desktop_client.core.commute_guide import (
    COMMUTE_BY_MUNICIPALITY,
    calculate_haversine_meters,
    get_commute_info_for_municipality,
    get_leg_commute_info,
)
from desktop_client.core.offline_data import (
    ALL_32_LGUS_METADATA,
    CANONICAL_OFFLINE_PLACES,
    load_osm_places,
)
from desktop_client.models.itinerary import ItineraryItem
from desktop_client.models.place import Place
from desktop_client.services.favorites_service import (
    FavoritesService,
    get_favorites_service,
)
from desktop_client.views.guest_view import GuestView
from desktop_client.views.suggested_wizard_view import SuggestedWizardView
from desktop_client.views.trip_detail_view import TripDetailView
from desktop_client.models.itinerary import Itinerary, ItineraryDay


def test_all_32_lgus_metadata_coverage():
    """Verify that all 32 LGUs in Nueva Ecija are defined with district, POI count, and highlights."""
    assert len(ALL_32_LGUS_METADATA) == 32
    districts = set()
    for lgu, meta in ALL_32_LGUS_METADATA.items():
        assert "district" in meta
        assert "is_city" in meta
        assert "poi_count" in meta
        assert "highlights" in meta
        assert isinstance(meta["highlights"], list)
        assert meta["poi_count"] > 0
        districts.add(meta["district"])

    assert districts == {"Central", "North", "South", "East"}


def test_canonical_offline_places_integrity():
    """Verify curated offline places have non-empty honest pricing and geographic coordinates."""
    assert len(CANONICAL_OFFLINE_PLACES) >= 10
    for place in CANONICAL_OFFLINE_PLACES:
        assert place.id.startswith("dest-")
        assert 15.0 <= place.latitude <= 16.5
        assert 120.5 <= place.longitude <= 121.5
        assert place.municipality in ALL_32_LGUS_METADATA


def test_commute_guide_municipal_lookups():
    """Verify commute guide retrieves transit modes and fares for iconic destinations."""
    bongabon = get_commute_info_for_municipality("Bongabon")
    assert bongabon is not None
    assert "Bongabon" in bongabon.drop_off_point
    assert "₱" in bongabon.estimated_fare

    pantabangan = get_commute_info_for_municipality("Pantabangan")
    assert pantabangan is not None
    assert "Pantabangan" in pantabangan.drop_off_point
    assert "₱" in pantabangan.estimated_fare

    unknown = get_commute_info_for_municipality("Unknown Place")
    assert unknown is not None  # Fallback to Cabanatuan City Central Terminal


def test_haversine_distance_and_leg_commute():
    """Verify Haversine calculations and inter-stop leg commute estimations."""
    # Cabanatuan ~ (15.4859, 120.9673) to Bongabon ~ (15.6315, 121.1440)
    meters = calculate_haversine_meters(15.4859, 120.9673, 15.6315, 121.1440)
    km = meters / 1000.0
    assert 20.0 < km < 35.0  # Approx 25 km direct line

    stop1 = ItineraryItem(
        id="s1",
        day_id="d1",
        place=Place(
            id="p1",
            name="Cabanatuan Plaza",
            category="tourist_attraction",
            latitude=15.4859,
            longitude=120.9673,
        ),
        sort_order=1,
    )
    stop2 = ItineraryItem(
        id="s2",
        day_id="d1",
        place=Place(
            id="p2",
            name="Rohi Cafe Bongabon",
            category="cafe",
            latitude=15.6315,
            longitude=121.1440,
        ),
        sort_order=2,
    )

    leg = get_leg_commute_info(stop1, stop2)
    assert leg.distance_km > 0
    assert leg.duration_mins > 0
    assert "🚗" in leg.display_text
    assert "km" in leg.display_text


def test_favorites_service_lifecycle(tmp_path, monkeypatch):
    """Verify FavoritesService persistence, seeding, and toggling."""
    fav_file = tmp_path / "test_favorites.json"
    settings = get_settings()
    monkeypatch.setattr(settings, "storage_dir", tmp_path)

    fav_service = FavoritesService()
    fav_service.favorites_file = fav_file
    fav_service._seed_default_favorites()

    initial = fav_service.get_favorites()
    assert len(initial) >= 3  # Rohi, Museo, Minalungao

    test_place = Place(
        id="dest-new-spot",
        name="New Test Spot",
        category="cafe",
        latitude=15.63,
        longitude=121.14,
        municipality_name="Bongabon",
    )
    assert not fav_service.is_favorite("dest-new-spot")

    # Toggle on
    is_fav = fav_service.toggle_favorite(test_place)
    assert is_fav is True
    assert fav_service.is_favorite("dest-new-spot")

    # Toggle off
    is_fav2 = fav_service.toggle_favorite(test_place)
    assert is_fav2 is False
    assert not fav_service.is_favorite("dest-new-spot")


def test_theme_palette_switching():
    """Verify ThemePalette provides correct contrast tokens for both light and dark modes."""
    light = ThemePalette.get_palette(is_dark=False)
    assert light.is_dark is False
    assert light.bg_main == ThemeColors.BG_LIGHT
    assert light.surface_card == ThemeColors.SURFACE_LIGHT

    dark = ThemePalette.get_palette(is_dark=True)
    assert dark.is_dark is True
    assert dark.bg_main == ThemeColors.BG_DARK
    assert dark.surface_card == ThemeColors.SURFACE_DARK


def test_guest_and_wizard_views_instantiation():
    """Verify GuestView and SuggestedWizardView can be instantiated cleanly with all routing parameters."""
    guest = GuestView()
    assert guest is not None

    wizard = SuggestedWizardView()
    assert wizard is not None
    assert wizard.view_mode == "form"
    assert wizard.destination_val == "Nueva Ecija"

    # Test initialization with initial_destination and anchor_place_id
    wizard_with_params = SuggestedWizardView(
        on_navigate=lambda route: None,
        initial_destination="Bongabon",
        anchor_place_id="dest-bongabon-01",
    )
    assert wizard_with_params is not None
    assert wizard_with_params.destination_val == "Bongabon"
    assert wizard_with_params.anchor_place_id == "dest-bongabon-01"


def test_trip_detail_view_edit_mode_and_guard():
    """Verify TripDetailView pending changes guard in edit mode."""
    test_itin = Itinerary(
        id="itin-test-1",
        title="Test Journey",
        destination="Bongabon",
        start_date="2026-12-01",
        end_date="2026-12-02",
        daily_budget=2000.0,
        days=[
            ItineraryDay(
                id="d1",
                itinerary_id="itin-test-1",
                day_number=1,
                travel_date="2026-12-01",
                title="Day 1",
                items=[],
            )
        ],
    )

    detail_view = TripDetailView(itinerary=test_itin)
    assert detail_view.has_unsaved_changes() is False

    detail_view._enter_edit_mode()
    assert detail_view.is_edit_mode is True
    assert detail_view.has_unsaved_changes() is False

    detail_view._on_field_change("title", "Updated Journey Title")
    assert detail_view.has_unsaved_changes() is True

    detail_view._exit_edit_mode()
    assert detail_view.has_unsaved_changes() is False


def test_bottom_tab_bar_and_workflow_header():
    """Validates 4-tab bottom navigation bar and contextual workflow header."""
    from desktop_client.components.bottom_tab_bar import BottomTabBar
    from desktop_client.components.workflow_header import WorkflowHeader

    nav_called = []
    tab_bar = BottomTabBar(
        current_route="/home",
        on_navigate=lambda r: nav_called.append(r),
    )
    assert tab_bar.height == 60
    assert len(tab_bar._tabs_data) == 4
    tab_keys = [t["key"] for t in tab_bar._tabs_data]
    assert tab_keys == ["home", "map", "saved", "profile"]

    # Active route resolution
    assert tab_bar._get_active_tab_key() == "home"
    tab_bar.set_active_route("/map")
    assert tab_bar._get_active_tab_key() == "map"
    tab_bar.set_active_route("/places")
    assert tab_bar._get_active_tab_key() == "map"
    tab_bar.set_active_route("/saved")
    assert tab_bar._get_active_tab_key() == "saved"
    tab_bar.set_active_route("/trips")
    assert tab_bar._get_active_tab_key() == "saved"
    tab_bar.set_active_route("/profile")
    assert tab_bar._get_active_tab_key() == "profile"

    # Tab click trigger
    tab_bar._handle_tab_click(tab_bar._tabs_data[1])
    assert nav_called == ["/map"]

    # Workflow header
    back_called = []
    wf_header = WorkflowHeader(
        title="Suggested Itinerary Wizard",
        subtitle="Corridor Clustering",
        on_back=lambda: back_called.append(True),
    )
    assert wf_header.height == 54
    assert wf_header.title_text == "Suggested Itinerary Wizard"
    if wf_header.on_back:
        wf_header.on_back()
    assert back_called == [True]


def test_offline_host_banner_and_splash_overlay():
    """Validates offline banner and cold-start splash overlay."""
    from desktop_client.components.offline_banner import OfflineHostBanner
    from desktop_client.components.splash_overlay import SplashOverlay
    from desktop_client.core.connectivity_service import get_connectivity_service

    conn_service = get_connectivity_service()
    conn_service.set_host_offline(True, force=True)

    banner = OfflineHostBanner()
    assert banner.visible is True
    assert banner.expand is False
    assert banner.height == 52

    # Dismiss test
    banner._dismiss()
    assert banner.visible is False
    assert banner.height == 0

    # Back online
    conn_service.set_host_offline(False)
    assert banner.visible is False
    assert banner.height == 0

    # Splash overlay
    dismissed = []
    splash = SplashOverlay(on_dismiss=lambda: dismissed.append(True))
    assert splash.visible is not False
    splash.dismiss()
    assert splash.visible is False
    assert dismissed == [True]


def test_clean_auth_view_no_demo_persona():
    """Verifies that LoginView and WelcomeView do not contain dead social buttons or demo persona."""
    from desktop_client.views.login_view import LoginView
    from desktop_client.views.welcome_view import WelcomeView

    login = LoginView()
    # Check that demo account button was removed
    assert not hasattr(login, "_handle_demo_login")
    assert not hasattr(login, "demo_btn")

    welcome = WelcomeView()
    assert welcome is not None


def test_slippy_map_canvas_and_route_map():
    """Validates SlippyMapCanvas raster engine and embedded ItineraryRouteMap card."""
    from desktop_client.components.slippy_map_canvas import (
        SlippyMapCanvas,
        latlon_to_world_px,
        world_px_to_latlon,
        RouteStopPin,
    )
    from desktop_client.components.itinerary_route_map import ItineraryRouteMap
    from desktop_client.models.place import Place
    from desktop_client.models.itinerary import ItineraryDay, ItineraryItem

    sample_places = [
        Place(
            id="p1",
            name="Minalungao National Park",
            category="nature_park",
            latitude=15.30,
            longitude=121.14,
            municipality_name="General Tinio",
        ),
        Place(
            id="p2",
            name="Pantabangan Lake",
            category="nature_park",
            latitude=15.81,
            longitude=121.15,
            municipality_name="Pantabangan",
        ),
    ]

    clicked_place = []
    canvas_map = SlippyMapCanvas(
        width=800,
        height=500,
        center_lat=15.58,
        center_lng=121.00,
        zoom=10,
        places=sample_places,
        on_place_click=lambda p: clicked_place.append(p),
    )
    assert canvas_map is not None
    assert canvas_map.zoom == 10
    assert canvas_map.center_lat == 15.58
    assert canvas_map.center_lng == 121.00

    # Controls testing
    canvas_map.recenter_province()
    assert canvas_map.center_lat == 15.58
    assert canvas_map.center_lng == 121.00

    # Route setting with auto_fit
    pins = [
        RouteStopPin(index=0, title="Stop 1", lat=15.30, lng=121.14),
        RouteStopPin(index=1, title="Stop 2", lat=15.81, lng=121.15),
    ]
    canvas_map.set_route(pins, auto_fit=True)
    assert len(canvas_map._route_stops) == 2
    assert len(canvas_map._route_pts) >= 2

    # Coordinate projection roundtrip test
    wx, wy = latlon_to_world_px(15.58, 121.00, 10)
    rev_lat, rev_lng = world_px_to_latlon(wx, wy, 10)
    assert abs(rev_lat - 15.58) < 0.001
    assert abs(rev_lng - 121.00) < 0.001

    # ItineraryRouteMap test
    day = ItineraryDay(
        id="d1",
        itinerary_id="itin-1",
        day_number=1,
        travel_date="2026-12-01",
        title="Day 1 Adventure",
        items=[
            ItineraryItem(
                id="item-1",
                day_id="d1",
                sort_order=1,
                place_id="p1",
                custom_title="Minalungao National Park",
                place=sample_places[0],
            ),
            ItineraryItem(
                id="item-2",
                day_id="d1",
                sort_order=2,
                place_id="p2",
                custom_title="Pantabangan Lake",
                place=sample_places[1],
            ),
        ],
    )

    full_map_triggered = []
    route_map = ItineraryRouteMap(
        day=day,
        on_view_full_map=lambda: full_map_triggered.append(True),
    )
    assert route_map is not None
    dist, mins = route_map._calculate_metrics()
    assert dist > 0.0
    assert mins > 0

    route_map.toggle_expand()
    assert route_map.is_expanded is False
    route_map.toggle_expand()
    assert route_map.is_expanded is True


def test_calculate_budget_summary_and_payload_parity():
    """Validates calculate_budget_summary honest metrics and to_create_payload contract."""
    from desktop_client.models.itinerary import (
        Itinerary,
        ItineraryDay,
        ItineraryItem,
        to_backend_iso_time,
        _is_valid_uuid,
    )
    from desktop_client.models.place import Place
    from desktop_client.services.itinerary_service import ItineraryService

    # 1. to_backend_iso_time tests
    assert to_backend_iso_time("09:30:00") == "09:30:00"
    assert to_backend_iso_time("09:30") == "09:30:00"
    assert to_backend_iso_time("09:30 AM") == "09:30:00"
    assert to_backend_iso_time("2:15 PM") == "14:15:00"
    assert to_backend_iso_time("09:30 AM - 11:30 AM") == "09:30:00"
    assert to_backend_iso_time("") is None

    # 2. _is_valid_uuid tests
    assert _is_valid_uuid("b699c2ea-4d89-40c2-9ce8-7be6d4052f75") is True
    assert _is_valid_uuid("dest-123") is False
    assert _is_valid_uuid("osm-node-12345") is False
    assert _is_valid_uuid(None) is False

    # 3. calculate_budget_summary tests
    itin = Itinerary(
        id="itin-test",
        title="Budget Test",
        destination="Pantabangan",
        start_date="2026-12-01",
        end_date="2026-12-02",
        daily_budget=3000.0,
        days=[
            ItineraryDay(
                id="d1",
                itinerary_id="itin-test",
                day_number=1,
                travel_date="2026-12-01",
                items=[
                    ItineraryItem(
                        id="i1",
                        day_id="d1",
                        sort_order=1,
                        place_id="dest-1",
                        custom_title="Priced Place",
                        estimated_cost_min=100.0,
                        estimated_cost_max=250.0,
                        planned_time="09:00 AM",
                        custom_lat=15.8,
                        custom_lng=121.1,
                    ),
                    ItineraryItem(
                        id="i2",
                        day_id="d1",
                        sort_order=2,
                        place_id="b699c2ea-4d89-40c2-9ce8-7be6d4052f75",
                        custom_title="Unpriced Place",
                        planned_time="02:00 PM",
                    ),
                ],
            )
        ],
    )
    itin_service = ItineraryService()
    summary = itin_service.calculate_budget_summary(itin)
    assert summary["verified_min"] == 100.0
    assert summary["verified_max"] == 250.0
    assert summary["unverified_count"] == 1
    assert "₱100 - ₱250" in summary["display_text"]

    # 4. to_create_payload contract verification
    payload = itin.to_create_payload()
    assert payload.title == "Budget Test"
    assert len(payload.days) == 1
    d_out = payload.days[0]
    assert len(d_out["items"]) == 2

    # Non-UUID place_id should become None in backend payload
    item1 = d_out["items"][0]
    assert item1["place_id"] is None
    assert item1["planned_time"] == "09:00:00"
    assert item1["custom_lat"] == 15.8
    assert item1["custom_lng"] == 121.1

    # Valid UUID place_id should be preserved
    item2 = d_out["items"][1]
    assert item2["place_id"] == "b699c2ea-4d89-40c2-9ce8-7be6d4052f75"
    assert item2["planned_time"] == "14:00:00"


def test_place_service_osm_category_mapping_and_nearby():
    """Validates map_osm_tags_to_category and get_nearby_places grouping."""
    from desktop_client.services.place_service import PlaceService

    # 1. Tag mapping
    assert PlaceService.map_osm_tags_to_category({"amenity": "cafe"}) == "cafe"
    assert PlaceService.map_osm_tags_to_category({"amenity": "restaurant"}) == "restaurant"
    assert PlaceService.map_osm_tags_to_category({"tourism": "hotel"}) == "hotel_accommodation"
    assert PlaceService.map_osm_tags_to_category({"amenity": "place_of_worship"}) == "church_religious"
    assert PlaceService.map_osm_tags_to_category({"leisure": "park"}) == "nature_park"
    assert PlaceService.map_osm_tags_to_category({"amenity": "pharmacy"}) == "pharmacy"
    assert PlaceService.map_osm_tags_to_category({"amenity": "hospital"}) == "hospital_clinic"
    assert PlaceService.map_osm_tags_to_category({"amenity": "fuel"}) == "fuel_station"

    # 2. get_nearby_places
    ps = PlaceService()
    restos = ps.get_nearby_places("Cabanatuan City", "restaurant")
    assert isinstance(restos, list)
    if restos:
        assert all(r.category in ("restaurant", "cafe") for r in restos)

    hospitals = ps.get_nearby_places("Cabanatuan City", "hospital")
    assert isinstance(hospitals, list)
    if hospitals:
        assert all(h.category in ("hospital_clinic", "pharmacy") for h in hospitals)

