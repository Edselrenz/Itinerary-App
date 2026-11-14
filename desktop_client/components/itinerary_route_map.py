"""Nueva Ecija Travel — Collapsible Itinerary Day Route Map Card.

Embedded inside:
- SuggestedWizardView (Result View)
- CustomBuilderView (Timeline Pane)
- TripDetailView (Top of Day Schedule)

Provides:
- Collapsible interactive GIS route map preview powered by SlippyMapCanvas
- Numbered stop badges (1..N) and OSRM road polyline
- Total day distance and commute duration estimate
- [Full Map] navigation button to jump into full-screen Map tab
"""

from __future__ import annotations

from typing import Callable, Optional
import flet as ft

from desktop_client.components.slippy_map_canvas import RouteStopPin, SlippyMapCanvas
from desktop_client.config.settings import ThemeColors
from desktop_client.core.commute_guide import get_leg_commute_info
from desktop_client.models.itinerary import ItineraryDay, ItineraryItem
from desktop_client.models.place import Place


class ItineraryRouteMap(ft.Container):
    """Collapsible GIS map card showing day itinerary stops and route polyline."""

    def __init__(
        self,
        day: Optional[ItineraryDay] = None,
        on_view_full_map: Optional[Callable[[], None]] = None,
        on_stop_click: Optional[Callable[[int], None]] = None,
        initial_expanded: bool = True,
        height_expanded: int = 240,
    ):
        super().__init__()
        self.day = day
        self.on_view_full_map = on_view_full_map
        self.on_stop_click = on_stop_click
        self.is_expanded = initial_expanded
        self.height_expanded = height_expanded

        self.bgcolor = ThemeColors.SURFACE_LIGHT
        self.border = ft.Border.all(1, ThemeColors.BORDER_LIGHT)
        self.border_radius = 12
        self.padding = ft.Padding.all(12)
        self.shadow = ft.BoxShadow(
            spread_radius=1,
            blur_radius=8,
            color=ft.Colors.with_opacity(0.06, "#000000"),
            offset=ft.Offset(0, 3),
        )

        self.map_component: Optional[SlippyMapCanvas] = None
        self._build_content()

    def set_day(self, day: ItineraryDay) -> None:
        """Updates the active day stops and re-renders the route preview."""
        self.day = day
        self._build_content()
        try:
            self.update()
        except Exception:
            pass

    def toggle_expand(self) -> None:
        self.is_expanded = not self.is_expanded
        self._build_content()
        try:
            self.update()
        except Exception:
            pass

    def _calculate_metrics(self) -> tuple[float, int]:
        """Calculates total day route distance in km and duration in minutes."""
        if not self.day or len(self.day.items) < 2:
            return 0.0, 0

        total_km = 0.0
        total_mins = 0
        sorted_items = sorted(self.day.items, key=lambda x: x.sort_order)

        for i in range(len(sorted_items) - 1):
            s1 = sorted_items[i]
            s2 = sorted_items[i + 1]

            leg = get_leg_commute_info(s1, s2)
            total_km += leg.distance_km
            total_mins += leg.duration_mins

        return round(total_km, 1), total_mins

    def _extract_route_stops(self) -> list[RouteStopPin]:
        """Extracts structured RouteStopPin objects for the map component."""
        if not self.day or not self.day.items:
            return []

        pins: list[RouteStopPin] = []
        sorted_items = sorted(self.day.items, key=lambda x: x.sort_order)
        for idx, it in enumerate(sorted_items):
            p = getattr(it, "place", None)
            lat = (p.latitude if p and p.latitude else None) or getattr(it, "latitude", None) or getattr(it, "custom_lat", None)
            lng = (p.longitude if p and p.longitude else None) or getattr(it, "longitude", None) or getattr(it, "custom_lng", None)
            title = it.custom_title or (p.name if p else f"Stop {idx + 1}")
            planned_time = getattr(it, "planned_time", "") or ""
            cat = (p.category if p and p.category else "attraction")

            if lat and lng:
                pins.append(
                    RouteStopPin(
                        index=idx,
                        title=title,
                        lat=float(lat),
                        lng=float(lng),
                        planned_time=planned_time,
                        category=cat,
                        place=p,
                    )
                )
        return pins

    def _build_content(self) -> None:
        day_num = self.day.day_number if self.day else 1
        num_stops = len(self.day.items) if self.day else 0
        total_km, total_mins = self._calculate_metrics()

        # Header Title
        title_row = ft.Row(
            controls=[
                ft.Icon(ft.Icons.ROUTE_ROUNDED, size=18, color=ThemeColors.PRIMARY_BLUE),
                ft.Text(
                    f"Day {day_num} Route Preview",
                    size=14,
                    weight=ft.FontWeight.W_700,
                    color=ThemeColors.TEXT_BLACK,
                ),
                ft.Container(
                    content=ft.Text(
                        f"{num_stops} stop{'s' if num_stops != 1 else ''}",
                        size=11,
                        color=ThemeColors.AZURE_DEEP,
                        weight=ft.FontWeight.BOLD,
                    ),
                    bgcolor=ThemeColors.AZURE_SOFT,
                    border_radius=10,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Distance & Duration Badges
        metrics_chips: list[ft.Control] = []
        if total_km > 0:
            hrs = total_mins // 60
            mins = total_mins % 60
            duration_str = f"{hrs}h {mins}m" if hrs > 0 else f"{mins} mins"

            metrics_chips.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.STRAIGHTEN_ROUNDED, size=12, color=ThemeColors.BUDGET_GREEN),
                            ft.Text(f"{total_km} km", size=11, color=ThemeColors.BUDGET_GREEN, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=4,
                    ),
                    bgcolor=ThemeColors.SUCCESS_BG,
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                )
            )
            metrics_chips.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ACCESS_TIME_ROUNDED, size=12, color=ThemeColors.AZURE_DEEP),
                            ft.Text(f"~{duration_str}", size=11, color=ThemeColors.AZURE_DEEP, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=4,
                    ),
                    bgcolor=ThemeColors.AZURE_SOFT,
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                )
            )

        # Header Action Controls: [Full Map] & Expand/Collapse Toggle
        full_map_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.MAP_ROUNDED, size=13, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text("Full Map", size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                ],
                spacing=4,
            ),
            bgcolor=ThemeColors.AZURE_SOFT,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            ink=True,
            tooltip="Explore this route in the interactive full Map tab",
            on_click=lambda _: self.on_view_full_map() if self.on_view_full_map else None,
        )

        expand_btn = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_UP_ROUNDED if self.is_expanded else ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED,
            icon_size=18,
            icon_color=ThemeColors.TEXT_MUTED_LIGHT,
            tooltip="Collapse route map" if self.is_expanded else "Expand route map",
            on_click=lambda _: self.toggle_expand(),
        )

        header = ft.Row(
            controls=[
                title_row,
                ft.Row(
                    controls=metrics_chips + [full_map_btn, expand_btn],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        if not self.is_expanded:
            self.content = header
            return

        # Build Slippy Map Canvas with Route Stops & Road Geometry
        route_stops = self._extract_route_stops()
        self.map_component = SlippyMapCanvas(
            width=760,
            height=self.height_expanded,
            route_stops=route_stops,
            on_stop_click=lambda idx, s: self.on_stop_click(idx) if self.on_stop_click else None,
            border_radius=8,
        )

        map_wrapper = ft.Container(
            content=self.map_component,
            height=self.height_expanded,
            border_radius=8,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        self.content = ft.Column(
            controls=[
                header,
                ft.Container(height=4),
                map_wrapper,
            ],
            spacing=4,
        )
