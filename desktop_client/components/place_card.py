"""Place Card component conforming strictly to the Figma & Web Client design system."""

from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors
from desktop_client.models.place import Place


class PlaceCard(ft.Container):
    """Destination card highlighting Nueva Ecija identity, honest pricing,

    overlaid category badges, and one-click stop addition matching Web UI.
    """

    def __init__(
        self,
        place: Place,
        on_view_details: Optional[Callable[[Place], None]] = None,
        on_add_to_day: Optional[Callable[[Place], None]] = None,
        width: Optional[float] = 300,
    ):
        super().__init__()
        self.place = place
        self.on_view_details = on_view_details
        self.on_add_to_day = on_add_to_day

        self.width = width
        self.border_radius = 14
        self.bgcolor = ThemeColors.SURFACE_LIGHT
        self.border = ft.Border.all(1.2, ThemeColors.BORDER_LIGHT)
        self.clip_behavior = ft.ClipBehavior.HARD_EDGE
        self.ink = True
        self.on_click = lambda _: self._view_details()

        self._build_content()

    def _build_content(self) -> None:
        # Thumbnail image or fallback with top-left category badge overlay
        img_src = self.place.resolved_image_path
        if img_src:
            image_widget = ft.Image(
                src=img_src,
                height=140,
                width=float("inf"),
                fit=ft.BoxFit.COVER,
                error_content=ft.Container(
                    content=ft.Icon(
                        ft.Icons.LANDSCAPE_OUTLINED,
                        size=36,
                        color=ThemeColors.PRIMARY_BLUE,
                    ),
                    height=140,
                    bgcolor=ThemeColors.PRIMARY_LIGHT,
                    alignment=ft.Alignment(0, 0),
                ),
            )
        else:
            image_widget = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            ft.Icons.LANDSCAPE_OUTLINED,
                            size=36,
                            color=ThemeColors.PRIMARY_BLUE,
                        ),
                        ft.Text(
                            self.place.formatted_category,
                            size=11,
                            color=ThemeColors.TEXT_MUTED_LIGHT,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
                height=140,
                bgcolor=ThemeColors.PRIMARY_LIGHT,
                alignment=ft.Alignment(0, 0),
            )

        # Overlaid Category Badge (matching web .dest-badge-category / .result-category-badge)
        category_overlay_badge = ft.Container(
            content=ft.Text(
                self.place.formatted_category,
                size=10,
                weight=ft.FontWeight.W_700,
                color=ft.Colors.WHITE,
            ),
            bgcolor=ft.Colors.with_opacity(0.85, ThemeColors.TEXT_MAIN_LIGHT),
            border_radius=5,
            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
            margin=ft.Margin.only(top=8, left=8),
        )

        image_stack = ft.Stack(
            controls=[
                image_widget,
                category_overlay_badge,
            ]
        )

        # Rating badge if available
        rating_controls: list[ft.Control] = []
        if self.place.rating:
            rating_controls = [
                ft.Icon(ft.Icons.STAR, size=14, color=ThemeColors.WARM_GOLD),
                ft.Text(
                    f"{self.place.rating:.1f}",
                    size=11,
                    weight=ft.FontWeight.BOLD,
                    color=ThemeColors.TEXT_MAIN_LIGHT,
                ),
                ft.Text(
                    f"({self.place.user_rating_count or 0})",
                    size=10,
                    color=ThemeColors.TEXT_MUTED_LIGHT,
                ),
            ]

        # Municipality line with travel azure pin icon
        muni_text = self.place.municipality_name or "Nueva Ecija"
        location_row = ft.Row(
            controls=[
                ft.Icon(ft.Icons.LOCATION_ON, size=14, color=ThemeColors.PRIMARY_BLUE),
                ft.Text(
                    muni_text,
                    size=12,
                    weight=ft.FontWeight.W_500,
                    color=ThemeColors.PRIMARY_BLUE,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    expand=True,
                ),
                ft.Row(controls=rating_controls, spacing=2) if rating_controls else ft.Container(),
            ],
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Honest pricing chip (matching web .dest-cost-chip / verified-budget)
        cost_chip = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PAYMENTS_OUTLINED, size=13, color=ThemeColors.BUDGET_GREEN),
                    ft.Text(
                        self.place.formatted_cost,
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=ThemeColors.BUDGET_GREEN,
                    ),
                ],
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.SUCCESS_BG,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
        )

        # Action buttons
        actions_row = ft.Row(
            controls=[
                ft.TextButton(
                    content="View Details",
                    icon=ft.Icons.VISIBILITY_OUTLINED,
                    style=ft.ButtonStyle(color=ThemeColors.PRIMARY_BLUE),
                    on_click=lambda _: self._view_details(),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        if self.on_add_to_day:
            actions_row.controls.append(
                ft.FilledButton(
                    content="+ Add to Trip",
                    icon=ft.Icons.ADD,
                    style=ft.ButtonStyle(
                        bgcolor=ThemeColors.PRIMARY_BLUE,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda _: self._add_to_day(),
                )
            )

        details_column = ft.Container(
            content=ft.Column(
                controls=[
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
                    cost_chip,
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    actions_row,
                ],
                spacing=6,
            ),
            padding=12,
        )

        self.content = ft.Column(
            controls=[
                image_stack,
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
