"""Nueva Ecija Travel — Standalone Python Flet Desktop Application.

Canonical Entry Point conforming to Web & Figma design parity:
- 4-Tab Bottom Navigation Bar (.custom-tab-bar, 60px) on primary views (/home, /map, /saved, /profile)
- Contextual Workflow Header (.figma-header-bar) on creation workflows (/suggested, /builder)
- Global Floating Offline Host Banner (.offline-host-banner) across all views
- Cold-Start Splash Overlay (loading_screen.jpg) auto-dismissing after 2.8s
- Clean email/password authentication & guest mode
- Pending Changes Guard protecting unsaved itineraries
"""

import asyncio
import os
from pathlib import Path
import sys
from typing import Optional
import flet as ft

# Auto-detect bundled flet view in frozen standalone builds
if getattr(sys, "frozen", False):
    exe_dir = Path(sys.executable).parent
    candidates = [
        exe_dir / "flet",
        exe_dir / "_internal" / "flet",
        Path(getattr(sys, "_MEIPASS", "")) / "flet",
    ]
    for cand in candidates:
        if (cand / "flet.exe").is_file():
            os.environ["FLET_VIEW_PATH"] = str(cand)
            break

from desktop_client.components.bottom_tab_bar import BottomTabBar
from desktop_client.components.offline_banner import OfflineHostBanner
from desktop_client.components.splash_overlay import SplashOverlay
from desktop_client.components.workflow_header import WorkflowHeader
from desktop_client.config.settings import ThemeColors, ThemePalette, get_settings
from desktop_client.core.api_client import get_api_client
from desktop_client.core.connectivity_service import get_connectivity_service
from desktop_client.core.session import get_session_manager
from desktop_client.core.storage import get_guest_storage
from desktop_client.models.itinerary import Itinerary
from desktop_client.models.place import Place
from desktop_client.services.auth_service import get_auth_service
from desktop_client.views.custom_builder_view import CustomBuilderView
from desktop_client.views.dashboard_view import DashboardView
from desktop_client.views.guest_view import GuestView
from desktop_client.views.login_view import LoginView
from desktop_client.views.places_view import PlacesView
from desktop_client.views.profile_view import ProfileView
from desktop_client.views.saved_trips_view import SavedTripsView
from desktop_client.views.signup_view import SignupView
from desktop_client.views.suggested_wizard_view import SuggestedWizardView
from desktop_client.views.trip_detail_view import TripDetailView
from desktop_client.views.welcome_view import WelcomeView


def main(page: ft.Page) -> None:
    settings = get_settings()
    session_manager = get_session_manager()
    api_client = get_api_client()
    auth_service = get_auth_service()
    connectivity_service = get_connectivity_service()

    # Window & Page Setup
    page.title = settings.app_title
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    page.bgcolor = ThemeColors.BG_LIGHT

    current_route = "/welcome"
    selected_trip: Optional[Itinerary] = None
    cached_views: dict[str, ft.Control] = {}

    # App Shell Structure
    content_area = ft.Container(expand=True)
    workflow_header = WorkflowHeader(title="Workflow", on_back=lambda: navigate_to("/home"))
    workflow_header.visible = False

    def _on_map_tap():
        # Reset follow-route or filter on places view if active
        if current_route in ("/map", "/places") and content_area.content:
            recenter = getattr(content_area.content, "recenter_map", None)
            if callable(recenter):
                recenter()

    bottom_tab_bar = BottomTabBar(
        current_route="/home",
        on_navigate=lambda r: navigate_to(r),
        on_map_tap_when_active=_on_map_tap,
    )
    bottom_tab_bar.visible = False

    offline_banner = OfflineHostBanner()

    def toggle_theme() -> None:
        """Toggles between Light and Dark theme modes across the entire shell."""
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = ThemeColors.BG_DARK
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.bgcolor = ThemeColors.BG_LIGHT

        bottom_tab_bar._build_content()
        workflow_header._build_content()
        navigate_to(current_route, selected_trip, force=True)

    def navigate_to(
        route: str,
        trip_data: Optional[Itinerary] = None,
        pre_added_place: Optional[Place] = None,
        force: bool = False,
    ) -> None:
        """Central navigation dispatcher managing route state and shell chrome."""
        nonlocal current_route, selected_trip

        # Pending Changes Guard: check if active view has unsaved modifications
        if (
            not force
            and content_area
            and content_area.content
            and route != current_route
        ):
            has_unsaved = getattr(content_area.content, "has_unsaved_changes", None)
            if callable(has_unsaved) and has_unsaved():

                def _confirm_discard(_):
                    dlg.open = False
                    page.update()
                    navigate_to(route, trip_data, pre_added_place, force=True)

                def _cancel_discard(_):
                    dlg.open = False
                    bottom_tab_bar.set_active_route(current_route)
                    page.update()

                dlg = ft.AlertDialog(
                    title=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.WARNING_ROUNDED, color=ThemeColors.WARNING
                            ),
                            ft.Text(
                                "Discard Unsaved Changes?", weight=ft.FontWeight.BOLD
                            ),
                        ],
                        spacing=10,
                    ),
                    content=ft.Text(
                        "You have unsaved changes in your itinerary. If you leave now, your changes will be discarded.",
                        size=13,
                    ),
                    actions=[
                        ft.TextButton("Keep Editing", on_click=_cancel_discard),
                        ft.FilledButton(
                            "Discard & Leave",
                            bgcolor=ThemeColors.ERROR,
                            color=ft.Colors.WHITE,
                            on_click=_confirm_discard,
                        ),
                    ],
                )
                page.overlay.append(dlg)
                dlg.open = True
                page.update()
                return

        current_route = route
        if trip_data:
            selected_trip = trip_data

        # 1. Fullscreen Standalone Views (Auth & Onboarding)
        if route in ("/welcome", "/guest", "/login", "/signup") or route.startswith(
            "/welcome"
        ):
            bottom_tab_bar.visible = False
            workflow_header.visible = False

            if route == "/guest":
                content_area.content = GuestView(on_navigate=navigate_to)
            elif route.startswith("/welcome"):
                is_logout = "logout=1" in route or "loggedOut=true" in route
                content_area.content = WelcomeView(
                    on_navigate=navigate_to, is_after_logout=is_logout
                )
            elif route == "/login":
                content_area.content = LoginView(on_navigate=navigate_to)
            elif route == "/signup":
                content_area.content = SignupView(on_navigate=navigate_to)

            page.update()
            return

        # 2. Workflow Views (Modal creation & detail with contextual header)
        if route in ("/suggested", "/builder") or route.startswith("/trips/"):
            bottom_tab_bar.visible = False

            if route == "/suggested":
                workflow_header.visible = True
                workflow_header.title_text = "Suggested Itinerary Wizard"
                workflow_header.subtitle_text = "Automated Proximity & Corridor Clustering"
                workflow_header.on_back = lambda: navigate_to("/home")
                workflow_header._build_content()
                if "/suggested" not in cached_views:
                    cached_views["/suggested"] = SuggestedWizardView(
                        on_navigate=navigate_to
                    )
                content_area.content = cached_views["/suggested"]

            elif route == "/builder":
                workflow_header.visible = True
                workflow_header.title_text = "Custom Itinerary Builder"
                workflow_header.subtitle_text = "Interactive Stop-by-Stop Scheduling"
                workflow_header.on_back = lambda: navigate_to("/home")
                workflow_header._build_content()
                if pre_added_place or "/builder" not in cached_views:
                    cached_views["/builder"] = CustomBuilderView(
                        on_navigate=navigate_to,
                        pre_added_place=pre_added_place,
                    )
                content_area.content = cached_views["/builder"]

            elif route.startswith("/trips/"):
                # Trip detail view embeds its own back bar
                workflow_header.visible = False
                trip_id = route.split("/trips/")[1].split("?")[0].strip()
                trip_obj = selected_trip
                if not trip_obj:
                    guest_storage = get_guest_storage()
                    trip_obj = guest_storage.get_itinerary(trip_id)
                if trip_obj:
                    content_area.content = TripDetailView(
                        itinerary=trip_obj,
                        on_back=lambda: navigate_to("/saved"),
                    )
                else:
                    navigate_to("/saved")
                    return

            page.update()
            return

        # 3. Primary 4-Tab Views (Home, Map, Saved, Profile)
        workflow_header.visible = False
        bottom_tab_bar.visible = True
        bottom_tab_bar.set_active_route(route)

        if route in ("/dashboard", "/home"):
            content_area.content = DashboardView(on_navigate=navigate_to)
        elif route in ("/map", "/places"):
            content_area.content = PlacesView(on_navigate=navigate_to)
        elif route in ("/saved", "/trips"):
            content_area.content = SavedTripsView(
                on_navigate=navigate_to,
                on_select_trip=lambda it: navigate_to(f"/trips/{it.id}", it),
            )
        elif route == "/profile":
            content_area.content = ProfileView(
                on_navigate=navigate_to,
                on_toggle_theme=toggle_theme,
            )
        else:
            content_area.content = DashboardView(on_navigate=navigate_to)

        page.update()

    # Session change listener
    def _on_session_changed():
        if current_route in ("/profile", "/home", "/dashboard"):
            navigate_to(current_route, force=True)

    session_manager.add_listener(_on_session_changed)

    # Root Layout Hierarchy
    main_column = ft.Column(
        controls=[
            workflow_header,
            content_area,
            bottom_tab_bar,
        ],
        expand=True,
        spacing=0,
    )

    splash_overlay = SplashOverlay(on_dismiss=None)

    root_stack = ft.Stack(
        controls=[
            main_column,
            offline_banner,
            splash_overlay,
        ],
        expand=True,
    )

    page.controls = [root_stack]
    page.update()

    # Launch Cold-Start Splash Timer (2.8s auto-dismiss)
    splash_overlay.start_timer(2.8)

    # Background Host Health Loop (queries every 15s)
    async def check_backend_loop():
        while True:
            try:
                await connectivity_service.check_host_health(api_client)
            except Exception:
                pass
            await asyncio.sleep(15)

    page.run_task(check_backend_loop)

    # Initial Route Resolution
    if session_manager.is_authenticated or session_manager.is_guest:
        navigate_to("/home")
    else:
        navigate_to("/welcome")


if __name__ == "__main__":
    _st = get_settings()
    ft.run(main, assets_dir=str(_st.assets_dir), view=ft.AppView.FLET_APP)
