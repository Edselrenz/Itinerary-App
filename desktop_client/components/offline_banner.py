"""Nueva Ecija Travel — Global Floating Offline Host Banner (.offline-host-banner).

Displays at the top of the root Stack across all views when the backend server
is unreachable or responding with network errors. Provides immediate offline awareness,
one-click manual health probe with spinner, and dismiss capability.
"""

import asyncio
from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors
from desktop_client.core.connectivity_service import get_connectivity_service


class OfflineHostBanner(ft.Container):
    """Global floating banner notifying user of disconnected backend host."""

    def __init__(
        self,
        on_status_change: Optional[Callable[[bool], None]] = None,
    ):
        super().__init__()
        self.on_status_change = on_status_change
        self.connectivity_service = get_connectivity_service()

        self.margin = ft.Margin.only(top=12, left=16, right=16)
        self.padding = ft.Padding.symmetric(horizontal=16, vertical=10)
        self.bgcolor = "#0f172a"
        self.border = ft.Border.all(1, "#f59e0b")
        self.border_radius = 14
        self.shadow = ft.BoxShadow(
            spread_radius=1,
            blur_radius=16,
            color=ft.Colors.with_opacity(0.35, "#000000"),
            offset=ft.Offset(0, 4),
        )

        self._is_dismissed = False
        self._is_retrying = False

        # Set initial visibility based on connectivity service
        self.visible = self.connectivity_service.is_host_offline and not self._is_dismissed

        self._build_content()
        self.connectivity_service.register_listener(self._on_connectivity_event)

    @property
    def safe_page(self) -> Optional[ft.Page]:
        try:
            return self.page
        except Exception:
            return None

    def _on_connectivity_event(self, is_offline: Optional[bool] = None) -> None:
        """Invoked automatically by ConnectivityService whenever host state changes."""
        if is_offline is None:
            is_offline = self.connectivity_service.is_host_offline
        if not is_offline:
            self._is_dismissed = False  # Reset dismiss when coming back online
            self.visible = False
        else:
            self.visible = not self._is_dismissed

        try:
            self.update()
        except Exception:
            pass

        if self.on_status_change:
            self.on_status_change(is_offline)

    def _dismiss(self, _=None) -> None:
        self._is_dismissed = True
        self.visible = False
        try:
            self.update()
        except Exception:
            pass

    def _trigger_retry(self, _=None) -> None:
        if self._is_retrying:
            return

        self._is_retrying = True
        self._build_content()
        try:
            self.update()
        except Exception:
            pass

        async def _run_retry():
            try:
                is_online = await self.connectivity_service.check_host_health()
                p = self.safe_page
                if is_online:
                    self._is_dismissed = False
                    self.visible = False
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
                self._build_content()
                try:
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

    def _build_content(self) -> None:
        # Retry control: spinner or button
        if self._is_retrying:
            retry_ctrl = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.ProgressRing(width=14, height=14, stroke_width=2, color="#f59e0b"),
                        ft.Text("Checking...", size=12, color="#f59e0b", weight=ft.FontWeight.W_600),
                    ],
                    spacing=6,
                ),
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            )
        else:
            retry_ctrl = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.REFRESH, size=14, color="#ffffff"),
                        ft.Text("Retry", size=12, color="#ffffff", weight=ft.FontWeight.BOLD),
                    ],
                    spacing=4,
                ),
                bgcolor="#d97706",
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                ink=True,
                on_click=self._trigger_retry,
            )

        dismiss_btn = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=16,
            icon_color="#94a3b8",
            tooltip="Dismiss offline notice",
            on_click=self._dismiss,
        )

        self.content = ft.Row(
            controls=[
                ft.Icon(ft.Icons.CLOUD_OFF, size=24, color="#f59e0b"),
                ft.Column(
                    controls=[
                        ft.Text(
                            "Cloud Sync Paused",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            "Backend server unreachable. Offline mode is active with local data.",
                            size=11,
                            color="#cbd5e1",
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
                retry_ctrl,
                dismiss_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        )
