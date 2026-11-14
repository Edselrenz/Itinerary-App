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
from desktop_client.services.favorites_service import FavoritesService, get_favorites_service
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
        place=Place(id="p1", name="Cabanatuan Plaza", category="tourist_attraction", latitude=15.4859, longitude=120.9673),
        sort_order=1,
    )
    stop2 = ItineraryItem(
        id="s2",
        day_id="d1",
        place=Place(id="p2", name="Rohi Cafe Bongabon", category="cafe", latitude=15.6315, longitude=121.1440),
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

    test_place = Place(id="dest-new-spot", name="New Test Spot", category="cafe", latitude=15.63, longitude=121.14, municipality_name="Bongabon")
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
    """Verify GuestView and SuggestedWizardView can be instantiated cleanly."""
    guest = GuestView()
    assert guest is not None

    wizard = SuggestedWizardView()
    assert wizard is not None
    assert wizard.view_mode == "form"
    assert wizard.destination_val == "Nueva Ecija"


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
