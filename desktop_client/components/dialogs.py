"""Standard modal dialogs for venue details, custom off-grid stops, export, and confirmations."""

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors, get_settings
from desktop_client.core.export import export_to_ics, export_to_json, export_to_text
from desktop_client.models.itinerary import Itinerary, ItineraryItem
from desktop_client.models.place import Place


def show_place_detail_dialog(
    page: ft.Page,
    place: Place,
    on_add_to_day: Optional[Callable[[Place], None]] = None,
) -> None:
    """Displays comprehensive place modal with editorial summary, honest pricing,

    operating hours, Google Maps navigation link, and one-click add to schedule.
    """
    def close_dlg(_=None):
        page.pop_dialog()

    def handle_add(_=None):
        page.pop_dialog()
        if on_add_to_day:
            on_add_to_day(place)

    # Image or category hero
    if place.image_url and place.image_url.startswith("http"):
        hero_media = ft.Image(
            src=place.image_url,
            height=200,
            width=float("inf"),
            fit=ft.BoxFit.COVER,
            border_radius=8,
        )
    else:
        hero_media = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.LANDSCAPE_ROUNDED, size=48, color=ThemeColors.EMERALD_MINT),
                    ft.Text(place.formatted_category, size=13, color=ThemeColors.EMERALD_MINT),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            height=160,
            bgcolor=ThemeColors.EMERALD_DARK,
            border_radius=8,
            alignment=ft.Alignment(0, 0),
        )

    # Info rows
    info_rows: list[ft.Control] = [
        ft.Row(
            controls=[
                ft.Icon(ft.Icons.LOCATION_ON, size=16, color=ThemeColors.EMERALD_PRIMARY),
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
                ft.Text(f"Pricing: {place.formatted_cost}", size=12, weight=ft.FontWeight.W_600),
            ],
            spacing=8,
        ),
    ]

    if place.opening_hours:
        info_rows.append(
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.SCHEDULE, size=16, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ft.Text(f"Hours: {place.opening_hours}", size=12, expand=True),
                ],
                spacing=8,
            )
        )

    if place.phone:
        info_rows.append(
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PHONE, size=16, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ft.Text(f"Phone: {place.phone}", size=12),
                ],
                spacing=8,
            )
        )

    description_text = (
        place.editorial_summary
        or place.description
        or "A curated destination in the historic province of Nueva Ecija."
    )

    content_column = ft.Column(
        controls=[
            hero_media,
            ft.Container(height=4),
            ft.Text(place.name, size=18, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Text(place.formatted_category, size=11, color=ThemeColors.AZURE_DEEP),
                bgcolor=ThemeColors.AZURE_SOFT,
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
            ),
            ft.Divider(height=1),
            ft.Column(controls=info_rows, spacing=8),
            ft.Divider(height=1),
            ft.Text("About this Destination", size=13, weight=ft.FontWeight.BOLD),
            ft.Text(description_text, size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
        ],
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        width=520,
    )

    actions: list[ft.Control] = []
    if place.directions_url:
        actions.append(
            ft.FilledButton(
                content="Get Directions",
                icon=ft.Icons.DIRECTIONS,
                url=place.directions_url,
                style=ft.ButtonStyle(
                    bgcolor=ThemeColors.PRIMARY_BLUE,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
            )
        )

    if on_add_to_day:
        actions.append(
            ft.FilledButton(
                content="+ Add to Day",
                icon=ft.Icons.ADD,
                style=ft.ButtonStyle(
                    bgcolor=ThemeColors.PRIMARY_BLUE,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
                on_click=handle_add,
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
    """Modal allowing traveler to add an unlisted or off-grid venue."""
    title_field = ft.TextField(label="Venue Name *", hint_text="e.g. Hidden Farm Bistro, Sierra Madre Campsite", autofocus=True)
    notes_field = ft.TextField(label="Activity / Notes", hint_text="Special instructions, what to bring...", multiline=True, min_lines=2)
    time_field = ft.TextField(label="Planned Time", hint_text="e.g. 10:30 AM", width=180)
    duration_field = ft.TextField(label="Duration (minutes)", value="90", width=180)
    cost_field = ft.TextField(label="Estimated Cost (₱)", hint_text="e.g. 350", width=180)

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
        })

    dialog = ft.AlertDialog(
        title=ft.Text("Add Off-Grid Custom Venue", size=16, weight=ft.FontWeight.BOLD),
        content=ft.Column(
            controls=[
                ft.Text("Add a local scenic spot, meeting point, or off-grid restaurant not yet in the official POI registry.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                title_field,
                notes_field,
                ft.Row(controls=[time_field, duration_field], spacing=12),
                cost_field,
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
) -> None:
    """Modal to edit stop notes, planned time, duration, and estimated cost."""
    time_field = ft.TextField(label="Planned Time", value=item.planned_time or "", hint_text="e.g. 02:00 PM", width=180)
    duration_field = ft.TextField(label="Duration (minutes)", value=str(item.duration_minutes or 90), width=180)
    cost_val = str(item.estimated_cost_max) if item.estimated_cost_max is not None else ""
    cost_field = ft.TextField(label="Estimated Cost (₱)", value=cost_val, hint_text="e.g. 500", width=180)
    notes_field = ft.TextField(label="Traveler Notes", value=item.notes or "", multiline=True, min_lines=3)

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

        page.pop_dialog()
        on_save({
            "planned_time": (time_field.value or "").strip() or None,
            "duration_minutes": dur,
            "notes": (notes_field.value or "").strip() or None,
            "estimated_cost_min": cost,
            "estimated_cost_max": cost,
        })

    dialog = ft.AlertDialog(
        title=ft.Text(f"Edit Stop: {item.display_title}", size=15, weight=ft.FontWeight.BOLD),
        content=ft.Column(
            controls=[
                ft.Row(controls=[time_field, duration_field], spacing=12),
                cost_field,
                notes_field,
            ],
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
