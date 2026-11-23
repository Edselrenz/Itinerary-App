"""Welcome and Onboarding View conforming to Web & Figma design."""

from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors, ThemePalette, get_settings
from desktop_client.core.session import get_session_manager


class WelcomeView(ft.Container):
    """First-time onboarding view matching Figma Screen 1 (Standard Welcome) & Screen 3 (After-Logout)."""

    def __init__(
        self,
        on_navigate: Optional[Callable[[str], None]] = None,
        is_after_logout: bool = False,
    ):
        super().__init__()
        self.on_navigate = on_navigate
        self.is_after_logout = is_after_logout
        self.session_manager = get_session_manager()
        self.settings = get_settings()

        self.expand = True
        self.padding = 0
        self.alignment = ft.Alignment(0, 0)
        self._viewport_w: float = 0.0
        self._viewport_h: float = 0.0

        self._build_content()

    def on_resize(self, width: float, height: float) -> None:
        """Dynamically recomputes full-width mirrored skyline dimensions on window resize."""
        self._viewport_w = float(width or 0.0)
        self._viewport_h = float(height or 0.0)
        self._build_content()
        try:
            self.update()
        except Exception:
            pass

    def _get_viewport_size(self) -> tuple[float, float]:
        p = self.safe_page
        pw = self._viewport_w or (float(p.width) if (p and getattr(p, "width", None)) else 0.0)
        ph = self._viewport_h or (float(p.height) if (p and getattr(p, "height", None)) else 0.0)
        if pw <= 320:
            pw = float(self.settings.window_width or 1280)
        if ph <= 240:
            ph = float(self.settings.window_height or 840)
        return pw, ph

    def _resolve_buildings_asset(self) -> str:
        from pathlib import Path
        wide_path = self.settings.get_asset_path("welcome_hero_buildings_wide.png")
        if wide_path and Path(wide_path).is_file():
            return wide_path
        return self.settings.get_asset_path("welcome_hero_buildings.png")

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

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)

    def _continue_as_guest(self) -> None:
        self.session_manager.set_guest_mode()
        self._navigate("/dashboard")

    def _build_content(self) -> None:
        is_dark = self._get_is_dark()
        palette = ThemePalette.get_palette(is_dark)
        self.bgcolor = palette.surface_card if not is_dark else palette.bg_main

        # 1. Airplane Icon (rotated 45 deg matching Web SVG) & Brand Title
        brand_row = ft.Row(
            controls=[
                ft.Icon(
                    ft.Icons.AIRPLANEMODE_ACTIVE,
                    size=36,
                    color=ThemeColors.PRIMARY_BLUE,
                    rotate=ft.Rotate(angle=0.785398),
                ),
                ft.Text(
                    "Trip mo, trip ko",
                    size=30,
                    weight=ft.FontWeight.W_800,
                    color=palette.text_primary,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        )

        if self.is_after_logout:
            self._build_after_logout_content(brand_row, palette)
        else:
            self._build_standard_welcome_content(brand_row, palette)

    def _build_standard_welcome_content(self, brand_row: ft.Row, palette: ThemePalette) -> None:
        is_dark = self._get_is_dark()
        btn_w = 324

        hero_headline = ft.Text(
            "Your next adventure\nis waiting.",
            size=24,
            weight=ft.FontWeight.W_800,
            color=palette.text_primary,
            text_align=ft.TextAlign.CENTER,
        )

        hero_subtitle = ft.Text(
            "Get personalized itineraries, easy commutes,\nand nearby essentials.",
            size=14,
            color="#334155" if not is_dark else palette.text_muted,
            text_align=ft.TextAlign.CENTER,
        )

        login_btn = ft.Container(
            content=ft.Text("Log in", size=16, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=9999,
            width=btn_w,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._navigate("/login"),
        )

        signup_btn = ft.Container(
            content=ft.Text("Sign up", size=16, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=9999,
            width=btn_w,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._navigate("/signup"),
        )

        divider_row = ft.Row(
            controls=[
                ft.Container(expand=True, height=1, bgcolor="#cbd5e1" if not is_dark else palette.border_main),
                ft.Text("or", size=14, color="#94a3b8" if not is_dark else palette.text_muted, weight=ft.FontWeight.W_500),
                ft.Container(expand=True, height=1, bgcolor="#cbd5e1" if not is_dark else palette.border_main),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            width=btn_w,
        )

        # Continues to /guest screen matching Web App (.guest-pill-btn: 1.5px solid #0084ff, #0084ff icon & text)
        guest_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PERSON, size=18, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text("Continue as Guest", size=15, weight=ft.FontWeight.W_600, color=ThemeColors.PRIMARY_BLUE),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            border=ft.Border.all(1.5, ThemeColors.PRIMARY_BLUE),
            bgcolor=palette.surface_card,
            border_radius=9999,
            width=btn_w,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._navigate("/guest"),
        )

        action_column = ft.Column(
            controls=[
                login_btn,
                signup_btn,
                divider_row,
                guest_btn,
            ],
            spacing=13,
            width=btn_w,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Top/Center content matching Web .welcome-container (no card box, no border, no drop shadow)
        welcome_container = ft.Container(
            width=380,
            padding=ft.Padding.only(top=48, left=28, right=28, bottom=12),
            content=ft.Column(
                controls=[
                    brand_row,
                    ft.Container(height=12),
                    hero_headline,
                    ft.Container(height=4),
                    hero_subtitle,
                    ft.Container(height=22),
                    action_column,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                tight=True,
            ),
        )

        # Bottom City Skyline Silhouette (mirrored widescreen welcome_hero_buildings_wide.png) spanning 100% of screen width flush at bottom
        vw, vh = self._get_viewport_size()
        buildings_h = round(min(max(185.0, vw * (336.0 / 1848.0)), max(185.0, vh - 430.0)))
        buildings_asset = self._resolve_buildings_asset()
        bottom_buildings = ft.Container(
            content=ft.Image(
                src=buildings_asset,
                width=vw,
                height=buildings_h,
                fit=ft.BoxFit.FILL,
                filter_quality=ft.FilterQuality.HIGH,
            ),
            alignment=ft.Alignment(0, 1),
            padding=0,
            margin=0,
            width=float("inf"),
            height=buildings_h,
        )

        self.content = ft.Column(
            controls=[
                welcome_container,
                bottom_buildings,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            width=float("inf"),
            spacing=0,
        )

    def _build_after_logout_content(self, brand_row: ft.Row, palette: ThemePalette) -> None:
        is_dark = self._get_is_dark()
        btn_w = 300

        skyscraper_asset = self.settings.get_asset_path("logout_skyscrapers_blob.png")
        blob_frame = ft.Container(
            content=ft.Image(
                src=skyscraper_asset,
                width=250,
                height=135,
                fit=ft.BoxFit.CONTAIN,
            ),
            alignment=ft.Alignment(0, 0),
            margin=ft.Margin.only(top=6, bottom=12),
        )

        logout_headline = ft.Text(
            "You’re now logged out",
            size=23,
            weight=ft.FontWeight.W_800,
            color=palette.text_primary,
            text_align=ft.TextAlign.CENTER,
        )

        logout_subtitle = ft.Text(
            "Your account has been signed out. Explore as guest\nor log in again to access your saved trips and preferences.",
            size=13.5,
            color="#475569" if not is_dark else palette.text_muted,
            text_align=ft.TextAlign.CENTER,
        )

        guest_btn = ft.Container(
            content=ft.Text("Continue as Guest", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=9999,
            width=btn_w,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._continue_as_guest(),
        )

        login_btn = ft.Container(
            content=ft.Text("Log In", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=9999,
            width=btn_w,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._navigate("/login"),
        )

        action_column = ft.Column(
            controls=[
                guest_btn,
                login_btn,
            ],
            spacing=12,
            width=btn_w,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        welcome_container = ft.Container(
            width=360,
            padding=ft.Padding.only(top=36, left=24, right=24, bottom=12),
            content=ft.Column(
                controls=[
                    brand_row,
                    blob_frame,
                    logout_headline,
                    ft.Container(height=4),
                    logout_subtitle,
                    ft.Container(height=18),
                    action_column,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                tight=True,
            ),
        )

        vw, vh = self._get_viewport_size()
        buildings_h = round(min(max(180.0, vw * (336.0 / 1848.0)), max(180.0, vh - 450.0)))
        buildings_asset = self._resolve_buildings_asset()
        bottom_silhouette = ft.Container(
            content=ft.Image(
                src=buildings_asset,
                width=vw,
                height=buildings_h,
                fit=ft.BoxFit.FILL,
                filter_quality=ft.FilterQuality.HIGH,
            ),
            alignment=ft.Alignment(0, 1),
            padding=0,
            margin=0,
            width=float("inf"),
            height=buildings_h,
        )

        self.content = ft.Column(
            controls=[
                welcome_container,
                bottom_silhouette,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            width=float("inf"),
            spacing=0,
        )
