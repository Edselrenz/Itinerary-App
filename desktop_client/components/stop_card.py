"""Stop Card component for chronological itinerary schedules and day timelines."""

from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors
from desktop_client.models.itinerary import ItineraryItem


class StopCard(ft.Container):
    """Timeline stop item supporting in-place reordering, duration editing,

    notes annotation, and turn-by-turn routing indicators.
    """

    def __init__(
        self,
        item: ItineraryItem,
        is_first: bool = False,
        is_last: bool = False,
        on_move_up: Optional[Callable[[ItineraryItem], None]] = None,
        on_move_down: Optional[Callable[[ItineraryItem], None]] = None,
        on_edit: Optional[Callable[[ItineraryItem], None]] = None,
        on_delete: Optional[Callable[[ItineraryItem], None]] = None,
        editable: bool = True,
    ):
        super().__init__()
        self.item = item
        self.is_first = is_first
        self.is_last = is_last
        self.on_move_up = on_move_up
        self.on_move_down = on_move_down
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.editable = editable

        self.border_radius = 10
        self.bgcolor = ThemeColors.SURFACE_LIGHT
        self.border = ft.Border.all(1, ThemeColors.BORDER_LIGHT)
        self.padding = ft.padding.all(12)
        self.margin = ft.margin.only(bottom=8)

        self._build_content()

    def _build_content(self) -> None:
        # Sequence number badge
        sequence_badge = ft.Container(
            content=ft.Text(
                str(self.item.sort_order),
                size=12,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
            ),
            width=26,
            height=26,
            border_radius=13,
            bgcolor=ThemeColors.EMERALD_PRIMARY,
            alignment=ft.Alignment(0, 0),
        )

        # Planned time / duration pills
        time_text = self.item.planned_time or f"Stop #{self.item.sort_order}"
        duration_text = f"{self.item.duration_minutes} mins"
        
        time_pill = ft.Container(
            content=ft.Text(
                time_text,
                size=10,
                weight=ft.FontWeight.W_600,
                color=ThemeColors.AZURE_DEEP,
            ),
            bgcolor=ThemeColors.AZURE_SOFT,
            border_radius=6,
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
        )

        duration_pill = ft.Container(
            content=ft.Text(
                duration_text,
                size=10,
                color=ThemeColors.TEXT_MUTED_LIGHT,
            ),
            bgcolor=ThemeColors.BG_LIGHT,
            border_radius=6,
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
        )

        cost_pill = ft.Container(
            content=ft.Text(
                self.item.display_cost,
                size=10,
                weight=ft.FontWeight.W_600,
                color=ThemeColors.EMERALD_PRIMARY,
            ),
            bgcolor=ThemeColors.EMERALD_MINT,
            border_radius=6,
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
        )

        # Title & location
        title_text = self.item.display_title
        category_or_custom = (
            self.item.place.formatted_category
            if self.item.place
            else "Off-Grid Custom Venue"
        )
        location_text = (
            self.item.place.address_text or self.item.place.municipality_name or "Nueva Ecija"
            if self.item.place
            else "Custom Coordinates"
        )

        # Reorder and action controls
        action_controls: list[ft.Control] = []
        if self.editable:
            action_controls = [
                ft.IconButton(
                    icon=ft.Icons.KEYBOARD_ARROW_UP,
                    icon_size=18,
                    disabled=self.is_first,
                    tooltip="Move Up",
                    on_click=lambda _: self.on_move_up(self.item) if self.on_move_up else None,
                ),
                ft.IconButton(
                    icon=ft.Icons.KEYBOARD_ARROW_DOWN,
                    icon_size=18,
                    disabled=self.is_last,
                    tooltip="Move Down",
                    on_click=lambda _: self.on_move_down(self.item) if self.on_move_down else None,
                ),
                ft.IconButton(
                    icon=ft.Icons.EDIT_OUTLINED,
                    icon_size=18,
                    tooltip="Edit Stop Details",
                    on_click=lambda _: self.on_edit(self.item) if self.on_edit else None,
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_size=18,
                    icon_color=ThemeColors.ERROR,
                    tooltip="Remove Stop",
                    on_click=lambda _: self.on_delete(self.item) if self.on_delete else None,
                ),
            ]

        # Travel routing banner if distance exists
        route_banner = None
        if self.item.travel_distance_meters:
            dist_km = self.item.travel_distance_meters / 1000.0
            dur_min = (self.item.travel_duration_seconds or 0) // 60
            route_banner = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.DIRECTIONS_CAR, size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ft.Text(
                            f"Drive: {dist_km:.1f} km • ~{dur_min} min from previous stop",
                            size=10,
                            color=ThemeColors.TEXT_MUTED_LIGHT,
                        ),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.only(top=4),
            )

        notes_row = None
        if self.item.notes:
            notes_row = ft.Container(
                content=ft.Text(
                    f"Note: {self.item.notes}",
                    size=11,
                    italic=True,
                    color=ThemeColors.TEXT_MUTED_LIGHT,
                ),
                padding=ft.padding.only(top=4),
            )

        main_details = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        time_pill,
                        duration_pill,
                        cost_pill,
                    ],
                    spacing=6,
                ),
                ft.Text(
                    title_text,
                    size=13,
                    weight=ft.FontWeight.W_600,
                    color=ThemeColors.TEXT_MAIN_LIGHT,
                ),
                ft.Text(
                    f"{category_or_custom} • {location_text}",
                    size=11,
                    color=ThemeColors.TEXT_MUTED_LIGHT,
                ),
            ],
            spacing=4,
            expand=True,
        )

        if notes_row:
            main_details.controls.append(notes_row)
        if route_banner:
            main_details.controls.append(route_banner)

        self.content = ft.Row(
            controls=[
                sequence_badge,
                main_details,
                ft.Row(controls=action_controls, spacing=0),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
