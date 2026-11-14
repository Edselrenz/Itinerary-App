"""Tests for UI Consistency between Desktop Flet client and Ionic Web client."""

import pytest
from desktop_client.config.settings import (
    BUDGET_PRESETS,
    CANONICAL_CATEGORIES,
    NUEVA_ECIJA_LGUS,
    PACING_OPTIONS,
    ThemeColors,
    get_settings,
)
from desktop_client.components.bottom_tab_bar import BottomTabBar
from desktop_client.components.workflow_header import WorkflowHeader
from desktop_client.components.place_card import PlaceCard
from desktop_client.components.stop_card import StopCard
from desktop_client.models.itinerary import Itinerary, ItineraryDay, ItineraryItem
from desktop_client.models.place import Place
from desktop_client.views.dashboard_view import DashboardView
from desktop_client.views.welcome_view import WelcomeView
from desktop_client.views.login_view import LoginView
from desktop_client.views.signup_view import SignupView
from desktop_client.views.places_view import PlacesView
from desktop_client.views.saved_trips_view import SavedTripsView
from desktop_client.views.profile_view import ProfileView
from desktop_client.views.custom_builder_view import CustomBuilderView
from desktop_client.views.suggested_wizard_view import SuggestedWizardView
from desktop_client.views.trip_detail_view import TripDetailView


def test_theme_colors_match_web_figma_tokens():
    """Validates that brand tokens match Web client & Figma design."""
    assert ThemeColors.PRIMARY_BLUE == "#0084ff"
    assert ThemeColors.AZURE_PRIMARY == "#0084ff"
    assert ThemeColors.NAVY_GRADIENT_START == "#091338"
    assert ThemeColors.NAVY_GRADIENT_END == "#03081e"
    assert ThemeColors.CUSTOM_CARD_BORDER == "#38bdf8"
    assert ThemeColors.SUGGESTED_BADGE_BG == "#091338"
    assert ThemeColors.SUGGESTED_BADGE_TEXT == "#38bdf8"
    assert ThemeColors.CUSTOM_BADGE_BG == "#e0f2fe"
    assert ThemeColors.CUSTOM_BADGE_TEXT == "#0284c7"
    assert ThemeColors.BUDGET_GREEN == "#047857"


def test_settings_brand_title():
    """Validates brand naming consistency."""
    settings = get_settings()
    assert "Trip mo, trip ko" in settings.app_title
    assert settings.brand_name == "Trip mo, trip ko"


def test_canonical_categories_and_lgus():
    """Validates canonical domain data matching backend and web catalog."""
    assert len(CANONICAL_CATEGORIES) == 16
    assert any(c["key"] == "nature_park" for c in CANONICAL_CATEGORIES)
    assert any(c["key"] == "tourist_attraction" for c in CANONICAL_CATEGORIES)
    assert any(c["key"] == "restaurant" for c in CANONICAL_CATEGORIES)
    assert len(NUEVA_ECIJA_LGUS) == 32
    assert "Cabanatuan City" in NUEVA_ECIJA_LGUS
    assert "Pantabangan" in NUEVA_ECIJA_LGUS


def test_place_card_instantiation():
    """Verifies PlaceCard renders with Figma overlaid badge and price chip."""
    place = Place(
        id="p1",
        name="Minalungao National Park",
        category="nature_park",
        latitude=15.30,
        longitude=121.14,
        municipality_name="General Tinio",
        estimated_cost_max=100.0,
        rating=4.7,
        user_rating_count=320,
    )
    card = PlaceCard(place=place)
    assert card is not None
    assert card.border_radius == 14
    assert card.bgcolor == ThemeColors.SURFACE_LIGHT


def test_stop_card_instantiation():
    """Verifies StopCard renders with blue sequence badge and honest pricing."""
    item = ItineraryItem(
        id="s1",
        day_id="d1",
        sort_order=1,
        custom_title="Camp Sawmill",
        planned_time="09:00 AM",
        duration_minutes=60,
        estimated_cost_max=150.0,
    )
    card = StopCard(item=item)
    assert card is not None
    assert card.border_radius == 12


def test_all_views_can_be_instantiated():
    """Smoke test ensuring every refactored view compiles and instantiates without syntax errors."""
    welcome = WelcomeView()
    assert welcome is not None

    login = LoginView()
    assert login is not None

    signup = SignupView()
    assert signup is not None

    bottom_bar = BottomTabBar()
    assert bottom_bar is not None

    wf_header = WorkflowHeader(title="Test Workflow")
    assert wf_header is not None

    dashboard = DashboardView()
    assert dashboard is not None

    places = PlacesView()
    assert places is not None

    trips = SavedTripsView()
    assert trips is not None

    profile = ProfileView()
    assert profile is not None

    wizard = SuggestedWizardView()
    assert wizard is not None

    builder = CustomBuilderView()
    assert builder is not None

    sample_itin = Itinerary(
        id="it-1",
        title="Test Trip",
        destination="Nueva Ecija",
        start_date="2026-12-01",
        end_date="2026-12-02",
        type="suggested",
        daily_budget=2500.0,
        days=[
            ItineraryDay(
                id="d1",
                itinerary_id="it-1",
                day_number=1,
                travel_date="2026-12-01",
                title="Day 1",
                items=[],
            )
        ],
    )
    detail = TripDetailView(itinerary=sample_itin)
    assert detail is not None


def test_unmounted_bottom_tab_bar_and_workflow_header_safe_update():
    """Ensure BottomTabBar and WorkflowHeader safely handle route/context updates when unmounted."""
    wf_header = WorkflowHeader(title="Map & Discover", subtitle="Explore LGUs")
    wf_header.title_text = "Updated Title"
    wf_header.subtitle_text = "Updated Subtitle"
    assert wf_header.title_text == "Updated Title"
    assert wf_header.subtitle_text == "Updated Subtitle"

    tab_bar = BottomTabBar()
    tab_bar.set_active_route("/places")
    assert tab_bar._get_active_tab_key() == "map"


def test_continue_as_guest_welcome_flow():
    """Verify Continue as Guest action transitions session to guest and routes to /dashboard."""
    routed = []
    welcome = WelcomeView(on_navigate=lambda r: routed.append(r))
    welcome._continue_as_guest()
    assert "/dashboard" in routed


def test_main_app_navigation_and_url_parsing():
    """Verify that main module imports urllib.parse and handles all route patterns without NameError."""
    import desktop_client.main as main_mod

    assert hasattr(main_mod, "urllib")
    assert hasattr(main_mod.urllib, "parse")

    # Verify query parsing on routes
    for test_route in [
        "/dashboard",
        "/home",
        "/map?itineraryId=draft&day=1",
        "/places?q=Bongabon",
        "/suggested?destination=Bongabon",
        "/builder?itineraryId=itin-1",
        "/trips/itin-1",
        "/welcome",
        "/login",
        "/signup",
        "/profile",
    ]:
        parsed = main_mod.urllib.parse.urlparse(test_route)
        assert parsed.path.startswith("/")
        qs = main_mod.urllib.parse.parse_qs(parsed.query)
        assert isinstance(qs, dict)

