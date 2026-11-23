"""Nueva Ecija Travel — Cold Start Splash Overlay.

Displays loading_screen.jpg matching the canonical web splash behavior.
Auto-dismisses after 2.8 seconds or immediately on click.
"""

import asyncio
from typing import Callable, Optional
from pathlib import Path
import flet as ft

from desktop_client.config.settings import ThemeColors, get_settings


class SplashOverlay(ft.Container):
    """Full-screen splash overlay shown on cold application launch."""

    def __init__(self, on_dismiss: Optional[Callable[[], None]] = None):
        super().__init__()
        self.on_dismiss = on_dismiss
        self.settings = get_settings()

        self.left = 0
        self.top = 0
        self.right = 0
        self.bottom = 0
        self.expand = True
        self.alignment = ft.Alignment(0, 0)
        self.bgcolor = "#0b1329"

        self._is_dismissed = False
        self._build_content()

    @property
    def safe_page(self) -> Optional[ft.Page]:
        try:
            return self.page
        except Exception:
            return None

    def dismiss(self, _=None) -> None:
        if self._is_dismissed:
            return
        self._is_dismissed = True
        self.visible = False
        self.content = None
        self.on_click = None
        try:
            self.update()
        except Exception:
            pass
        if self.on_dismiss:
            self.on_dismiss()

    def start_timer(self, delay_seconds: float = 2.8, page: Optional[ft.Page] = None) -> None:
        """Schedules auto-dismissal after delay_seconds."""
        async def _dismiss_later():
            await asyncio.sleep(delay_seconds)
            self.dismiss()

        p = page or self.safe_page
        if p:
            p.run_task(_dismiss_later)
        else:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_dismiss_later())
            except RuntimeError:
                asyncio.run(_dismiss_later())

    def _build_content(self) -> None:
        splash_asset = self.settings.get_asset_path("images/loading_screen.jpg")
        if not Path(splash_asset).is_file():
            splash_asset = self.settings.get_asset_path("images/login_pics/Loading screen.jpg")

        # 1. Full-bleed background image (Positioned.fill + BoxFit.COVER across entire window)
        splash_image = ft.Image(
            src=splash_asset,
            fit=ft.BoxFit.COVER,
            width=float("inf"),
            height=float("inf"),
            left=0,
            top=0,
            right=0,
            bottom=0,
            filter_quality=ft.FilterQuality.HIGH,
            error_content=ft.Container(
                bgcolor="#0b1329",
                expand=True,
            ),
        )

        # 2. Full-bleed gradient scrim matching Web .splash-scrim
        splash_scrim = ft.Container(
            left=0,
            top=0,
            right=0,
            bottom=0,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(0, -1),
                end=ft.Alignment(0, 1),
                colors=[
                    ft.Colors.with_opacity(0.52, "#0a1226"),
                    ft.Colors.with_opacity(0.22, "#0a1226"),
                    ft.Colors.with_opacity(0.62, "#0a1226"),
                ],
                stops=[0.0, 0.40, 1.0],
            ),
        )

        # 3. Centered Brand Header & Tagline matching Web .splash-content-container
        brand_header = ft.Row(
            controls=[
                ft.Icon(
                    ft.Icons.AIRPLANEMODE_ACTIVE,
                    size=36,
                    color=ft.Colors.WHITE,
                ),
                ft.Text(
                    "Trip mo, trip ko",
                    size=34,
                    weight=ft.FontWeight.W_800,
                    color=ft.Colors.WHITE,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        )

        tagline = ft.Text(
            "Plan your trip, explore new places,\nmake better memories.",
            size=17,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.WHITE,
            text_align=ft.TextAlign.CENTER,
        )

        hero_center_block = ft.Column(
            controls=[
                brand_header,
                ft.Container(height=8),
                tagline,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
            tight=True,
        )

        # 4. Bottom centered loading indicator & hint pill matching Web .splash-footer-hint
        loading_row = ft.Row(
            controls=[
                ft.ProgressRing(width=18, height=18, stroke_width=2.5, color="#38bdf8"),
                ft.Text(
                    "Loading province guides...",
                    size=12,
                    weight=ft.FontWeight.W_500,
                    color=ft.Colors.WHITE,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            tight=True,
        )

        hint_pill = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=8,
                        height=8,
                        border_radius=4,
                        bgcolor="#38bdf8",
                    ),
                    ft.Text(
                        "Click anywhere to enter",
                        size=12,
                        weight=ft.FontWeight.W_600,
                        color="#e2e8f0",
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                tight=True,
            ),
            bgcolor=ft.Colors.with_opacity(0.60, "#0f172a"),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.22, ft.Colors.WHITE)),
            border_radius=9999,
            padding=ft.Padding.symmetric(horizontal=18, vertical=8),
        )

        footer_block = ft.Column(
            controls=[
                loading_row,
                hint_pill,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            tight=True,
        )

        foreground_layer = ft.Container(
            left=0,
            top=0,
            right=0,
            bottom=0,
            padding=ft.Padding.only(top=96, bottom=44, left=24, right=24),
            on_click=self.dismiss,
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=hero_center_block,
                        alignment=ft.Alignment(0, -0.35),
                        expand=True,
                        width=float("inf"),
                    ),
                    ft.Container(
                        content=footer_block,
                        alignment=ft.Alignment(0, 0),
                        width=float("inf"),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                width=float("inf"),
            ),
        )

        self.content = ft.Stack(
            controls=[
                splash_image,
                splash_scrim,
                foreground_layer,
            ],
            expand=True,
        )
