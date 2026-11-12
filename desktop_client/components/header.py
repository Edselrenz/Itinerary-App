"""Top application header matching Web Client design system."""

from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors
from desktop_client.core.api_client import get_api_client
from desktop_client.core.session import get_session_manager


class TopHeader(ft.Container):
    """Desktop top navigation header providing context, search shortcut,

    and server connectivity status.
    """

    def __init__(
        self,
        title: str = "Home",
        subtitle: str = "Trip mo, trip ko",
        on_search_click: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.title_text = title
        self.subtitle_text = subtitle
        self.on_search_click = on_search_click
        self.api_client = get_api_client()
        self.session_manager = get_session_manager()

        self.height = 64
        self.bgcolor = ThemeColors.SURFACE_LIGHT
        self.padding = ft.Padding.symmetric(horizontal=24, vertical=8)
        self.border = ft.Border(
            bottom=ft.BorderSide(1.2, ThemeColors.BORDER_LIGHT)
        )
        self.is_online = True

        self._build_content()

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass

    def set_header_context(self, title: str, subtitle: Optional[str] = None) -> None:
        """Updates the header title and subtitle dynamically."""
        self.title_text = title
        if subtitle is not None:
            self.subtitle_text = subtitle
        self._build_content()
        self._safe_update()

    def set_online_status(self, online: bool) -> None:
        """Updates the server status indicator."""
        self.is_online = online
        self._build_content()
        self._safe_update()

    def _build_content(self) -> None:
        # Title and breadcrumbs
        title_section = ft.Column(
            controls=[
                ft.Text(
                    self.title_text,
                    size=17,
                    weight=ft.FontWeight.W_800,
                    color=ThemeColors.TEXT_BLACK,
                ),
                ft.Text(
                    self.subtitle_text,
                    size=11,
                    color=ThemeColors.TEXT_MUTED_LIGHT,
                ),
            ],
            spacing=1,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Server status badge
        status_color = ThemeColors.SUCCESS if self.is_online else ThemeColors.WARNING
        status_text = "Backend Connected" if self.is_online else "Offline / Local"
        status_dot = ft.Container(
            width=8,
            height=8,
            border_radius=4,
            bgcolor=status_color,
        )
        status_pill = ft.Container(
            content=ft.Row(
                controls=[
                    status_dot,
                    ft.Text(
                        status_text,
                        size=11,
                        weight=ft.FontWeight.W_600,
                        color=ThemeColors.TEXT_MUTED_LIGHT,
                    ),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=10, vertical=5),
            border_radius=12,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
        )

        # Traveler greeting pill
        user_name = self.session_manager.display_name
        is_guest = self.session_manager.is_guest or not self.session_manager.is_authenticated

        traveler_pill = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.ACCOUNT_CIRCLE,
                        size=20,
                        color=ThemeColors.PRIMARY_BLUE,
                    ),
                    ft.Text(
                        user_name,
                        size=12,
                        weight=ft.FontWeight.W_600,
                        color=ThemeColors.TEXT_MAIN_LIGHT,
                    ),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=10, vertical=5),
            border_radius=10,
            bgcolor=ThemeColors.BG_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
        )

        right_actions = ft.Row(
            controls=[
                status_pill,
                traveler_pill,
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.content = ft.Row(
            controls=[
                title_section,
                right_actions,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
