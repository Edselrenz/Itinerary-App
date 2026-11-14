"""Compact, non-blocking top connectivity banner matching Project/src/app/app.component.html.

CRITICAL FLET 1.1.2 LAYOUT RULE:
- `expand` MUST be `False` and `height` MUST be fixed (`52` when visible, `0` when hidden)
  so it NEVER stretches across the application viewport.
- Renders an inner dark pill card (width=620, height=42, border_radius=12, bgcolor="#0f172a").
"""

from __future__ import annotations

import asyncio
from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors
from desktop_client.core.connectivity_service import ConnectivityService, get_connectivity_service


class OfflineHostBanner(ft.Container):
    """Floating pill banner (`.offline-host-banner`) rendered at the top of the root Column."""

    def __init__(
        self,
        connectivity_service: Optional[ConnectivityService] = None,
        on_status_change: Optional[Callable[[bool], None]] = None,
        on_retry: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__()
        self._connectivity = connectivity_service or get_connectivity_service()
        self.on_status_change = on_status_change
        self._on_retry = on_retry

        # Strictly non-expanding top bar wrapper
        self.expand = False
        self.height = 0
        self.visible = False
        self.alignment = ft.Alignment(0, 0)
        self.padding = ft.Padding.only(top=6, bottom=4, left=16, right=16)
        self.bgcolor = ft.Colors.TRANSPARENT

        self._is_dismissed = False
        self._is_retrying = False

        self._title_text = ft.Text(
            "You are offline",
            size=12,
            weight=ft.FontWeight.W_700,
            color="#f8fafc",
        )
        self._sub_text = ft.Text(
            "Showing cached Nueva Ecija places & saved itineraries",
            size=11,
            color="#94a3b8",
        )
        self._retry_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.REFRESH_ROUNDED, size=13, color="#38bdf8"),
                    ft.Text("Retry", size=11, weight=ft.FontWeight.W_700, color="#38bdf8"),
                ],
                spacing=4,
                tight=True,
            ),
            bgcolor="#1e293b",
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            ink=True,
            on_click=self._handle_retry,
        )
        self._dismiss_btn = ft.IconButton(
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_size=15,
            icon_color="#94a3b8",
            tooltip="Dismiss offline notice",
            on_click=self._handle_dismiss,
            style=ft.ButtonStyle(padding=ft.Padding.all(4)),
        )

        # Inner dark pill card matching Web App `.offline-banner-content` (max-width 620px, height 42px)
        self.content = ft.Container(
            width=620,
            height=42,
            bgcolor="#0f172a",
            border=ft.Border.all(1, "#334155"),
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=14, vertical=6),
            shadow=ft.BoxShadow(
                blur_radius=12,
                color=ft.Colors.with_opacity(0.18, "#0f172a"),
                offset=ft.Offset(0, 4),
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.CLOUD_OFF_ROUNDED, color="#f59e0b", size=18),
                            ft.Column(
                                spacing=0,
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[self._title_text, self._sub_text],
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[self._retry_btn, self._dismiss_btn],
                    ),
                ],
            ),
        )

        # Set initial visibility
        should_show = self._connectivity.is_host_offline and not self._is_dismissed
        self.visible = should_show
        self.height = 52 if should_show else 0

        self._connectivity.register_listener(self._on_connectivity_event)

    @property
    def safe_page(self) -> Optional[ft.Page]:
        try:
            return self.page
        except Exception:
            return None

    def _on_connectivity_event(self, is_offline: Optional[bool] = None) -> None:
        """Invoked automatically by ConnectivityService whenever host state changes."""
        if is_offline is None:
            is_offline = self._connectivity.is_host_offline

        if not is_offline:
            self._is_dismissed = False
            self.visible = False
            self.height = 0
        else:
            should_show = not self._is_dismissed
            self.visible = should_show
            self.height = 52 if should_show else 0

        if self._connectivity.is_checking_health:
            self._title_text.value = "Reconnecting to server..."
        else:
            self._title_text.value = "You are offline"

        try:
            if self.page:
                self.update()
        except Exception:
            pass

        if self.on_status_change:
            self.on_status_change(is_offline)

    def _handle_dismiss(self, _e: Optional[ft.ControlEvent] = None) -> None:
        self._is_dismissed = True
        self.visible = False
        self.height = 0
        self._connectivity.dismiss_banner()
        try:
            if self.page:
                self.update()
        except Exception:
            pass

    _dismiss = _handle_dismiss


    def _handle_retry(self, _e: Optional[ft.ControlEvent] = None) -> None:
        if self._is_retrying:
            return

        if self._on_retry:
            self._on_retry()

        self._is_retrying = True
        self._title_text.value = "Reconnecting to server..."
        self._retry_btn.content = ft.Row(
            controls=[
                ft.ProgressRing(width=12, height=12, stroke_width=2, color="#38bdf8"),
                ft.Text("Testing...", size=11, color="#38bdf8"),
            ],
            spacing=4,
            tight=True,
        )
        try:
            if self.page:
                self.update()
        except Exception:
            pass

        async def _run_retry():
            try:
                is_online = await self._connectivity.check_host_health()
                p = self.safe_page
                if is_online:
                    self._is_dismissed = False
                    self.visible = False
                    self.height = 0
                    if p:
                        p.snack_bar = ft.SnackBar(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.WHITE, size=18),
                                    ft.Text("Cloud connection restored!", color=ft.Colors.WHITE),
                                ],
                                spacing=8,
                            ),
                            bgcolor=ThemeColors.SUCCESS,
                            open=True,
                        )
                else:
                    self.visible = True
                    self.height = 52
                    self._title_text.value = "You are offline"
                    if p:
                        p.snack_bar = ft.SnackBar(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.WHITE, size=18),
                                    ft.Text("Backend server still unreachable. Operating in offline mode.", color=ft.Colors.WHITE),
                                ],
                                spacing=8,
                            ),
                            bgcolor="#d97706",
                            open=True,
                        )
                if p:
                    p.update()
            finally:
                self._is_retrying = False
                self._retry_btn.content = ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.REFRESH_ROUNDED, size=13, color="#38bdf8"),
                        ft.Text("Retry", size=11, weight=ft.FontWeight.W_700, color="#38bdf8"),
                    ],
                    spacing=4,
                    tight=True,
                )
                try:
                    if self.page:
                        self.update()
                except Exception:
                    pass

        p = self.safe_page
        if p:
            p.run_task(_run_retry)
        else:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_run_retry())
            except RuntimeError:
                asyncio.run(_run_retry())
