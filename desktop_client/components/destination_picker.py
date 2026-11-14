"""Destination Picker with Quick Chips and All 32 Towns Regional Explorer Modal.

Conforms to Figma and Ionic tabs/suggested travel destination selection.
"""

from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import NUEVA_ECIJA_LGUS, ThemeColors
from desktop_client.core.offline_data import ALL_32_LGUS_METADATA


class DestinationPicker(ft.Container):
    """Reusable Destination Autocomplete / Selector with quick suggestion chips

    and 32-LGU district categorized regional explorer.
    """

    def __init__(
        self,
        value: str = "Nueva Ecija",
        label: str = "Destination / Municipality",
        on_change: Optional[Callable[[str], None]] = None,
        initial_value: Optional[str] = None,
    ):
        super().__init__()
        self.selected_destination = initial_value or value or "Nueva Ecija"
        self.label = label
        self.on_change = on_change

        self._build_content()

    @property
    def value(self) -> str:
        return self.selected_destination

    @value.setter
    def value(self, new_val: str) -> None:
        self.selected_destination = new_val or "Nueva Ecija"
        self._build_content()
        self._safe_update()

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass

    def _build_content(self) -> None:
        # Autocomplete / Dropdown options
        options = [ft.dropdown.Option("Nueva Ecija", "All Nueva Ecija (Provincial)")]
        for lgu in sorted(NUEVA_ECIJA_LGUS):
            meta = ALL_32_LGUS_METADATA.get(lgu, {})
            dist = meta.get("district", "")
            suffix = f" [{dist}]" if dist else ""
            options.append(ft.dropdown.Option(lgu, f"{lgu}{suffix}"))

        self.dropdown = ft.Dropdown(
            label=self.label,
            options=options,
            value=self.selected_destination if any(o.key == self.selected_destination for o in options) else "Nueva Ecija",
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            expand=True,
            dense=True,
            on_select=lambda e: self._handle_select(e.control.value),
        )

        all_32_btn = ft.OutlinedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.MAP_OUTLINED, size=16, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text("32 Towns Explorer", size=12, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                ],
                spacing=6,
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                side=ft.BorderSide(1.2, ThemeColors.CUSTOM_CARD_BORDER),
            ),
            on_click=lambda _: self._open_regional_explorer(),
        )

        input_row = ft.Row(
            controls=[self.dropdown, all_32_btn],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Quick Suggestion Chips
        quick_targets = [
            ("Nueva Ecija", "All Nueva Ecija"),
            ("Bongabon", "Bongabon"),
            ("Pantabangan", "Pantabangan"),
            ("Cabanatuan City", "Cabanatuan"),
            ("Gapan City", "Gapan"),
            ("General Tinio", "Gen. Tinio"),
        ]

        quick_chips = []
        for target_val, label in quick_targets:
            is_active = self.selected_destination == target_val
            chip = ft.Container(
                content=ft.Text(
                    label,
                    size=11,
                    weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.W_500,
                    color=ft.Colors.WHITE if is_active else ThemeColors.TEXT_MAIN_LIGHT,
                ),
                bgcolor=ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.SURFACE_LIGHT,
                border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.BORDER_LIGHT),
                border_radius=14,
                padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                ink=True,
                on_click=lambda _, val=target_val: self._handle_select(val),
            )
            quick_chips.append(chip)

        chips_row = ft.Row(
            controls=quick_chips,
            scroll=ft.ScrollMode.AUTO,
            spacing=6,
        )

        self.content = ft.Column(
            controls=[
                input_row,
                ft.Container(height=2),
                chips_row,
            ],
            spacing=4,
        )

    def _handle_select(self, val: str) -> None:
        self.selected_destination = val or "Nueva Ecija"
        self._build_content()
        self._safe_update()
        if self.on_change:
            self.on_change(self.selected_destination)

    def _open_regional_explorer(self) -> None:
        """Opens Regional Explorer Modal with district filter tabs."""
        if not self.page:
            return

        active_district = "All"
        districts = ["All", "Central", "North", "South", "East"]

        content_container = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=380)

        def render_lgus():
            items = []
            for lgu, meta in sorted(ALL_32_LGUS_METADATA.items()):
                dist = meta.get("district", "")
                if active_district != "All" and dist != active_district:
                    continue

                is_city = meta.get("is_city", False)
                poi_count = meta.get("poi_count", 0)
                highlights = meta.get("highlights", [])
                hl_text = " • ".join(highlights[:2])

                is_active = self.selected_destination == lgu

                items.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Icon(
                                        ft.Icons.LOCATION_CITY if is_city else ft.Icons.LANDSCAPE,
                                        size=18,
                                        color=ThemeColors.PRIMARY_BLUE if not is_active else ft.Colors.WHITE,
                                    ),
                                    bgcolor=ThemeColors.PRIMARY_LIGHT if not is_active else ThemeColors.PRIMARY_BLUE,
                                    border_radius=8,
                                    padding=6,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Row(
                                            controls=[
                                                ft.Text(lgu, size=13, weight=ft.FontWeight.BOLD),
                                                ft.Container(
                                                    content=ft.Text(
                                                        "City" if is_city else dist,
                                                        size=9,
                                                        weight=ft.FontWeight.BOLD,
                                                        color=ThemeColors.AZURE_DEEP,
                                                    ),
                                                    bgcolor=ThemeColors.AZURE_SOFT,
                                                    border_radius=4,
                                                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                                ),
                                            ],
                                            spacing=6,
                                        ),
                                        ft.Text(
                                            f"{poi_count} destinations{f' • {hl_text}' if hl_text else ''}",
                                            size=11,
                                            color=ThemeColors.TEXT_MUTED_LIGHT,
                                            max_lines=1,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.FilledButton(
                                    content="Select",
                                    style=ft.ButtonStyle(
                                        bgcolor=ThemeColors.PRIMARY_BLUE,
                                        color=ft.Colors.WHITE,
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                    ),
                                    on_click=lambda _, name=lgu: pick_and_close(name),
                                ),
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=ThemeColors.SURFACE_LIGHT,
                        border=ft.Border.all(1.2, ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.BORDER_LIGHT),
                        border_radius=10,
                        padding=ft.Padding.all(8),
                    )
                )
            content_container.controls = items
            try:
                content_container.update()
            except Exception:
                pass

        def set_tab(d: str):
            nonlocal active_district
            active_district = d
            for c in tab_row.controls:
                is_sel = getattr(c, "data", None) == d
                c.bgcolor = ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.SURFACE_LIGHT
                c.content.color = ft.Colors.WHITE if is_sel else ThemeColors.TEXT_MAIN_LIGHT
            try:
                tab_row.update()
            except Exception:
                pass
            render_lgus()

        def pick_and_close(name: str):
            dlg.open = False
            self.page.update()
            self._handle_select(name)

        tab_buttons = []
        for d in districts:
            is_sel = d == active_district
            btn = ft.Container(
                content=ft.Text(d, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE if is_sel else ThemeColors.TEXT_MAIN_LIGHT),
                bgcolor=ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.SURFACE_LIGHT,
                border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.BORDER_LIGHT),
                border_radius=14,
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                ink=True,
                data=d,
                on_click=lambda _, dist_name=d: set_tab(dist_name),
            )
            tab_buttons.append(btn)

        tab_row = ft.Row(controls=tab_buttons, spacing=6, scroll=ft.ScrollMode.AUTO)
        render_lgus()

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.MAP, color=ThemeColors.PRIMARY_BLUE, size=22),
                    ft.Text("Nueva Ecija 32 LGUs Explorer", size=16, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            content=ft.Column(
                controls=[
                    tab_row,
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    content_container,
                ],
                width=520,
                spacing=10,
                tight=True,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _: close_dlg()),
            ],
        )

        def close_dlg():
            dlg.open = False
            self.page.update()

        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
