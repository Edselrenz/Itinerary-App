"""Profile, Account Settings, and Local Cache Management View mirroring Ionic tabs/profile."""

import asyncio
from typing import Callable, Optional
import flet as ft

from desktop_client.components.dialogs import show_confirm_dialog
from desktop_client.config.settings import ThemeColors, get_settings
from desktop_client.core.session import get_session_manager
from desktop_client.core.storage import get_guest_storage
from desktop_client.models.user import UserUpdatePayload
from desktop_client.services.auth_service import get_auth_service


class ProfileView(ft.Container):
    """Profile view matching Ionic tabs/profile:

    - Traveler identity row (Authenticated photo vs Guest Explorer).
    - Unsynced local guest trips banner with [Sync] button.
    - Settings card (Theme toggle, local cache info, and logout).
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
        self.settings = get_settings()

        self.expand = True
        self.padding = ft.Padding.symmetric(horizontal=32, vertical=20)
        self.bgcolor = ThemeColors.BG_LIGHT

        self.status_msg: Optional[str] = None
        self.is_migrating = False

        self._build_content()

    def _build_content(self) -> None:
        user = self.session_manager.current_user
        is_guest = self.session_manager.is_guest or not self.session_manager.is_authenticated

        # Page Title
        title_block = ft.Column(
            controls=[
                ft.Text("Profile", size=24, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                ft.Text("Account details, sync status, and desktop preferences.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
            ],
            spacing=2,
        )

        # Identity Header Section matching .identity-row
        name_val = user.full_name if user else "Guest Explorer"
        email_val = user.email if user else "Browsing in Guest Mode (Offline)"

        avatar_ctrl: ft.Control
        if not is_guest:
            avatar_ctrl = ft.CircleAvatar(
                content=ft.Icon(ft.Icons.PERSON, size=32, color=ft.Colors.WHITE),
                radius=32,
                bgcolor=ThemeColors.PRIMARY_BLUE,
            )
            auth_action_btn = ft.Container(
                content=ft.Text("Edit Profile", size=12, weight=ft.FontWeight.W_700, color=ThemeColors.PRIMARY_BLUE),
                border=ft.Border.all(1.2, ThemeColors.PRIMARY_BLUE),
                border_radius=20,
                padding=ft.Padding.symmetric(horizontal=14, vertical=6),
                ink=True,
                on_click=lambda _: self._open_edit_profile_dialog(),
            )
        else:
            avatar_ctrl = ft.CircleAvatar(
                content=ft.Icon(ft.Icons.PERSON_OUTLINE, size=32, color=ThemeColors.TEXT_MUTED_LIGHT),
                radius=32,
                bgcolor=ThemeColors.SURFACE_DARK_HOVER,
            )
            auth_action_btn = ft.Container(
                content=ft.Text("Log In / Sign Up", size=12, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                bgcolor=ThemeColors.PRIMARY_BLUE,
                border_radius=20,
                padding=ft.Padding.symmetric(horizontal=16, vertical=7),
                ink=True,
                on_click=lambda _: self._navigate("/login"),
            )

        identity_info = ft.Column(
            controls=[
                ft.Text(name_val, size=18, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                ft.Text(email_val, size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                ft.Container(height=4),
                auth_action_btn,
            ],
            spacing=3,
            expand=True,
        )

        identity_row = ft.Container(
            content=ft.Row(
                controls=[avatar_ctrl, identity_info],
                spacing=18,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            border_radius=18,
            padding=ft.Padding.all(20),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.04, "#000000"),
            ),
        )

        # Unsynced Local Guest Trips Migration Prompt matching .sync-banner
        guest_trips_count = len(self.guest_storage.list_itineraries())
        sync_banner = ft.Container()
        if guest_trips_count > 0:
            sync_banner = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.CLOUD_UPLOAD_OUTLINED, size=20, color=ThemeColors.PRIMARY_BLUE),
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
                            content="Sync Now" if not self.is_migrating else "Syncing...",
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

        # Settings Card matching .profile-card
        settings_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Preferences & Desktop Settings", size=15, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                    ft.Divider(color=ThemeColors.BORDER_LIGHT, height=1),
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.DARK_MODE_OUTLINED, size=20, color=ThemeColors.PRIMARY_BLUE),
                            ft.Column(
                                controls=[
                                    ft.Text("Theme Mode", size=13, weight=ft.FontWeight.W_600),
                                    ft.Text("Switch between Light and Dark Material 3 palette", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.OutlinedButton(
                                content="Toggle Theme",
                                on_click=lambda _: self._toggle_theme(),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Divider(color=ThemeColors.BORDER_LIGHT, height=1),
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.STORAGE_OUTLINED, size=20, color=ThemeColors.PRIMARY_BLUE),
                            ft.Column(
                                controls=[
                                    ft.Text("Local Offline Storage", size=13, weight=ft.FontWeight.W_600),
                                    ft.Text(f"Cached in: {self.settings.storage_dir}", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.TextButton(
                                content="Clear Cache",
                                style=ft.ButtonStyle(color=ThemeColors.ERROR),
                                on_click=lambda _: self._clear_local_cache(),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Divider(color=ThemeColors.BORDER_LIGHT, height=1),
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.API, size=20, color=ThemeColors.PRIMARY_BLUE),
                            ft.Column(
                                controls=[
                                    ft.Text("Backend API Endpoint", size=13, weight=ft.FontWeight.W_600),
                                    ft.Text(self.settings.api_base_url, size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=2,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=14,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            border_radius=18,
            padding=ft.Padding.all(20),
            margin=ft.Margin.only(top=16),
        )

        # Account Session Action (Log In or Log Out)
        account_action_row: ft.Control
        if not is_guest:
            account_action_row = ft.Container(
                content=ft.FilledButton(
                    content="Log Out",
                    icon=ft.Icons.LOGOUT,
                    style=ft.ButtonStyle(
                        bgcolor=ThemeColors.ERROR,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    on_click=lambda _: self._handle_logout(),
                ),
                margin=ft.Margin.only(top=20),
            )
        else:
            account_action_row = ft.Container(
                content=ft.FilledButton(
                    content="Log In to Sync Trips Across Devices",
                    icon=ft.Icons.LOGIN,
                    style=ft.ButtonStyle(
                        bgcolor=ThemeColors.PRIMARY_BLUE,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    on_click=lambda _: self._navigate("/login"),
                ),
                margin=ft.Margin.only(top=20),
            )

        self.content = ft.Column(
            controls=[
                title_block,
                ft.Container(height=14),
                identity_row,
                sync_banner,
                settings_card,
                account_action_row,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _open_edit_profile_dialog(self) -> None:
        user = self.session_manager.current_user
        name_field = ft.TextField(
            label="Full Name",
            value=user.full_name if user else "",
            border_radius=10,
        )

        def close_dlg(_=None):
            self.page.pop_dialog()

        def save_name(_=None):
            val = (name_field.value or "").strip()
            if val:
                async def _worker():
                    try:
                        await self.auth_service.update_profile(UserUpdatePayload(full_name=val))
                        self._build_content()
                        self.update()
                    except Exception:
                        pass
                asyncio.run(_worker())
            self.page.pop_dialog()

        dlg = ft.AlertDialog(
            title=ft.Text("Edit Profile Name", size=16, weight=ft.FontWeight.BOLD),
            content=ft.Column(controls=[name_field], tight=True, width=360),
            actions=[
                ft.TextButton(content="Cancel", on_click=close_dlg),
                ft.FilledButton(
                    content="Save",
                    style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                    on_click=save_name,
                ),
            ],
        )
        self.page.show_dialog(dlg)

    def _sync_guest_trips(self) -> None:
        if not self.session_manager.is_authenticated:
            self._navigate("/login")
            return

        self.is_migrating = True
        self._build_content()
        self.update()

        async def _worker():
            try:
                await self.auth_service.migrate_guest_trips()
            finally:
                self.is_migrating = False
                self._build_content()
                self.update()

        asyncio.run(_worker())

    def _clear_local_cache(self) -> None:
        def confirm():
            self.guest_storage.clear_all()
            self._build_content()
            self.update()

        show_confirm_dialog(
            self.page,
            title="Clear Local Storage Cache?",
            message="This will delete all guest itineraries stored on this machine.",
            on_confirm=confirm,
        )

    def _handle_logout(self) -> None:
        def confirm():
            self.session_manager.clear_session()
            self._navigate("/welcome")

        show_confirm_dialog(
            self.page,
            title="Log Out?",
            message="Are you sure you want to sign out from your account?",
            on_confirm=confirm,
        )

    def _toggle_theme(self) -> None:
        if self.on_toggle_theme:
            self.on_toggle_theme()

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
