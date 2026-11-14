"""Dedicated Guest Mode Onboarding Screen matching Project/src/app/features/auth/guest/guest.page.html."""

import os
from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors, ThemePalette, get_settings
from desktop_client.core.session import get_session_manager


class GuestView(ft.Container):
    """Figma-aligned Guest Mode Onboarding View featuring top hero hiker artwork and cloud sync disclosure."""

    def __init__(self, on_navigate: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.on_navigate = on_navigate
        self.session_manager = get_session_manager()
        self.settings = get_settings()

        self.expand = True
        self.alignment = ft.Alignment(0, 0)
        self._build_content()

    @property
    def safe_page(self) -> Optional[ft.Page]:
        try:
            return self.page
        except Exception:
            return None

    def _get_is_dark(self) -> bool:
        p = self.safe_page
        if p and p.theme_mode == ft.ThemeMode.DARK:
            return True
        return False

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)

    def _continue_as_guest(self, _=None) -> None:
        self.session_manager.set_guest_mode()
        self._navigate("/dashboard")

    def _create_account(self, _=None) -> None:
        self._navigate("/signup")

    def _go_back(self, _=None) -> None:
        self._navigate("/welcome")

    def _build_content(self) -> None:
        palette = ThemePalette.get_palette(self._get_is_dark())
        self.bgcolor = palette.bg_main

        # Hero Image path
        hero_img_path = self.settings.get_asset_path("guest_hiker_hero.png")
        if not hero_img_path or not os.path.exists(hero_img_path):
            hero_img_path = self.settings.get_asset_path("images/guest_hiker_hero.png")

        # Top Hero section with floating back button
        hero_section = ft.Stack(
            controls=[
                ft.Container(
                    content=ft.Image(
                        src=hero_img_path,
                        fit=ft.BoxFit.COVER,
                        width=460,
                        height=300,
                        border_radius=ft.BorderRadius(top_left=24, top_right=24, bottom_left=0, bottom_right=0),
                    ),
                    width=460,
                    height=300,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.BLACK),
                        icon_size=20,
                        on_click=self._go_back,
                        tooltip="Back to Welcome",
                    ),
                    top=16,
                    left=16,
                ),
            ],
            width=460,
            height=300,
        )

        # Bottom content card
        bottom_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Explore as a guest",
                        size=24,
                        weight=ft.FontWeight.W_800,
                        color=palette.text_primary,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Your trips are saved locally on this device.\nSign in anytime to back them up to the cloud.",
                        size=14,
                        color=palette.text_muted,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=16),
                    # Primary pill: Continue as Guest
                    ft.FilledButton(
                        content=ft.Text(
                            "Continue as Guest",
                            size=15,
                            weight=ft.FontWeight.W_700,
                            color=ft.Colors.WHITE,
                        ),
                        width=380,
                        height=48,
                        style=ft.ButtonStyle(
                            bgcolor=ThemeColors.PRIMARY_BLUE,
                            shape=ft.RoundedRectangleBorder(radius=24),
                        ),
                        on_click=self._continue_as_guest,
                    ),
                    # Outline pill: Create an Account
                    ft.OutlinedButton(
                        content=ft.Text(
                            "Create an Account",
                            size=15,
                            weight=ft.FontWeight.W_700,
                            color=palette.text_primary,
                        ),
                        width=380,
                        height=48,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=24),
                            side=ft.BorderSide(1.5, palette.border_main),
                        ),
                        on_click=self._create_account,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            bgcolor=palette.surface_card,
            padding=ft.Padding.symmetric(horizontal=32, vertical=32),
            border_radius=ft.BorderRadius(top_left=0, top_right=0, bottom_left=24, bottom_right=24),
            border=ft.Border.all(1, palette.border_main),
            width=460,
        )

        card_wrapper = ft.Container(
            content=ft.Column(
                controls=[hero_section, bottom_card],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            border_radius=24,
            shadow=ft.BoxShadow(
                blur_radius=20,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 6),
            ),
        )

        self.content = ft.Column(
            controls=[card_wrapper],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
