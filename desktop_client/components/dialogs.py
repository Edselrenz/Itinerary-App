"""Standard modal dialogs for venue details, custom off-grid stops, export, and confirmations."""

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors, get_settings
from desktop_client.core.commute_guide import get_commute_info_for_municipality
from desktop_client.core.export import export_to_ics, export_to_json, export_to_text
from desktop_client.models.itinerary import Itinerary, ItineraryItem
from desktop_client.models.place import Place
from desktop_client.services.favorites_service import get_favorites_service


def show_place_detail_dialog(
    page: ft.Page,
    place: Place,
    on_add_to_day: Optional[Callable[[Place], None]] = None,
    on_navigate: Optional[Callable[..., None]] = None,
) -> None:
    """Displays comprehensive place modal with editorial summary, honest pricing,
    operating hours, commute guide, favorites toggle, and action CTAs.
    """
    fav_service = get_favorites_service()
    is_fav = fav_service.is_favorite(place.id)

    def close_dlg(_=None):
        page.pop_dialog()

    def handle_add(_=None):
        page.pop_dialog()
        if on_add_to_day:
            on_add_to_day(place)
        elif on_navigate:
            on_navigate("/builder", pre_added_place=place)

    def handle_start_trip(_=None):
        page.pop_dialog()
        if on_navigate:
            on_navigate("/suggested")

    def toggle_fav(_=None):
        nonlocal is_fav
        is_fav = fav_service.toggle_favorite(place)
        fav_icon_btn.icon = ft.Icons.FAVORITE if is_fav else ft.Icons.FAVORITE_BORDER
        fav_icon_btn.icon_color = ft.Colors.RED_500 if is_fav else ft.Colors.WHITE
        fav_icon_btn.tooltip = "Saved in Favorites" if is_fav else "Save to Favorites"
        try:
            fav_icon_btn.update()
        except Exception:
            pass

    # Image or category hero
    img_src = place.resolved_image_path
    if img_src:
        hero_media = ft.Image(
            src=img_src,
            height=210,
            width=520,
            fit=ft.BoxFit.COVER,
            border_radius=12,
            error_content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.LANDSCAPE_ROUNDED, size=48, color=ThemeColors.PRIMARY_BLUE),
                        ft.Text(place.formatted_category, size=13, color=ThemeColors.PRIMARY_BLUE),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                height=210,
                bgcolor=ThemeColors.PRIMARY_LIGHT,
                border_radius=12,
                alignment=ft.Alignment(0, 0),
            ),
        )
    else:
        hero_media = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.LANDSCAPE_ROUNDED, size=48, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text(place.formatted_category, size=13, color=ThemeColors.PRIMARY_BLUE),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            height=210,
            bgcolor=ThemeColors.PRIMARY_LIGHT,
            border_radius=12,
            alignment=ft.Alignment(0, 0),
        )

    # Top-right favorite button overlay
    fav_icon_btn = ft.IconButton(
        icon=ft.Icons.FAVORITE if is_fav else ft.Icons.FAVORITE_BORDER,
        icon_color=ft.Colors.RED_500 if is_fav else ft.Colors.WHITE,
        icon_size=22,
        bgcolor=ft.Colors.with_opacity(0.45, "#000000"),
        tooltip="Saved in Favorites" if is_fav else "Save to Favorites",
        on_click=toggle_fav,
    )

    # Bottom-right status pill overlay
    status_text = "Open Now" if place.opening_hours else "Open Daily"
    status_color = ThemeColors.EMERALD_PRIMARY
    status_bg = ft.Colors.with_opacity(0.92, ThemeColors.SURFACE_LIGHT)

    status_pill = ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(width=7, height=7, border_radius=4, bgcolor=status_color),
                ft.Text(status_text, size=10, weight=ft.FontWeight.BOLD, color=status_color),
            ],
            spacing=5,
        ),
        bgcolor=status_bg,
        border_radius=12,
        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
        border=ft.Border.all(0.8, ThemeColors.BORDER_LIGHT),
    )

    hero_stack = ft.Stack(
        controls=[
            hero_media,
            ft.Container(
                content=fav_icon_btn,
                top=8,
                right=8,
            ),
            ft.Container(
                content=status_pill,
                bottom=10,
                right=10,
            ),
        ],
        width=520,
        height=210,
    )

    # Info rows
    info_rows: list[ft.Control] = [
        ft.Row(
            controls=[
                ft.Icon(ft.Icons.LOCATION_ON, size=16, color=ThemeColors.PRIMARY_BLUE),
                ft.Text(
                    place.address_text or f"{place.municipality_name or 'Nueva Ecija'}, Philippines",
                    size=12,
                    expand=True,
                ),
            ],
            spacing=8,
        ),
        ft.Row(
            controls=[
                ft.Icon(ft.Icons.PAYMENTS, size=16, color=ThemeColors.EMERALD_PRIMARY),
                ft.Text(f"Admission / Cost: {place.formatted_cost}", size=12, weight=ft.FontWeight.W_600),
            ],
            spacing=8,
        ),
    ]

    if place.opening_hours:
        info_rows.append(
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.SCHEDULE, size=16, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ft.Text(f"Operating Hours: {place.opening_hours}", size=12, expand=True),
                ],
                spacing=8,
            )
        )

    if place.phone:
        info_rows.append(
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PHONE, size=16, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ft.Text(f"Contact: {place.phone}", size=12),
                ],
                spacing=8,
            )
        )

    description_text = (
        place.editorial_summary
        or place.description
        or "A curated destination in the historic province of Nueva Ecija."
    )

    # Local Commute Guide Box
    commute_section: list[ft.Control] = []
    commute_info = get_commute_info_for_municipality(place.municipality_name)
    if commute_info:
        commute_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.DIRECTIONS_BUS, size=16, color=ThemeColors.PRIMARY_BLUE),
                            ft.Text("How to get there? (Local Transit Guide)", size=12, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                        ],
                        spacing=6,
                    ),
                    ft.Text(f"• Hub: {commute_info.departure_hub}", size=11, color=ThemeColors.TEXT_MAIN_LIGHT),
                    ft.Text(f"• Mode: {commute_info.transit_mode}", size=11, color=ThemeColors.TEXT_MAIN_LIGHT),
                    ft.Text(f"• Drop-off: {commute_info.drop_off_point}", size=11, color=ThemeColors.TEXT_MAIN_LIGHT),
                    ft.Row(
                        controls=[
                            ft.Text(f"• Time: {commute_info.estimated_travel_time}", size=11, color=ThemeColors.TEXT_MAIN_LIGHT),
                            ft.Text(f"• Fare: {commute_info.estimated_fare}", size=11, weight=ft.FontWeight.BOLD, color=ThemeColors.EMERALD_PRIMARY),
                        ],
                        spacing=12,
                    ),
                    ft.Container(height=2),
                    ft.Text(f"💡 Tip: {commute_info.travel_reminder}", size=11, color=ThemeColors.TEXT_MUTED_LIGHT, italic=True),
                ],
                spacing=3,
            ),
            bgcolor=ThemeColors.AZURE_SOFT,
            border=ft.Border.all(1, ThemeColors.CUSTOM_CARD_BORDER),
            border_radius=10,
            padding=10,
        )
        commute_section.append(commute_box)

    content_column = ft.Column(
        controls=[
            hero_stack,
            ft.Container(height=4),
            ft.Row(
                controls=[
                    ft.Text(place.name, size=18, weight=ft.FontWeight.BOLD, expand=True),
                    ft.Container(
                        content=ft.Text(place.formatted_category, size=10, weight=ft.FontWeight.BOLD, color=ThemeColors.AZURE_DEEP),
                        bgcolor=ThemeColors.AZURE_SOFT,
                        border_radius=6,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
            ft.Column(controls=info_rows, spacing=6),
            ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
            ft.Text("About this Destination", size=13, weight=ft.FontWeight.BOLD),
            ft.Text(description_text, size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
            *commute_section,
        ],
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        width=520,
    )

    actions: list[ft.Control] = []
    if on_navigate:
        actions.append(
            ft.FilledButton(
                content="✨ Start Trip Here",
                style=ft.ButtonStyle(
                    bgcolor=ThemeColors.PRIMARY_BLUE,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
                on_click=handle_start_trip,
            )
        )

    actions.append(
        ft.FilledButton(
            content="+ Add to Trip",
            icon=ft.Icons.ADD,
            style=ft.ButtonStyle(
                bgcolor=ThemeColors.AZURE_DEEP,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=handle_add,
        )
    )

    if place.directions_url:
        actions.append(
            ft.OutlinedButton(
                content="Directions",
                icon=ft.Icons.DIRECTIONS,
                url=place.directions_url,
            )
        )

    actions.append(ft.TextButton(content="Close", on_click=close_dlg))

    dialog = ft.AlertDialog(
        content=content_column,
        actions=actions,
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)


def show_custom_venue_dialog(
    page: ft.Page,
    on_save: Callable[[dict[str, Any]], None],
) -> None:
    """Modal allowing traveler to add an unlisted or off-grid venue with geofenced coordinate validation."""
    title_field = ft.TextField(label="Venue Name *", hint_text="e.g. Hidden Farm Bistro, Sierra Madre Campsite", autofocus=True)
    notes_field = ft.TextField(label="Activity / Notes", hint_text="Special instructions, what to bring...", multiline=True, min_lines=2)
    time_field = ft.TextField(label="Planned Time", hint_text="e.g. 10:30 AM", width=180)
    duration_field = ft.TextField(label="Duration (minutes)", value="90", width=180)
    cost_field = ft.TextField(label="Estimated Cost (₱)", hint_text="e.g. 350", width=180)

    # Optional geofenced coordinates
    lat_field = ft.TextField(label="Latitude (15.15 - 16.15)", hint_text="e.g. 15.632", width=180)
    lng_field = ft.TextField(label="Longitude (120.70 - 121.40)", hint_text="e.g. 121.144", width=180)

    error_text = ft.Text("", color=ThemeColors.ERROR, size=11, visible=False)

    def close_dlg(_=None):
        page.pop_dialog()

    def handle_save(_=None):
        val = title_field.value or ""
        if not val.strip():
            error_text.value = "Venue Name is required."
            error_text.visible = True
            page.update()
            return

        lat_val = None
        if lat_field.value and lat_field.value.strip():
            try:
                lat_val = float(lat_field.value.strip())
                if not (15.10 <= lat_val <= 16.25):
                    error_text.value = "Latitude is outside the Nueva Ecija provincial boundary (15.10 – 16.25)."
                    error_text.visible = True
                    page.update()
                    return
            except ValueError:
                error_text.value = "Latitude must be a valid decimal number."
                error_text.visible = True
                page.update()
                return

        lng_val = None
        if lng_field.value and lng_field.value.strip():
            try:
                lng_val = float(lng_field.value.strip())
                if not (120.65 <= lng_val <= 121.50):
                    error_text.value = "Longitude is outside the Nueva Ecija provincial boundary (120.65 – 121.50)."
                    error_text.visible = True
                    page.update()
                    return
            except ValueError:
                error_text.value = "Longitude must be a valid decimal number."
                error_text.visible = True
                page.update()
                return

        try:
            dur = int(duration_field.value or 90)
        except ValueError:
            dur = 90

        try:
            cost = float(cost_field.value or 0.0) if cost_field.value else None
        except ValueError:
            cost = None

        page.pop_dialog()
        on_save({
            "custom_title": val.strip(),
            "notes": (notes_field.value or "").strip() or None,
            "planned_time": (time_field.value or "").strip() or None,
            "duration_minutes": dur,
            "estimated_cost_min": cost,
            "estimated_cost_max": cost,
            "latitude": lat_val,
            "longitude": lng_val,
        })

    dialog = ft.AlertDialog(
        title=ft.Row(
            controls=[
                ft.Icon(ft.Icons.ADD_LOCATION_ALT, color=ThemeColors.PRIMARY_BLUE, size=22),
                ft.Text("Add Off-Grid Custom Venue", size=16, weight=ft.FontWeight.BOLD),
            ],
            spacing=8,
        ),
        content=ft.Column(
            controls=[
                ft.Text("Add a local scenic spot, meeting point, or off-grid restaurant not yet in the official POI registry.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                title_field,
                notes_field,
                ft.Row(controls=[time_field, duration_field], spacing=12),
                ft.Row(controls=[cost_field], spacing=12),
                ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                ft.Text("Optional Coordinates (Geofenced to Nueva Ecija)", size=11, weight=ft.FontWeight.W_600),
                ft.Row(controls=[lat_field, lng_field], spacing=12),
                error_text,
            ],
            spacing=10,
            width=460,
            tight=True,
        ),
        actions=[
            ft.TextButton(content="Cancel", on_click=close_dlg),
            ft.FilledButton(
                content="Add Venue",
                style=ft.ButtonStyle(
                    bgcolor=ThemeColors.PRIMARY_BLUE,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
                on_click=handle_save,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)


def show_edit_stop_dialog(
    page: ft.Page,
    item: ItineraryItem,
    on_save: Callable[[dict[str, Any]], None],
    available_days: Optional[list[int]] = None,
    current_day: int = 1,
) -> None:
    """Modal to edit stop notes, planned time, duration, and estimated cost."""
    time_field = ft.TextField(label="Planned Time", value=item.planned_time or "", hint_text="e.g. 02:00 PM", width=180)
    duration_field = ft.TextField(label="Duration (minutes)", value=str(item.duration_minutes or 90), width=180)
    cost_val = str(item.estimated_cost_max) if item.estimated_cost_max is not None else ""
    cost_field = ft.TextField(label="Estimated Cost (₱)", value=cost_val, hint_text="e.g. 500", width=180)
    notes_field = ft.TextField(label="Traveler Notes", value=item.notes or "", multiline=True, min_lines=3)

    day_dropdown = None
    if available_days and len(available_days) > 1:
        day_dropdown = ft.Dropdown(
            label="Move to Day",
            options=[ft.dropdown.Option(str(d), f"Day {d}") for d in available_days],
            value=str(current_day),
            width=180,
            dense=True,
        )

    def close_dlg(_=None):
        page.pop_dialog()

    def handle_save(_=None):
        try:
            dur = int(duration_field.value or 90)
        except ValueError:
            dur = 90

        try:
            cost = float(cost_field.value or 0.0) if cost_field.value else None
        except ValueError:
            cost = None

        target_day = int(day_dropdown.value) if day_dropdown and day_dropdown.value else current_day

        page.pop_dialog()
        on_save({
            "planned_time": (time_field.value or "").strip() or None,
            "duration_minutes": dur,
            "notes": (notes_field.value or "").strip() or None,
            "estimated_cost_min": cost,
            "estimated_cost_max": cost,
            "target_day": target_day,
        })

    row_controls = [time_field, duration_field]
    content_controls = [
        ft.Row(controls=row_controls, spacing=12),
        cost_field,
    ]
    if day_dropdown:
        content_controls.append(day_dropdown)
    content_controls.append(notes_field)

    dialog = ft.AlertDialog(
        title=ft.Text(f"Edit Stop: {item.display_title}", size=15, weight=ft.FontWeight.BOLD),
        content=ft.Column(
            controls=content_controls,
            spacing=10,
            width=440,
            tight=True,
        ),
        actions=[
            ft.TextButton(content="Cancel", on_click=close_dlg),
            ft.FilledButton(
                content="Save Changes",
                style=ft.ButtonStyle(
                    bgcolor=ThemeColors.PRIMARY_BLUE,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
                on_click=handle_save,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)


def show_export_dialog(page: ft.Page, itinerary: Itinerary) -> None:
    """Modal enabling export of itinerary to iCalendar (.ics), Markdown summary, or JSON."""
    status_label = ft.Text("", size=11, color=ThemeColors.SUCCESS, visible=False)

    def close_dlg(_=None):
        page.pop_dialog()

    def do_export(fmt: str):
        settings = get_settings()
        exports_dir = settings.storage_dir / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in itinerary.title if c.isalnum() or c in (" ", "_", "-")).strip()
        filename_base = f"{safe_title}_{timestamp}".replace(" ", "_")

        if fmt == "ics":
            content = export_to_ics(itinerary)
            filepath = exports_dir / f"{filename_base}.ics"
            filepath.write_text(content, encoding="utf-8")
        elif fmt == "txt":
            content = export_to_text(itinerary)
            filepath = exports_dir / f"{filename_base}.md"
            filepath.write_text(content, encoding="utf-8")
        else:
            content = export_to_json(itinerary)
            filepath = exports_dir / f"{filename_base}.json"
            filepath.write_text(content, encoding="utf-8")

        status_label.value = f"Saved to {filepath.name}"
        status_label.visible = True
        page.update()

    content_box = ft.Column(
        controls=[
            ft.Text("Export your travel itinerary to take offline or sync with your calendar:", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
            ft.Container(height=6),
            ft.FilledButton(
                content="Export as iCalendar (.ics) for Google/Apple Calendar",
                icon=ft.Icons.CALENDAR_MONTH,
                style=ft.ButtonStyle(bgcolor=ThemeColors.AZURE_PRIMARY, color=ft.Colors.WHITE),
                on_click=lambda _: do_export("ics"),
                width=float("inf"),
            ),
            ft.FilledButton(
                content="Export as Travel Dossier (Markdown / .md)",
                icon=ft.Icons.DESCRIPTION,
                style=ft.ButtonStyle(bgcolor=ThemeColors.EMERALD_PRIMARY, color=ft.Colors.WHITE),
                on_click=lambda _: do_export("txt"),
                width=float("inf"),
            ),
            ft.FilledButton(
                content="Export as Structured Data (.json)",
                icon=ft.Icons.DATA_OBJECT,
                style=ft.ButtonStyle(bgcolor=ThemeColors.SURFACE_DARK_HOVER, color=ft.Colors.WHITE),
                on_click=lambda _: do_export("json"),
                width=float("inf"),
            ),
            status_label,
        ],
        spacing=10,
        width=460,
        tight=True,
    )

    dialog = ft.AlertDialog(
        title=ft.Text("Export Itinerary", size=16, weight=ft.FontWeight.BOLD),
        content=content_box,
        actions=[ft.TextButton(content="Done", on_click=close_dlg)],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)


def show_confirm_dialog(
    page: ft.Page,
    title: str,
    message: str,
    on_confirm: Callable[[], None],
) -> None:
    """Destructive action confirmation dialog."""
    def close_dlg(_=None):
        page.pop_dialog()

    def handle_confirm(_=None):
        page.pop_dialog()
        on_confirm()

    dialog = ft.AlertDialog(
        title=ft.Text(title, size=15, weight=ft.FontWeight.BOLD),
        content=ft.Text(message, size=13),
        actions=[
            ft.TextButton(content="Cancel", on_click=close_dlg),
            ft.FilledButton(
                content="Confirm",
                style=ft.ButtonStyle(bgcolor=ThemeColors.ERROR, color=ft.Colors.WHITE),
                on_click=handle_confirm,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)
