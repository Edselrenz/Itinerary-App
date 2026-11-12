"""Place Card component for catalog exploration and destination grids."""

from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors
from desktop_client.models.place import Place


class PlaceCard(ft.Container):
    """Destination card highlighting Nueva Ecija identity, honest pricing,

    and one-click stop addition.
    """

    def __init__(
        self,
        place: Place,
        on_view_details: Optional[Callable[[Place], None]] = None,
        on_add_to_day: Optional[Callable[[Place], None]] = None,
        width: Optional[float] = 320,
    ):
        super().__init__()
        self.place = place
        self.on_view_details = on_view_details
        self.on_add_to_day = on_add_to_day

        self.width = width
        self.border_radius = 12
        self.bgcolor = ThemeColors.SURFACE_LIGHT
        self.border = ft.Border.all(1, ThemeColors.BORDER_LIGHT)
        self.clip_behavior = ft.ClipBehavior.HARD_EDGE
        self.ink = True
        self.on_click = lambda _: self._view_details()

        self._build_content()

    def _build_content(self) -> None:
        # Thumbnail image or placeholder
        if self.place.image_url and self.place.image_url.startswith("http"):
            image_control = ft.Image(
                src=self.place.image_url,
                height=150,
                width=float("inf"),
                fit=ft.BoxFit.COVER,
            )
        else:
            image_control = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            ft.Icons.LANDSCAPE_OUTLINED,
                            size=40,
                            color=ThemeColors.EMERALD_MINT,
                        ),
                        ft.Text(
                            self.place.formatted_category,
                            size=11,
                            color=ThemeColors.EMERALD_MINT,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
                height=150,
                bgcolor=ThemeColors.EMERALD_DARK,
                alignment=ft.Alignment(0, 0),
            )

        # Category chip
        category_chip = ft.Container(
            content=ft.Text(
                self.place.formatted_category,
                size=10,
                weight=ft.FontWeight.W_600,
                color=ThemeColors.AZURE_DEEP,
            ),
            bgcolor=ThemeColors.AZURE_SOFT,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
        )

        # Rating badge if available
        rating_controls: list[ft.Control] = []
        if self.place.rating:
            rating_controls = [
                ft.Icon(ft.Icons.STAR, size=14, color=ThemeColors.WARM_GOLD),
                ft.Text(
                    f"{self.place.rating:.1f}",
                    size=11,
                    weight=ft.FontWeight.W_600,
                    color=ThemeColors.TEXT_MAIN_LIGHT,
                ),
                ft.Text(
                    f"({self.place.user_rating_count or 0})",
                    size=10,
                    color=ThemeColors.TEXT_MUTED_LIGHT,
                ),
            ]

        # Municipality line
        muni_text = self.place.municipality_name or "Nueva Ecija"
        location_row = ft.Row(
            controls=[
                ft.Icon(ft.Icons.LOCATION_ON_OUTLINED, size=14, color=ThemeColors.TEXT_MUTED_LIGHT),
                ft.Text(
                    muni_text,
                    size=11,
                    color=ThemeColors.TEXT_MUTED_LIGHT,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    expand=True,
                ),
            ],
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Honest pricing pill
        cost_pill = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PAYMENTS_OUTLINED, size=13, color=ThemeColors.EMERALD_PRIMARY),
                    ft.Text(
                        self.place.formatted_cost,
                        size=11,
                        weight=ft.FontWeight.W_600,
                        color=ThemeColors.EMERALD_PRIMARY,
                    ),
                ],
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.EMERALD_MINT,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
        )

        # Action buttons
        actions_row = ft.Row(
            controls=[
                ft.TextButton(
                    content="Details",
                    icon=ft.Icons.INFO_OUTLINE,
                    on_click=lambda _: self._view_details(),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        if self.on_add_to_day:
            actions_row.controls.append(
                ft.FilledButton(
                    content="+ Add",
                    icon=ft.Icons.ADD,
                    style=ft.ButtonStyle(
                        bgcolor=ThemeColors.EMERALD_PRIMARY,
                        color=ft.Colors.WHITE,
                    ),
                    on_click=lambda _: self._add_to_day(),
                )
            )

        details_column = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        category_chip,
                        ft.Row(controls=rating_controls, spacing=2) if rating_controls else ft.Container(),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text(
                    self.place.name,
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ThemeColors.TEXT_MAIN_LIGHT,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                location_row,
                ft.Container(height=2),
                cost_pill,
                ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                actions_row,
            ],
            spacing=8,
            padding=12,
        )

        self.content = ft.Column(
            controls=[
                image_control,
                details_column,
            ],
            spacing=0,
        )

    def _view_details(self) -> None:
        if self.on_view_details:
            self.on_view_details(self.place)

    def _add_to_day(self) -> None:
        if self.on_add_to_day:
            self.on_add_to_day(self.place)
