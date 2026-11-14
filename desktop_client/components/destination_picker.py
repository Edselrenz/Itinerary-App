"""Destination Picker with Live Autocomplete, Quick Chips, and 32-Town Regional Explorer Modal.

Conforms 1:1 to Project/src/app/shared/components/destination-autocomplete/ and Figma specifications.
"""

from __future__ import annotations

from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import NUEVA_ECIJA_LGUS, ThemeColors
from desktop_client.core.offline_data import ALL_32_LGUS_METADATA

TOP_LANDMARKS = [
    {"name": "Minalungao National Park", "municipality": "General Tinio", "place_id": "poi_minalungao", "category": "nature_park"},
    {"name": "Highland Bali Villas Resort and Spa", "municipality": "Pantabangan", "place_id": "poi_highland_bali", "category": "resort_swimming"},
    {"name": "Camp Pangatian War Memorial Shrine", "municipality": "Cabanatuan City", "place_id": "poi_pangatian", "category": "museum_cultural"},
    {"name": "General Luna Statue and Plaza Lucero", "municipality": "Cabanatuan City", "place_id": "poi_general_luna", "category": "museum_cultural"},
    {"name": "Fort Magsaysay Army Museum", "municipality": "Palayan City", "place_id": "poi_fort_magsaysay", "category": "museum_cultural"},
    {"name": "Pantabangan Dam & Lake Viewpoint", "municipality": "Pantabangan", "place_id": "poi_pantabangan_dam", "category": "tourist_attraction"},
    {"name": "Three Kings Parish Church", "municipality": "Gapan City", "place_id": "poi_three_kings", "category": "church_religious"},
    {"name": "St. Nicholas of Tolentine Cathedral", "municipality": "Cabanatuan City", "place_id": "poi_st_nicholas", "category": "church_religious"},
    {"name": "Gabaldon Falls & Eco Park", "municipality": "Gabaldon", "place_id": "poi_gabaldon_falls", "category": "nature_park"},
    {"name": "Dalton Pass Historical Landmark", "municipality": "Santa Fe", "place_id": "poi_dalton_pass", "category": "tourist_attraction"},
    {"name": "PhilRice Central Experiment Station", "municipality": "Science City of Muñoz", "place_id": "poi_philrice", "category": "tourist_attraction"},
    {"name": "Central Luzon State University (CLSU)", "municipality": "Science City of Muñoz", "place_id": "poi_clsu", "category": "tourist_attraction"},
]


class DestinationPicker(ft.Container):
    """Reusable Destination Autocomplete with live suggestions for Province, 32 LGUs,

    and 12 Top Landmarks, plus wrapped Quick Chips matching Web DestinationAutocompleteComponent.
    """

    def __init__(
        self,
        value: str = "Nueva Ecija",
        label: str = "Destination / Municipality",
        on_change: Optional[Callable[[str], None]] = None,
        on_landmark_select: Optional[Callable[[str], None]] = None,
        initial_value: Optional[str] = None,
    ):
        super().__init__()
        self.selected_destination = initial_value or value or "Nueva Ecija"
        self.label = label
        self.on_change = on_change
        self.on_landmark_select = on_landmark_select
        self.anchor_place_id: Optional[str] = None
        self._is_dropdown_open = False
        self._search_text = self.selected_destination

        self._build_content()

    @property
    def value(self) -> str:
        return self.selected_destination

    @value.setter
    def value(self, new_val: str) -> None:
        self.selected_destination = new_val or "Nueva Ecija"
        self._search_text = self.selected_destination
        if hasattr(self, "_text_field"):
            self._text_field.value = self._search_text
        self._build_content()
        self._safe_update()

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass

    def _build_content(self) -> None:
        self._text_field = ft.TextField(
            value=self._search_text,
            hint_text="Choose a town, city, or landmark",
            hint_style=ft.TextStyle(size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
            prefix_icon=ft.Icons.LOCATION_ON,
            border_radius=10,
            border_color="#cbd5e1",
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            dense=True,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            on_change=lambda e: self._on_input_change(e.control.value),
            on_focus=lambda _: self._open_suggestions(),
        )

        clear_btn = ft.IconButton(
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_size=16,
            icon_color=ThemeColors.TEXT_MUTED_LIGHT,
            tooltip="Clear input",
            on_click=lambda _: self._clear_input(),
        )

        input_container = ft.Row(
            controls=[
                ft.Container(content=self._text_field, expand=True),
                clear_btn,
            ],
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Floating Suggestion Panel
        suggestion_list = self._build_suggestions_list()
        self._suggestion_panel = ft.Container(
            visible=self._is_dropdown_open,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=12,
            padding=ft.Padding.symmetric(vertical=6, horizontal=8),
            shadow=ft.BoxShadow(blur_radius=14, color=ft.Colors.with_opacity(0.12, "#000000"), offset=ft.Offset(0, 4)),
            content=suggestion_list,
        )

        # Wrapped Quick Chips in exact Web order
        quick_targets = [
            ("Bongabon", "Bongabon"),
            ("Pantabangan", "Pantabangan"),
            ("Cabanatuan City", "Cabanatuan City"),
            ("Gapan City", "Gapan City"),
            ("General Tinio", "General Tinio"),
            ("Nueva Ecija", "Nueva Ecija"),
            ("__explorer__", "🗺️ All 32 Towns"),
        ]

        chips = []
        for target_val, label in quick_targets:
            is_active = (self.selected_destination == target_val)
            if target_val == "__explorer__":
                chip = ft.Container(
                    content=ft.Text(label, size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                    bgcolor=ThemeColors.PRIMARY_LIGHT,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE),
                    border_radius=14,
                    padding=ft.Padding.symmetric(horizontal=11, vertical=5),
                    ink=True,
                    on_click=lambda _: self._open_regional_explorer(),
                )
            else:
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
                    padding=ft.Padding.symmetric(horizontal=11, vertical=5),
                    ink=True,
                    on_click=lambda _, v=target_val: self._handle_select(v),
                )
            chips.append(chip)

        chips_row = ft.Row(
            controls=chips,
            wrap=True,
            spacing=6,
            run_spacing=6,
        )

        self.content = ft.Column(
            controls=[
                input_container,
                self._suggestion_panel,
                ft.Container(height=2),
                chips_row,
            ],
            spacing=4,
            tight=True,
        )

    def _build_suggestions_list(self) -> ft.Control:
        q = (self._search_text or "").strip().lower()
        items: list[ft.Control] = []

        # 1. Province Option
        if not q or "nueva ecija" in q or "all" in q:
            items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.TRAVEL_EXPLORE, size=18, color=ThemeColors.PRIMARY_BLUE),
                            ft.Column(
                                controls=[
                                    ft.Text("All of Nueva Ecija", size=13, weight=ft.FontWeight.BOLD),
                                    ft.Text("Province-Wide Corridor • 2,673 Places", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=1,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=ft.Padding.symmetric(vertical=6, horizontal=8),
                    border_radius=8,
                    ink=True,
                    on_click=lambda _: self._handle_select("Nueva Ecija"),
                )
            )

        # 2. Municipalities Matching Query
        matched_lgus = [
            lgu for lgu in sorted(NUEVA_ECIJA_LGUS)
            if not q or q in lgu.lower()
        ][:8]

        for lgu in matched_lgus:
            meta = ALL_32_LGUS_METADATA.get(lgu, {})
            is_city = meta.get("is_city", False)
            poi_count = meta.get("poi_count", 0)
            items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.LOCATION_CITY if is_city else ft.Icons.LOCATION_ON, size=16, color=ThemeColors.PRIMARY_BLUE),
                            ft.Text(lgu, size=13, weight=ft.FontWeight.W_600),
                            ft.Container(
                                content=ft.Text(f"{poi_count} places", size=10, color=ThemeColors.TEXT_MUTED_LIGHT),
                                bgcolor="#f1f5f9",
                                border_radius=6,
                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=ft.Padding.symmetric(vertical=6, horizontal=8),
                    border_radius=8,
                    ink=True,
                    on_click=lambda _, name=lgu: self._handle_select(name),
                )
            )

        # 3. Landmarks Matching Query
        matched_landmarks = [
            lm for lm in TOP_LANDMARKS
            if not q or q in lm["name"].lower() or q in lm["municipality"].lower()
        ][:5]

        for lm in matched_landmarks:
            items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.STAR_ROUNDED, size=16, color="#f59e0b"),
                            ft.Column(
                                controls=[
                                    ft.Text(lm["name"], size=12, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{lm['municipality']} • Anchor Attraction", size=10, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=1,
                                expand=True,
                            ),
                            ft.Container(
                                content=ft.Text("⭐ Anchor", size=9, weight=ft.FontWeight.BOLD, color="#d97706"),
                                bgcolor="#fef3c7",
                                border_radius=4,
                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=ft.Padding.symmetric(vertical=6, horizontal=8),
                    border_radius=8,
                    ink=True,
                    on_click=lambda _, landmark=lm: self._handle_select_landmark(landmark),
                )
            )

        # 4. Footer link to All 32 Towns Explorer
        items.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.MAP_OUTLINED, size=14, color=ThemeColors.PRIMARY_BLUE),
                        ft.Text("Browse All 32 Nueva Ecija Towns & Cities →", size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                    ],
                    spacing=6,
                ),
                padding=ft.Padding.symmetric(vertical=6, horizontal=8),
                ink=True,
                on_click=lambda _: self._open_regional_explorer(),
            )
        )

        return ft.Column(controls=items, spacing=2, tight=True, scroll=ft.ScrollMode.AUTO, height=200 if len(items) > 5 else None)

    def _open_suggestions(self) -> None:
        self._is_dropdown_open = True
        self._build_content()
        self._safe_update()

    def _close_suggestions(self) -> None:
        self._is_dropdown_open = False
        self._build_content()
        self._safe_update()

    def _on_input_change(self, val: str) -> None:
        self._search_text = val
        self._is_dropdown_open = True
        self._build_content()
        self._safe_update()

    def _clear_input(self) -> None:
        self._search_text = ""
        self.selected_destination = "Nueva Ecija"
        self.anchor_place_id = None
        self._is_dropdown_open = False
        self._build_content()
        self._safe_update()
        if self.on_change:
            self.on_change(self.selected_destination)

    def _handle_select(self, val: str) -> None:
        self.selected_destination = val or "Nueva Ecija"
        self._search_text = self.selected_destination
        self.anchor_place_id = None
        self._is_dropdown_open = False
        self._build_content()
        self._safe_update()
        if self.on_change:
            self.on_change(self.selected_destination)

    def _handle_select_landmark(self, landmark: dict[str, str]) -> None:
        self.selected_destination = landmark["municipality"]
        self._search_text = landmark["name"]
        self.anchor_place_id = landmark["place_id"]
        self._is_dropdown_open = False
        self._build_content()
        self._safe_update()
        if self.on_landmark_select:
            self.on_landmark_select(landmark["place_id"])
        elif self.on_change:
            self.on_change(self.selected_destination)

    def _open_regional_explorer(self) -> None:
        """Opens Regional Explorer Modal with district filter tabs."""
        self._close_suggestions()
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
            is_sel = d == "All"
            btn = ft.Container(
                data=d,
                content=ft.Text(d, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE if is_sel else ThemeColors.TEXT_MAIN_LIGHT),
                bgcolor=ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.SURFACE_LIGHT,
                border_radius=12,
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                ink=True,
                on_click=lambda _, dist_name=d: set_tab(dist_name),
            )
            tab_buttons.append(btn)

        tab_row = ft.Row(controls=tab_buttons, spacing=6)

        render_lgus()

        dlg = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Text("32 Towns Regional Explorer", size=18, weight=ft.FontWeight.W_800),
                    ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda _: pick_and_close(self.selected_destination)),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            content=ft.Container(
                width=520,
                content=ft.Column(
                    controls=[
                        tab_row,
                        ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                        content_container,
                    ],
                    spacing=10,
                    tight=True,
                ),
            ),
        )

        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
