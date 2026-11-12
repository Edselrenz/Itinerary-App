"""Profile, Account Settings, and Local Cache Management View."""

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
    """User profile management, theme configuration, and offline cache clearing."""

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
        self.padding = ft.Padding.all(24)
        self.bgcolor = ThemeColors.BG_LIGHT

        self.status_msg: Optional[str] = None
        self._build_content()

    def _build_content(self) -> None:
        user = self.session_manager.current_user
        is_guest = self.session_manager.is_guest or not self.session_manager.is_authenticated

        # Profile Card
        name_val = user.full_name if user else "Guest Traveler"
        email_val = user.email if user else "Guest Mode (Local Offline Storage)"

        self.name_field = ft.TextField(
            label="Display Name",
            value=name_val,
            disabled=is_guest,
            expand=True,
        )

        update_name_btn = ft.FilledButton(
            content="Update Name",
            style=ft.ButtonStyle(bgcolor=ThemeColors.EMERALD_PRIMARY, color=ft.Colors.WHITE),
            disabled=is_guest,
            on_click=lambda _: self._update_profile_name(),
        )

        profile_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.CircleAvatar(
                                content=ft.Icon(
                                    ft.Icons.PERSON if not is_guest else ft.Icons.PERSON_OUTLINE,
                                    size=32,
                                    color=ft.Colors.WHITE,
                                ),
                                radius=28,
                                bgcolor=ThemeColors.EMERALD_PRIMARY,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(name_val, size=18, weight=ft.FontWeight.BOLD),
                                    ft.Text(email_val, size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                                    ft.Container(
                                        content=ft.Text(
                                            "Verified Account" if not is_guest else "Guest Session",
                                            size=10,
                                            weight=ft.FontWeight.W_600,
                                            color=ThemeColors.SUCCESS if not is_guest else ThemeColors.WARM_GOLD,
                                        ),
                                        bgcolor=ThemeColors.SUCCESS_BG if not is_guest else ThemeColors.AMBER_LIGHT,
                                        border_radius=6,
                                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                    ),
                                ],
                                spacing=2,
                            ),
                        ],
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    ft.Row(
                        controls=[self.name_field, update_name_btn],
                        spacing=12,
                    ),
                ],
                spacing=14,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=14,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            padding=20,
        )

        # Desktop Environment Settings Card
        guest_trips_count = len(self.guest_storage.list_itineraries())

        settings_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Desktop Settings & Diagnostics", size=16, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Theme Mode", size=13, weight=ft.FontWeight.W_600),
                                    ft.Text("Toggle between light and dark visual themes.", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=1,
                            ),
                            ft.OutlinedButton(
                                content="Toggle Theme",
                                icon=ft.Icons.DARK_MODE,
                                on_click=lambda _: self._toggle_theme(),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Backend Connection", size=13, weight=ft.FontWeight.W_600),
                                    ft.Text(f"Target Base: {self.settings.api_base_url}", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=1,
                            ),
                            ft.Container(
                                content=ft.Text("Connected", size=11, weight=ft.FontWeight.W_600, color=ThemeColors.SUCCESS),
                                bgcolor=ThemeColors.SUCCESS_BG,
                                border_radius=6,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Local Guest Storage", size=13, weight=ft.FontWeight.W_600),
                                    ft.Text(f"{guest_trips_count} offline guest itineraries stored locally.", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=1,
                            ),
                            ft.OutlinedButton(
                                content="Clear Guest Cache",
                                icon=ft.Icons.DELETE_SWEEP,
                                style=ft.ButtonStyle(color=ThemeColors.ERROR),
                                on_click=lambda _: self._confirm_clear_cache(),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=12,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=14,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            padding=20,
        )

        # Account Actions (Sign In / Sign Out)
        auth_action_title = "Switch Account / Sign In" if is_guest else "Log Out"
        auth_btn = ft.FilledButton(
            content=auth_action_title,
            icon=ft.Icons.LOGOUT if not is_guest else ft.Icons.LOGIN,
            style=ft.ButtonStyle(
                bgcolor=ThemeColors.ERROR if not is_guest else ThemeColors.EMERALD_PRIMARY,
                color=ft.Colors.WHITE,
                padding=ft.Padding.symmetric(horizontal=24, vertical=12),
            ),
            on_click=lambda _: self._handle_auth_action(),
        )

        status_banner = ft.Container()
        if self.status_msg:
            status_banner = ft.Container(
                content=ft.Text(self.status_msg, color=ThemeColors.SUCCESS, size=12),
                bgcolor=ThemeColors.SUCCESS_BG,
                border_radius=8,
                padding=10,
            )

        self.content = ft.Column(
            controls=[
                ft.Text("Profile & Settings", size=22, weight=ft.FontWeight.BOLD),
                ft.Text("Manage your traveler identity and desktop client preferences.", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                ft.Container(height=16),
                status_banner,
                profile_card,
                ft.Container(height=16),
                settings_card,
                ft.Container(height=24),
                ft.Row(controls=[auth_btn], alignment=ft.MainAxisAlignment.END),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

    def _update_profile_name(self) -> None:
        new_name = (self.name_field.value or "").strip()
        if not new_name:
            return

        async def _do_update():
            try:
                payload = UserUpdatePayload(full_name=new_name)
                await self.auth_service.update_profile(payload)
                self.status_msg = "Profile display name updated successfully."
            except Exception as err:
                self.status_msg = f"Failed to update profile: {str(err)}"
            self._build_content()
            try:
                self.update()
            except Exception:
                pass

        asyncio.create_task(_do_update())

    def _toggle_theme(self) -> None:
        if self.on_toggle_theme:
            self.on_toggle_theme()

    def _confirm_clear_cache(self) -> None:
        if not self.page:
            return

        def do_clear():
            self.guest_storage.clear_all()
            self.status_msg = "Local guest storage cache cleared."
            self._build_content()
            self.update()

        show_confirm_dialog(
            self.page,
            title="Clear Guest Storage?",
            message="This will delete all locally saved guest itineraries. Trips synced to a registered cloud account will not be affected.",
            on_confirm=do_clear,
        )

    def _handle_auth_action(self) -> None:
        if self.session_manager.is_authenticated:
            self.auth_service.logout()
        if self.on_navigate:
            self.on_navigate("/login")
