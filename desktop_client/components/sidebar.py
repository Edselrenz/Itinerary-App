"""Persistent desktop sidebar navigation component."""

from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors
from desktop_client.core.session import get_session_manager


class SidebarNav(ft.Container):
    """Desktop left-hand navigation sidebar with active route highlighting,

    traveler status, and dark/light mode toggle.
    """

    def __init__(
        self,
        current_route: str = "/dashboard",
        on_navigate: Optional[Callable[[str], None]] = None,
        on_toggle_theme: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.current_route = current_route
        self.on_navigate = on_navigate
        self.on_toggle_theme = on_toggle_theme
        self.session_manager = get_session_manager()

        self.width = 250
        self.bgcolor = ThemeColors.SURFACE_DARK
        self.border = ft.Border(
            right=ft.BorderSide(1, ThemeColors.BORDER_DARK)
        )
        self.padding = ft.Padding.all(16)
        
        self._build_content()

    def set_active_route(self, route: str) -> None:
        """Updates the highlighted route."""
        self.current_route = route
        self._build_content()
        self.update()

    def _build_content(self) -> None:
        items = [
            ("/dashboard", ft.Icons.DASHBOARD_ROUNDED, "Dashboard"),
            ("/places", ft.Icons.EXPLORE_ROUNDED, "Explore Places"),
            ("/suggested", ft.Icons.AUTO_AWESOME_ROUNDED, "Suggested Wizard"),
            ("/builder", ft.Icons.EDIT_CALENDAR_ROUNDED, "Custom Builder"),
            ("/trips", ft.Icons.BOOKMARK_ROUNDED, "Saved Trips"),
            ("/profile", ft.Icons.SETTINGS_ROUNDED, "Profile & Settings"),
        ]

        nav_buttons: list[ft.Control] = []
        for route, icon, label in items:
            is_active = self.current_route == route
            nav_buttons.append(self._create_nav_item(route, icon, label, is_active))

        # Brand header
        brand_header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.LANDSCAPE_ROUNDED,
                            size=26,
                            color=ThemeColors.EMERALD_MINT,
                        ),
                        bgcolor=ThemeColors.EMERALD_DARK,
                        border_radius=8,
                        padding=8,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                "Nueva Ecija",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ThemeColors.TEXT_MAIN_DARK,
                            ),
                            ft.Text(
                                "Travel Platform",
                                size=11,
                                color=ThemeColors.TEXT_MUTED_DARK,
                            ),
                        ],
                        spacing=1,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.only(bottom=20, top=4),
        )

        # Traveler session status card
        is_guest = self.session_manager.is_guest or not self.session_manager.is_authenticated
        user_name = self.session_manager.display_name
        badge_label = "Guest Mode" if is_guest else "Verified Traveler"
        badge_color = ThemeColors.WARM_GOLD if is_guest else ThemeColors.SUCCESS

        user_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.CircleAvatar(
                        content=ft.Icon(
                            ft.Icons.PERSON if not is_guest else ft.Icons.PERSON_OUTLINE,
                            size=18,
                            color=ThemeColors.TEXT_MAIN_DARK,
                        ),
                        bgcolor=ThemeColors.SURFACE_DARK_HOVER,
                        radius=16,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                user_name,
                                size=12,
                                weight=ft.FontWeight.W_600,
                                color=ThemeColors.TEXT_MAIN_DARK,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    badge_label,
                                    size=10,
                                    weight=ft.FontWeight.W_500,
                                    color=badge_color,
                                ),
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.SURFACE_DARK_HOVER,
            border_radius=10,
            padding=10,
            margin=ft.Margin.only(bottom=10),
        )

        # Bottom actions: Theme toggle and Sign In / Sign Out
        auth_action_text = "Sign In" if is_guest else "Log Out"
        auth_action_icon = ft.Icons.LOGIN if is_guest else ft.Icons.LOGOUT

        bottom_actions = ft.Column(
            controls=[
                user_card,
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.DARK_MODE_OUTLINED,
                            icon_color=ThemeColors.TEXT_MUTED_DARK,
                            tooltip="Toggle Theme",
                            on_click=lambda _: self._toggle_theme(),
                        ),
                        ft.FilledButton(
                            content=auth_action_text,
                            icon=auth_action_icon,
                            style=ft.ButtonStyle(
                                bgcolor=ThemeColors.SURFACE_DARK_HOVER,
                                color=ThemeColors.TEXT_MAIN_DARK,
                            ),
                            on_click=lambda _: self._on_auth_click(),
                            expand=True,
                        ),
                    ],
                    spacing=6,
                ),
            ],
            spacing=8,
        )

        self.content = ft.Column(
            controls=[
                brand_header,
                ft.Divider(color=ThemeColors.BORDER_DARK, height=1),
                ft.Container(height=10),
                ft.Column(
                    controls=nav_buttons,
                    spacing=6,
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                ft.Divider(color=ThemeColors.BORDER_DARK, height=1),
                ft.Container(height=10),
                bottom_actions,
            ],
            expand=True,
        )

    def _create_nav_item(
        self,
        route: str,
        icon: str,
        label: str,
        is_active: bool,
    ) -> ft.Control:
        bg = ThemeColors.EMERALD_PRIMARY if is_active else ft.Colors.TRANSPARENT
        text_color = ThemeColors.TEXT_MAIN_DARK if is_active else ThemeColors.TEXT_MUTED_DARK
        icon_color = ThemeColors.EMERALD_MINT if is_active else ThemeColors.TEXT_MUTED_DARK

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, size=20, color=icon_color),
                    ft.Text(label, size=13, weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL, color=text_color),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=bg,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            ink=True,
            on_click=lambda _: self._nav_clicked(route),
        )

    def _nav_clicked(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)

    def _toggle_theme(self) -> None:
        if self.on_toggle_theme:
            self.on_toggle_theme()

    def _on_auth_click(self) -> None:
        if self.session_manager.is_authenticated:
            self.session_manager.clear_session()
            if self.on_navigate:
                self.on_navigate("/login")
        else:
            if self.on_navigate:
                self.on_navigate("/login")
