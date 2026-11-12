"""Welcome and Onboarding View conforming to Web & Figma design."""

from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors
from desktop_client.core.session import get_session_manager
from desktop_client.services.auth_service import get_auth_service


class WelcomeView(ft.Container):
    """First-time onboarding view matching Figma Screen 1 & Screen 3."""

    def __init__(self, on_navigate: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.on_navigate = on_navigate
        self.auth_service = get_auth_service()
        self.session_manager = get_session_manager()

        self.expand = True
        self.bgcolor = ThemeColors.BG_LIGHT
        self.alignment = ft.Alignment(0, 0)

        self._build_content()

    def _build_content(self) -> None:
        # 1. Airplane Icon & Brand Title (matching Figma brand-row)
        brand_row = ft.Row(
            controls=[
                ft.Icon(
                    ft.Icons.AIRPLANEMODE_ACTIVE,
                    size=32,
                    color=ThemeColors.PRIMARY_BLUE,
                ),
                ft.Text(
                    "Trip mo, trip ko",
                    size=22,
                    weight=ft.FontWeight.W_800,
                    color=ThemeColors.PRIMARY_BLUE,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )

        # 2. Hero Headline (matching Figma)
        hero_headline = ft.Text(
            "Your next adventure\nis waiting.",
            size=36,
            weight=ft.FontWeight.W_800,
            color=ThemeColors.TEXT_BLACK,
            text_align=ft.TextAlign.CENTER,
        )

        # 3. Hero Subtitle (matching Figma)
        hero_subtitle = ft.Text(
            "Get personalized itineraries, easy commutes,\nand nearby essentials across Nueva Ecija.",
            size=14,
            color=ThemeColors.TEXT_MUTED_LIGHT,
            text_align=ft.TextAlign.CENTER,
        )

        # 4. Action Buttons (matching Figma .figma-solid-blue-btn & .guest-pill-btn)
        login_btn = ft.Container(
            content=ft.Text("Log In", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=12,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._navigate("/login"),
        )

        signup_btn = ft.Container(
            content=ft.Text("Sign Up", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=12,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._navigate("/signup"),
        )

        divider_row = ft.Row(
            controls=[
                ft.Container(expand=True, height=1, bgcolor=ThemeColors.BORDER_LIGHT),
                ft.Text("or", size=12, color=ThemeColors.TEXT_MUTED_LIGHT, weight=ft.FontWeight.W_500),
                ft.Container(expand=True, height=1, bgcolor=ThemeColors.BORDER_LIGHT),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,
        )

        guest_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PERSON, size=18, color=ThemeColors.TEXT_MAIN_LIGHT),
                    ft.Text("Continue as Guest", size=14, weight=ft.FontWeight.W_600, color=ThemeColors.TEXT_MAIN_LIGHT),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=12,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._continue_as_guest(),
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

        # Feature highlights for desktop layout
        feature_highlights = ft.Row(
            controls=[
                self._create_highlight(
                    ft.Icons.EXPLORE,
                    "2,670+ Curated Places",
                    "32 LGUs from Sierra Madre to Pantabangan Lake with verified entrance fees.",
                ),
                self._create_highlight(
                    ft.Icons.AUTO_AWESOME,
                    "Smart Route Clustering",
                    "Optimized itineraries grouped by geographic proximity to prevent backtracking.",
                ),
                self._create_highlight(
                    ft.Icons.FILE_DOWNLOAD,
                    "Offline & Calendar Export",
                    "Export to .ics calendar files, travel dossier guides, or local offline storage.",
                ),
            ],
            spacing=16,
            width=760,
        )

        center_card = ft.Container(
            content=ft.Column(
                controls=[
                    brand_row,
                    ft.Container(height=8),
                    hero_headline,
                    hero_subtitle,
                    ft.Container(height=16),
                    action_column,
                    ft.Container(height=24),
                    ft.Divider(color=ThemeColors.BORDER_LIGHT, height=1),
                    ft.Container(height=8),
                    feature_highlights,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            border_radius=20,
            padding=ft.Padding.symmetric(horizontal=40, vertical=36),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.06, "#000000"),
            ),
        )

        self.content = ft.Container(
            content=center_card,
            alignment=ft.Alignment(0, 0),
            padding=20,
        )

    def _create_highlight(self, icon: str, title: str, desc: str) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icon, size=16, color=ThemeColors.PRIMARY_BLUE),
                            ft.Text(title, size=12, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                        ],
                        spacing=6,
                    ),
                    ft.Text(desc, size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                ],
                spacing=4,
            ),
            expand=True,
            padding=10,
            bgcolor=ThemeColors.BG_LIGHT,
            border_radius=10,
        )

    def _continue_as_guest(self) -> None:
        self.auth_service.continue_as_guest()
        self._navigate("/dashboard")

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
