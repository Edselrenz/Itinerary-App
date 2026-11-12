"""Login and Authentication View."""

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
        self.email_input = ft.TextField(
            label="Email Address",
            hint_text="traveler@example.com",
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
            autofocus=True,
        )

        self.password_input = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
        )

        self.remember_cb = ft.Checkbox(
            label="Remember me on this computer",
            value=True,
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

        self.submit_btn = ft.FilledButton(
            content="Sign In",
            icon=ft.Icons.LOGIN,
            style=ft.ButtonStyle(
                bgcolor=ThemeColors.EMERALD_PRIMARY,
                color=ft.Colors.WHITE,
                padding=ft.Padding.symmetric(vertical=14),
            ),
            on_click=lambda _: self._handle_login(),
            width=float("inf"),
        )

        card = ft.Container(
            content=ft.Column(
                controls=[
                    # Card Header
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(ft.Icons.LANDSCAPE_ROUNDED, size=28, color=ThemeColors.EMERALD_MINT),
                                bgcolor=ThemeColors.EMERALD_DARK,
                                border_radius=8,
                                padding=8,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("Welcome Back", size=18, weight=ft.FontWeight.BOLD),
                                    ft.Text("Sign in to sync your Nueva Ecija itineraries", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=1,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    self.error_container,
                    self.email_input,
                    self.password_input,
                    self.remember_cb,
                    ft.Container(height=4),
                    self.submit_btn,
                    ft.Row(
                        controls=[
                            ft.Text("Don't have an account?", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ft.TextButton(
                                content="Register",
                                on_click=lambda _: self._go_signup(),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    ft.OutlinedButton(
                        content="Continue as Guest",
                        icon=ft.Icons.PERSON_OUTLINE,
                        on_click=lambda _: self._continue_as_guest(),
                        width=float("inf"),
                    ),
                ],
                spacing=12,
            ),
            width=420,
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=16,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            padding=32,
        )

        self.content = card

    def _show_error(self, message: str) -> None:
        self.error_text.value = message
        self.error_container.visible = True
        self.submit_btn.disabled = False
        self.submit_btn.content = "Sign In"
        self.update()

    def _handle_login(self) -> None:
        email = (self.email_input.value or "").strip()
        pwd = (self.password_input.value or "").strip()

        if not email or not pwd:
            self._show_error("Please enter both email and password.")
            return

        self.error_container.visible = False
        self.submit_btn.disabled = True
        self.submit_btn.content = "Authenticating..."
        self.update()

        async def _do_login():
            try:
                await self.auth_service.login(
                    email=email,
                    password=pwd,
                    remember_me=self.remember_cb.value,
                )
                if self.on_navigate:
                    self.on_navigate("/dashboard")
            except ApiClientError as err:
                self._show_error(f"Sign in failed: {err.message}")
            except Exception as err:
                self._show_error(f"Unexpected error: {str(err)}")

        asyncio.create_task(_do_login())

    def _go_signup(self) -> None:
        if self.on_navigate:
            self.on_navigate("/signup")

    def _continue_as_guest(self) -> None:
        self.auth_service.continue_as_guest()
        if self.on_navigate:
            self.on_navigate("/dashboard")
