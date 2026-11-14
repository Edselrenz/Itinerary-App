"""Profile, Account Settings, and Local Cache Management View mirroring Ionic tabs/profile."""

import asyncio
from typing import Callable, Optional
import flet as ft

from desktop_client.components.dialogs import show_place_detail_dialog
from desktop_client.config.settings import ThemeColors, get_settings
from desktop_client.core.connectivity_service import get_connectivity_service
from desktop_client.core.session import get_session_manager
from desktop_client.core.storage import get_guest_storage
from desktop_client.models.place import Place
from desktop_client.models.user import UserUpdatePayload
from desktop_client.services.auth_service import get_auth_service
from desktop_client.services.favorites_service import get_favorites_service


class ProfileView(ft.Container):
    """Profile view matching Ionic tabs/profile:

    - Authentic traveler identity row with traveler avatar.
    - Figma-aligned 5-row profile navigation card (Settings, Favorites, Help, About, Logout).
    - Rounded soft blue square icon boxes and NO chevron arrows.
    - Sub-window modals for Edit Profile (7 fields), Favorites (backed by FavoritesService),
      Settings, Help & Support (Provincial Hotlines), and Logout confirmation.
    """

    def __init__(
        self,
        on_navigate: Optional[Callable[[str], None]] = None,
        on_toggle_theme: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.on_navigate = on_navigate
        self.on_toggle_theme = on_toggle_theme
        self.session_manager = get_session_manager()
        self.auth_service = get_auth_service()
        self.guest_storage = get_guest_storage()
        self.favorites_service = get_favorites_service()
        self.connectivity_service = get_connectivity_service()
        self.settings = get_settings()

        self.expand = True
        self.padding = ft.Padding.symmetric(horizontal=36, vertical=24)
        self.bgcolor = ThemeColors.BG_LIGHT

        self.status_msg: Optional[str] = None
        self.is_migrating = False
        self._has_refreshed_profile = False

        self._build_content()

    def _build_content(self) -> None:
        user = self.session_manager.current_user
        is_guest = (
            self.session_manager.is_guest or not self.session_manager.is_authenticated
        )

        # Page Title
        title_block = ft.Column(
            controls=[
                ft.Text(
                    "Profile",
                    size=28,
                    weight=ft.FontWeight.W_800,
                    color=ThemeColors.TEXT_BLACK,
                ),
                ft.Text(
                    "Manage your traveler identity and preferences.",
                    size=13,
                    color=ThemeColors.TEXT_MUTED_LIGHT,
                ),
            ],
            spacing=2,
        )

        # 1. Identity Header Section (matching Figma Screen Profile)
        avatar_path = self.settings.get_asset_path("images/default_avatar_placeholder.png")
        if not is_guest:
            name_val = user.full_name if user and user.full_name else (user.username if user else "Traveler")
            handle_val = (
                f"@{user.username}"
                if user and user.username
                else (user.email if user and user.email else "@traveler")
            )
            raw_avatar = user.avatar_url if user and user.avatar_url else None
            avatar_src = self.settings.get_asset_path(raw_avatar) if raw_avatar else avatar_path
            avatar_ctrl = ft.Container(
                content=ft.Image(
                    src=avatar_src,
                    width=68,
                    height=68,
                    fit=ft.BoxFit.COVER,
                    border_radius=34,
                    error_content=ft.CircleAvatar(
                        content=ft.Icon(
                            ft.Icons.PERSON, size=34, color=ft.Colors.WHITE
                        ),
                        radius=34,
                        bgcolor=ThemeColors.PRIMARY_BLUE,
                    ),
                ),
                width=68,
                height=68,
                border_radius=34,
                border=ft.Border.all(2, ThemeColors.PRIMARY_BLUE),
            )
            auth_action_btn = ft.Container(
                content=ft.Text(
                    "Edit Profile",
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=ThemeColors.PRIMARY_BLUE,
                ),
                border=ft.Border.all(1.5, ThemeColors.PRIMARY_BLUE),
                border_radius=20,
                padding=ft.Padding.symmetric(horizontal=16, vertical=6),
                ink=True,
                on_click=lambda _: self._open_edit_profile_dialog(),
            )
        else:
            name_val = user.full_name if (user and user.first_name) else "Guest Explorer"
            handle_val = f"@{user.username}" if (user and user.username) else "Browsing in Guest Mode (Offline)"
            raw_avatar = user.avatar_url if (user and user.avatar_url) else None
            avatar_src = self.settings.get_asset_path(raw_avatar) if raw_avatar else None
            avatar_ctrl = ft.Container(
                content=ft.Image(
                    src=avatar_src,
                    width=68,
                    height=68,
                    fit=ft.BoxFit.COVER,
                    border_radius=34,
                    error_content=ft.Icon(
                        ft.Icons.PERSON, size=34, color=ThemeColors.TEXT_MUTED_LIGHT
                    ),
                ) if avatar_src else ft.Icon(
                    ft.Icons.PERSON, size=34, color=ThemeColors.TEXT_MUTED_LIGHT
                ),
                width=68,
                height=68,
                border_radius=34,
                bgcolor=ThemeColors.SURFACE_DARK_HOVER,
                alignment=ft.Alignment(0, 0),
            )
            auth_action_btn = ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            "Edit Profile",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ThemeColors.PRIMARY_BLUE,
                        ),
                        border=ft.Border.all(1.5, ThemeColors.PRIMARY_BLUE),
                        border_radius=20,
                        padding=ft.Padding.symmetric(horizontal=14, vertical=6),
                        ink=True,
                        on_click=lambda _: self._open_edit_profile_dialog(),
                    ),
                    ft.Container(
                        content=ft.Text(
                            "Log In / Sign Up",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        bgcolor=ThemeColors.PRIMARY_BLUE,
                        border_radius=20,
                        padding=ft.Padding.symmetric(horizontal=14, vertical=6),
                        ink=True,
                        on_click=lambda _: self._navigate("/login"),
                    ),
                ],
                spacing=8,
            )

        # Extended Profile Metadata Badges
        profile_badges: list[ft.Control] = []
        if user:
            if user.email and not is_guest:
                profile_badges.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.EMAIL_OUTLINED, size=12, color=ThemeColors.PRIMARY_BLUE),
                                ft.Text(user.email, size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ],
                            spacing=4,
                            tight=True,
                        ),
                        bgcolor=ThemeColors.BG_LIGHT,
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    )
                )
            if user.phone_number:
                profile_badges.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.PHONE_OUTLINED, size=12, color=ThemeColors.PRIMARY_BLUE),
                                ft.Text(user.phone_number, size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ],
                            spacing=4,
                            tight=True,
                        ),
                        bgcolor=ThemeColors.BG_LIGHT,
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    )
                )
            if user.birthday:
                profile_badges.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.CAKE_OUTLINED, size=12, color=ThemeColors.PRIMARY_BLUE),
                                ft.Text(user.birthday, size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ],
                            spacing=4,
                            tight=True,
                        ),
                        bgcolor=ThemeColors.BG_LIGHT,
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    )
                )
            if user.gender:
                profile_badges.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.PERSON_OUTLINE, size=12, color=ThemeColors.PRIMARY_BLUE),
                                ft.Text(user.gender, size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ],
                            spacing=4,
                            tight=True,
                        ),
                        bgcolor=ThemeColors.BG_LIGHT,
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    )
                )
            if user.default_daily_budget:
                profile_badges.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.PAYMENTS_OUTLINED, size=12, color=ThemeColors.PRIMARY_BLUE),
                                ft.Text(f"₱{int(user.default_daily_budget):,}/day", size=11, weight=ft.FontWeight.W_600, color=ThemeColors.PRIMARY_BLUE),
                            ],
                            spacing=4,
                            tight=True,
                        ),
                        bgcolor=ThemeColors.BG_LIGHT,
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    )
                )

        badge_row = ft.Row(
            controls=profile_badges,
            spacing=6,
            wrap=True,
        ) if profile_badges else ft.Container(height=0)

        identity_info = ft.Column(
            controls=[
                ft.Text(
                    name_val,
                    size=20,
                    weight=ft.FontWeight.W_800,
                    color=ThemeColors.TEXT_BLACK,
                ),
                ft.Text(handle_val, size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                badge_row,
                ft.Container(height=4),
                auth_action_btn,
            ],
            spacing=4,
            expand=True,
        )

        identity_card = ft.Container(
            content=ft.Row(
                controls=[avatar_ctrl, identity_info],
                spacing=20,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            border_radius=20,
            padding=ft.Padding.all(22),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=ft.Colors.with_opacity(0.04, "#000000"),
                offset=ft.Offset(0, 4),
            ),
        )

        # 2. Unsynced Local Guest Trips Banner
        guest_trips_count = len(self.guest_storage.list_itineraries())
        sync_banner = ft.Container()
        if guest_trips_count > 0:
            sync_banner = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.CLOUD_UPLOAD_OUTLINED,
                                    size=20,
                                    color=ThemeColors.PRIMARY_BLUE,
                                ),
                                ft.Text(
                                    f"{guest_trips_count} local {'trip' if guest_trips_count == 1 else 'trips'} not synced",
                                    size=13,
                                    weight=ft.FontWeight.W_600,
                                    color=ThemeColors.TEXT_BLACK,
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.FilledButton(
                            content=(
                                "Sync Now" if not self.is_migrating else "Syncing..."
                            ),
                            style=ft.ButtonStyle(
                                bgcolor=ThemeColors.PRIMARY_BLUE,
                                color=ft.Colors.WHITE,
                                shape=ft.RoundedRectangleBorder(radius=8),
                            ),
                            disabled=self.is_migrating,
                            on_click=lambda _: self._sync_guest_trips(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=ThemeColors.PRIMARY_LIGHT,
                border=ft.Border.all(1, ThemeColors.CUSTOM_CARD_BORDER),
                border_radius=14,
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                margin=ft.Margin.only(top=14),
            )

        # 3. 5-Row Profile Navigation Card matching Figma (NO chevrons, blue rounded squares)
        menu_rows = ft.Column(
            controls=[
                self._create_menu_row(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    icon_color=ThemeColors.PRIMARY_BLUE,
                    box_bgcolor=ThemeColors.AZURE_SOFT,
                    title="Settings",
                    desc="Manage your account and customize your app experience.",
                    on_click=lambda: self._open_settings_dialog(),
                ),
                ft.Divider(color=ThemeColors.BORDER_LIGHT, height=1),
                self._create_menu_row(
                    icon=ft.Icons.FAVORITE,
                    icon_color=ThemeColors.PRIMARY_BLUE,
                    box_bgcolor=ThemeColors.AZURE_SOFT,
                    title="Favorites",
                    desc=f"Your favorite places ({len(self.favorites_service.get_favorites())} saved).",
                    on_click=lambda: self._open_favorites_dialog(),
                ),
                ft.Divider(color=ThemeColors.BORDER_LIGHT, height=1),
                self._create_menu_row(
                    icon=ft.Icons.HELP_OUTLINE,
                    icon_color=ThemeColors.PRIMARY_BLUE,
                    box_bgcolor=ThemeColors.AZURE_SOFT,
                    title="Help & Support",
                    desc="Provincial hotlines, emergency contacts, and FAQs.",
                    on_click=lambda: self._open_help_dialog(),
                ),
                ft.Divider(color=ThemeColors.BORDER_LIGHT, height=1),
                self._create_menu_row(
                    icon=ft.Icons.INFO_OUTLINE,
                    icon_color=ThemeColors.PRIMARY_BLUE,
                    box_bgcolor=ThemeColors.AZURE_SOFT,
                    title="About",
                    desc=f"Trip mo, trip ko — Desktop Client v{self.settings.app_version}.",
                    on_click=lambda: self._open_about_dialog(),
                ),
                ft.Divider(color=ThemeColors.BORDER_LIGHT, height=1),
                self._create_menu_row(
                    icon=ft.Icons.LOGOUT,
                    icon_color=ThemeColors.ERROR,
                    box_bgcolor=ThemeColors.ERROR_BG,
                    title="Log Out" if not is_guest else "Exit Guest Mode",
                    desc=(
                        "Sign out of your account."
                        if not is_guest
                        else "Return to welcome screen."
                    ),
                    title_color=ThemeColors.ERROR,
                    on_click=lambda: self._confirm_logout(),
                ),
            ],
            spacing=0,
        )

        profile_menu_card = ft.Container(
            content=menu_rows,
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            border_radius=20,
            padding=ft.Padding.symmetric(vertical=8, horizontal=16),
            margin=ft.Margin.only(top=16),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=ft.Colors.with_opacity(0.04, "#000000"),
                offset=ft.Offset(0, 4),
            ),
        )

        main_column = ft.Column(
            controls=[
                title_block,
                ft.Container(height=14),
                identity_card,
                sync_banner,
                profile_menu_card,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.content = main_column

    def _create_menu_row(
        self,
        icon: str,
        icon_color: str,
        box_bgcolor: str,
        title: str,
        desc: str,
        on_click: Callable[[], None],
        title_color: Optional[str] = None,
    ) -> ft.Control:
        """Creates a modern menu row with rounded square icon box and NO chevrons."""
        icon_box = ft.Container(
            content=ft.Icon(icon, size=22, color=icon_color),
            width=42,
            height=42,
            bgcolor=box_bgcolor,
            border_radius=12,
            alignment=ft.Alignment(0, 0),
        )

        text_block = ft.Column(
            controls=[
                ft.Text(
                    title,
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    color=title_color or ThemeColors.TEXT_BLACK,
                ),
                ft.Text(desc, size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
            ],
            spacing=2,
            expand=True,
        )

        return ft.Container(
            content=ft.Row(
                controls=[icon_box, text_block],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(vertical=14, horizontal=10),
            ink=True,
            border_radius=12,
            on_click=lambda _: on_click(),
        )

    def _open_settings_dialog(self) -> None:
        """Opens dedicated Settings sub-window modal with connectivity controls."""
        notif_switch = ft.Switch(
            label="Push Notifications",
            value=True,
            active_color=ThemeColors.PRIMARY_BLUE,
        )
        offline_switch = ft.Switch(
            label="Offline Map Cache", value=True, active_color=ThemeColors.PRIMARY_BLUE
        )
        dark_switch = ft.Switch(
            label="Dark Theme Mode",
            value=(
                self.safe_page.theme_mode == ft.ThemeMode.DARK
                if self.safe_page
                else False
            ),
            active_color=ThemeColors.PRIMARY_BLUE,
            on_change=lambda _: self._toggle_theme(),
        )

        def _clear_cache(_):
            self.guest_storage.clear_all()
            cache_status.value = "Local cache cleared successfully."
            dlg.update()

        cache_status = ft.Text("", size=12, color=ThemeColors.BUDGET_GREEN)

        # Server Connectivity Controls
        is_offline = self.connectivity_service.is_host_offline
        status_icon = ft.Icon(
            ft.Icons.CLOUD_OFF if is_offline else ft.Icons.CHECK_CIRCLE,
            size=16,
            color="#f59e0b" if is_offline else ThemeColors.SUCCESS,
        )
        status_label = ft.Text(
            "Offline / Cloud Sync Paused" if is_offline else "Online (Backend Connected)",
            size=12,
            weight=ft.FontWeight.BOLD,
            color="#d97706" if is_offline else ThemeColors.SUCCESS,
        )

        api_url_input = ft.TextField(
            label="Backend Server API URL",
            value=self.connectivity_service.current_api_url,
            hint_text="http://localhost:8000",
            dense=True,
            border_radius=10,
        )
        api_status = ft.Text("", size=11)

        def _test_health(_):
            api_status.value = "Probing health endpoint..."
            api_status.color = ThemeColors.PRIMARY_BLUE
            dlg.update()

            async def _do_test():
                online = await self.connectivity_service.check_host_health()
                if online:
                    status_icon.name = ft.Icons.CHECK_CIRCLE
                    status_icon.color = ThemeColors.SUCCESS
                    status_label.value = "Online (HTTP 200 OK)"
                    status_label.color = ThemeColors.SUCCESS
                    api_status.value = f"Connection successful to {self.connectivity_service.current_api_url}!"
                    api_status.color = ThemeColors.SUCCESS
                else:
                    status_icon.name = ft.Icons.CLOUD_OFF
                    status_icon.color = "#f59e0b"
                    status_label.value = "Offline / Host Unreachable"
                    status_label.color = "#d97706"
                    api_status.value = "Host unreachable. Please check backend process."
                    api_status.color = ThemeColors.ERROR
                dlg.update()

            if self.safe_page:
                self.safe_page.run_task(_do_test)
            else:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(_do_test())
                except RuntimeError:
                    pass

        def _save_url(_):
            new_url = (api_url_input.value or "").strip()
            try:
                self.connectivity_service.set_custom_api_url(new_url)
                api_status.value = f"Saved custom URL: {new_url}"
                api_status.color = ThemeColors.SUCCESS
            except ValueError as err:
                api_status.value = str(err)
                api_status.color = ThemeColors.ERROR
            dlg.update()

        def _reset_url(_):
            self.connectivity_service.clear_custom_api_url()
            api_url_input.value = self.connectivity_service.current_api_url
            api_status.value = "Reset to default: http://localhost:8000"
            api_status.color = ThemeColors.BUDGET_GREEN
            dlg.update()

        dlg = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.SETTINGS, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text("App Settings & Connectivity", size=18, weight=ft.FontWeight.BOLD),
                ]
            ),
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Customize preferences and configure backend API connectivity.",
                        size=12,
                        color=ThemeColors.TEXT_MUTED_LIGHT,
                    ),
                    ft.Divider(color=ThemeColors.BORDER_LIGHT),
                    notif_switch,
                    offline_switch,
                    dark_switch,
                    ft.Divider(color=ThemeColors.BORDER_LIGHT),
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Local Cache Storage",
                                size=13,
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.OutlinedButton("Clear Cache", on_click=_clear_cache),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    cache_status,
                    ft.Divider(color=ThemeColors.BORDER_LIGHT),
                    ft.Row(
                        controls=[
                            ft.Text("Backend Connection Status", size=13, weight=ft.FontWeight.W_600),
                            ft.Row(controls=[status_icon, status_label], spacing=6),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    api_url_input,
                    ft.Row(
                        controls=[
                            ft.FilledButton(
                                content="Test Connection",
                                style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                                on_click=_test_health,
                            ),
                            ft.OutlinedButton(
                                content="Save URL",
                                on_click=_save_url,
                            ),
                            ft.TextButton(
                                content="Reset Default",
                                on_click=_reset_url,
                            ),
                        ],
                        spacing=8,
                    ),
                    api_status,
                ],
                spacing=10,
                tight=True,
                width=480,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _: self._close_dialog(dlg)),
            ],
        )
        self._show_dialog(dlg)

    def _open_favorites_dialog(self) -> None:
        """Opens dedicated Favorites Subview Modal (UI-25)."""
        if not self.safe_page:
            return

        favorites = self.favorites_service.get_favorites()
        active_cat = "all"
        fav_listview = ft.ListView(spacing=8, height=360)

        def render_favs():
            filtered = [
                f for f in favorites if active_cat == "all" or f.category == active_cat
            ]
            if not filtered:
                fav_listview.controls = [
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(
                                    ft.Icons.FAVORITE_BORDER,
                                    size=36,
                                    color=ThemeColors.TEXT_FAINT_LIGHT,
                                ),
                                ft.Text(
                                    "No favorites saved in this category.",
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    "Explore destinations on the map and click the heart icon to save them.",
                                    size=11,
                                    color=ThemeColors.TEXT_MUTED_LIGHT,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4,
                        ),
                        padding=30,
                        alignment=ft.Alignment(0, 0),
                    )
                ]
            else:
                cards = []
                for place in filtered:
                    cards.append(
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Image(
                                        src=place.resolved_image_path,
                                        width=75,
                                        height=60,
                                        fit=ft.BoxFit.COVER,
                                        border_radius=8,
                                        error_content=ft.Icon(
                                            ft.Icons.LANDSCAPE,
                                            size=24,
                                            color=ThemeColors.PRIMARY_BLUE,
                                        ),
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text(
                                                place.name,
                                                size=13,
                                                weight=ft.FontWeight.BOLD,
                                                max_lines=1,
                                                overflow=ft.TextOverflow.ELLIPSIS,
                                            ),
                                            ft.Text(
                                                f"{place.municipality_name or 'Nueva Ecija'} • {place.formatted_category}",
                                                size=11,
                                                color=ThemeColors.TEXT_MUTED_LIGHT,
                                            ),
                                            ft.Text(
                                                place.formatted_cost,
                                                size=11,
                                                weight=ft.FontWeight.BOLD,
                                                color=ThemeColors.EMERALD_PRIMARY,
                                            ),
                                        ],
                                        spacing=2,
                                        expand=True,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.FAVORITE,
                                        icon_color=ft.Colors.RED_500,
                                        icon_size=20,
                                        tooltip="Remove from Favorites",
                                        on_click=lambda _, pl=place: remove_fav(pl),
                                    ),
                                    ft.FilledButton(
                                        content="View",
                                        style=ft.ButtonStyle(
                                            bgcolor=ThemeColors.PRIMARY_BLUE,
                                            color=ft.Colors.WHITE,
                                            padding=ft.Padding.symmetric(
                                                horizontal=10, vertical=4
                                            ),
                                            shape=ft.RoundedRectangleBorder(radius=6),
                                        ),
                                        on_click=lambda _, pl=place: show_place_detail_dialog(
                                            self.safe_page,
                                            pl,
                                            on_navigate=self.on_navigate,
                                        ),
                                    ),
                                ],
                                spacing=10,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            bgcolor=ThemeColors.SURFACE_LIGHT,
                            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
                            border_radius=10,
                            padding=8,
                        )
                    )
                fav_listview.controls = cards
            try:
                fav_listview.update()
            except Exception:
                pass

        def remove_fav(pl: Place):
            nonlocal favorites
            self.favorites_service.remove_favorite(pl.id)
            favorites = self.favorites_service.get_favorites()
            render_favs()
            self._build_content()
            self._safe_update()

        def set_cat(cat_key: str):
            nonlocal active_cat
            active_cat = cat_key
            for c in cat_row.controls:
                is_sel = getattr(c, "data", None) == cat_key
                c.bgcolor = (
                    ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.SURFACE_LIGHT
                )
                c.content.color = (
                    ft.Colors.WHITE if is_sel else ThemeColors.TEXT_MAIN_LIGHT
                )
            try:
                cat_row.update()
            except Exception:
                pass
            render_favs()

        cats = [
            ("all", "All"),
            ("nature_park", "Nature"),
            ("cafe", "Cafes"),
            ("museum_cultural", "Heritage"),
            ("resort_swimming", "Resorts"),
        ]
        cat_buttons = []
        for ck, cl in cats:
            is_sel = ck == active_cat
            btn = ft.Container(
                content=ft.Text(
                    cl,
                    size=11,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE if is_sel else ThemeColors.TEXT_MAIN_LIGHT,
                ),
                bgcolor=(
                    ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.SURFACE_LIGHT
                ),
                border=ft.Border.all(
                    1, ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.BORDER_LIGHT
                ),
                border_radius=14,
                padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                ink=True,
                data=ck,
                on_click=lambda _, k=ck: set_cat(k),
            )
            cat_buttons.append(btn)

        cat_row = ft.Row(controls=cat_buttons, spacing=6)
        render_favs()

        dlg = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.FAVORITE, color=ft.Colors.RED_500, size=22),
                    ft.Text("Saved Favorites", size=18, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            content=ft.Column(
                controls=[
                    cat_row,
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    fav_listview,
                ],
                spacing=10,
                width=500,
                tight=True,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _: self._close_dialog(dlg)),
            ],
        )
        self._show_dialog(dlg)

    def _open_help_dialog(self) -> None:
        """Opens Help & Support sub-window dialog with Emergency Provincial Hotlines."""
        dlg = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.HELP_OUTLINE, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text("Help & Support", size=18, weight=ft.FontWeight.BOLD),
                ]
            ),
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Emergency Provincial Hotlines:",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    "🚨 PDRRMO Emergency Hotline: (044) 940 3388",
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                    color=ThemeColors.ERROR,
                                ),
                                ft.Text(
                                    "🚔 PNP Nueva Ecija Command: 117 / (044) 463 0565",
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    "🚑 Cabanatuan Rescue Station: (044) 463 8888",
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                            spacing=3,
                        ),
                        bgcolor=ThemeColors.ERROR_BG,
                        border_radius=8,
                        padding=10,
                    ),
                    ft.Container(height=4),
                    ft.Text(
                        "Frequently Asked Questions:",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "• How do I plan a trip? Use the Suggested Wizard or Custom Builder from the Home Dashboard.",
                        size=12,
                        color=ThemeColors.TEXT_MUTED_LIGHT,
                    ),
                    ft.Text(
                        "• Are prices verified? Yes, entrance fees are recorded directly from Nueva Ecija municipal registries.",
                        size=12,
                        color=ThemeColors.TEXT_MUTED_LIGHT,
                    ),
                    ft.Text(
                        "• Can I use the app offline? Yes, cached itineraries and points of interest remain accessible offline.",
                        size=12,
                        color=ThemeColors.TEXT_MUTED_LIGHT,
                    ),
                    ft.Text(
                        "• Contact: support@nuevaecijatravel.ph",
                        size=12,
                        weight=ft.FontWeight.W_600,
                        color=ThemeColors.PRIMARY_BLUE,
                    ),
                ],
                spacing=6,
                tight=True,
                width=450,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _: self._close_dialog(dlg)),
            ],
        )
        self._show_dialog(dlg)

    def _open_about_dialog(self) -> None:
        """Opens About dialog matching web client."""
        dlg = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text(
                        "About Trip mo, trip ko", size=18, weight=ft.FontWeight.BOLD
                    ),
                ]
            ),
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"Version {self.settings.app_version}",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "Nueva Ecija Travel Platform — Desktop Client",
                        size=13,
                        color=ThemeColors.TEXT_BLACK,
                    ),
                    ft.Text(
                        "Built with Python Flet & FastAPI backend, exploring all 32 LGUs from Sierra Madre to Pantabangan Lake.",
                        size=12,
                        color=ThemeColors.TEXT_MUTED_LIGHT,
                    ),
                    ft.Text(
                        "© 2026 Nueva Ecija Tourism Council. All rights reserved.",
                        size=11,
                        color=ThemeColors.TEXT_FAINT_LIGHT,
                    ),
                ],
                spacing=6,
                tight=True,
                width=380,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _: self._close_dialog(dlg)),
            ],
        )
        self._show_dialog(dlg)

    def _confirm_logout(self) -> None:
        """Opens log out confirmation modal dialog."""

        def _do_logout(_):
            self._close_dialog(dlg)
            self.session_manager.clear_session()
            self._navigate("/welcome?logout=1")

        dlg = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.LOGOUT, color=ThemeColors.PRIMARY_BLUE, size=24),
                    ft.Text("Confirm Log Out", size=18, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            content=ft.Text(
                "Are you sure you want to log out of your account? Your offline trips will remain safely stored on this device.",
                size=13,
                color=ThemeColors.TEXT_MUTED_LIGHT,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton(
                    content="Log Out",
                    style=ft.ButtonStyle(
                        bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE
                    ),
                    on_click=_do_logout,
                ),
            ],
        )
        self._show_dialog(dlg)

    def _show_dialog(self, dlg: ft.AlertDialog) -> None:
        if self.page:
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()

    def _close_dialog(self, dlg: ft.AlertDialog) -> None:
        dlg.open = False
        if self.page:
            self.page.update()

    def _toggle_theme(self) -> None:
        if self.on_toggle_theme:
            self.on_toggle_theme()
        self._build_content()
        self._safe_update()

    def _open_edit_profile_dialog(self) -> None:
        user = self.session_manager.current_user
        current_avatar_url = [user.avatar_url if user and user.avatar_url else None]

        # Photo Preview Avatar Control
        def _get_avatar_content():
            if current_avatar_url[0]:
                return ft.Image(
                    src=current_avatar_url[0],
                    width=64,
                    height=64,
                    fit=ft.BoxFit.COVER,
                    border_radius=32,
                    error_content=ft.Icon(ft.Icons.PERSON, size=32, color=ThemeColors.PRIMARY_BLUE),
                )
            return ft.Icon(ft.Icons.PERSON, size=32, color=ThemeColors.TEXT_MUTED_LIGHT)

        photo_preview = ft.Container(
            content=_get_avatar_content(),
            width=64,
            height=64,
            border_radius=32,
            border=ft.Border.all(2, ThemeColors.PRIMARY_BLUE),
            alignment=ft.Alignment(0, 0),
        )

        def _pick_photo(_):
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                f_path = filedialog.askopenfilename(
                    title="Select Profile Avatar",
                    filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.webp")],
                )
                root.destroy()
                if f_path:
                    try:
                        import base64
                        from pathlib import Path
                        ext = Path(f_path).suffix.lstrip(".").lower()
                        if ext == "jpg":
                            ext = "jpeg"
                        with open(f_path, "rb") as img_f:
                            b64_str = base64.b64encode(img_f.read()).decode("ascii")
                        current_avatar_url[0] = f"data:image/{ext};base64,{b64_str}"
                    except Exception:
                        current_avatar_url[0] = f_path
                    photo_preview.content = _get_avatar_content()
                    dlg.update()
            except Exception:
                pass

        def _remove_photo(_):
            current_avatar_url[0] = None
            photo_preview.content = _get_avatar_content()
            dlg.update()

        def _set_preset_avatar(preset_path: str):
            current_avatar_url[0] = preset_path
            photo_preview.content = _get_avatar_content()
            dlg.update()

        preset_row = ft.Row(
            controls=[
                ft.TextButton(
                    "Hiker",
                    on_click=lambda _: _set_preset_avatar(self.settings.get_asset_path("images/guest_hiker_hero.png")),
                    style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=8, vertical=2)),
                ),
                ft.TextButton(
                    "Default",
                    on_click=lambda _: _set_preset_avatar(self.settings.get_asset_path("images/default_avatar_placeholder.png")),
                    style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=8, vertical=2)),
                ),
            ],
            spacing=4,
        )

        photo_section = ft.Row(
            controls=[
                photo_preview,
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.FilledButton(
                                    content="Change Photo",
                                    style=ft.ButtonStyle(
                                        bgcolor=ThemeColors.PRIMARY_BLUE,
                                        color=ft.Colors.WHITE,
                                        padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                                    ),
                                    on_click=_pick_photo,
                                ),
                                ft.OutlinedButton(
                                    content="Remove",
                                    style=ft.ButtonStyle(
                                        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                                    ),
                                    on_click=_remove_photo,
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Row(
                            controls=[
                                ft.Text("Presets:", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                preset_row,
                            ],
                            spacing=4,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=4,
                    expand=True,
                ),
            ],
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        first_input = ft.TextField(
            label="First Name *",
            value=user.first_name if user and user.first_name else "",
            border_radius=10,
            dense=True,
            expand=True,
        )
        mi_input = ft.TextField(
            label="M.I.",
            value=user.middle_initial if user and user.middle_initial else "",
            width=70,
            border_radius=10,
            dense=True,
            max_length=2,
        )
        last_input = ft.TextField(
            label="Last Name *",
            value=user.last_name if user and user.last_name else "",
            border_radius=10,
            dense=True,
        )
        username_input = ft.TextField(
            label="Username",
            value=user.username if user and user.username else "",
            prefix_icon=ft.Icons.ALTERNATE_EMAIL,
            border_radius=10,
            dense=True,
        )
        is_guest_user = self.session_manager.is_guest or (user and user.is_guest)
        email_input = ft.TextField(
            label="Email Address",
            value=user.email if user and user.email else "",
            prefix_icon=ft.Icons.MAIL_OUTLINE,
            border_radius=10,
            dense=True,
            read_only=not is_guest_user,
        )
        phone_input = ft.TextField(
            label="Phone Number",
            value=user.phone_number if user and user.phone_number else "",
            prefix_icon=ft.Icons.PHONE,
            hint_text="+63 9XX XXX XXXX",
            border_radius=10,
            dense=True,
        )
        birthday_input = ft.TextField(
            label="Birthday (YYYY-MM-DD)",
            value=user.birthday if user and user.birthday else "",
            prefix_icon=ft.Icons.CAKE,
            hint_text="1998-05-12",
            border_radius=10,
            dense=True,
        )
        gender_options = [
            ft.dropdown.Option("Male"),
            ft.dropdown.Option("Female"),
            ft.dropdown.Option("Non-binary"),
            ft.dropdown.Option("Prefer not to say"),
        ]
        gender_input = ft.Dropdown(
            label="Gender",
            options=gender_options,
            value=user.gender if user and user.gender else None,
            border_radius=10,
            dense=True,
        )
        budget_input = ft.TextField(
            label="Default Daily Budget (PHP)",
            value=str(int(user.default_daily_budget)) if user and user.default_daily_budget else "3000",
            prefix=ft.Text("₱ "),
            border_radius=10,
            dense=True,
        )
        current_pwd_input = ft.TextField(
            label="Current Password (optional)",
            password=True,
            can_reveal_password=True,
            border_radius=10,
            dense=True,
        )
        new_pwd_input = ft.TextField(
            label="New Password (min 8 chars)",
            password=True,
            can_reveal_password=True,
            border_radius=10,
            dense=True,
        )

        validation_text = ft.Text("", size=11, color=ThemeColors.ERROR)

        def _save(_):
            f_val = first_input.value.strip() if first_input.value else ""
            l_val = last_input.value.strip() if last_input.value else ""
            mi_val = mi_input.value.strip() if mi_input.value else ""
            u_val = username_input.value.strip() if username_input.value else ""
            e_val = email_input.value.strip() if email_input.value else ""
            p_val = phone_input.value.strip() if phone_input.value else ""
            b_val = birthday_input.value.strip() if birthday_input.value else ""
            g_val = gender_input.value if gender_input.value else ""
            try:
                bud_val = float(budget_input.value.replace(",", "").strip()) if budget_input.value else 3000.0
            except ValueError:
                bud_val = 3000.0

            cur_pwd_val = (current_pwd_input.value or "").strip()
            new_pwd_val = (new_pwd_input.value or "").strip()
            if new_pwd_val and len(new_pwd_val) < 8:
                validation_text.value = "New password must be at least 8 characters."
                dlg.update()
                return

            if not f_val or not l_val:
                validation_text.value = "First Name and Last Name are required."
                dlg.update()
                return

            payload = UserUpdatePayload(
                first_name=f_val,
                last_name=l_val,
                middle_initial=mi_val,
                username=u_val or None,
                email=e_val or None,
                phone_number=p_val or None,
                birthday=b_val or None,
                gender=g_val or None,
                default_daily_budget=bud_val,
                avatar_url=current_avatar_url[0],
                current_password=cur_pwd_val or None,
                new_password=new_pwd_val or None,
            )

            async def _update():
                try:
                    await self.auth_service.update_profile(payload)
                    self._close_dialog(dlg)
                    self._build_content()
                    self._safe_update()
                    p = self.safe_page
                    if p:
                        p.snack_bar = ft.SnackBar(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.WHITE, size=18),
                                    ft.Text("Profile updated successfully!", color=ft.Colors.WHITE),
                                ],
                                spacing=8,
                            ),
                            bgcolor=ThemeColors.SUCCESS,
                            open=True,
                        )
                        p.update()
                except Exception as err:
                    validation_text.value = f"Update failed: {str(err)}"
                    dlg.update()

            if self.page:
                self.page.run_task(_update)
            else:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(_update())
                except RuntimeError:
                    pass

        dlg = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.PERSON, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text("Edit Profile Details", size=18, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            content=ft.Column(
                controls=[
                    photo_section,
                    ft.Divider(color=ThemeColors.BORDER_LIGHT),
                    ft.Row(controls=[first_input, mi_input], spacing=8),
                    last_input,
                    username_input,
                    email_input,
                    phone_input,
                    birthday_input,
                    gender_input,
                    budget_input,
                    current_pwd_input,
                    new_pwd_input,
                    validation_text,
                ],
                spacing=8,
                tight=True,
                width=460,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton(
                    content="Save Changes",
                    style=ft.ButtonStyle(
                        bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE
                    ),
                    on_click=_save,
                ),
            ],
        )
        self._show_dialog(dlg)

    def _sync_guest_trips(self) -> None:
        self.is_migrating = True
        self._build_content()
        self._safe_update()

        async def _run():
            try:
                migrated = await self.auth_service.migrate_guest_trips()
            finally:
                self.is_migrating = False
                self._build_content()
                self._safe_update()

        if self.page:
            self.page.run_task(_run)
        else:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_run())
            except RuntimeError:
                pass

    def did_mount(self) -> None:
        if self._has_refreshed_profile:
            return
        if self.session_manager.is_authenticated and not self.session_manager.is_guest:
            self._has_refreshed_profile = True
            async def _refresh_profile():
                try:
                    latest_user = await self.auth_service.get_profile()
                    if latest_user:
                        self._build_content()
                        self._safe_update()
                except Exception:
                    pass

            if self.safe_page:
                self.safe_page.run_task(_refresh_profile)

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass

    @property
    def safe_page(self) -> Optional[ft.Page]:
        try:
            return self.page
        except Exception:
            return None

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
