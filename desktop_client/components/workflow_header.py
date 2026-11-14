"""Nueva Ecija Travel — Contextual Workflow Header Bar (.figma-header-bar).

Used on workflow views (/suggested, /builder, /trips/:id) that hide the bottom tab bar.
Provides back navigation, workflow title, subtitle, and contextual actions.
"""

from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors, ThemePalette


class WorkflowHeader(ft.Container):
    """Contextual header bar matching web .figma-header-bar for modal workflow views."""

    def __init__(
        self,
        title: str,
        subtitle: Optional[str] = None,
        on_back: Optional[Callable[[], None]] = None,
        actions: Optional[list[ft.Control]] = None,
    ):
        super().__init__()
        self.title_text = title
        self.subtitle_text = subtitle
        self.on_back = on_back
        self.actions_controls = actions or []

        self.height = 54
        self.expand = False
        self.padding = ft.Padding.symmetric(horizontal=16, vertical=6)

        self._build_content()

    @property
    def safe_page(self) -> Optional[ft.Page]:
        try:
            return self.page
        except Exception:
            return None

    def _get_is_dark(self) -> bool:
        p = self.safe_page
        if p and p.theme_mode == ft.ThemeMode.DARK:
            return True
        return False

    def _build_content(self) -> None:
        is_dark = self._get_is_dark()
        palette = ThemePalette.get_palette(is_dark)

        self.bgcolor = palette.surface_card
        self.border = ft.Border.only(
            bottom=ft.BorderSide(1.0, palette.border_main)
        )

        back_btn = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            icon_size=20,
            icon_color=palette.text_primary,
            tooltip="Back",
            on_click=lambda _: self.on_back() if self.on_back else None,
        )

        title_col_controls: list[ft.Control] = [
            ft.Text(
                self.title_text,
                size=16,
                weight=ft.FontWeight.W_700,
                color=palette.text_primary,
                no_wrap=True,
            )
        ]
        if self.subtitle_text:
            title_col_controls.append(
                ft.Text(
                    self.subtitle_text,
                    size=11,
                    color=palette.text_muted,
                    no_wrap=True,
                )
            )

        title_col = ft.Column(
            controls=title_col_controls,
            spacing=1,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        left_group = ft.Row(
            controls=[back_btn, title_col],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        right_group = ft.Row(
            controls=self.actions_controls,
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.content = ft.Row(
            controls=[left_group, right_group],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
