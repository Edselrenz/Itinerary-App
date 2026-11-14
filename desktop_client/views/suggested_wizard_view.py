"""Suggested Itinerary Wizard View mirroring Ionic features/itinerary/suggested-wizard/ and UC-S01-UC-S12.

Conforms 1:1 to Web App:
- View 1 (Form): "Tell us your travel details", zero Trip Title field, zero Pacing selector, Destination combobox + quick chips,
  travel dates box + helper note, daily budget input + 4 pills, preferences pills, travel mode pills, rating pills, Find Itinerary button.
- View 2 (Itinerary): Top header bar with trailing ✏️, .figma-trip-card (thumbnail + destination + days + budget/day + preference tags),
  .verified-budget-card (target budget, admission label, unpriced badge, footnote), collapsible .assumptions-info-box with structured insight cards,
  2-line day capsule bar, Day X - {Municipality} header + italic subtitle, embedded route map, leg commute badges, .figma-stop-card,
  .nearby-banner-trigger, bottom action CTAs (Accept & Save, Customize in Builder).
- View 3 (Nearby): Header title "Nearby Places", 3 capsule tabs (Restaurants, Hospital & Pharmacies, Stores),
  .figma-nearby-card with category badge + opening hours, Maps + Add to Day X buttons. Adding stays on View 3.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from typing import Callable, Optional
import uuid
import flet as ft

from desktop_client.components.destination_picker import DestinationPicker
from desktop_client.components.dialogs import show_date_range_dialog, show_place_detail_dialog
from desktop_client.components.itinerary_route_map import ItineraryRouteMap
from desktop_client.config.settings import ThemeColors, get_settings
from desktop_client.core.polyline import haversine_distance_meters
from desktop_client.models.itinerary import Itinerary, ItineraryDay, ItineraryItem
from desktop_client.models.place import Place
from desktop_client.services.itinerary_service import get_itinerary_service
from desktop_client.services.place_service import get_place_service


def parse_assumption(note: str) -> dict[str, str]:
    """Parses raw itinerary assumption string into category badge, title, and description."""
    clean = str(note).strip()
    cat = "Advice"
    title = "Travel Note"
    desc = clean

    if clean.startswith("[") and "]" in clean:
        prefix, rest = clean[1:].split("]", 1)
        p_low = prefix.strip().lower()
        title = prefix.strip()
        desc = rest.strip().lstrip(":").strip()
        if "pacing" in p_low:
            cat = "Pacing"
        elif any(k in p_low for k in ("transit", "corridor", "routing", "mode", "transport")):
            cat = "Routing"
        elif any(k in p_low for k in ("budget", "cost", "meals")):
            cat = "Budget"
        elif any(k in p_low for k in ("schedule", "time", "lunch")):
            cat = "Schedule"
        else:
            cat = title.capitalize()
    elif ":" in clean:
        prefix, rest = clean.split(":", 1)
        p_low = prefix.strip().lower()
        title = prefix.strip()
        desc = rest.strip()
        if "pacing" in p_low:
            cat = "Pacing"
        elif any(k in p_low for k in ("transit", "corridor", "routing", "mode", "transport")):
            cat = "Routing"
        elif any(k in p_low for k in ("budget", "cost", "meals")):
            cat = "Budget"
        elif any(k in p_low for k in ("schedule", "time", "lunch")):
            cat = "Schedule"
        else:
            cat = "Advice"

    return {
        "category": cat,
        "type": title.upper(),
        "title": title,
        "description": desc,
        "detail": desc,
    }


class SuggestedWizardView(ft.Container):
    """Suggested Itinerary Wizard View conforming 1:1 to Web SuggestedWizardPage."""

    def __init__(
        self,
        on_navigate: Optional[Callable[[str], None]] = None,
        anchor_place_id: Optional[str] = None,
        anchor_place: Optional[Place] = None,
        restore_draft: bool = False,
        draft_itinerary: Optional[Itinerary] = None,
        initial_destination: Optional[str] = None,
    ):
        super().__init__()
        self.on_navigate = on_navigate
        self.itinerary_service = get_itinerary_service()
        self.place_service = get_place_service()
        self.settings = get_settings()

        self.expand = True
        self.padding = ft.Padding.symmetric(horizontal=24, vertical=16)
        self.bgcolor = ThemeColors.BG_LIGHT

        # Wizard State
        self.view_mode = "form"  # 'form' | 'itinerary' | 'nearby'
        self.is_generating = False
        self.destination_val = initial_destination or "Nueva Ecija"
        self.anchor_place_id = anchor_place_id
        if anchor_place and anchor_place.municipality_name:
            self.destination_val = anchor_place.municipality_name
            self.anchor_place_id = anchor_place.id

        today = date.today()
        d2 = today + timedelta(days=2)
        self.start_date_val = today.strftime("%Y-%m-%d")
        self.end_date_val = d2.strftime("%Y-%m-%d")

        self.travel_mode_val = "car"  # 'car' | 'motorcycle' | 'transit'
        self.daily_budget_val = 3000.0
        self.pacing_val = "moderate"
        self.min_rating_val = 0.0
        self.selected_preferences: set[str] = {"food", "culture", "resort"}

        self.error_message: Optional[str] = None
        self.generated_itinerary: Optional[Itinerary] = None
        self.active_day_index = 0
        self.save_feedback: Optional[str] = None
        self.is_assumptions_expanded = False

        # Restore draft if returning from map or builder
        if (restore_draft or draft_itinerary) and not anchor_place_id:
            existing_draft = draft_itinerary or self.itinerary_service.get_active_draft_itinerary()
            if existing_draft and existing_draft.days:
                self.generated_itinerary = existing_draft
                self.view_mode = "itinerary"

        # Nearby Amenities State
        self.nearby_category = "restaurant"
        self.nearby_amenities: list[Place] = []
        self.nearby_loading = False

        self._build_content()

    def handle_back(self) -> bool:
        """Handles back button stepping through wizard state machine."""
        if self.view_mode == "nearby":
            self._return_to_itinerary()
            return True
        if self.view_mode == "itinerary" and self.generated_itinerary:
            self.view_mode = "form"
            self._build_content()
            self._safe_update()
            return True
        return False

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass

    @property
    def safe_page(self) -> Optional[ft.Page]:
        try:
            return self.page
        except Exception:
            return None

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)

    def _format_date_range_display(self, start_iso: str, end_iso: str) -> tuple[str, str]:
        """Returns ('Nov 14 – Nov 16, 2026', 'Nov 14 – Nov 16, 2026 (3 days, 2 nights)')."""
        try:
            s_d = datetime.strptime(start_iso, "%Y-%m-%d").date()
            e_d = datetime.strptime(end_iso, "%Y-%m-%d").date()
            days = (e_d - s_d).days + 1
            nights = max(0, days - 1)
            night_str = f", {nights} {'night' if nights == 1 else 'nights'}" if nights > 0 else ""
            date_str = f"{s_d.strftime('%b %d')} – {e_d.strftime('%b %d, %Y')}"
            subtitle = f"{date_str} ({days} {'day' if days == 1 else 'days'}{night_str})"
            return date_str, subtitle
        except Exception:
            return f"{start_iso} → {end_iso}", f"{start_iso} → {end_iso}"

    # =========================================================================
    # HEADER BAR (UC-S01)
    # =========================================================================
    def _build_header_bar(self) -> ft.Control:
        is_nearby = self.view_mode == "nearby"
        title_text = "Nearby Places" if is_nearby else "Suggested Itinerary"

        def _on_back(_):
            if is_nearby:
                self._return_to_itinerary()
            elif self.view_mode == "itinerary":
                self._reset_wizard()
            else:
                self._navigate("/home")

        edit_btn = ft.Container()
        if self.view_mode == "itinerary" and self.generated_itinerary:
            edit_btn = ft.IconButton(
                icon=ft.Icons.CREATE_OUTLINED,
                icon_color=ThemeColors.PRIMARY_BLUE,
                icon_size=20,
                tooltip="Change Travel Details",
                on_click=lambda _: self._reset_wizard(),
            )

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color=ThemeColors.PRIMARY_BLUE,
                        icon_size=22,
                        tooltip="Back",
                        on_click=_on_back,
                    ),
                    ft.Text(title_text, size=20, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                    edit_btn,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.only(bottom=ft.BorderSide(1, ThemeColors.BORDER_LIGHT)),
            padding=ft.Padding.symmetric(horizontal=16, vertical=8),
            margin=ft.Margin.only(bottom=14),
        )

    def _build_content(self) -> None:
        header = self._build_header_bar()
        if self.is_generating:
            body = self._build_generating_view()
        elif self.view_mode == "nearby":
            body = self._build_nearby_view()
        elif self.generated_itinerary and self.view_mode == "itinerary":
            body = self._build_result_view()
        else:
            body = self._build_wizard_form()

        self.content = ft.Column(
            controls=[header, ft.Container(content=body, expand=True)],
            spacing=0,
            expand=True,
        )

    # =========================================================================
    # VIEW 1: WIZARD FORM (UC-S02 - UC-S06)
    # =========================================================================
    def _build_wizard_form(self) -> ft.Control:
        # Heading: "Tell us your travel details"
        heading = ft.Text(
            "Tell us your travel details",
            size=22,
            weight=ft.FontWeight.W_800,
            color=ThemeColors.TEXT_BLACK,
        )

        # 1. Destination
        dest_picker = DestinationPicker(
            value=self.destination_val,
            on_change=lambda val: setattr(self, "destination_val", val),
            on_landmark_select=lambda pid: setattr(self, "anchor_place_id", pid),
        )
        dest_block = ft.Column(
            controls=[
                ft.Text("Destination", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                dest_picker,
            ],
            spacing=6,
        )

        # 2. Travel Dates Trigger Box & Pop-Up Modal
        date_range_str, date_sub_str = self._format_date_range_display(self.start_date_val, self.end_date_val)
        date_trigger_box = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CALENDAR_MONTH, color=ThemeColors.PRIMARY_BLUE, size=20),
                    ft.Text(date_range_str, size=13, weight=ft.FontWeight.W_600, color=ThemeColors.TEXT_BLACK),
                ],
                spacing=10,
            ),
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, "#cbd5e1"),
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            ink=True,
            on_click=lambda _: self._open_dates_picker(),
        )
        date_helper_note = ft.Text(date_sub_str, size=11, color=ThemeColors.TEXT_FAINT_LIGHT)
        dates_block = ft.Column(
            controls=[
                ft.Text("Travel Dates", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                date_trigger_box,
                date_helper_note,
            ],
            spacing=4,
        )

        # 3. Daily Budget Input & 4 Preset Chips
        self._budget_tf = ft.TextField(
            value=str(int(self.daily_budget_val)),
            prefix_icon=ft.Icons.PAYMENTS_OUTLINED,
            hint_text="₱ Amount per day",
            dense=True,
            border_radius=10,
            border_color="#cbd5e1",
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            on_change=lambda e: self._on_budget_change(e.control.value),
        )

        budget_presets = [1500, 2500, 4000, 6000]
        budget_chips: list[ft.Control] = []
        for b_val in budget_presets:
            is_b = int(self.daily_budget_val) == b_val
            b_chip = ft.Container(
                content=ft.Text(
                    f"₱{b_val:,}",
                    size=11,
                    weight=ft.FontWeight.BOLD if is_b else ft.FontWeight.W_500,
                    color=ft.Colors.WHITE if is_b else ThemeColors.TEXT_MAIN_LIGHT,
                ),
                bgcolor=ThemeColors.PRIMARY_BLUE if is_b else ThemeColors.SURFACE_LIGHT,
                border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_b else ThemeColors.BORDER_LIGHT),
                border_radius=14,
                padding=ft.Padding.symmetric(horizontal=14, vertical=6),
                ink=True,
                on_click=lambda _, v=b_val: self._set_budget(v),
            )
            budget_chips.append(b_chip)

        budget_block = ft.Column(
            controls=[
                ft.Text("Daily Budget", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                self._budget_tf,
                ft.Row(controls=budget_chips, spacing=8),
            ],
            spacing=6,
        )

        # 4. Preferences (optional) — 5 text-only pill buttons
        pref_options = [
            ("nature", "Nature & Parks"),
            ("food", "Food Trip"),
            ("culture", "Culture & History"),
            ("shopping", "Shopping"),
            ("resort", "Resort"),
        ]
        pref_chips: list[ft.Control] = []
        for p_key, p_lbl in pref_options:
            is_p = p_key in self.selected_preferences

            def _toggle_pref(_, pk=p_key):
                if pk in self.selected_preferences:
                    self.selected_preferences.remove(pk)
                else:
                    self.selected_preferences.add(pk)
                self._build_content()
                self._safe_update()

            pref_chips.append(
                ft.Container(
                    content=ft.Text(
                        p_lbl,
                        size=12,
                        weight=ft.FontWeight.BOLD if is_p else ft.FontWeight.W_500,
                        color=ft.Colors.WHITE if is_p else ThemeColors.TEXT_MAIN_LIGHT,
                    ),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_p else ThemeColors.SURFACE_LIGHT,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_p else ThemeColors.BORDER_LIGHT),
                    border_radius=16,
                    padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                    ink=True,
                    on_click=_toggle_pref,
                )
            )

        pref_block = ft.Column(
            controls=[
                ft.Text("Preferences (optional)", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                ft.Row(controls=pref_chips, wrap=True, spacing=8, run_spacing=6),
            ],
            spacing=6,
        )

        # 5. Travel Mode — 3 icon+label pills
        mode_options = [
            ("car", "Drive / Car", ft.Icons.DIRECTIONS_CAR),
            ("motorcycle", "Motorcycle / Tricycle", ft.Icons.TWO_WHEELER),
            ("transit", "Walking / Transit", ft.Icons.DIRECTIONS_WALK),
        ]
        mode_chips: list[ft.Control] = []
        for m_key, m_lbl, m_ic in mode_options:
            is_m = self.travel_mode_val == m_key

            def _pick_mode(_, mk=m_key):
                self.travel_mode_val = mk
                self._build_content()
                self._safe_update()

            mode_chips.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(m_ic, size=14, color=ft.Colors.WHITE if is_m else ThemeColors.PRIMARY_BLUE),
                            ft.Text(
                                m_lbl,
                                size=11,
                                weight=ft.FontWeight.BOLD if is_m else ft.FontWeight.W_500,
                                color=ft.Colors.WHITE if is_m else ThemeColors.TEXT_MAIN_LIGHT,
                            ),
                        ],
                        spacing=6,
                        tight=True,
                    ),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_m else ThemeColors.SURFACE_LIGHT,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_m else ThemeColors.BORDER_LIGHT),
                    border_radius=16,
                    padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                    ink=True,
                    on_click=_pick_mode,
                )
            )

        mode_block = ft.Column(
            controls=[
                ft.Text("Travel Mode", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                ft.Row(controls=mode_chips, wrap=True, spacing=8),
            ],
            spacing=6,
        )

        # 6. Minimum Place Rating — 3 pills
        rating_options = [
            (0.0, "All Ratings"),
            (4.0, "★ 4.0+ ★"),
            (4.5, "★ 4.5+ ★"),
        ]
        rating_chips: list[ft.Control] = []
        for r_val, r_lbl in rating_options:
            is_r = self.min_rating_val == r_val

            def _pick_rating(_, rv=r_val):
                self.min_rating_val = rv
                self._build_content()
                self._safe_update()

            rating_chips.append(
                ft.Container(
                    content=ft.Text(
                        r_lbl,
                        size=11,
                        weight=ft.FontWeight.BOLD if is_r else ft.FontWeight.W_500,
                        color=ft.Colors.WHITE if is_r else ThemeColors.TEXT_MAIN_LIGHT,
                    ),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_r else ThemeColors.SURFACE_LIGHT,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_r else ThemeColors.BORDER_LIGHT),
                    border_radius=14,
                    padding=ft.Padding.symmetric(horizontal=14, vertical=7),
                    ink=True,
                    on_click=_pick_rating,
                )
            )

        rating_block = ft.Column(
            controls=[
                ft.Text("Minimum Place Rating", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                ft.Row(controls=rating_chips, spacing=8),
            ],
            spacing=6,
        )

        # Error Banner
        error_banner = ft.Container(
            visible=bool(self.error_message),
            bgcolor=ThemeColors.ERROR_BG,
            border_radius=8,
            padding=10,
            content=ft.Text(self.error_message or "", size=12, color=ThemeColors.ERROR),
        )

        # 7. Action CTA: "Find Itinerary"
        submit_btn = ft.Container(
            content=ft.Text("Find Itinerary", size=15, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=10,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._start_generation(),
        )

        form_card = ft.Container(
            width=680,
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=18,
            padding=24,
            content=ft.Column(
                controls=[
                    heading,
                    ft.Container(height=12),
                    dest_block,
                    ft.Container(height=6),
                    dates_block,
                    ft.Container(height=6),
                    budget_block,
                    ft.Container(height=6),
                    pref_block,
                    ft.Container(height=6),
                    mode_block,
                    ft.Container(height=6),
                    rating_block,
                    ft.Container(height=8),
                    error_banner,
                    ft.Container(height=4),
                    submit_btn,
                ],
                spacing=8,
            ),
        )

        return ft.Column(
            controls=[form_card],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _toggle_preference(self, pref: str) -> None:
        if pref in self.selected_preferences:
            self.selected_preferences.remove(pref)
        else:
            self.selected_preferences.add(pref)
        self._build_content()
        self._safe_update()

    def _on_budget_change(self, val: str) -> None:
        try:
            cleaned = "".join(c for c in val if c.isdigit())
            if cleaned:
                self.daily_budget_val = float(cleaned)
        except Exception:
            pass

    def _set_budget(self, val: int) -> None:
        self.daily_budget_val = float(val)
        if hasattr(self, "_budget_tf"):
            self._budget_tf.value = str(val)
        self._build_content()
        self._safe_update()

    def _open_dates_picker(self) -> None:
        if self.safe_page:
            show_date_range_dialog(
                self.safe_page,
                self.start_date_val,
                self.end_date_val,
                on_apply=self._on_dates_picked,
            )

    def _on_dates_picked(self, s: str, e: str) -> None:
        self.start_date_val = s
        self.end_date_val = e
        self._build_content()
        self._safe_update()

    # =========================================================================
    # GENERATING VIEW
    # =========================================================================
    def _build_generating_view(self) -> ft.Control:
        return ft.Container(
            expand=True,
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                controls=[
                    ft.ProgressRing(width=56, height=56, stroke_width=4, color=ThemeColors.PRIMARY_BLUE),
                    ft.Container(height=14),
                    ft.Text("Generating Clustered Itinerary...", size=20, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                    ft.Text(f"Clustering stops around {self.destination_val} across Nueva Ecija", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
            ),
        )

    def _start_generation(self) -> None:
        self.is_generating = True
        self.error_message = None
        self._build_content()
        self._safe_update()

        async def _run():
            try:
                auto_title = f"Suggested {self.destination_val} Trip"
                itinerary = await self.itinerary_service.generate_suggested_itinerary(
                    destination=self.destination_val,
                    start_date=self.start_date_val,
                    end_date=self.end_date_val,
                    pacing=self.pacing_val,
                    daily_budget=self.daily_budget_val,
                    preferences=list(self.selected_preferences),
                    travel_mode=self.travel_mode_val,
                    min_rating=self.min_rating_val,
                    anchor_place_id=self.anchor_place_id,
                )
                if itinerary:
                    itinerary.title = auto_title
                    self.generated_itinerary = itinerary
                    self.itinerary_service.set_active_draft_itinerary(itinerary)
                    self.view_mode = "itinerary"
                    self.active_day_index = 0
                else:
                    self.error_message = "Could not generate an itinerary. Please adjust your criteria and try again."
                    self.view_mode = "form"
            except Exception as e:
                self.error_message = str(e)
                self.view_mode = "form"
            finally:
                self.is_generating = False
                self._build_content()
                self._safe_update()

        if self.safe_page:
            self.safe_page.run_task(_run)
        else:
            try:
                asyncio.get_running_loop().create_task(_run())
            except RuntimeError:
                pass

    # =========================================================================
    # VIEW 2: ITINERARY RESULT VIEW (UC-S07 - UC-S12)
    # =========================================================================
    def _build_result_view(self) -> ft.Control:
        itin = self.generated_itinerary
        if not itin:
            return ft.Container()

        num_days = len(itin.days) if itin.days else 1

        # 1. .figma-trip-card (UC-S07)
        arch_img_path = self.settings.get_asset_path("images/nueva_ecija_arch.png")
        trip_card = ft.Container(
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=16,
            padding=16,
            content=ft.Row(
                controls=[
                    ft.Image(
                        src=arch_img_path,
                        width=76,
                        height=76,
                        fit=ft.BoxFit.COVER,
                        border_radius=10,
                        error_content=ft.Icon(ft.Icons.LANDSCAPE, size=32, color=ThemeColors.PRIMARY_BLUE),
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(itin.destination or "Nueva Ecija", size=18, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                            ft.Row(
                                controls=[
                                    ft.Text(f"{num_days} {'day' if num_days == 1 else 'days'}", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                                    ft.Text("•", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                                    ft.Text(f"₱ {itin.daily_budget:,.0f}/day", size=12, weight=ft.FontWeight.BOLD, color=ThemeColors.EMERALD_PRIMARY),
                                ],
                                spacing=6,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Text(p.title(), size=10, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                                        bgcolor=ThemeColors.PRIMARY_LIGHT,
                                        border_radius=6,
                                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                    )
                                    for p in (itin.preferences or list(self.selected_preferences))[:3]
                                ],
                                spacing=6,
                            ),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                ],
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # 2. .verified-budget-card (UC-S07)
        budget_summary = self.itinerary_service.calculate_budget_summary(itin)
        unpriced_count = budget_summary.get("unpriced_count", 0)
        display_cost = budget_summary.get("display_text", "Free Admission")

        verified_card = ft.Container(
            bgcolor="#f0fdf4",
            border=ft.Border.all(1, "#bbf7d0"),
            border_radius=16,
            padding=16,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("🛡️", size=14),
                                    ft.Text("Verified Estimated Costs", size=13, weight=ft.FontWeight.BOLD, color="#166534"),
                                ],
                                spacing=6,
                            ),
                            ft.Text(f"Target: ₱{itin.daily_budget:,.0f}/day", size=11, color="#166534"),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(display_cost, size=20, weight=ft.FontWeight.W_800, color="#15803d"),
                            ft.Text("estimated venue admission & activities", size=11, color="#166534"),
                            ft.Container(
                                visible=unpriced_count > 0,
                                content=ft.Text(f"ⓘ {unpriced_count} unpriced", size=10, weight=ft.FontWeight.BOLD, color="#15803d"),
                                bgcolor="#dcfce7",
                                border_radius=6,
                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                            ),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(
                        f"* {unpriced_count} stop(s) do not list verified pricing in open public records." if unpriced_count > 0 else "All stops have verified open pricing.",
                        size=10,
                        color="#166534",
                        italic=True,
                    ),
                ],
                spacing=6,
            ),
        )

        # 3. Collapsible Trip Assumptions & Structured Insight Cards (UC-S08)
        assumptions = itin.assumptions or [
            "Pacing: Moderate • Balanced stops and driving intervals",
            "Routing: Geographic corridor clustering around municipal hubs",
            "Budget: Target budget allocation includes activities and admission",
            "Schedule: 12:00 PM – 1:00 PM lunch stop window",
        ]

        insight_cards = []
        for a_note in assumptions:
            parsed = parse_assumption(a_note)
            insight_cards.append(
                ft.Container(
                    bgcolor=ThemeColors.SURFACE_LIGHT,
                    border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
                    border_radius=10,
                    padding=10,
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(parsed["category"], size=10, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                                bgcolor=ThemeColors.AZURE_SOFT,
                                border_radius=6,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(parsed["title"], size=12, weight=ft.FontWeight.BOLD),
                                    ft.Text(parsed["description"], size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                    ),
                )
            )

        assumptions_box = ft.Container(
            bgcolor=ThemeColors.AZURE_SOFT,
            border=ft.Border.all(1, ThemeColors.CUSTOM_CARD_BORDER),
            border_radius=14,
            padding=14,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.EXPLORE, size=18, color=ThemeColors.PRIMARY_BLUE),
                                    ft.Text("Trip Assumptions & Travel Notes", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                                ],
                                spacing=8,
                            ),
                            ft.TextButton(
                                "Hide" if self.is_assumptions_expanded else f"View {len(assumptions)}",
                                on_click=lambda _: self._toggle_assumptions(),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Column(controls=insight_cards, spacing=6, visible=self.is_assumptions_expanded),
                ],
                spacing=8,
            ),
        )

        # 4. Segmented Day Switcher Capsule Bar (UC-S09)
        day_capsules: list[ft.Control] = []
        for idx, day in enumerate(itin.days):
            is_active = idx == self.active_day_index
            day_loc = "Nueva Ecija"
            if day.items and day.items[0].place and day.items[0].place.municipality_name:
                day_loc = day.items[0].place.municipality_name
            elif day.title and ": " in day.title:
                day_loc = day.title.split(": ")[1]

            day_capsules.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(f"Day {day.day_number}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE if is_active else ThemeColors.TEXT_BLACK),
                            ft.Text(day_loc, size=10, color=ft.Colors.WHITE if is_active else ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        spacing=1,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_active else ft.Colors.WHITE,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_active else ThemeColors.BORDER_LIGHT),
                    border_radius=12,
                    padding=ft.Padding.symmetric(horizontal=16, vertical=8),
                    ink=True,
                    on_click=lambda _, day_idx=idx: self._select_day(day_idx),
                )
            )

        capsule_bar = ft.Row(controls=day_capsules, spacing=8, scroll=ft.ScrollMode.AUTO)

        # Active Day Header & Route Map (UC-S09, UC-S10)
        active_day = itin.days[self.active_day_index] if itin.days else None
        active_muni = "Nueva Ecija"
        if active_day and active_day.items and active_day.items[0].place and active_day.items[0].place.municipality_name:
            active_muni = active_day.items[0].place.municipality_name

        day_heading_block = ft.Column(
            controls=[
                ft.Text(f"Day {active_day.day_number if active_day else 1} - {active_muni}", size=18, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                ft.Text(f"Food spots, local culture, and historic sites in {active_muni}!", size=12, italic=True, color=ThemeColors.TEXT_MUTED_LIGHT),
            ],
            spacing=2,
        )

        route_map = ItineraryRouteMap(
            day=active_day,
            on_view_full_map=lambda: self._open_full_map_draft(),
            on_stop_click=lambda idx, pin: show_place_detail_dialog(self.safe_page, pin.place, on_navigate=self.on_navigate) if (pin.place and self.safe_page) else None,
        )

        # Stop Cards & Inter-Stop Leg Commute Badges (UC-S10)
        timeline_controls: list[ft.Control] = []
        if active_day and active_day.items:
            for idx, item in enumerate(active_day.items):
                if idx > 0:
                    prev_item = active_day.items[idx - 1]
                    dist_km = (item.travel_distance_meters or 4200) / 1000.0
                    drive_mins = max(5, int((item.travel_duration_seconds or 600) / 60))
                    trike_mins = int(drive_mins * 1.3)
                    fare_min = int(25 + dist_km * 12)
                    fare_max = int(fare_min * 1.5)

                    timeline_controls.append(
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Text("🚗", size=12),
                                    ft.Text(
                                        f"{dist_km:.1f} km • ~{drive_mins} mins drive / {trike_mins} mins tricycle • Est. Fare ₱{fare_min}–₱{fare_max}",
                                        size=11,
                                        weight=ft.FontWeight.W_600,
                                        color=ThemeColors.PRIMARY_BLUE,
                                    ),
                                ],
                                spacing=6,
                            ),
                            bgcolor=ThemeColors.AZURE_SOFT,
                            border_radius=8,
                            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                            margin=ft.Margin.only(left=20, top=2, bottom=2),
                        )
                    )

                timeline_controls.append(self._build_figma_stop_card(item, idx))

        # Bottom .nearby-banner-trigger (UC-S11)
        nearby_trigger = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.NEAR_ME_ROUNDED, size=22, color=ThemeColors.PRIMARY_BLUE),
                    ft.Column(
                        controls=[
                            ft.Text(f"Nearby Places in {active_muni}", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.TEXT_BLACK),
                            ft.Text("Find nearby restaurants, pharmacies, and stores", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.ARROW_FORWARD, size=18, color=ThemeColors.PRIMARY_BLUE),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=14,
            padding=14,
            ink=True,
            on_click=lambda _: self._open_nearby_view(),
        )

        # Bottom Action CTAs (UC-S12)
        bottom_actions = ft.Row(
            controls=[
                ft.FilledButton(
                    content="✓ Accept & Save Itinerary",
                    style=ft.ButtonStyle(
                        bgcolor="#10b981",
                        color=ft.Colors.WHITE,
                        padding=ft.Padding.symmetric(horizontal=20, vertical=12),
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    on_click=lambda _: self._save_generated_itinerary(),
                ),
                ft.OutlinedButton(
                    content="✏️ Customize in Builder",
                    style=ft.ButtonStyle(
                        color=ThemeColors.PRIMARY_BLUE,
                        padding=ft.Padding.symmetric(horizontal=18, vertical=12),
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    on_click=lambda _: self._customize_in_builder(),
                ),
            ],
            spacing=12,
        )

        return ft.Column(
            controls=[
                trip_card,
                ft.Container(height=10),
                verified_card,
                ft.Container(height=10),
                assumptions_box,
                ft.Container(height=12),
                capsule_bar,
                ft.Container(height=14),
                day_heading_block,
                ft.Container(height=8),
                route_map,
                ft.Container(height=12),
                ft.Column(controls=timeline_controls, spacing=6),
                ft.Container(height=12),
                nearby_trigger,
                ft.Container(height=12),
                bottom_actions,
                ft.Container(height=24),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_figma_stop_card(self, item: ItineraryItem, idx: int) -> ft.Control:
        p = item.place
        title = item.custom_title or (p.name if p else f"Stop {idx + 1}")
        rating_val = p.rating if (p and p.rating) else 4.5
        rev_count = getattr(p, "user_rating_count", None) or getattr(p, "reviews_count", None) or 120
        time_text = item.planned_time or "09:30 AM - 11:30 AM (2 hrs)"
        img_src = p.resolved_image_path if p else ""

        return ft.Container(
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=14,
            padding=12,
            ink=True,
            on_click=lambda _: show_place_detail_dialog(self.safe_page, p, on_navigate=self.on_navigate) if (p and self.safe_page) else None,
            content=ft.Row(
                controls=[
                    ft.Image(
                        src=img_src,
                        width=68,
                        height=68,
                        fit=ft.BoxFit.COVER,
                        border_radius=8,
                        error_content=ft.Icon(ft.Icons.LANDSCAPE, size=24, color=ThemeColors.PRIMARY_BLUE),
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(f"{idx + 1}. {title}", size=14, weight=ft.FontWeight.W_700, color=ThemeColors.TEXT_BLACK),
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Text(f"★ {rating_val:.1f} ({rev_count})", size=10, weight=ft.FontWeight.BOLD, color="#d97706"),
                                        bgcolor="#fef3c7",
                                        border_radius=4,
                                        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                    ),
                                    ft.Text(p.municipality_name or "Nueva Ecija" if p else "Nueva Ecija", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=6,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.SCHEDULE, size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                                    ft.Text(time_text, size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=4,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    # =========================================================================
    # VIEW 3: NEARBY PLACES VIEW (UC-S11)
    # =========================================================================
    def _build_nearby_view(self) -> ft.Control:
        active_day = self.generated_itinerary.days[self.active_day_index] if self.generated_itinerary else None
        day_num = active_day.day_number if active_day else 1

        intro_text = ft.Text(
            "Find nearby restaurants, pharmacies, and stores to make your trip more convenient and comfortable.",
            size=12,
            color=ThemeColors.TEXT_MUTED_LIGHT,
        )

        # 3 Capsule Tabs (Restaurants, Hospital & Pharmacies, Stores)
        tabs = [
            ("restaurant", "Restaurants"),
            ("hospital", "Hospital & Pharmacies"),
            ("store", "Stores"),
        ]
        tab_buttons = []
        for t_key, t_label in tabs:
            is_sel = self.nearby_category == t_key
            tab_buttons.append(
                ft.Container(
                    content=ft.Text(
                        t_label,
                        size=12,
                        weight=ft.FontWeight.BOLD if is_sel else ft.FontWeight.W_500,
                        color=ft.Colors.WHITE if is_sel else ThemeColors.TEXT_MAIN_LIGHT,
                    ),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.SURFACE_LIGHT,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_sel else ThemeColors.BORDER_LIGHT),
                    border_radius=16,
                    padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                    ink=True,
                    on_click=lambda _, tk=t_key: self._set_nearby_category(tk),
                )
            )

        tabs_row = ft.Row(controls=tab_buttons, spacing=8)

        cards_col = ft.Column(spacing=10)
        if self.nearby_loading:
            cards_col.controls = [
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.ProgressRing(width=20, height=20, stroke_width=2),
                            ft.Text("Locating nearby amenities...", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        spacing=10,
                    ),
                    padding=20,
                )
            ]
        elif self.nearby_amenities:
            for idx, p in enumerate(self.nearby_amenities):
                cards_col.controls.append(self._build_figma_nearby_card(p, idx, day_num))
        else:
            cards_col.controls = [
                ft.Container(
                    content=ft.Text("No amenities found in this category.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                    padding=20,
                )
            ]

        return ft.Column(
            controls=[
                intro_text,
                ft.Container(height=8),
                tabs_row,
                ft.Container(height=12),
                cards_col,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_figma_nearby_card(self, p: Place, idx: int, day_num: int) -> ft.Control:
        hours_str = p.opening_hours or "Open Daily"
        maps_url = p.directions_url or f"https://www.google.com/maps/dir/?api=1&destination={p.latitude},{p.longitude}"
        cat_badge_label = "Restaurant" if "restaurant" in (p.category or "").lower() else ("Health & Pharmacy" if "pharmacy" in (p.category or "").lower() or "hospital" in (p.category or "").lower() else "Retail & Store")

        return ft.Container(
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=12,
            padding=12,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(cat_badge_label, size=10, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                                bgcolor=ThemeColors.AZURE_SOFT,
                                border_radius=6,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                            ),
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.SCHEDULE, size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                                    ft.Text(hours_str, size=10, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=4,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(f"{idx + 1}. {p.name}", size=14, weight=ft.FontWeight.W_700, color=ThemeColors.TEXT_BLACK),
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.LOCATION_ON, size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ft.Text(p.municipality_name or "Nueva Ecija", size=11, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ],
                        spacing=4,
                    ),
                    ft.Row(
                        controls=[
                            ft.OutlinedButton(
                                content="Maps",
                                icon=ft.Icons.MAP_OUTLINED,
                                style=ft.ButtonStyle(
                                    color=ThemeColors.PRIMARY_BLUE,
                                    padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                                ),
                                on_click=lambda _, url=maps_url: self.safe_page.launch_url(url) if self.safe_page else None,
                            ),
                            ft.FilledButton(
                                content=f"Add to Day {day_num}",
                                style=ft.ButtonStyle(
                                    bgcolor=ThemeColors.PRIMARY_BLUE,
                                    color=ft.Colors.WHITE,
                                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                                ),
                                on_click=lambda _, pl=p: self._inject_nearby_to_day(pl),
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=6,
            ),
        )

    def _open_nearby_view(self) -> None:
        self.view_mode = "nearby"
        self._load_nearby_amenities()

    def _return_to_itinerary(self) -> None:
        self.view_mode = "itinerary"
        self._build_content()
        self._safe_update()

    def _set_nearby_category(self, cat: str) -> None:
        self.nearby_category = cat
        self._load_nearby_amenities()

    def _toggle_assumptions(self) -> None:
        self.is_assumptions_expanded = not self.is_assumptions_expanded
        self._build_content()
        self._safe_update()

    def _select_day(self, idx: int) -> None:
        self.active_day_index = idx
        self._build_content()
        self._safe_update()

    def _load_nearby_amenities(self) -> None:
        self.nearby_loading = True
        self._build_content()
        self._safe_update()

        async def _query():
            try:
                itin = self.generated_itinerary
                muni = itin.destination if itin else "Nueva Ecija"
                if itin and itin.days and self.active_day_index < len(itin.days):
                    act_day = itin.days[self.active_day_index]
                    for itm in act_day.items:
                        if itm.place and itm.place.municipality_name:
                            muni = itm.place.municipality_name
                            break
                self.nearby_amenities = self.place_service.get_nearby_places(muni, self.nearby_category)
            except Exception:
                self.nearby_amenities = []
            finally:
                self.nearby_loading = False
                self._build_content()
                self._safe_update()

        if self.safe_page:
            self.safe_page.run_task(_query)
        else:
            try:
                asyncio.get_running_loop().create_task(_query())
            except RuntimeError:
                pass

    def _inject_nearby_to_day(self, place: Place) -> None:
        """Injects a nearby essential stop into active day and stays on nearby view (UC-S11)."""
        if not self.generated_itinerary or not self.generated_itinerary.days:
            return
        active_day = self.generated_itinerary.days[self.active_day_index]
        new_order = len(active_day.items) + 1

        dist_m = None
        dur_s = None
        if active_day.items:
            last_item = active_day.items[-1]
            last_p = last_item.place
            if last_p and last_p.latitude and last_p.longitude and place.latitude and place.longitude:
                raw_dist = haversine_distance_meters(last_p.latitude, last_p.longitude, place.latitude, place.longitude)
                dist_m = int(raw_dist * 1.28)
                transit_mins = max(15, min(90, int(dist_m / 666.0) + 10))
                dur_s = transit_mins * 60
            planned_time = "04:00 PM - 05:00 PM"
        else:
            planned_time = "09:30 AM - 10:30 AM"

        new_item = ItineraryItem(
            id=str(uuid.uuid4()),
            day_id=active_day.id,
            place_id=place.id,
            place=place,
            custom_title=place.name,
            sort_order=new_order,
            planned_time=planned_time,
            duration_minutes=60,
            estimated_cost_min=place.estimated_cost_min,
            estimated_cost_max=place.estimated_cost_max,
            travel_distance_meters=dist_m,
            travel_duration_seconds=dur_s,
        )
        active_day.items.append(new_item)

        if self.safe_page:
            self.safe_page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Added {place.name} to Day {active_day.day_number}!"),
                open=True,
            )
            self.safe_page.update()

    def _save_generated_itinerary(self) -> None:
        if not self.generated_itinerary:
            return

        async def _run():
            try:
                saved = await self.itinerary_service.create_itinerary(self.generated_itinerary)
                self.itinerary_service.clear_active_draft_itinerary()
                if self.safe_page:
                    self.safe_page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Saved '{saved.title}' successfully!"),
                        open=True,
                    )
                    self.safe_page.update()
                self._navigate(f"/trips/{saved.id}")
            except Exception as e:
                if self.safe_page:
                    self.safe_page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Failed to save itinerary: {e}"),
                        open=True,
                    )
                    self.safe_page.update()

        if self.safe_page:
            self.safe_page.run_task(_run)
        else:
            try:
                asyncio.get_running_loop().create_task(_run())
            except RuntimeError:
                pass

    def _customize_in_builder(self) -> None:
        if self.generated_itinerary:
            self.itinerary_service.set_active_draft_itinerary(self.generated_itinerary)
            if self.on_navigate:
                self.on_navigate("/builder?draft=true")

    def _open_full_map_draft(self) -> None:
        if self.generated_itinerary:
            self.itinerary_service.set_active_draft_itinerary(self.generated_itinerary)
            day_num = self.active_day_index + 1
            if self.on_navigate:
                self.on_navigate(f"/map?itineraryId=draft&day={day_num}")

    def _reset_wizard(self) -> None:
        self.view_mode = "form"
        self._build_content()
        self._safe_update()
