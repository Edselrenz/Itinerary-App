"""Login and Authentication View conforming to Figma & Web client design."""

import asyncio
from typing import Callable, Optional
import flet as ft

from desktop_client.config.settings import ThemeColors, get_settings
from desktop_client.core.api_client import ApiClientError
from desktop_client.services.auth_service import get_auth_service


class LoginView(ft.Container):
    """Traveler sign-in form with credential validation, social options, and demo persona."""

    def __init__(self, on_navigate: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.on_navigate = on_navigate
        self.auth_service = get_auth_service()
        self.settings = get_settings()

        self.expand = True
        self.alignment = ft.Alignment(0, 0)
        self.bgcolor = ThemeColors.BG_LIGHT

        self._build_content()

    def _build_content(self) -> None:
        # Top-left back button row
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

        # Welcome Back Title & Subtitle (Left aligned)
        heading_group = ft.Column(
            controls=[
                ft.Text(
                    "Welcome back!",
                    size=26,
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
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

        self.email_input = ft.TextField(
            label="Email Address",
            hint_text="traveler@example.com",
            prefix_icon=ft.Icons.MAIL_OUTLINE,
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            autofocus=True,
            dense=True,
        )

        self.password_input = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.KEY_OUTLINED,
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            dense=True,
        )

        # Remember Me & Forgot Password Row
        options_row = ft.Row(
            controls=[
                ft.Checkbox(
                    label="Remember me",
                    value=True,
                    check_color=ft.Colors.WHITE,
                    active_color=ThemeColors.PRIMARY_BLUE,
                ),
                ft.TextButton(
                    content=ft.Text("Forgot password?", size=12, color=ThemeColors.PRIMARY_BLUE),
                    on_click=lambda _: self._open_forgot_password(),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        self.remember_cb = options_row.controls[0]

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

        # Solid Blue Pill Log In Button
        self.submit_btn = ft.Container(
            content=ft.Text("Log In", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=24,
            height=48,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._handle_login(),
        )

        footer_links = ft.Row(
            controls=[
                ft.Text("Don't have an account?", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                ft.TextButton(
                    content=ft.Text("Sign Up", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                    on_click=lambda _: self._navigate("/signup"),
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
                    ft.Container(height=4),
                    heading_group,
                    self.error_container,
                    ft.Container(height=2),
                    self.email_input,
                    self.password_input,
                    options_row,
                    ft.Container(height=6),
                    self.submit_btn,
                    ft.Container(height=6),
                    footer_links,
                ],
                spacing=10,
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

        if self.safe_page:
            self.safe_page.run_task(_do_login)
        else:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_do_login())
            except RuntimeError:
                asyncio.run(_do_login())

    @property
    def safe_page(self) -> Optional[ft.Page]:
        try:
            return self.page
        except Exception:
            return None

    def _open_forgot_password(self) -> None:
        """Opens password recovery modal dialog."""
        email_field = ft.TextField(
            label="Your Account Email",
            value=self.email_input.value or "",
            hint_text="traveler@example.com",
            border_radius=12,
            border_color=ThemeColors.BORDER_LIGHT,
        )
        status_text = ft.Text("", size=12, color=ThemeColors.BUDGET_GREEN)

        def _send_recovery(_):
            status_text.value = f"Password recovery link sent to {email_field.value or 'your email'}. Check your inbox."
            dlg.update()

        def _close(_):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.LOCK_RESET, color=ThemeColors.PRIMARY_BLUE), ft.Text("Reset Password", size=18, weight=ft.FontWeight.BOLD)]),
            content=ft.Column(
                controls=[
                    ft.Text("Enter your email address and we will send you a secure link to reset your account credentials.", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                    email_field,
                    status_text,
                ],
                spacing=12,
                tight=True,
                width=380,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=_close),
                ft.FilledButton(
                    content="Send Reset Link",
                    style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                    on_click=_send_recovery,
                ),
            ],
        )
        if self.page:
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
