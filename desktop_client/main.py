"""Nueva Ecija Travel — Standalone Python Flet Desktop Application.

Entry point initializing window configuration, persistent sidebar navigation,
theme controls, health monitoring, and view switching.
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

from desktop_client.components.header import TopHeader
from desktop_client.components.sidebar import SidebarNav
from desktop_client.config.settings import ThemeColors, ThemePalette, get_settings
from desktop_client.core.api_client import get_api_client
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

    # Window & Page Setup
    page.title = settings.app_title
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    page.bgcolor = ThemeColors.BG_LIGHT

    current_route = "/welcome"
    selected_trip: Optional[Itinerary] = None
    cached_views: dict[str, ft.Control] = {}

    # App Shell Components
    sidebar: Optional[SidebarNav] = None
    header: Optional[TopHeader] = None
    content_area = ft.Container(expand=True)

    def toggle_theme() -> None:
        """Toggles between Light and Dark Material 3 theme modes."""
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = ThemeColors.BG_DARK
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.bgcolor = ThemeColors.BG_LIGHT

        # Re-theme persistent components and active view
        if sidebar:
            sidebar._build_content()
        if header:
            header._build_content()
        navigate_to(current_route, selected_trip)

    def navigate_to(
        route: str,
        trip_data: Optional[Itinerary] = None,
        pre_added_place: Optional[Place] = None,
        force: bool = False,
    ) -> None:
        """Central navigation handler switching views and managing shell layout."""
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
                    if sidebar:
                        sidebar.set_active_route(current_route)
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
                        ft.ElevatedButton(
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

        # Full-screen standalone views (no sidebar shell)
        if route in ("/welcome", "/guest", "/login", "/signup") or route.startswith(
            "/welcome"
        ):
            if route == "/guest":
                page.controls = [GuestView(on_navigate=navigate_to)]
            elif route.startswith("/welcome"):
                is_logout = "logout=1" in route or "loggedOut=true" in route
                page.controls = [
                    WelcomeView(on_navigate=navigate_to, is_after_logout=is_logout)
                ]
            elif route == "/login":
                page.controls = [LoginView(on_navigate=navigate_to)]
            elif route == "/signup":
                page.controls = [SignupView(on_navigate=navigate_to)]
            page.update()
            return

        # App Shell Views (Sidebar + Header + Content Area)
        nonlocal sidebar, header
        if sidebar is None:
            sidebar = SidebarNav(
                current_route=route,
                on_navigate=navigate_to,
                on_toggle_theme=toggle_theme,
            )
        else:
            sidebar.set_active_route(route)

        if header is None:
            header = TopHeader(
                title="Home",
                subtitle="Trip mo, trip ko",
                on_search_click=lambda: navigate_to("/places"),
            )

        # Resolve view content and update header breadcrumbs
        if route in ("/dashboard", "/home"):
            header.set_header_context("Home", "Where are you going next?")
            content_area.content = DashboardView(on_navigate=navigate_to)
        elif route == "/places":
            header.set_header_context(
                "Map & Discover", "Explore 2,670+ destinations across 32 LGUs"
            )
            content_area.content = PlacesView(on_navigate=navigate_to)
        elif route == "/suggested":
            header.set_header_context(
                "Suggested Itinerary Wizard", "Automated Proximity Clustering"
            )
            if "/suggested" not in cached_views:
                cached_views["/suggested"] = SuggestedWizardView(
                    on_navigate=navigate_to
                )
            content_area.content = cached_views["/suggested"]
        elif route == "/builder":
            header.set_header_context(
                "Custom Itinerary Builder", "Interactive Stop-by-Stop Scheduling"
            )
            if pre_added_place or "/builder" not in cached_views:
                cached_views["/builder"] = CustomBuilderView(
                    on_navigate=navigate_to,
                    pre_added_place=pre_added_place,
                )
            content_area.content = cached_views["/builder"]
        elif route == "/trips":
            header.set_header_context(
                "Saved Itineraries", "Your Planned Trips in Nueva Ecija"
            )
            content_area.content = SavedTripsView(
                on_navigate=navigate_to,
                on_select_trip=lambda it: navigate_to(f"/trips/{it.id}", it),
            )
        elif route == "/profile":
            header.set_header_context("Profile", "Traveler Identity & Preferences")
            content_area.content = ProfileView(
                on_navigate=navigate_to,
                on_toggle_theme=toggle_theme,
            )
        elif route.startswith("/trips/"):
            trip_id = route.split("/trips/")[1].split("?")[0].strip()
            trip_obj = selected_trip
            if not trip_obj:
                guest_storage = get_guest_storage()
                trip_obj = guest_storage.get_itinerary(trip_id)
            if trip_obj:
                header.set_header_context(
                    f"Trip: {trip_obj.title}", "Chronological Timeline & Export"
                )
                content_area.content = TripDetailView(
                    itinerary=trip_obj,
                    on_back=lambda: navigate_to("/trips"),
                )
            else:
                navigate_to("/trips")
                return
        else:
            header.set_header_context("Home", "Where are you going next?")
            content_area.content = DashboardView(on_navigate=navigate_to)

        shell = ft.Row(
            controls=[
                sidebar,
                ft.Column(
                    controls=[
                        header,
                        content_area,
                    ],
                    expand=True,
                    spacing=0,
                ),
            ],
            expand=True,
            spacing=0,
        )

        page.controls = [shell]
        page.update()

    # Subscribe session changes to update header/sidebar
    def _on_session_changed():
        if sidebar:
            sidebar._build_content()
            try:
                sidebar.update()
            except Exception:
                pass
        if header:
            header._build_content()
            try:
                header.update()
            except Exception:
                pass

    session_manager.add_listener(_on_session_changed)

    # Background Backend Health Monitor
    async def check_backend_loop():
        while True:
            try:
                is_healthy = await api_client.check_health()
                if header:
                    header.set_online_status(is_healthy)
            except Exception:
                if header:
                    header.set_online_status(False)
            await asyncio.sleep(15)

    page.run_task(check_backend_loop)

    # Initial routing decision
    if session_manager.is_authenticated or session_manager.is_guest:
        navigate_to("/dashboard")
    else:
        navigate_to("/welcome")


if __name__ == "__main__":
    _st = get_settings()
    ft.run(main, assets_dir=str(_st.assets_dir), view=ft.AppView.FLET_APP)
