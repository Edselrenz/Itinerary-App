"""Welcome and Onboarding View conforming to Web & Figma design."""

from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors, ThemePalette, get_settings
from desktop_client.core.session import get_session_manager


class WelcomeView(ft.Container):
    """First-time onboarding view matching Figma Screen 1 (Standard Welcome) & Screen 3 (After-Logout)."""

    def __init__(
        self,
        on_navigate: Optional[Callable[[str], None]] = None,
        is_after_logout: bool = False,
    ):
        super().__init__()
        self.on_navigate = on_navigate
        self.is_after_logout = is_after_logout
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

    def _continue_as_guest(self) -> None:
        self.session_manager.set_guest_mode()
        self._navigate("/dashboard")

    def _build_content(self) -> None:
        palette = ThemePalette.get_palette(self._get_is_dark())
        self.bgcolor = palette.bg_main

        # 1. Airplane Icon & Brand Title
        brand_row = ft.Row(
            controls=[
                ft.Icon(
                    ft.Icons.AIRPLANEMODE_ACTIVE,
                    size=34,
                    color=ThemeColors.PRIMARY_BLUE,
                ),
                ft.Text(
                    "Trip mo, trip ko",
                    size=26,
                    weight=ft.FontWeight.W_800,
                    color=palette.text_primary,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )

        if self.is_after_logout:
            self._build_after_logout_content(brand_row, palette)
        else:
            self._build_standard_welcome_content(brand_row, palette)

    def _build_standard_welcome_content(self, brand_row: ft.Row, palette: ThemePalette) -> None:
        # Hero Illustration: Skyscrapers in organic blob frame
        skyscraper_asset = self.settings.get_asset_path("logout_skyscrapers_blob.png")
        blob_frame = ft.Container(
            content=ft.Image(
                src=skyscraper_asset,
                width=240,
                height=130,
                fit=ft.BoxFit.CONTAIN,
                error_content=ft.Container(
                    width=220,
                    height=120,
                    bgcolor=ThemeColors.PRIMARY_LIGHT,
                    border_radius=30,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(ft.Icons.LOCATION_CITY, size=48, color=ThemeColors.PRIMARY_BLUE),
                ),
            ),
            alignment=ft.Alignment(0, 0),
            margin=ft.Margin.only(top=4, bottom=8),
        )

        hero_headline = ft.Text(
            "Your next adventure\nis waiting.",
            size=30,
            weight=ft.FontWeight.W_800,
            color=palette.text_primary,
            text_align=ft.TextAlign.CENTER,
        )

        hero_subtitle = ft.Text(
            "Get personalized itineraries, easy commutes,\nand nearby essentials.",
            size=14,
            color=palette.text_muted,
            text_align=ft.TextAlign.CENTER,
        )

        login_btn = ft.Container(
            content=ft.Text("Log In", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=24,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._navigate("/login"),
        )

        signup_btn = ft.Container(
            content=ft.Text("Sign Up", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=24,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._navigate("/signup"),
        )

        divider_row = ft.Row(
            controls=[
                ft.Container(expand=True, height=1, bgcolor=palette.border_main),
                ft.Text("or", size=12, color=palette.text_muted, weight=ft.FontWeight.W_500),
                ft.Container(expand=True, height=1, bgcolor=palette.border_main),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,
        )

        # Continues to /guest screen matching Web App
        guest_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PERSON, size=18, color=palette.text_primary),
                    ft.Text("Continue as Guest", size=14, weight=ft.FontWeight.W_700, color=palette.text_primary),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            border=ft.Border.all(1.5, palette.text_primary),
            bgcolor=palette.surface_card,
            border_radius=24,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._navigate("/guest"),
        )

        action_column = ft.Column(
            controls=[
                login_btn,
                signup_btn,
                divider_row,
                guest_btn,
            ],
            spacing=12,
            width=360,
        )

        # Bottom City Skyline Silhouette (welcome_hero_buildings.png)
        buildings_asset = self.settings.get_asset_path("welcome_hero_buildings.png")
        bottom_buildings = ft.Container(
            content=ft.Image(
                src=buildings_asset,
                height=90,
                fit=ft.BoxFit.FIT_HEIGHT,
                opacity=0.9,
            ),
            alignment=ft.Alignment(0, 1),
            margin=ft.Margin.only(top=16),
        )

        center_card = ft.Container(
            content=ft.Column(
                controls=[
                    brand_row,
                    blob_frame,
                    hero_headline,
                    hero_subtitle,
                    ft.Container(height=16),
                    action_column,
                    bottom_buildings,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=palette.surface_card,
            padding=ft.Padding.symmetric(horizontal=48, vertical=36),
            border_radius=28,
            border=ft.Border.all(1, palette.border_main),
            width=540,
            shadow=ft.BoxShadow(
                blur_radius=24,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 8),
            ),
        )

        self.content = ft.Column(
            controls=[center_card],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _build_after_logout_content(self, brand_row: ft.Row, palette: ThemePalette) -> None:
        skyscraper_asset = self.settings.get_asset_path("logout_skyscrapers_blob.png")
        blob_frame = ft.Container(
            content=ft.Image(
                src=skyscraper_asset,
                width=240,
                height=130,
                fit=ft.BoxFit.CONTAIN,
            ),
            alignment=ft.Alignment(0, 0),
            margin=ft.Margin.only(top=4, bottom=8),
        )

        logout_headline = ft.Text(
            "You're now logged out",
            size=28,
            weight=ft.FontWeight.W_800,
            color=palette.text_primary,
            text_align=ft.TextAlign.CENTER,
        )

        logout_subtitle = ft.Text(
            "Your account has been signed out. Explore as guest\nor log in again to access your saved trips.",
            size=14,
            color=palette.text_muted,
            text_align=ft.TextAlign.CENTER,
        )

        guest_btn = ft.Container(
            content=ft.Text("Continue as Guest", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=24,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._continue_as_guest(),
        )

        login_btn = ft.Container(
            content=ft.Text("Log In", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=24,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._navigate("/login"),
        )

        action_column = ft.Column(
            controls=[
                guest_btn,
                login_btn,
            ],
            spacing=12,
            width=360,
        )

        silhouette_asset = self.settings.get_asset_path("logout_cityscape_silhouette.png")
        bottom_silhouette = ft.Container(
            content=ft.Image(
                src=silhouette_asset,
                height=80,
                fit=ft.BoxFit.FIT_HEIGHT,
                opacity=0.85,
            ),
            alignment=ft.Alignment(0, 1),
            margin=ft.Margin.only(top=16),
        )

        center_card = ft.Container(
            content=ft.Column(
                controls=[
                    brand_row,
                    blob_frame,
                    logout_headline,
                    logout_subtitle,
                    ft.Container(height=16),
                    action_column,
                    bottom_silhouette,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=palette.surface_card,
            padding=ft.Padding.symmetric(horizontal=48, vertical=36),
            border_radius=28,
            border=ft.Border.all(1, palette.border_main),
            width=540,
            shadow=ft.BoxShadow(
                blur_radius=24,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 8),
            ),
        )

        self.content = ft.Column(
            controls=[center_card],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
