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
        on_click: Optional[Callable[[ItineraryItem], None]] = None,
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
        self.on_click_card = on_click
        self.editable = editable

        self.border_radius = 12
        self.bgcolor = ThemeColors.SURFACE_LIGHT
        self.border = ft.Border.all(1.2, ThemeColors.BORDER_LIGHT)
        self.padding = ft.Padding.all(12)
        self.margin = ft.Margin.only(bottom=8)
        if self.on_click_card:
            self.ink = True
            self.on_click = lambda _: self.on_click_card(self.item)

        self._build_content()

    def _build_content(self) -> None:
        # Sequence number badge (matching Web UI blue circles)
        sequence_badge = ft.Container(
            content=ft.Text(
                str(self.item.sort_order),
                size=12,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
            ),
            width=28,
            height=28,
            border_radius=14,
            bgcolor=ThemeColors.PRIMARY_BLUE,
            alignment=ft.Alignment(0, 0),
        )

        # Planned time / duration pills
        time_text = self.item.planned_time or f"Stop #{self.item.sort_order}"
        duration_text = f"{self.item.duration_minutes} mins"

        time_pill = ft.Container(
            content=ft.Text(
                time_text,
                size=10,
                weight=ft.FontWeight.W_700,
                color=ThemeColors.PRIMARY_BLUE,
            ),
            bgcolor=ThemeColors.PRIMARY_LIGHT,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
        )

        duration_pill = ft.Container(
            content=ft.Text(
                duration_text,
                size=10,
                color=ThemeColors.TEXT_MUTED_LIGHT,
            ),
            bgcolor=ThemeColors.BG_LIGHT,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
        )

        cost_pill = ft.Container(
            content=ft.Text(
                self.item.display_cost,
                size=10,
                weight=ft.FontWeight.BOLD,
                color=ThemeColors.BUDGET_GREEN,
            ),
            bgcolor=ThemeColors.SUCCESS_BG,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
        )

        rating_pill = None
        if self.item.place and self.item.place.rating:
            rating_pill = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.STAR, size=11, color="#f59e0b"),
                        ft.Text(f"{self.item.place.rating:.1f}", size=10, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_MAIN_LIGHT),
                    ],
                    spacing=2,
                    tight=True,
                ),
                bgcolor=ThemeColors.BG_LIGHT,
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            )

        # Thumbnail image if place is present
        thumbnail = None
        if self.item.place:
            img_path = self.item.place.resolved_image_path
            if img_path:
                thumbnail = ft.Container(
                    content=ft.Image(
                        src=img_path,
                        width=48,
                        height=48,
                        fit=ft.BoxFit.COVER,
                        border_radius=8,
                        error_content=ft.Icon(ft.Icons.PLACE, size=24, color=ThemeColors.PRIMARY_BLUE),
                    ),
                    width=48,
                    height=48,
                    border_radius=8,
                )

        # Title & location
        title_text = self.item.display_title
        muni_text = "Nueva Ecija"
        if self.item.place and self.item.place.municipality_name:
            muni_text = self.item.place.municipality_name

        header_controls: list[ft.Control] = [sequence_badge]
        if thumbnail:
            header_controls.append(thumbnail)

        header_controls.append(
            ft.Column(
                controls=[
                    ft.Text(
                        title_text,
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=ThemeColors.TEXT_MAIN_LIGHT,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.LOCATION_ON, size=12, color=ThemeColors.PRIMARY_BLUE),
                            ft.Text(
                                muni_text,
                                size=11,
                                color=ThemeColors.TEXT_MUTED_LIGHT,
                            ),
                        ],
                        spacing=3,
                    ),
                ],
                spacing=2,
                expand=True,
            )
        )

        header_row = ft.Row(
            controls=header_controls,
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        chip_controls = [time_pill, duration_pill, cost_pill]
        if rating_pill:
            chip_controls.append(rating_pill)

        chips_row = ft.Row(
            controls=chip_controls,
            spacing=6,
        )

        # Action buttons for editable mode
        actions: list[ft.Control] = []
        if self.editable:
            actions = [
                ft.IconButton(
                    icon=ft.Icons.ARROW_UPWARD,
                    icon_size=16,
                    tooltip="Move Up",
                    disabled=self.is_first,
                    on_click=lambda _: self.on_move_up(self.item) if self.on_move_up else None,
                ),
                ft.IconButton(
                    icon=ft.Icons.ARROW_DOWNWARD,
                    icon_size=16,
                    tooltip="Move Down",
                    disabled=self.is_last,
                    on_click=lambda _: self.on_move_down(self.item) if self.on_move_down else None,
                ),
                ft.IconButton(
                    icon=ft.Icons.EDIT_OUTLINED,
                    icon_size=16,
                    tooltip="Edit Stop",
                    on_click=lambda _: self.on_edit(self.item) if self.on_edit else None,
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_size=16,
                    icon_color=ThemeColors.ERROR,
                    tooltip="Remove Stop",
                    on_click=lambda _: self.on_delete(self.item) if self.on_delete else None,
                ),
            ]

        bottom_row = ft.Row(
            controls=[
                chips_row,
                ft.Row(controls=actions, spacing=2) if actions else ft.Container(),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        controls_list: list[ft.Control] = [header_row, bottom_row]

        if self.item.notes:
            controls_list.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.NOTE_OUTLINED, size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ft.Text(
                                self.item.notes,
                                size=11,
                                italic=True,
                                color=ThemeColors.TEXT_MUTED_LIGHT,
                                expand=True,
                            ),
                        ],
                        spacing=4,
                    ),
                    bgcolor=ThemeColors.BG_LIGHT,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    border_radius=4,
                )
            )

        self.content = ft.Column(
            controls=controls_list,
            spacing=8,
        )
