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
from typing import Any, Optional
import urllib.parse
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
from desktop_client.components.dialogs import close_overlay_dialog, open_overlay_dialog
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
from desktop_client.services.itinerary_service import get_itinerary_service
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
    itinerary_service = get_itinerary_service()
    connectivity_service = get_connectivity_service()

    # Window & Page Setup
    page.title = settings.app_title
    page.theme_mode = ft.ThemeMode.DARK if settings.is_dark_mode else ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            surface=ThemeColors.SURFACE_LIGHT,
            on_surface=ThemeColors.TEXT_BLACK,
            primary=ThemeColors.PRIMARY_BLUE,
            on_primary=ft.Colors.WHITE,
            surface_container=ThemeColors.BG_LIGHT,
            surface_container_lowest=ThemeColors.BG_LIGHT,
        )
    )
    page.dark_theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            surface=ThemeColors.SURFACE_DARK,
            on_surface=ThemeColors.TEXT_MAIN_DARK,
            primary=ThemeColors.PRIMARY_BLUE,
            on_primary=ft.Colors.WHITE,
            surface_container=ThemeColors.BG_DARK,
            surface_container_lowest=ThemeColors.BG_DARK,
        )
    )
    page.bgcolor = settings.palette.bg_primary
    try:
        page.window.width = settings.window_width
        page.window.height = settings.window_height
        page.window.min_width = settings.window_min_width
        page.window.min_height = settings.window_min_height
    except Exception:
        pass

    current_route = "/welcome"
    selected_trip: Optional[Itinerary] = None
    previous_route: str = "/saved"
    cached_views: dict[str, ft.Control] = {}

    # App Shell Structure
    content_area = ft.Container(expand=True, width=float("inf"))
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

    def toggle_theme(is_dark: Optional[bool] = None) -> None:
        """Toggles between Light and Dark theme modes across the entire shell, preserving Settings subview."""
        saved_subview = getattr(content_area.content, "_subview", None) if content_area else None
        if is_dark is None:
            new_is_dark = page.theme_mode == ft.ThemeMode.LIGHT
        else:
            new_is_dark = is_dark

        settings.set_dark_mode(new_is_dark)
        palette = settings.palette
        page.theme_mode = ft.ThemeMode.DARK if new_is_dark else ft.ThemeMode.LIGHT
        page.bgcolor = palette.bg_primary
        if content_area:
            content_area.bgcolor = palette.bg_primary

        bottom_tab_bar.refresh_theme()
        workflow_header._build_content()
        navigate_to(
            current_route,
            trip_data=selected_trip,
            force=True,
            preserve_profile_subview=saved_subview,
        )

    def navigate_to(
        route: str,
        trip_data: Optional[Any] = None,
        pre_added_place: Optional[Place] = None,
        force: bool = False,
        preserve_profile_subview: Optional[str] = None,
    ) -> None:
        """Central navigation dispatcher managing route state and shell chrome."""
        nonlocal current_route, selected_trip, previous_route

        # Guard against Place passed positionally as 2nd argument (BUG-NEW-03)
        if isinstance(trip_data, Place):
            pre_added_place = trip_data
            trip_data = None

        parsed_url = urllib.parse.urlparse(route)
        base_route = parsed_url.path
        query_str = parsed_url.query

        if base_route.startswith("/trips/") and not current_route.startswith("/trips/"):
            previous_route = "/home" if current_route in ("/home", "/dashboard") else "/saved"

        # Explicitly update or clear selected_trip to prevent stale draft leaks (BUG-NEW-02)
        if trip_data is not None:
            selected_trip = trip_data
        elif (
            base_route not in ("/map", "/places", "/trips", "/trip-detail")
            and not base_route.startswith("/trips/")
            and "restore=draft" not in query_str
            and "itineraryId=" not in query_str
        ):
            selected_trip = None

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
                    close_overlay_dialog(page, dlg)
                    navigate_to(route, trip_data, pre_added_place, force=True)

                def _cancel_discard(_):
                    close_overlay_dialog(page, dlg)
                    bottom_tab_bar.set_active_route(current_route)

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
                open_overlay_dialog(page, dlg)
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
            if content_area and content_area.content is not None:
                active_ctrl = content_area.content
                if hasattr(active_ctrl, "on_resize") and callable(active_ctrl.on_resize):
                    try:
                        active_ctrl.on_resize(float(page.width or 1280), float(page.height or 840))
                    except Exception:
                        pass
            return

        # 2. Workflow Views (Modal creation & detail with contextual header)
        parsed_url = urllib.parse.urlparse(route)
        base_route = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        if base_route in ("/suggested", "/builder") or base_route.startswith("/trips/"):
            bottom_tab_bar.visible = False

            def _handle_workflow_back():
                if content_area.content and hasattr(content_area.content, "handle_back"):
                    if content_area.content.handle_back():
                        return
                navigate_to("/home")

            if base_route == "/suggested":
                workflow_header.visible = False
                dest_param = query_params.get("destination", [None])[0]
                place_id_param = query_params.get("placeId", [None])[0]
                restore_param = query_params.get("restore", [None])[0] == "draft" or (selected_trip is not None and getattr(selected_trip, "id", None) == "draft")
                content_area.content = SuggestedWizardView(
                    on_navigate=navigate_to,
                    initial_destination=dest_param or "Nueva Ecija",
                    anchor_place_id=place_id_param,
                    restore_draft=restore_param,
                    draft_itinerary=selected_trip if (selected_trip and getattr(selected_trip, "id", None) == "draft") else None,
                )

            elif base_route == "/builder":
                workflow_header.visible = False
                is_draft_wizard = query_params.get("draft", ["false"])[0].lower() == "true"
                content_area.content = CustomBuilderView(
                    on_navigate=navigate_to,
                    pre_added_place=pre_added_place,
                    existing_itinerary=selected_trip,
                    is_draft_from_wizard=is_draft_wizard,
                )

            elif base_route.startswith("/trips/"):
                # Trip detail view embeds its own back bar
                workflow_header.visible = False
                trip_id = base_route.split("/trips/")[1].strip()
                trip_obj = (
                    selected_trip
                    if (selected_trip and str(getattr(selected_trip, "id", "")) == str(trip_id))
                    else None
                )
                if not trip_obj:
                    trip_obj = itinerary_service.get_itinerary_or_draft(trip_id)
                if trip_obj:
                    selected_trip = trip_obj
                    back_target = previous_route if previous_route in ("/home", "/dashboard", "/saved") else "/saved"
                    content_area.content = TripDetailView(
                        itinerary=trip_obj,
                        on_back=lambda bt=back_target: navigate_to(bt),
                        on_navigate=navigate_to,
                    )
                else:
                    navigate_to("/saved")
                    return

            page.update()
            if content_area and content_area.content is not None:
                active_ctrl = content_area.content
                if hasattr(active_ctrl, "on_resize") and callable(active_ctrl.on_resize):
                    try:
                        active_ctrl.on_resize(float(page.width or 1280), float(page.height or 840))
                    except Exception:
                        pass
            return

        # 3. Primary 4-Tab Views (Home, Map, Saved, Profile)
        workflow_header.visible = False
        bottom_tab_bar.visible = True
        bottom_tab_bar.set_active_route(base_route)

        if base_route in ("/dashboard", "/home"):
            content_area.content = DashboardView(on_navigate=navigate_to)
        elif base_route in ("/map", "/places"):
            has_route_param = ("itineraryId=" in route) or ("followRoute=true" in route)
            init_w = float(getattr(getattr(page, "window", None), "width", None) or page.width or 1280.0)
            init_h = float(getattr(getattr(page, "window", None), "height", None) or page.height or 840.0)
            content_area.content = PlacesView(
                on_navigate=navigate_to,
                route_query=route,
                active_trip=selected_trip if has_route_param else None,
                initial_width=init_w,
                initial_height=init_h,
            )
        elif base_route in ("/saved", "/trips"):
            content_area.content = SavedTripsView(
                on_navigate=navigate_to,
                on_select_trip=lambda it: navigate_to(f"/trips/{it.id}", it),
            )
        elif base_route == "/profile":
            prof_view = ProfileView(
                on_navigate=navigate_to,
                on_toggle_theme=toggle_theme,
            )
            if preserve_profile_subview in ("profile", "edit", "settings", "favorites", "help", "about"):
                prof_view._subview = preserve_profile_subview
                prof_view._rebuild()
            content_area.content = prof_view
        else:
            content_area.content = DashboardView(on_navigate=navigate_to)

        page.update()
        if content_area and content_area.content is not None:
            active_ctrl = content_area.content
            if hasattr(active_ctrl, "on_resize") and callable(active_ctrl.on_resize):
                try:
                    active_ctrl.on_resize(float(page.width or 1280), float(page.height or 840))
                except Exception:
                    pass

    # Session change listener - only reload view when authentication identity actually changes
    last_auth_identity = (
        session_manager.is_authenticated,
        session_manager.is_guest,
        getattr(session_manager.current_user, "id", None),
    )

    def _on_session_changed():
        nonlocal last_auth_identity
        new_auth_identity = (
            session_manager.is_authenticated,
            session_manager.is_guest,
            getattr(session_manager.current_user, "id", None),
        )
        if new_auth_identity != last_auth_identity:
            last_auth_identity = new_auth_identity
            if current_route in ("/home", "/dashboard"):
                navigate_to(current_route, force=True)
            elif current_route == "/profile" and not session_manager.is_authenticated and not session_manager.is_guest:
                navigate_to("/welcome", force=True)

    session_manager.add_listener(_on_session_changed)

    # Root Layout Hierarchy: offline_banner is placed at top of main_column
    # so it NEVER stretches across the entire screen via Flutter StackFit.expand
    main_column = ft.Column(
        controls=[
            offline_banner,
            workflow_header,
            content_area,
            bottom_tab_bar,
        ],
        expand=True,
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )

    def _on_splash_dismiss() -> None:
        try:
            if splash_overlay in root_stack.controls:
                root_stack.controls.remove(splash_overlay)
                page.update()
        except Exception:
            pass

    splash_overlay = SplashOverlay(on_dismiss=_on_splash_dismiss)

    root_stack = ft.Stack(
        controls=[
            main_column,
            splash_overlay,
        ],
        expand=True,
    )

    page.controls = [root_stack]
    page.update()

    # Launch Cold-Start Splash Timer (2.8s auto-dismiss)
    splash_overlay.start_timer(2.8)

    def _on_page_resize(e: Any = None) -> None:
        palette = settings.palette
        page.bgcolor = palette.bg_main
        # Extract true logical pixels from resize event, window, or page
        new_w = getattr(e, "width", None)
        new_h = getattr(e, "height", None)
        if not new_w or not new_h:
            new_w = getattr(getattr(page, "window", None), "width", None) or page.width or 1280.0
            new_h = getattr(getattr(page, "window", None), "height", None) or page.height or 840.0
        new_w = float(new_w)
        new_h = float(new_h)
        page.width = new_w
        page.height = new_h

        if content_area:
            content_area.bgcolor = palette.bg_main
            active_ctrl = content_area.content
            if active_ctrl is not None:
                if hasattr(active_ctrl, "on_resize") and callable(active_ctrl.on_resize):
                    try:
                        active_ctrl.on_resize(new_w, new_h)
                    except Exception:
                        pass
                elif hasattr(active_ctrl, "_build_content") and callable(active_ctrl._build_content):
                    try:
                        active_ctrl._build_content()
                        active_ctrl.update()
                    except Exception:
                        pass
        try:
            page.update()
        except Exception:
            pass

    page.on_resize = _on_page_resize
    page.on_resized = _on_page_resize

    # Background Host Health Loop (queries every 15s)
    async def check_backend_loop():
        while True:
            try:
                await connectivity_service.check_host_health()
            except Exception:
                pass
            await asyncio.sleep(15)

    page.run_task(check_backend_loop)

    # Initial cloud sync for authenticated sessions
    if session_manager.is_authenticated:
        async def _initial_sync():
            try:
                await auth_service.fetch_current_user()
            except Exception:
                pass
            try:
                await itinerary_service.sync_guest_itineraries_to_cloud()
            except Exception:
                pass
        page.run_task(_initial_sync)

    # Initial Route Resolution
    if session_manager.is_authenticated or session_manager.is_guest:
        navigate_to("/home")
    else:
        navigate_to("/welcome")


if __name__ == "__main__":
    _st = get_settings()
    ft.run(main, assets_dir=str(_st.assets_dir), view=ft.AppView.FLET_APP)
