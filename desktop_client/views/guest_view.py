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
        is_dark = self._get_is_dark()
        palette = ThemePalette.get_palette(is_dark)
        self.padding = 0
        self.bgcolor = palette.surface_card if not is_dark else palette.bg_main

        # Hero Image path
        hero_img_path = self.settings.get_asset_path("guest_hiker_hero.png")
        if not hero_img_path or not os.path.exists(hero_img_path):
            hero_img_path = self.settings.get_asset_path("images/guest_hiker_hero.png")

        # Top Hero section matching Web .hero-image-section (full width, 48vh, floating back button)
        hero_section = ft.Stack(
            controls=[
                ft.Image(
                    src=hero_img_path,
                    fit=ft.BoxFit.COVER,
                    width=float("inf"),
                    height=340,
                    left=0,
                    top=0,
                    right=0,
                    bottom=0,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color=ft.Colors.BLACK,
                        bgcolor=ft.Colors.with_opacity(0.45, ft.Colors.WHITE),
                        icon_size=20,
                        on_click=self._go_back,
                        tooltip="Back to Welcome",
                    ),
                    top=18,
                    left=20,
                ),
            ],
            width=float("inf"),
            height=340,
        )

        btn_w = 340
        # Bottom content section matching Web .guest-content-section (no card box)
        bottom_section = ft.Container(
            expand=True,
            width=float("inf"),
            alignment=ft.Alignment(0, 0),
            padding=ft.Padding.symmetric(horizontal=28, vertical=28),
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Explore as a guest",
                        size=28,
                        weight=ft.FontWeight.W_800,
                        color=palette.text_primary,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Your trips are saved locally on this device.\nSign in anytime to back them up to the cloud.",
                        size=14.5,
                        color="#334155" if not is_dark else palette.text_muted,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=16),
                    # Primary pill: Continue as Guest
                    ft.Container(
                        content=ft.Text(
                            "Continue as Guest",
                            size=16,
                            weight=ft.FontWeight.W_700,
                            color=ft.Colors.WHITE,
                        ),
                        width=btn_w,
                        height=48,
                        bgcolor=ThemeColors.PRIMARY_BLUE,
                        border_radius=9999,
                        alignment=ft.Alignment(0, 0),
                        ink=True,
                        on_click=self._continue_as_guest,
                    ),
                    # Outline pill: Create an Account (1.5px solid #0084ff, #0084ff text matching guest.page.scss)
                    ft.Container(
                        content=ft.Text(
                            "Create an Account",
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=ThemeColors.PRIMARY_BLUE,
                        ),
                        width=btn_w,
                        height=48,
                        bgcolor=palette.surface_card,
                        border=ft.Border.all(1.5, ThemeColors.PRIMARY_BLUE),
                        border_radius=9999,
                        alignment=ft.Alignment(0, 0),
                        ink=True,
                        on_click=self._create_account,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
                width=380,
                tight=True,
            ),
        )

        self.content = ft.Column(
            controls=[hero_section, bottom_section],
            spacing=0,
            expand=True,
            width=float("inf"),
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
