"""Figma travel date range selector and duration preset modal."""

from datetime import date, datetime, timedelta
from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors


def show_date_range_dialog(
    page: ft.Page,
    current_start: str,
    current_end: str,
    on_save: Callable[[str, str], None],
) -> None:
    """Opens Figma travel date picker with quick duration presets and validation."""
    today = date.today()

    # Parse current dates or default
    try:
        start_d = datetime.strptime(current_start, "%Y-%m-%d").date()
    except Exception:
        start_d = today + timedelta(days=5)

    try:
        end_d = datetime.strptime(current_end, "%Y-%m-%d").date()
    except Exception:
        end_d = start_d + timedelta(days=2)

    if end_d < start_d:
        end_d = start_d + timedelta(days=1)

    start_str = start_d.strftime("%Y-%m-%d")
    end_str = end_d.strftime("%Y-%m-%d")

    start_input = ft.TextField(
        label="Departure Date (YYYY-MM-DD)",
        value=start_str,
        hint_text="YYYY-MM-DD",
        prefix_icon=ft.Icons.CALENDAR_MONTH,
        border_radius=10,
        expand=True,
        dense=True,
    )

    end_input = ft.TextField(
        label="Return Date (YYYY-MM-DD)",
        value=end_str,
        hint_text="YYYY-MM-DD",
        prefix_icon=ft.Icons.EVENT,
        border_radius=10,
        expand=True,
        dense=True,
    )

    duration_text = ft.Text(
        f"Trip Duration: {(end_d - start_d).days + 1} Days ({(end_d - start_d).days} Nights)",
        size=12,
        weight=ft.FontWeight.BOLD,
        color=ThemeColors.PRIMARY_BLUE,
    )

    error_text = ft.Text("", size=11, color=ThemeColors.ERROR, visible=False)

    def _update_duration():
        s_val = (start_input.value or "").strip()
        e_val = (end_input.value or "").strip()
        try:
            s = datetime.strptime(s_val, "%Y-%m-%d").date()
            e = datetime.strptime(e_val, "%Y-%m-%d").date()
            if e < s:
                duration_text.value = "⚠️ Return date cannot be before departure date."
                duration_text.color = ThemeColors.ERROR
            else:
                days = (e - s).days + 1
                nights = (e - s).days
                duration_text.value = f"Trip Duration: {days} Day{'s' if days > 1 else ''} ({nights} Night{'s' if nights != 1 else ''})"
                duration_text.color = ThemeColors.PRIMARY_BLUE
                error_text.visible = False
        except Exception:
            duration_text.value = "Enter valid dates in YYYY-MM-DD format."
            duration_text.color = ThemeColors.TEXT_MUTED_LIGHT
        try:
            duration_text.update()
            error_text.update()
        except Exception:
            pass

    start_input.on_change = lambda _: _update_duration()
    end_input.on_change = lambda _: _update_duration()

    def set_preset(num_days: int):
        s = today + timedelta(days=3)
        e = s + timedelta(days=num_days - 1)
        start_input.value = s.strftime("%Y-%m-%d")
        end_input.value = e.strftime("%Y-%m-%d")
        _update_duration()
        try:
            start_input.update()
            end_input.update()
        except Exception:
            pass

    presets = [
        ("2D / 1N", 2),
        ("3D / 2N", 3),
        ("4D / 3N", 4),
        ("1 Week (7D)", 7),
    ]

    preset_buttons = []
    for label, days in presets:
        btn = ft.Container(
            content=ft.Text(label, size=11, weight=ft.FontWeight.W_600, color=ThemeColors.PRIMARY_BLUE),
            bgcolor=ThemeColors.AZURE_SOFT,
            border=ft.Border.all(1, ThemeColors.CUSTOM_CARD_BORDER),
            border_radius=14,
            padding=ft.Padding.symmetric(horizontal=10, vertical=5),
            ink=True,
            on_click=lambda _, d=days: set_preset(d),
        )
        preset_buttons.append(btn)

    preset_row = ft.Row(controls=preset_buttons, spacing=6, wrap=True)

    def close_dlg(_=None):
        dlg.open = False
        page.update()

    def apply_dates(_=None):
        s_val = (start_input.value or "").strip()
        e_val = (end_input.value or "").strip()
        try:
            s = datetime.strptime(s_val, "%Y-%m-%d").date()
            e = datetime.strptime(e_val, "%Y-%m-%d").date()
            if e < s:
                error_text.value = "Return date cannot be earlier than departure date."
                error_text.visible = True
                error_text.update()
                return
            close_dlg()
            on_save(s_val, e_val)
        except Exception:
            error_text.value = "Invalid date format. Please use YYYY-MM-DD."
            error_text.visible = True
            error_text.update()

    dlg = ft.AlertDialog(
        title=ft.Row(
            controls=[
                ft.Icon(ft.Icons.DATE_RANGE, color=ThemeColors.PRIMARY_BLUE, size=22),
                ft.Text("Select Travel Dates", size=16, weight=ft.FontWeight.BOLD),
            ],
            spacing=8,
        ),
        content=ft.Column(
            controls=[
                ft.Text("Quick Duration Presets", size=12, weight=ft.FontWeight.BOLD),
                preset_row,
                ft.Container(height=4),
                ft.Row(controls=[start_input, end_input], spacing=8),
                duration_text,
                error_text,
            ],
            spacing=10,
            width=460,
            tight=True,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=close_dlg),
            ft.FilledButton(
                content="Apply Dates",
                style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                on_click=apply_dates,
            ),
        ],
    )

    page.overlay.append(dlg)
    dlg.open = True
    page.update()
