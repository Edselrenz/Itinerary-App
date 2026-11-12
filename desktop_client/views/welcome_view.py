"""Welcome and Onboarding View."""

from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors
from desktop_client.services.auth_service import get_auth_service


class WelcomeView(ft.Container):
    """First-time onboarding view introducing Nueva Ecija travel capabilities."""

    def __init__(self, on_navigate: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.on_navigate = on_navigate
        self.auth_service = get_auth_service()

        self.expand = True
        self.padding = ft.padding.symmetric(horizontal=48, vertical=32)
        self.bgcolor = ThemeColors.BG_LIGHT

        self._build_content()

    def _build_content(self) -> None:
        # Hero Icon & Header
        hero_badge = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.LANDSCAPE_ROUNDED, size=32, color=ThemeColors.EMERALD_MINT),
                    ft.Text(
                        "Nueva Ecija Travel Platform",
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=ThemeColors.EMERALD_MINT,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=ThemeColors.EMERALD_DARK,
            border_radius=20,
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        )

        title_text = ft.Text(
            "Discover the Heart of Central Luzon",
            size=36,
            weight=ft.FontWeight.BOLD,
            color=ThemeColors.TEXT_MAIN_LIGHT,
            text_align=ft.TextAlign.CENTER,
        )

        subtitle_text = ft.Text(
            "From the Sierra Madre peaks in Gabaldon and Pantabangan Dam to historic colonial churches, "
            "agri-tourism centers, and vibrant local cuisine — your complete desktop travel companion.",
            size=15,
            color=ThemeColors.TEXT_MUTED_LIGHT,
            text_align=ft.TextAlign.CENTER,
            max_lines=3,
        )

        # Feature highlights (3 desktop cards)
        features = [
            (
                ft.Icons.PLACE_ROUNDED,
                "2,670+ Curated Places",
                "Explore 32 municipalities across 16 categories with honest pricing, operating hours, and GIS locations.",
            ),
            (
                ft.Icons.AUTO_AWESOME_ROUNDED,
                "Smart Clustered Routes",
                "Generate balanced multi-day itineraries that cluster nearby spots to avoid unnecessary backtracking.",
            ),
            (
                ft.Icons.BOOKMARK_ADDED_ROUNDED,
                "Guest & Cloud Sync",
                "Build itineraries immediately without an account, or log in to sync securely across all your devices.",
            ),
        ]

        feature_cards: list[ft.Control] = []
        for icon, feat_title, feat_desc in features:
            feature_cards.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Container(
                                content=ft.Icon(icon, size=28, color=ThemeColors.EMERALD_PRIMARY),
                                bgcolor=ThemeColors.EMERALD_MINT,
                                border_radius=10,
                                padding=12,
                            ),
                            ft.Text(feat_title, size=15, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN_LIGHT),
                            ft.Text(feat_desc, size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        spacing=8,
                    ),
                    bgcolor=ThemeColors.SURFACE_LIGHT,
                    border_radius=12,
                    border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
                    padding=20,
                    expand=True,
                )
            )

        # Action Buttons
        guest_btn = ft.FilledButton(
            content="Start Planning as Guest",
            icon=ft.Icons.EXPLORE,
            style=ft.ButtonStyle(
                bgcolor=ThemeColors.EMERALD_PRIMARY,
                color=ft.Colors.WHITE,
                padding=ft.padding.symmetric(horizontal=24, vertical=16),
            ),
            on_click=lambda _: self._start_as_guest(),
        )

        signin_btn = ft.OutlinedButton(
            content="Sign In / Register Account",
            icon=ft.Icons.LOGIN,
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=24, vertical=16),
            ),
            on_click=lambda _: self._go_login(),
        )

        actions_row = ft.Row(
            controls=[guest_btn, signin_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=16,
        )

        self.content = ft.Column(
            controls=[
                ft.Container(height=20),
                ft.Row(controls=[hero_badge], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=10),
                title_text,
                ft.Container(height=6),
                subtitle_text,
                ft.Container(height=30),
                ft.Row(controls=feature_cards, spacing=16),
                ft.Container(height=40),
                actions_row,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )

    def _start_as_guest(self) -> None:
        self.auth_service.continue_as_guest()
        if self.on_navigate:
            self.on_navigate("/dashboard")

    def _go_login(self) -> None:
        if self.on_navigate:
            self.on_navigate("/login")
