"""Login and Authentication View conforming to Figma & Web client design."""

import asyncio
from typing import Callable, Optional
import flet as ft

from desktop_client.components.dialogs import close_overlay_dialog, open_overlay_dialog, show_toast
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
        palette = self.settings.palette
        self.bgcolor = palette.surface_card if not palette.is_dark else palette.bg_main
        form_w = 400

        # Top-left back button row matching Web .top-nav-row
        back_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_size=24,
                        icon_color=ThemeColors.PRIMARY_BLUE,
                        tooltip="Go back to welcome screen",
                        on_click=lambda _: self._navigate("/welcome"),
                    ),
                ],
            ),
            alignment=ft.Alignment(-1, 0),
            padding=ft.Padding.only(top=16, left=20),
        )

        # Centered Brand Header
        brand_header = ft.Row(
            controls=[
                ft.Icon(
                    ft.Icons.AIRPLANEMODE_ACTIVE,
                    size=30,
                    color=ThemeColors.PRIMARY_BLUE,
                    rotate=ft.Rotate(angle=0.785398),
                ),
                ft.Text(
                    "Trip mo, trip ko",
                    size=22,
                    weight=ft.FontWeight.W_800,
                    color=palette.text_primary,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

        # Welcome Back Title & Subtitle (Left aligned inside form_w)
        heading_group = ft.Container(
            width=form_w,
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Welcome back!",
                        size=26,
                        weight=ft.FontWeight.W_800,
                        color=palette.text_primary,
                    ),
                    ft.Text(
                        "Log in to continue your journey.",
                        size=14,
                        color=palette.text_muted,
                    ),
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
        )

        self.email_input = ft.TextField(
            label="Email Address",
            hint_text="traveler@example.com",
            prefix_icon=ft.Icons.MAIL_OUTLINE,
            width=form_w,
            border_radius=12,
            border_color=palette.input_border,
            bgcolor=palette.input_bg,
            text_style=ft.TextStyle(color=palette.text_primary),
            focused_border_color=ThemeColors.PRIMARY_BLUE,
            autofocus=True,
            dense=True,
        )

        self.password_input = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.KEY_OUTLINED,
            width=form_w,
            border_radius=12,
            border_color=palette.input_border,
            bgcolor=palette.input_bg,
            text_style=ft.TextStyle(color=palette.text_primary),
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

        # Centered "or" Divider
        or_divider = ft.Row(
            controls=[
                ft.Container(height=1, bgcolor=ThemeColors.BORDER_LIGHT, expand=True),
                ft.Text("or", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                ft.Container(height=1, bgcolor=ThemeColors.BORDER_LIGHT, expand=True),
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        google_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Image(src="assets/images/google_logo.png", width=18, height=18),
                    ft.Text("Continue with Google", size=13, weight=ft.FontWeight.W_600, color=palette.text_primary),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=palette.surface_card,
            border=ft.Border.all(1.2, palette.border_main),
            border_radius=24,
            height=44,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._show_social_notice("Google Sign-In"),
        )

        apple_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.APPLE, size=20, color=palette.text_primary),
                    ft.Text("Continue with Apple", size=13, weight=ft.FontWeight.W_600, color=palette.text_primary),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=palette.surface_card,
            border=ft.Border.all(1.2, palette.border_main),
            border_radius=24,
            height=44,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda _: self._show_social_notice("Apple Sign-In"),
        )

        footer_links = ft.Row(
            controls=[
                ft.Text("Don't have an account?", size=13, color=palette.text_muted),
                ft.TextButton(
                    content=ft.Text("Sign Up", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                    on_click=lambda _: self._navigate("/signup"),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
        )

        login_body = ft.Container(
            width=form_w,
            content=ft.Column(
                controls=[
                    brand_header,
                    ft.Container(height=12),
                    heading_group,
                    self.error_container,
                    ft.Container(height=4),
                    self.email_input,
                    self.password_input,
                    options_row,
                    ft.Container(height=4),
                    self.submit_btn,
                    ft.Container(height=4),
                    or_divider,
                    google_btn,
                    apple_btn,
                    ft.Container(height=6),
                    footer_links,
                ],
                spacing=10,
                width=form_w,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        self.content = ft.Column(
            controls=[
                back_btn,
                ft.Container(
                    content=login_body,
                    alignment=ft.Alignment(0, 0),
                    padding=ft.Padding.symmetric(vertical=12),
                    width=float("inf"),
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            width=float("inf"),
        )

    def on_resize(self, width: float, height: float) -> None:
        """Dynamically recomputes login view on window resize (BUG-04)."""
        self._build_content()
        self._safe_update()

    def _safe_update(self) -> None:
        p = self.safe_page
        if p:
            try:
                p.update()
                return
            except Exception:
                pass
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
            self._show_error("Please enter your email address or username.")
            return

        if not pwd:
            self._show_error("Password is required.")
            return

        self._clear_error()

        async def _do_login():
            self.submit_btn.content = ft.ProgressRing(width=20, height=20, stroke_width=2.5, color=ft.Colors.WHITE)
            self.submit_btn.disabled = True
            self._safe_update()
            try:
                user = await self.auth_service.login(email, pwd, remember_me=self.remember_cb.value or False)
                try:
                    await self.auth_service.migrate_guest_trips()
                except Exception:
                    pass
                if self.safe_page:
                    name = (user.first_name if user and user.first_name else "").strip()
                    msg = f"Welcome back, {name}!" if name else "Welcome back! Login successful."
                    show_toast(self.safe_page, msg, bgcolor=ThemeColors.SUCCESS)
                self._navigate("/dashboard")
            except ApiClientError as err:
                self._show_error(err.message or "Login failed. Check your credentials.")
            except Exception as ex:
                self._show_error(f"Error connecting to service: {str(ex)}")
            finally:
                if not getattr(self.auth_service.session_manager, "is_authenticated", False):
                    self.submit_btn.content = ft.Text("Log In", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                    self.submit_btn.disabled = False
                    self._safe_update()

        if self.safe_page:
            self.safe_page.run_task(_do_login)
        else:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_do_login())
            except RuntimeError:
                asyncio.run(_do_login())

    def _show_social_notice(self, provider: str) -> None:
        if self.safe_page:
            show_toast(self.safe_page, f"{provider} is disabled in this pilot build.", bgcolor="#334155")

    @property
    def safe_page(self) -> Optional[ft.Page]:
        if getattr(self, "_mock_page", None):
            return self._mock_page
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
            close_overlay_dialog(self.page, dlg)

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
        open_overlay_dialog(self.page, dlg)

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
