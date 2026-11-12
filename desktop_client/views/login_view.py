"""Login and Authentication View conforming to Figma & Web client design."""

import asyncio
from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors
from desktop_client.core.api_client import ApiClientError
from desktop_client.services.auth_service import get_auth_service


class LoginView(ft.Container):
    """Traveler sign-in form with credential validation and guest fallback."""

    def __init__(self, on_navigate: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.on_navigate = on_navigate
        self.auth_service = get_auth_service()

        self.expand = True
        self.alignment = ft.Alignment(0, 0)
        self.bgcolor = ThemeColors.BG_LIGHT

        self._build_content()

    def _build_content(self) -> None:
        # Centered Brand Header
        brand_header = ft.Row(
            controls=[
                ft.Icon(
                    ft.Icons.AIRPLANEMODE_ACTIVE,
                    size=26,
                    color=ThemeColors.PRIMARY_BLUE,
                ),
                ft.Text(
                    "Trip mo, trip ko",
                    size=18,
                    weight=ft.FontWeight.W_800,
                    color=ThemeColors.PRIMARY_BLUE,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        )

        # Welcome Back Title & Subtitle
        heading_group = ft.Column(
            controls=[
                ft.Text(
                    "Welcome back!",
                    size=24,
                    weight=ft.FontWeight.W_800,
                    color=ThemeColors.TEXT_BLACK,
                ),
                ft.Text(
                    "Log in to continue your journey.",
                    size=13,
                    color=ThemeColors.TEXT_MUTED_LIGHT,
                ),
            ],
            spacing=4,
        )

        self.email_input = ft.TextField(
            label="Email Address",
            hint_text="traveler@example.com",
            prefix_icon=ft.Icons.MAIL_OUTLINE,
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            autofocus=True,
        )

        self.password_input = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.KEY,
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
        )

        self.remember_cb = ft.Checkbox(
            label="Remember me on this computer",
            value=True,
            check_color=ft.Colors.WHITE,
            active_color=ThemeColors.PRIMARY_BLUE,
        )

        self.error_text = ft.Text(
            "",
            color=ThemeColors.ERROR,
            size=12,
            weight=ft.FontWeight.W_500,
        )

        self.error_container = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=16, color=ThemeColors.ERROR),
                    self.error_text,
                ],
                spacing=8,
            ),
            bgcolor=ThemeColors.ERROR_BG,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            visible=False,
        )

        self.submit_btn = ft.Container(
            content=ft.Text("Log In", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=12,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._handle_login(),
        )

        footer_links = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Don't have an account?", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ft.TextButton(
                            content="Sign Up",
                            style=ft.ButtonStyle(color=ThemeColors.PRIMARY_BLUE),
                            on_click=lambda _: self._navigate("/signup"),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=2,
                ),
                ft.TextButton(
                    content="← Back to Welcome / Guest",
                    style=ft.ButtonStyle(color=ThemeColors.TEXT_MUTED_LIGHT),
                    on_click=lambda _: self._navigate("/welcome"),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=2,
        )

        card = ft.Container(
            content=ft.Column(
                controls=[
                    brand_header,
                    ft.Container(height=6),
                    heading_group,
                    self.error_container,
                    ft.Container(height=4),
                    self.email_input,
                    self.password_input,
                    self.remember_cb,
                    ft.Container(height=4),
                    self.submit_btn,
                    ft.Container(height=6),
                    footer_links,
                ],
                spacing=10,
                width=380,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=18,
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            padding=ft.Padding.symmetric(horizontal=32, vertical=30),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.06, "#000000"),
            ),
        )

        self.content = card

    def _show_error(self, message: str) -> None:
        self.error_text.value = message
        self.error_container.visible = True
        self.update()

    def _clear_error(self) -> None:
        self.error_container.visible = False
        self.update()

    def _handle_login(self) -> None:
        email = (self.email_input.value or "").strip()
        pwd = (self.password_input.value or "").strip()

        if not email:
            self._show_error("Please enter your email address.")
            return

        if not pwd:
            self._show_error("Password is required.")
            return

        self._clear_error()

        async def _do_login():
            try:
                await self.auth_service.login(email, pwd, remember_me=self.remember_cb.value or False)
                self._navigate("/dashboard")
            except ApiClientError as err:
                self._show_error(err.message or "Login failed. Check your credentials.")
            except Exception as ex:
                self._show_error(f"Error connecting to service: {str(ex)}")

        asyncio.run(_do_login())

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
