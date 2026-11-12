"""Traveler Registration and Account Creation View conforming to Figma & Web client."""

import asyncio
from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors
from desktop_client.core.api_client import ApiClientError
from desktop_client.services.auth_service import get_auth_service


class SignupView(ft.Container):
    """Registration form allowing travelers to create a cloud account."""

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

        # Create Your Account Title & Subtitle
        heading_group = ft.Column(
            controls=[
                ft.Text(
                    "Create your account",
                    size=24,
                    weight=ft.FontWeight.W_800,
                    color=ThemeColors.TEXT_BLACK,
                ),
                ft.Text(
                    "Get started and plan your new adventure.",
                    size=13,
                    color=ThemeColors.TEXT_MUTED_LIGHT,
                ),
            ],
            spacing=4,
        )

        self.first_name_input = ft.TextField(
            label="First Name",
            hint_text="e.g. Maria",
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            expand=True,
            autofocus=True,
        )

        self.mi_input = ft.TextField(
            label="M.I.",
            hint_text="C.",
            width=70,
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
        )

        self.last_name_input = ft.TextField(
            label="Last Name",
            hint_text="e.g. Clara",
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
        )

        name_row = ft.Row(
            controls=[self.first_name_input, self.mi_input],
            spacing=8,
        )

        self.email_input = ft.TextField(
            label="Email Address",
            hint_text="traveler@example.com",
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
        )

        self.password_input = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.KEY,
            helper="At least 6 characters",
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
        )

        self.confirm_password_input = ft.TextField(
            label="Confirm Password",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_RESET,
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
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
            content=ft.Text("Create Account", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=12,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._handle_signup(),
        )

        footer_links = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Already have an account?", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                        ft.TextButton(
                            content="Log In",
                            style=ft.ButtonStyle(color=ThemeColors.PRIMARY_BLUE),
                            on_click=lambda _: self._navigate("/login"),
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
                    ft.Container(height=4),
                    heading_group,
                    self.error_container,
                    name_row,
                    self.last_name_input,
                    self.email_input,
                    self.password_input,
                    self.confirm_password_input,
                    ft.Container(height=4),
                    self.submit_btn,
                    ft.Container(height=4),
                    footer_links,
                ],
                spacing=8,
                width=400,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=18,
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            padding=ft.Padding.symmetric(horizontal=32, vertical=28),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.06, "#000000"),
            ),
        )

        self.content = card

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass

    def _show_error(self, message: str) -> None:
        self.error_text.value = message
        self.error_container.visible = True
        self._safe_update()

    def _clear_error(self) -> None:
        self.error_container.visible = False
        self._safe_update()

    def _handle_signup(self) -> None:
        first_name = (self.first_name_input.value or "").strip()
        last_name = (self.last_name_input.value or "").strip()
        full_name = f"{first_name} {last_name}".strip() or "Traveler"
        email = (self.email_input.value or "").strip()
        pwd = (self.password_input.value or "").strip()
        confirm_pwd = (self.confirm_password_input.value or "").strip()

        if not first_name:
            self._show_error("First name is required.")
            return

        if not last_name:
            self._show_error("Last name is required.")
            return

        if not email:
            self._show_error("Email address is required.")
            return

        if len(pwd) < 6:
            self._show_error("Password must be at least 6 characters.")
            return

        if pwd != confirm_pwd:
            self._show_error("Passwords do not match.")
            return

        self._clear_error()

        async def _do_signup():
            try:
                await self.auth_service.register(
                    email=email,
                    password=pwd,
                    full_name=full_name,
                )
                self._navigate("/dashboard")
            except ApiClientError as err:
                self._show_error(err.message or "Registration failed. Try another email.")
            except Exception as ex:
                self._show_error(f"Error connecting to service: {str(ex)}")

        asyncio.run(_do_signup())

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
