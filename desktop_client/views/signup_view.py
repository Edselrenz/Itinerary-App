"""Traveler Registration and Account Creation View conforming to Figma & Web client."""

import asyncio
import re
from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors, get_settings
from desktop_client.core.api_client import ApiClientError
from desktop_client.services.auth_service import get_auth_service


class SignupView(ft.Container):
    """Registration form allowing travelers to create a cloud account."""

    def __init__(self, on_navigate: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.on_navigate = on_navigate
        self.auth_service = get_auth_service()
        self.settings = get_settings()
        self._username_manually_edited = False

        self.expand = True
        self.alignment = ft.Alignment(0, 0)
        self.bgcolor = ThemeColors.BG_LIGHT

        self._build_content()

    def _build_content(self) -> None:
        # Top-left back button
        back_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_size=20,
                        icon_color=ThemeColors.TEXT_MAIN_LIGHT,
                        tooltip="Go back to welcome screen",
                        on_click=lambda _: self._navigate("/welcome"),
                    ),
                ],
            ),
            alignment=ft.Alignment(-1, 0),
        )

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
                    size=20,
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
                    size=26,
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
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

        def _on_name_change(_):
            if not self._username_manually_edited:
                first = (self.first_name_input.value or "").strip().lower()
                last = (self.last_name_input.value or "").strip().lower()
                first_clean = re.sub(r"[^a-z0-9]", "", first)
                last_clean = re.sub(r"[^a-z0-9]", "", last)
                if first_clean and last_clean:
                    self.username_input.value = f"{first_clean}_{last_clean}"
                elif first_clean:
                    self.username_input.value = first_clean
                elif last_clean:
                    self.username_input.value = last_clean
                try:
                    self.username_input.update()
                except Exception:
                    pass

        def _on_username_change(_):
            val = (self.username_input.value or "").strip()
            if val:
                self._username_manually_edited = True

        self.first_name_input = ft.TextField(
            label="First Name",
            hint_text="e.g. Maria",
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            expand=True,
            dense=True,
            autofocus=True,
            on_change=_on_name_change,
        )

        self.mi_input = ft.TextField(
            label="M.I.",
            hint_text="C.",
            width=70,
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            dense=True,
        )

        self.last_name_input = ft.TextField(
            label="Last Name",
            hint_text="e.g. Clara",
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            dense=True,
            on_change=_on_name_change,
        )

        name_row = ft.Row(
            controls=[self.first_name_input, self.mi_input],
            spacing=8,
        )

        self.username_input = ft.TextField(
            label="Username",
            hint_text="e.g. maria_clara",
            prefix_icon=ft.Icons.ALTERNATE_EMAIL,
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            dense=True,
            on_change=_on_username_change,
        )

        self.email_input = ft.TextField(
            label="Email Address",
            hint_text="traveler@example.com",
            prefix_icon=ft.Icons.MAIL_OUTLINE,
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            dense=True,
        )

        def _on_pwd_change(_):
            val = self.password_input.value or ""
            if len(val) == 0:
                self.password_input.helper = "Minimum 8 characters (letters and numbers)"
            elif len(val) < 8:
                self.password_input.helper = f"Needs {8 - len(val)} more character(s)"
            else:
                self.password_input.helper = "Strong password requirement met"
            try:
                self.password_input.update()
            except Exception:
                pass

        self.password_input = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.KEY_OUTLINED,
            helper="Minimum 8 characters (letters and numbers)",
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            dense=True,
            on_change=_on_pwd_change,
        )

        self.confirm_password_input = ft.TextField(
            label="Confirm Password",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            dense=True,
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

        # Solid Blue Pill Create Account Button
        self.submit_btn = ft.Container(
            content=ft.Text("Sign Up", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=24,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._handle_signup(),
        )

        footer_links = ft.Row(
            controls=[
                ft.Text("Already have an account?", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                ft.TextButton(
                    content=ft.Text("Log In", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                    on_click=lambda _: self._navigate("/login"),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
        )

        card = ft.Container(
            content=ft.Column(
                controls=[
                    back_btn,
                    brand_header,
                    ft.Container(height=2),
                    heading_group,
                    self.error_container,
                    ft.Container(height=2),
                    name_row,
                    self.last_name_input,
                    self.username_input,
                    self.email_input,
                    self.password_input,
                    self.confirm_password_input,
                    ft.Container(height=4),
                    self.submit_btn,
                    ft.Container(height=4),
                    footer_links,
                ],
                spacing=8,
                width=420,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border_radius=24,
            border=ft.Border.all(1.2, ThemeColors.BORDER_LIGHT),
            padding=ft.Padding.symmetric(horizontal=36, vertical=28),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=24,
                color=ft.Colors.with_opacity(0.08, "#000000"),
                offset=ft.Offset(0, 6),
            ),
        )

        self.content = ft.ListView(
            controls=[
                ft.Container(
                    content=card,
                    alignment=ft.Alignment(0, 0),
                    padding=ft.Padding.symmetric(vertical=24),
                )
            ],
            expand=True,
        )

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
        username = (self.username_input.value or "").strip()
        email = (self.email_input.value or "").strip()
        pwd = (self.password_input.value or "").strip()
        confirm_pwd = (self.confirm_password_input.value or "").strip()

        if not first_name:
            self._show_error("First name is required.")
            return

        if not last_name:
            self._show_error("Last name is required.")
            return

        if username and len(username) < 3:
            self._show_error("Username must be at least 3 characters.")
            return

        if not email:
            self._show_error("Email address is required.")
            return

        if len(pwd) < 8:
            self._show_error("Password must be at least 8 characters.")
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
                    first_name=first_name,
                    last_name=last_name,
                    middle_initial=(self.mi_input.value or "").strip(),
                    username=username or f"{first_name.lower()}_{last_name.lower()}",
                )
                try:
                    await self.auth_service.migrate_guest_trips()
                except Exception:
                    pass
                self._navigate("/dashboard")
            except ApiClientError as err:
                self._show_error(err.message or "Registration failed. Try another email or username.")
            except Exception as ex:
                self._show_error(f"Error connecting to service: {str(ex)}")

        if self.safe_page:
            self.safe_page.run_task(_do_signup)
        else:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_do_signup())
            except RuntimeError:
                asyncio.run(_do_signup())

    @property
    def safe_page(self) -> Optional[ft.Page]:
        try:
            return self.page
        except Exception:
            return None

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)

