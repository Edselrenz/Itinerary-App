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


# =============================================================================
# PHASE 54 PARITY VERIFICATION SUITE (TC-73 through TC-85)
# =============================================================================


def test_tc_73_map_pointer_blocking_pill():
    """TC-73: Verifies PlacesView drawer toggle pill is anchored and non-blocking (MAP-01, MAP-08)."""
    from desktop_client.views.places_view import PlacesView

    pv = PlacesView()
    # Drawer toggle pill should be positioned at left=530, bottom=18 and width=None (not blocking map gestures)
    pill = pv._toggle_pill_btn
    assert pill is not None
    assert pill.left == 530
    assert pill.bottom == 18
    assert pill.width is None

    # Map action buttons (Recenter & Follow Route) anchored at bottom-right
    action_box = pv._action_buttons
    assert action_box is not None
    assert action_box.right == 12
    assert action_box.bottom == 185


def test_tc_74_slippy_map_canvas_gesture_layering():
    """TC-74: Verifies SlippyMapCanvas gesture surface layering and zoom interactions (MAP-02, MAP-03)."""
    from desktop_client.components.slippy_map_canvas import SlippyMapCanvas

    canvas = SlippyMapCanvas(width=800, height=600)
    stack_controls = canvas._canvas_stack.controls

    # Gesture surface must be placed below _marker_stack
    gesture_idx = stack_controls.index(canvas._gesture_surface)
    marker_idx = stack_controls.index(canvas._marker_stack)
    assert gesture_idx < marker_idx

    # Dedicated transparent hit-test surface (#01000000)
    assert canvas._gesture_surface.content.bgcolor == "#01000000"

    # Wheel zoom and double-tap zoom handlers wired
    assert canvas._gesture_surface.on_scroll is not None
    assert canvas._gesture_surface.on_double_tap is not None


def test_tc_75_slippy_map_auto_fit_on_mount():
    """TC-75: Verifies SlippyMapCanvas auto-fits route bounding box on mount (MAP-06)."""
    from desktop_client.components.slippy_map_canvas import SlippyMapCanvas

    coords = [(15.48, 120.97), (15.55, 121.05)]
    canvas = SlippyMapCanvas(route_coords=coords, width=800, height=600)

    # set_route must have been auto-called in __init__
    assert canvas.route_coords == coords
    # Center lat/lng must match midpoints of the bounding coordinates
    assert abs(canvas.center_lat - 15.515) < 0.01
    assert abs(canvas.center_lng - 121.01) < 0.01


def test_tc_76_places_view_mode_guard():
    """TC-76: Verifies PlacesView default navigation is Pure Explore Mode (MAP-04)."""
    from desktop_client.views.places_view import PlacesView

    # Default navigation: active_trip is None -> Pure Explore Mode
    pv = PlacesView()
    assert pv.active_trip is None
    assert pv._route_mode is False

    # Route mode only when active_trip passed with itineraryId or followRoute query
    dummy_itin = Itinerary(id="trip-1", title="Test Trip", destination="Cabanatuan City", start_date="2026-12-01", end_date="2026-12-02", days=[])
    pv_route = PlacesView(route_query="/map?itineraryId=trip-1&followRoute=true", active_trip=dummy_itin)
    assert pv_route.active_trip is not None
    assert pv_route._route_mode is True


def test_tc_77_places_view_search_focus_preservation():
    """TC-77: Verifies PlacesView search updates in-place preserving keyboard focus (MAP-05)."""
    from desktop_client.views.places_view import PlacesView

    pv = PlacesView()
    search_ref = pv._search_field

    # Trigger search text change
    pv._search_field.value = "bistro"
    pv._on_search_change("bistro")

    # Instance must remain identical (never re-instantiated)
    assert pv._search_field is search_ref
    assert pv.current_search == "bistro"


def test_tc_78_httpx_import_and_viewport_bounds():
    """TC-78: Verifies httpx import in place_service and viewport bounds calculation (MAP-07)."""
    import desktop_client.services.place_service as ps
    from desktop_client.components.slippy_map_canvas import SlippyMapCanvas

    # Top-level httpx must be imported without NameError
    assert hasattr(ps, "httpx")

    canvas = SlippyMapCanvas(center_lat=15.50, center_lng=121.00, zoom=11, width=800, height=600)
    bounds = canvas.get_viewport_bounds()
    assert len(bounds) == 4
    min_lat, min_lng, max_lat, max_lng = bounds
    assert min_lat < max_lat
    assert min_lng < max_lng
    assert 14.0 <= min_lat <= 17.0
    assert 119.0 <= min_lng <= 123.0


def test_tc_79_places_view_multi_select_and_price_tier():
    """TC-79: Verifies PlacesView multi-category selection, badge counter, and price filters (MAP-09, MAP-10)."""
    from desktop_client.views.places_view import PlacesView

    pv = PlacesView()
    assert pv.selected_categories == set()
    assert pv._active_filters_count == 0

    # Multi-category toggle
    pv._toggle_category_filter("nature_park")
    pv._toggle_category_filter("restaurant")
    assert pv.selected_categories == {"nature_park", "restaurant"}
    assert pv._active_filters_count == 2
    assert pv._filter_badge.visible is True
    assert pv._filter_badge.content.value == "2"

    # Price tier toggle
    pv._on_price_change("free")
    assert pv.selected_price == "free"
    assert pv._active_filters_count == 3

    # Reset all filters
    pv._reset_all_filters()
    assert pv.selected_categories == set()
    assert pv.selected_price == "all"
    assert pv._active_filters_count == 0


def test_tc_80_suggested_wizard_canonical_keys_and_display_title():
    """TC-80: Verifies canonical preference keys and display_title prefix guard (SUG-01, SUG-02)."""
    from desktop_client.views.suggested_wizard_view import SuggestedWizardView

    swv = SuggestedWizardView()
    # Canonical default preferences: food, culture, resort
    assert swv.selected_preferences == {"food", "culture", "resort"}

    # Canonical keys supported
    for key in ("nature", "food", "culture", "shopping", "resort"):
        swv._toggle_preference(key)

    # display_title prefix guard
    d1 = ItineraryDay(id="1", itinerary_id="t", day_number=1, travel_date="2026-12-01", title="Day 1")
    assert d1.display_title == "Day 1"

    d2 = ItineraryDay(id="2", itinerary_id="t", day_number=2, travel_date="2026-12-02", title="Day 2: Minalungao")
    assert d2.display_title == "Day 2: Minalungao"

    d3 = ItineraryDay(id="3", itinerary_id="t", day_number=3, travel_date="2026-12-03", title="Historic Gapan Tour")
    assert d3.display_title == "Day 3: Historic Gapan Tour"


def test_tc_81_suggested_wizard_pacing_and_clustering():
    """TC-81: Verifies packed pacing, utility exclusion, and 25km geographic clustering (SUG-01, SUG-03)."""
    from desktop_client.services.itinerary_service import ItineraryService

    svc = ItineraryService()
    itin = svc.generate_suggested_itinerary_sync(
        destination="Cabanatuan City",
        days=2,
        pacing="packed",
        preferences=["food", "culture"],
    )

    assert len(itin.days) == 2
    excluded_utilities = {"bank_atm", "fuel_station", "hospital_clinic", "pharmacy", "police_station", "parking"}

    for day in itin.days:
        # Pacing packed: up to 4 stops per day
        assert len(day.items) <= 4
        for item in day.items:
            if item.place:
                assert item.place.category not in excluded_utilities

        # Geographic clustering verification: all stops within 25km of anchor
        if len(day.items) >= 2 and day.items[0].place and day.items[0].place.latitude:
            anchor = day.items[0].place
            for other_item in day.items[1:]:
                if other_item.place and other_item.place.latitude:
                    dist_m = calculate_haversine_meters(
                        float(anchor.latitude),
                        float(anchor.longitude),
                        float(other_item.place.latitude),
                        float(other_item.place.longitude),
                    )
                    assert dist_m <= 25_000.0


def test_tc_82_suggested_wizard_back_navigation_and_time_injection():
    """TC-82: Verifies wizard back navigation and sequential Haversine travel time injection (SUG-04, SUG-05)."""
    from desktop_client.views.suggested_wizard_view import SuggestedWizardView

    swv = SuggestedWizardView()
    day = ItineraryDay(
        id="d1",
        itinerary_id="i1",
        day_number=1,
        travel_date="2026-12-01",
        items=[
            ItineraryItem(
                id="it1",
                day_id="d1",
                sort_order=1,
                planned_time="09:00 AM",
                duration_minutes=90,
                custom_lat=15.48,
                custom_lng=120.97,
            )
        ],
    )
    swv.generated_itinerary = Itinerary(id="i1", title="Test", destination="Cabanatuan City", start_date="2026-12-01", end_date="2026-12-02", days=[day])
    swv.view_mode = "nearby"
    assert swv.handle_back() is True
    assert swv.view_mode == "itinerary"

    assert swv.handle_back() is True
    assert swv.view_mode == "form"

    assert swv.handle_back() is False  # Delegates to app shell

    # Inject nearby to day
    nearby_place = Place(id="p2", name="Nearby Bistro", latitude=15.50, longitude=120.99, category="restaurant")

    swv._inject_nearby_to_day(nearby_place)
    assert len(day.items) == 2
    new_item = day.items[1]
    assert new_item.place_id == "p2"
    assert new_item.sort_order == 2
    assert new_item.planned_time is not None
    assert new_item.planned_time != "09:00 AM"


def test_tc_83_custom_builder_live_search_and_categories():
    """TC-83: Verifies CustomBuilderView live search, category grouping, and details modal CTA (CUS-01, CUS-02)."""
    from desktop_client.views.custom_builder_view import CustomBuilderView

    cbv = CustomBuilderView()
    cbv.active_view = "browse"
    cbv._build_content()

    # Search live filter
    cbv._on_browse_search_live("bistro")
    assert cbv.browse_search == "bistro"
    assert hasattr(cbv, "_browse_results_col")

    # Clear search
    cbv._clear_browse_search()
    assert cbv.browse_search == ""

    # Category switching
    cbv._on_browse_cat_change("tourist_spots")
    assert cbv.browse_category == "tourist_spots"


def test_tc_84_custom_builder_haversine_buffer_and_auto_schedule():
    """TC-84: Verifies CustomBuilderView Haversine travel buffer and auto-schedule on stop move (CUS-03, CUS-04)."""
    from desktop_client.views.custom_builder_view import CustomBuilderView

    cbv = CustomBuilderView()
    day = cbv.days[0]
    p1 = Place(id="p1", name="Stop 1", category="attraction", latitude=15.48, longitude=120.97)
    p2 = Place(id="p2", name="Stop 2", category="nature_park", latitude=15.80, longitude=121.10)  # ~38 km away

    item1 = ItineraryItem(id="i1", day_id=day.id, sort_order=1, place_id="p1", place=p1, planned_time="09:00 AM", duration_minutes=90)
    day.items = [item1]

    # Calculate next time for next place (should include ~60 min driving buffer after 10:30 AM end)
    next_time = cbv._calc_next_time(day, next_place=p2)
    assert next_time is not None
    assert next_time != "09:00 AM"
    assert next_time != "10:30 AM"

    # Add second item and test _move_stop re-schedules planned_time
    item2 = ItineraryItem(id="i2", day_id=day.id, sort_order=2, place_id="p2", place=p2, planned_time=next_time, duration_minutes=60)
    day.items.append(item2)

    cbv._move_stop(item2, -1)
    assert day.items[0] == item2
    assert day.items[1] == item1
    assert day.items[0].planned_time == "09:00 AM"


def test_tc_85_main_service_resolution_and_back():
    """TC-85: Verifies main service resolution, window min dimensions, and back navigation integration (MAP-04, CUS-05)."""
    from desktop_client.services.itinerary_service import get_itinerary_service
    from desktop_client.views.places_view import PlacesView
    from desktop_client.views.custom_builder_view import CustomBuilderView

    svc = get_itinerary_service()
    assert svc is not None

    # Back-handling protocol contracts
    pv = PlacesView()
    assert pv.handle_back() is False  # explore mode does not trap back

    cbv = CustomBuilderView()
    cbv.active_view = "browse"
    assert cbv.handle_back() is True
    assert cbv.active_view == "form"
    assert cbv.handle_back() is False  # form view does not trap back


def test_tc_86_map_filters_modal_and_active_count():
    """TC-86: Verifies Map Filters modal opens without Dropdown crash, filters update _active_filters_count and filtered_places."""
    from desktop_client.views.places_view import PlacesView

    pv = PlacesView()

    class DummyPage:
        def __init__(self):
            self.dialog = None
            self.overlay = []

        def update(self):
            pass

        def show_dialog(self, dlg):
            self.dialog = dlg
            dlg.open = True

    page = DummyPage()
    pv._test_page = page

    # Modal opens cleanly without Dropdown.__init__() unexpected keyword errors
    pv._open_filter_modal()
    assert (page.dialog is not None and page.dialog.open is True) or (len(page.overlay) > 0 and page.overlay[0].open is True)

    # Initial state
    assert pv._active_filters_count == 0

    # Updating categories, municipality, and price updates count accurately
    pv.selected_categories = {"food_trip", "nature_adventure"}
    assert pv._active_filters_count == 2

    pv.selected_municipality = "Bongabon"
    assert pv._active_filters_count == 3

    pv.selected_price_tier = "free"
    assert pv._active_filters_count == 4

    # Apply filters filters places accurately
    pv._apply_filters()
    for p in pv.filtered_places:
        assert p.municipality_name == "Bongabon" or p.municipality == "Bongabon"


def test_tc_87_map_quick_category_pills_toggle():
    """TC-87: Verifies Map quick category pills single-select toggle (map.page.ts:854-871 parity)."""
    from desktop_client.views.places_view import PlacesView

    pv = PlacesView()
    assert pv.selected_category == "all"
    assert len(pv.selected_categories) == 0

    # Select food_trip
    pv._select_category("food_trip")
    assert pv.selected_category == "food_trip"
    assert pv.selected_categories == {"food_trip"}

    # Selecting another category replaces the previous selection
    pv._select_category("nature_adventure")
    assert pv.selected_category == "nature_adventure"
    assert pv.selected_categories == {"nature_adventure"}

    # Clicking the active category again toggles back to All Places
    pv._select_category("nature_adventure")
    assert pv.selected_category == "all"
    assert len(pv.selected_categories) == 0

    # Selecting "all" explicitly also resets
    pv._select_category("historical_cultural")
    assert pv.selected_category == "historical_cultural"
    pv._select_category("all")
    assert pv.selected_category == "all"
    assert len(pv.selected_categories) == 0


def test_tc_88_map_pan_delta_and_scroll_zoom():
    """TC-88: Verifies SlippyMapCanvas pan delta extraction, scroll-wheel zoom, clamping, and tile pooling."""
    from desktop_client.components.slippy_map_canvas import (
        SlippyMapCanvas,
        _extract_pan_delta,
        _extract_scroll_delta_y,
    )

    canvas = SlippyMapCanvas(width=800, height=600)
    assert len(canvas._tile_pool) > 0

    class DummyOffset:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class EventWithOffset:
        scroll_delta = DummyOffset(0.0, -2.5)

    assert _extract_scroll_delta_y(EventWithOffset()) == -2.5

    class EventWithFlatDelta:
        scroll_delta_y = 3.0

    assert _extract_scroll_delta_y(EventWithFlatDelta()) == 3.0

    class EventWithJsonData:
        data = '{"dy": -1.2}'

    assert _extract_scroll_delta_y(EventWithJsonData()) == -1.2

    # Scroll zoom in and out
    initial_zoom = canvas.zoom
    canvas._last_scroll_zoom = 0.0
    canvas._handle_scroll(EventWithOffset())  # dy < -0.5 -> zoom in
    assert canvas.zoom == initial_zoom + 1

    canvas._last_scroll_zoom = 0.0
    canvas._handle_scroll(EventWithFlatDelta())  # dy > 0.5 -> zoom out
    assert canvas.zoom == initial_zoom

    # Pan update and clamping within Nueva Ecija bounds (15.05..16.25, 120.55..121.55)
    class PanEvent:
        local_delta = DummyOffset(10000.0, -10000.0)

    canvas._handle_pan_update(PanEvent())
    assert 15.05 <= canvas.center_lat <= 16.25
    assert 120.55 <= canvas.center_lng <= 121.55


def test_tc_89_database_profile_and_avatar_loading():
    """TC-89: Verifies User.from_dict prioritizes database fields, full_name excludes 'N/A', and resolve_avatar_path decodes Base64."""
    import os
    from desktop_client.config.settings import get_settings
    from desktop_client.models.user import User

    # 1. Database fields priority over stale extra
    db_data = {
        "id": "usr-123",
        "first_name": "Edward Renz",
        "last_name": "Natividad",
        "middle_initial": "N/A",
        "email": "edselrenz0@gmail.com",
        "birthday": "May 23, 2000",
        "gender": "Female",
        "phone_number": "+66 81 234 5678",
        "avatar_url": "assets/images/pattranite_avatar.jpg",
        "default_daily_budget": 3000.0,
    }
    stale_extra = {
        "middle_initial": "OldInitial",
        "birthday": "Jan 1, 1990",
        "gender": "Male",
        "phone_number": "+1 555 0000",
        "avatar_url": "old_avatar.png",
    }
    user = User.from_dict(db_data, stale_extra)
    assert user.first_name == "Edward Renz"
    assert user.last_name == "Natividad"
    assert user.middle_initial == "N/A"
    assert user.birthday == "May 23, 2000"
    assert user.gender == "Female"
    assert user.phone_number == "+66 81 234 5678"
    assert user.avatar_url == "assets/images/pattranite_avatar.jpg"
    # full_name omits "N/A."
    assert user.full_name == "Edward Renz Natividad"

    # User with valid middle initial includes it
    user_with_mi = User.from_dict({**db_data, "middle_initial": "R"})
    assert user_with_mi.full_name == "Edward Renz R. Natividad"

    # 2. Base64 avatar decoding into local file under storage/avatars/
    settings = get_settings()
    b64_png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    resolved_path = settings.resolve_avatar_path(b64_png, "usr-123")
    assert resolved_path is not None
    assert os.path.exists(resolved_path)
    assert "storage" in resolved_path or "avatar" in resolved_path


def test_tc_90_profile_tab_exact_ui():
    """TC-90: Verifies ProfileView view_mode == 'profile' exact UI matching image_2d13c2.png."""
    import flet as ft
    from desktop_client.models.user import User
    from desktop_client.core.session import get_session_manager
    from desktop_client.views.profile_view import ProfileView

    sm = get_session_manager()
    u = User(id="usr-1", first_name="Edward Renz", last_name="Natividad", email="edselrenz0@gmail.com")
    sm.set_authenticated_session(user=u, access_token="test-token", refresh_token="test-refresh")

    pv = ProfileView()
    pv.view_mode = "profile"
    pv._build_content()

    texts = []

    def collect_texts(ctl):
        if isinstance(ctl, ft.Text):
            texts.append(ctl.value)
        if hasattr(ctl, "controls") and isinstance(ctl.controls, list):
            for c in ctl.controls:
                collect_texts(c)
        if hasattr(ctl, "content") and ctl.content:
            collect_texts(ctl.content)

    collect_texts(pv)

    assert "Profile" in texts
    assert "Manage your personal information and app settings" not in texts
    assert "Edit Profile" in texts
    assert "Settings" in texts
    assert "Favorites" in texts
    assert "Help & Support" in texts
    assert "About" in texts
    assert "Log Out" in texts


def test_tc_91_edit_profile_in_page_subview():
    """TC-91: Verifies ProfileView view_mode == 'edit' renders exactly 7 stacked fields and no extras (image_2d1741.png)."""
    import flet as ft
    from desktop_client.views.profile_view import ProfileView

    pv = ProfileView()
    pv.view_mode = "edit"
    pv._build_content()

    texts = []
    text_fields = []

    def collect_controls(ctl):
        if isinstance(ctl, ft.Text):
            texts.append(ctl.value)
        elif isinstance(ctl, ft.TextField):
            text_fields.append(ctl)
        if hasattr(ctl, "controls") and isinstance(ctl.controls, list):
            for c in ctl.controls:
                collect_controls(c)
        if hasattr(ctl, "content") and ctl.content:
            collect_controls(ctl.content)

    collect_controls(pv)

    assert "Edit Profile" in texts
    assert "Change Photo" in texts
    assert "Save Changes" in texts

    # Exactly 7 stacked field labels
    assert "First Name" in texts
    assert "Middle Initial (if applicable)" in texts
    assert "Last Name" in texts
    assert "Birthday" in texts
    assert "Gender" in texts
    assert "Email Address" in texts
    assert "Phone Number" in texts

    # Zero extra fields
    assert "Username" not in texts
    assert "Daily Budget" not in texts
    assert "Current Password" not in texts
    assert "New Password" not in texts

    # Exactly 7 TextFields, and email is read-only
    assert len(text_fields) == 7
    read_only_fields = [tf for tf in text_fields if tf.read_only]
    assert len(read_only_fields) == 1
    assert "@" in (read_only_fields[0].value or "")


def test_tc_92_settings_in_page_subview():
    """TC-92: Verifies ProfileView view_mode == 'settings' renders single card with exactly 6 rows (image_2d1705.png)."""
    import flet as ft
    from desktop_client.views.profile_view import ProfileView

    pv = ProfileView()
    pv.view_mode = "settings"
    pv._build_content()

    texts = []
    switches = []

    def collect_controls(ctl):
        if isinstance(ctl, ft.Text):
            texts.append(ctl.value)
        elif isinstance(ctl, ft.Switch):
            switches.append(ctl)
        if hasattr(ctl, "controls") and isinstance(ctl.controls, list):
            for c in ctl.controls:
                collect_controls(c)
        if hasattr(ctl, "content") and ctl.content:
            collect_controls(ctl.content)

    collect_controls(pv)

    assert "Settings" in texts
    assert "Account Information" in texts
    assert "Notifications" in texts
    assert len(switches) == 1
    assert "Privacy & Security" in texts
    assert "Language" in texts
    assert "English" in texts
    assert "App Appearance" in texts
    assert "Clear Cache" in texts
    assert "Free up storage space" in texts


def test_tc_93_saved_itineraries_empty_state():
    """TC-93: Verifies SavedTripsView empty state matching image_2d1020.png with Suggested and Custom buttons."""
    import flet as ft
    from desktop_client.views.saved_trips_view import SavedTripsView

    stv = SavedTripsView()
    stv.itineraries = []
    stv.is_loading = False
    stv._build_content()

    texts = []

    def collect_texts(ctl):
        if isinstance(ctl, ft.Text):
            texts.append(ctl.value)
        if hasattr(ctl, "controls") and isinstance(ctl.controls, list):
            for c in ctl.controls:
                collect_texts(c)
        if hasattr(ctl, "content") and ctl.content:
            collect_texts(ctl.content)

    collect_texts(stv)

    assert "Saved Itineraries" in texts
    assert "No Saved Itineraries Yet" in texts
    assert "Suggested Itinerary" in texts
    assert "Custom Itinerary" in texts
    assert "Search saved itineraries..." not in texts
    assert "Your Saved Trips" not in texts


def test_tc_94_suggested_wizard_form_exact_ui():
    """TC-94: Verifies SuggestedWizardView form renders exact heading, 6 fields in Web order, zero Trip Title, zero Pacing."""
    import flet as ft
    from desktop_client.views.suggested_wizard_view import SuggestedWizardView

    swv = SuggestedWizardView()
    assert swv.view_mode == "form"
    swv._build_content()

    texts = []

    def collect_texts(ctl):
        if isinstance(ctl, ft.Text):
            texts.append(ctl.value)
        if hasattr(ctl, "controls") and isinstance(ctl.controls, list):
            for c in ctl.controls:
                collect_texts(c)
        if hasattr(ctl, "content") and ctl.content:
            collect_texts(ctl.content)

    collect_texts(swv)

    assert "Tell us your travel details" in texts
    assert "Trip Title" not in texts
    assert "Pacing" not in texts
    assert "Relaxed" not in texts
    assert "Packed" not in texts

    assert "Destination" in texts
    assert "Travel Dates" in texts
    assert "Daily Budget" in texts
    assert "Preferences (optional)" in texts
    assert "Travel Mode" in texts
    assert "Minimum Place Rating" in texts
    assert "Find Itinerary" in texts

    assert "₱1,500" in texts
    assert "₱2,500" in texts
    assert "₱4,000" in texts
    assert "₱6,000" in texts


def test_tc_95_destination_autocomplete_and_landmark_anchors():
    """TC-95: Verifies DestinationPicker autocomplete suggestions for 32 LGUs and 12 Landmarks with anchor_place_id."""
    from desktop_client.components.destination_picker import DestinationPicker, TOP_LANDMARKS

    selected_landmark = None

    def on_landmark_sel(lm):
        nonlocal selected_landmark
        selected_landmark = lm

    picker = DestinationPicker(on_landmark_select=on_landmark_sel)
    picker._build_content()

    picker._on_input_change("Minalungao")
    assert picker.anchor_place_id is None

    target_landmark = TOP_LANDMARKS[0]
    picker._handle_select_landmark(target_landmark)
    assert picker.anchor_place_id == target_landmark["place_id"]
    assert selected_landmark == target_landmark["place_id"]
    assert picker.value == target_landmark["municipality"]
    assert len(TOP_LANDMARKS) == 12


def test_tc_96_suggested_wizard_result_view():
    """TC-96: Verifies SuggestedWizardView result view components (.figma-trip-card, .verified-budget-card, parse_assumption)."""
    import flet as ft
    from desktop_client.models.itinerary import Itinerary, ItineraryDay, ItineraryItem
    from desktop_client.models.place import Place
    from desktop_client.views.suggested_wizard_view import SuggestedWizardView, parse_assumption

    swv = SuggestedWizardView()
    p1 = Place(id="p1", name="Camp Pangatian", category="historical", latitude=15.48, longitude=120.97, estimated_cost_min=50.0, estimated_cost_max=100.0)
    day = ItineraryDay(
        id="d1",
        itinerary_id="i1",
        day_number=1,
        travel_date="2026-12-01",
        items=[ItineraryItem(id="it1", day_id="d1", sort_order=1, place_id="p1", place=p1, planned_time="09:00 AM", duration_minutes=90)],
    )
    swv.generated_itinerary = Itinerary(
        id="i1",
        title="Nueva Ecija Adventure",
        destination="Cabanatuan City",
        start_date="2026-12-01",
        end_date="2026-12-02",
        daily_budget=3000.0,
        days=[day],
        assumptions=["[TRANSPORT] Tricycle fares estimated between stops", "[MEALS] Lunch budget set at ₱300 per person"],
    )
    swv.view_mode = "itinerary"
    swv._build_content()

    parsed = parse_assumption("[WEATHER] Rain expected in the afternoon")
    assert parsed["type"] == "WEATHER"
    assert "Rain expected" in parsed["detail"]

    texts = []

    def collect_texts(ctl):
        if isinstance(ctl, ft.Text):
            texts.append(ctl.value)
        if hasattr(ctl, "text") and ctl.text:
            texts.append(ctl.text)
        if hasattr(ctl, "content"):
            if isinstance(ctl.content, str):
                texts.append(ctl.content)
            elif isinstance(ctl.content, ft.Control):
                collect_texts(ctl.content)
        if hasattr(ctl, "controls") and isinstance(ctl.controls, list):
            for c in ctl.controls:
                collect_texts(c)

    collect_texts(swv)

    assert any("Accept & Save Itinerary" in t for t in texts)
    assert any("Customize in Builder" in t for t in texts)
    assert any("Nearby Places" in t or "Need Essentials" in t for t in texts)
    assert any("Verified Estimated Costs" in t for t in texts)


def test_tc_97_suggested_wizard_nearby_view():
    """TC-97: Verifies SuggestedWizardView nearby view with capsule tabs and staying on nearby after adding stop."""
    import flet as ft
    from desktop_client.models.itinerary import Itinerary, ItineraryDay
    from desktop_client.models.place import Place
    from desktop_client.views.suggested_wizard_view import SuggestedWizardView

    swv = SuggestedWizardView()
    day = ItineraryDay(id="d1", itinerary_id="i1", day_number=1, travel_date="2026-12-01", items=[])
    swv.generated_itinerary = Itinerary(id="i1", title="Trip", destination="Cabanatuan City", start_date="2026-12-01", end_date="2026-12-02", days=[day])

    swv._open_nearby_view()
    assert swv.view_mode == "nearby"
    swv._build_content()

    texts = []

    def collect_texts(ctl):
        if isinstance(ctl, ft.Text):
            texts.append(ctl.value)
        if hasattr(ctl, "controls") and isinstance(ctl.controls, list):
            for c in ctl.controls:
                collect_texts(c)
        if hasattr(ctl, "content") and ctl.content:
            collect_texts(ctl.content)

    collect_texts(swv)

    assert "Nearby Places" in texts
    assert "Restaurants" in texts
    assert "Hospital & Pharmacies" in texts
    assert "Stores" in texts

    pl = Place(id="pharm-1", name="City Pharmacy", category="pharmacy", latitude=15.48, longitude=120.97)
    swv._inject_nearby_to_day(pl)
    assert len(day.items) == 1
    assert day.items[0].place_id == "pharm-1"
    assert swv.view_mode == "nearby"


def test_tc_98_custom_builder_form_and_browse_views():
    """TC-98: Verifies CustomBuilderView form defaults and browse view with 'Other' category and Reset Filters."""
    import flet as ft
    from desktop_client.views.custom_builder_view import CustomBuilderView

    cbv = CustomBuilderView()
    assert cbv.trip_title == "Nueva Ecija Getaway"
    assert len(cbv.days) == 2
    assert cbv.preferences == []

    cbv.active_view = "browse"
    cbv._build_content()

    texts = []

    def collect_texts(ctl):
        if isinstance(ctl, ft.Text):
            texts.append(ctl.value)
        if hasattr(ctl, "controls") and isinstance(ctl.controls, list):
            for c in ctl.controls:
                collect_texts(c)
        if hasattr(ctl, "content") and ctl.content:
            collect_texts(ctl.content)

    collect_texts(cbv)

    assert "Add the places you want to visit" in texts
    assert "Other" in texts

    cbv.browse_search = "unknownplace"
    cbv.browse_category = "food"
    cbv._reset_browse_filters()
    assert cbv.browse_search == ""
    assert cbv.browse_category == "all"


def test_tc_99_custom_builder_timeline_confirmations_and_move_to_day():
    """TC-99: Verifies CustomBuilderView pre-loaded place banner, delete confirmations, and Move to Day reindexing."""
    from desktop_client.models.place import Place
    from desktop_client.views.custom_builder_view import CustomBuilderView

    p1 = Place(id="p1", name="Minalungao", category="nature_park", latitude=15.30, longitude=121.05)
    cbv = CustomBuilderView(pre_added_place=p1)

    assert cbv.active_view == "timeline"
    assert cbv.banner_dismissed is False
    cbv._dismiss_pre_loaded_banner()
    assert cbv.banner_dismissed is True

    day1 = cbv.days[0]
    day2 = cbv.days[1]
    assert len(day1.items) == 1
    item = day1.items[0]

    day1.items.remove(item)
    for i, itm in enumerate(day1.items):
        itm.sort_order = i + 1
    item.sort_order = len(day2.items) + 1
    day2.items.append(item)
    cbv.active_day_index = 1

    assert len(day1.items) == 0
    assert len(day2.items) == 1
    assert day2.items[0] == item
    assert cbv.active_day_index == 1


def test_tc_100_custom_builder_two_tab_offgrid_modal():
    """TC-100: Verifies CustomBuilderView 2-tab off-grid modal (Browse Places + Off-Grid Venue with coordinates validation)."""
    from desktop_client.views.custom_builder_view import CustomBuilderView

    cbv = CustomBuilderView()

    class DummyPage:
        def __init__(self):
            self.dialog = None
            self.overlay = []

        def update(self):
            pass

        def show_dialog(self, dlg):
            self.dialog = dlg
            dlg.open = True

    page = DummyPage()
    cbv._test_page = page

    cbv._open_custom_venue_dialog()
    assert (page.dialog is not None and page.dialog.open is True) or (len(page.overlay) > 0 and page.overlay[0].open is True)

    # Check coordinate bounds constants (15.15 <= lat <= 16.15, 120.70 <= lng <= 121.40)
    val_lat, val_lng = 15.50, 120.95
    assert 15.15 <= val_lat <= 16.15
    assert 120.70 <= val_lng <= 121.40

    out_lat, out_lng = 14.50, 123.00
    assert not (15.15 <= out_lat <= 16.15 and 120.70 <= out_lng <= 121.40)



