"""Nueva Ecija Travel — 4-Tab Bottom Navigation Bar (.custom-tab-bar).

Conforms strictly to the canonical Ionic Angular web navigation ergonomics:
- 4 centered tabs: Home, Map, Saved, Profile
- 60px height with top subtle border
- Azure (#0084ff) active indicator and #94a3b8 inactive
- Route synchronization with reset capability for Map follow-mode
"""

from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors, ThemePalette


class BottomTabBar(ft.Container):
    """Persistent 4-tab bottom navigation bar matching web .custom-tab-bar (60px)."""

    def __init__(
        self,
        current_route: str = "/home",
        on_navigate: Optional[Callable[[str], None]] = None,
        on_map_tap_when_active: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.current_route = current_route
        self.on_navigate = on_navigate
        self.on_map_tap_when_active = on_map_tap_when_active

        self.height = 60
        self.expand = False
        self.padding = ft.Padding.symmetric(horizontal=8, vertical=4)

        self._tabs_data = [
            {
                "key": "home",
                "label": "Home",
                "routes": ["/home", "/dashboard"],
                "target": "/home",
                "icon_active": ft.Icons.HOME,
                "icon_inactive": ft.Icons.HOME_OUTLINED,
            },
            {
                "key": "map",
                "label": "Map",
                "routes": ["/map", "/places"],
                "target": "/map",
                "icon_active": ft.Icons.LOCATION_ON,
                "icon_inactive": ft.Icons.LOCATION_ON_OUTLINED,
            },
            {
                "key": "saved",
                "label": "Saved",
                "routes": ["/saved", "/trips"],
                "target": "/saved",
                "icon_active": ft.Icons.BOOKMARK,
                "icon_inactive": ft.Icons.BOOKMARK_BORDER,
            },
            {
                "key": "profile",
                "label": "Profile",
                "routes": ["/profile"],
                "target": "/profile",
                "icon_active": ft.Icons.PERSON,
                "icon_inactive": ft.Icons.PERSON_OUTLINE,
            },
        ]

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

    def _get_active_tab_key(self) -> str:
        route = self.current_route.lower()
        for tab in self._tabs_data:
            if any(route == r or route.startswith(f"{r}/") for r in tab["routes"]):
                return tab["key"]
        return "home"

    def set_active_route(self, route: str) -> None:
        """Updates the active tab styling to reflect current route."""
        self.current_route = route
        self._build_content()
        try:
            self.update()
        except Exception:
            pass

    def _handle_tab_click(self, tab: dict) -> None:
        active_key = self._get_active_tab_key()
        if tab["key"] == "map" and active_key == "map":
            if self.on_map_tap_when_active:
                self.on_map_tap_when_active()
        if self.on_navigate:
            self.on_navigate(tab["target"])

    def _build_content(self) -> None:
        is_dark = self._get_is_dark()
        palette = ThemePalette.get_palette(is_dark)

        self.bgcolor = palette.surface_card
        self.border = ft.Border.only(
            top=ft.BorderSide(1.0, palette.border_main)
        )

        active_key = self._get_active_tab_key()
        tab_buttons: list[ft.Control] = []

        for tab in self._tabs_data:
            is_active = (tab["key"] == active_key)
            icon = tab["icon_active"] if is_active else tab["icon_inactive"]
            color = ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.TEXT_MUTED_LIGHT
            font_weight = ft.FontWeight.W_700 if is_active else ft.FontWeight.W_500

            tab_ctrl = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            icon,
                            size=22,
                            color=color,
                        ),
                        ft.Text(
                            tab["label"],
                            size=11,
                            weight=font_weight,
                            color=color,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                ),
                expand=True,
                ink=True,
                border_radius=8,
                padding=ft.Padding.symmetric(vertical=4),
                on_click=lambda _, t=tab: self._handle_tab_click(t),
            )
            tab_buttons.append(tab_ctrl)

        self.content = ft.Row(
            controls=tab_buttons,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        )
