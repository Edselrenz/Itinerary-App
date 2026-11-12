"""Traveler Registration and Account Creation View."""

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
        self.name_input = ft.TextField(
            label="Full Name",
            hint_text="e.g. Maria Clara",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            autofocus=True,
        )

        self.email_input = ft.TextField(
            label="Email Address",
            hint_text="traveler@example.com",
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
        )

        self.password_input = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            helper_text="At least 6 characters",
        )

        self.confirm_password_input = ft.TextField(
            label="Confirm Password",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_RESET,
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
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            visible=False,
        )

        self.submit_btn = ft.FilledButton(
            content="Create Account",
            icon=ft.Icons.PERSON_ADD,
            style=ft.ButtonStyle(
                bgcolor=ThemeColors.EMERALD_PRIMARY,
                color=ft.Colors.WHITE,
                padding=ft.padding.symmetric(vertical=14),
            ),
            on_click=lambda _: self._handle_signup(),
            width=float("inf"),
        )

        card = ft.Container(
            content=ft.Column(
                controls=[
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
                                    ft.Text("Join Nueva Ecija Travel", size=18, weight=ft.FontWeight.BOLD),
                                    ft.Text("Create an account to save and sync itineraries", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                                ],
                                spacing=1,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Divider(height=1, color=ThemeColors.BORDER_LIGHT),
                    self.error_container,
                    self.name_input,
                    self.email_input,
                    self.password_input,
                    self.confirm_password_input,
                    ft.Container(height=4),
                    self.submit_btn,
                    ft.Row(
                        controls=[
                            ft.Text("Already have an account?", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ft.TextButton(
                                content="Sign In",
                                on_click=lambda _: self._go_login(),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=12,
            ),
            width=440,
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
        self.submit_btn.content = "Create Account"
        self.update()

    def _handle_signup(self) -> None:
        name = (self.name_input.value or "").strip()
        email = (self.email_input.value or "").strip()
        pwd = (self.password_input.value or "").strip()
        confirm = (self.confirm_password_input.value or "").strip()

        if not name or not email or not pwd:
            self._show_error("Please fill in all required fields.")
            return

        if len(pwd) < 6:
            self._show_error("Password must be at least 6 characters long.")
            return

        if pwd != confirm:
            self._show_error("Passwords do not match.")
            return

        self.error_container.visible = False
        self.submit_btn.disabled = True
        self.submit_btn.content = "Creating Account..."
        self.update()

        async def _do_signup():
            try:
                await self.auth_service.register(
                    email=email,
                    password=pwd,
                    full_name=name,
                )
                if self.on_navigate:
                    self.on_navigate("/dashboard")
            except ApiClientError as err:
                self._show_error(f"Registration failed: {err.message}")
            except Exception as err:
                self._show_error(f"Unexpected error: {str(err)}")

        asyncio.create_task(_do_signup())

    def _go_login(self) -> None:
        if self.on_navigate:
            self.on_navigate("/login")
