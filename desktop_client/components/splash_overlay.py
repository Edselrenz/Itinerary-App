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
        try:
            self.update()
        except Exception:
            pass
        if self.on_dismiss:
            self.on_dismiss()

    def start_timer(self, delay_seconds: float = 2.8) -> None:
        """Schedules auto-dismissal after delay_seconds."""
        async def _dismiss_later():
            await asyncio.sleep(delay_seconds)
            self.dismiss()

        p = self.safe_page
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

        splash_image = ft.Image(
            src=splash_asset,
            fit=ft.BoxFit.COVER,
            expand=True,
            error_content=ft.Container(
                bgcolor="#0b1329",
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.AIRPLANEMODE_ACTIVE, size=64, color=ThemeColors.PRIMARY_BLUE),
                        ft.Text("Trip mo, trip ko", size=28, weight=ft.FontWeight.W_800, color=ft.Colors.WHITE),
                        ft.Text("Nueva Ecija Travel Companion", size=14, color="#94a3b8"),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
            ),
        )

        loading_indicator = ft.Container(
            content=ft.Column(
                controls=[
                    ft.ProgressRing(width=28, height=28, stroke_width=3, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text("Loading province guides...", size=12, color=ft.Colors.WHITE_70),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment(0, 0.8),
        )

        self.content = ft.Stack(
            controls=[
                splash_image,
                loading_indicator,
                # Clickable layer allowing instant dismissal
                ft.Container(
                    expand=True,
                    on_click=self.dismiss,
                ),
            ],
            expand=True,
        )
