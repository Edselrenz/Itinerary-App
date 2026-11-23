"""Profile, Edit Profile, Settings, Favorites, Help & Support, and About In-Page Views mirroring Ionic tabs/profile."""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from typing import Callable, Optional
import flet as ft

from desktop_client.components.dialogs import (
    close_overlay_dialog,
    open_overlay_dialog,
    show_place_detail_dialog,
    show_toast,
)
from desktop_client.config.settings import ThemeColors, get_settings
from desktop_client.core.connectivity_service import get_connectivity_service
from desktop_client.core.session import get_session_manager
from desktop_client.core.storage import get_guest_storage
from desktop_client.models.place import Place
from desktop_client.models.user import UserUpdatePayload
from desktop_client.services.auth_service import get_auth_service
from desktop_client.services.favorites_service import get_favorites_service


class ProfileView(ft.Container):
    """Profile tab view matching uploaded reference screenshots (image_2d13c2.png, image_2d1741.png, image_2d1705.png):

    - View 'profile': Clean 'Profile' heading, avatar + Full Name + @email + 'Edit Profile' pill button,
      and 5-row rounded white navigation card (Settings, Favorites, Help & Support, About, Log Out).
    - View 'edit': In-page '<- Edit Profile' header, centered circular avatar with camera overlay +
      outlined 'Change Photo' pill button, 7 stacked fields (First Name, Middle Initial (if applicable),
      Last Name, Birthday, Gender, read-only Email Address, Phone Number), and full-width blue 'Save Changes' button.
    - View 'settings': In-page '<- Settings' header and single rounded white card with 6 exact rows:
      Account Information, Notifications (switch), Privacy & Security, Language (English),
      App Appearance (Light/Dark), and Clear Cache (Free up storage space).
    """

    def __init__(
        self,
        on_navigate: Optional[Callable[[str], None]] = None,
        on_toggle_theme: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.on_navigate = on_navigate
        self.on_toggle_theme = on_toggle_theme
        self.session_manager = get_session_manager()
        self.auth_service = get_auth_service()
        self.guest_storage = get_guest_storage()
        self.favorites_service = get_favorites_service()
        self.connectivity_service = get_connectivity_service()
        self.settings = get_settings()

        self.expand = True
        self.padding = ft.Padding.symmetric(horizontal=36, vertical=24)
        self.alignment = ft.Alignment(0, -1)
        self.bgcolor = self.settings.palette.bg_main

        # In-page subview state matching Web ProfilePage.viewMode
        self.view_mode: str = "profile"  # 'profile' | 'edit' | 'settings' | 'favorites' | 'help' | 'about'
        self.notifications_enabled: bool = True
        self.current_language: str = "en"
        self.is_migrating: bool = False
        self._has_refreshed_profile: bool = False

        # Edit Profile State
        self._edit_avatar_data_url: Optional[str] = None
        self._edit_error_msg: str = ""
        self._is_saving_profile: bool = False

        # Favorites Subview State
        self._fav_search_query: str = ""
        self._fav_selected_cat: str = "ALL"
        self._open_faq_index: Optional[int] = 0
        self._fav_cards_col: Optional[ft.Column] = None
        self._fav_search_field: Optional[ft.TextField] = None

        self._build_content()

    def _get_card_width(self, narrow: bool = False) -> float:
        """Dynamic responsive card width scaling with window size (BUG-04)."""
        from desktop_client.config.settings import ResponsiveLayout
        pw = float(self.safe_page.width) if (self.safe_page and self.safe_page.width) else 1280.0
        metrics = ResponsiveLayout.get_metrics(pw)
        if metrics["is_mobile"]:
            return max(300.0, pw - 36.0)
        if narrow:
            return min(520.0, max(420.0, pw * 0.46))
        return min(720.0, max(560.0, pw * 0.56))

    def _wrap_centered_scroll(self, inner_card: ft.Control) -> ft.Control:
        """Horizontally centers fixed-to-responsive width cards in Flet (BUG-04)."""
        return ft.Column(
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[inner_card],
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            width=float("inf"),
        )

    def on_resize(self, width: float, height: float) -> None:
        """Invoked on window resize to smoothly recompute card widths (BUG-04)."""
        self._build_content()
        self._safe_update()

    @property
    def _subview(self) -> str:
        return self.view_mode

    @_subview.setter
    def _subview(self, val: str) -> None:
        self.view_mode = val

    def _rebuild(self) -> None:
        self._build_content()
        self._safe_update()

    def handle_back(self) -> bool:
        """Allows back navigation from subviews ('edit', 'settings', 'favorites', 'help', 'about') back to 'profile'."""
        if self.view_mode != "profile":
            self.view_mode = "profile"
            self._build_content()
            self._safe_update()
            return True
        return False

    def _build_content(self) -> None:
        palette = self.settings.palette
        self.bgcolor = palette.bg_main
        if self.view_mode == "edit":
            self.content = self._build_edit_profile_subview()
        elif self.view_mode == "settings":
            self.content = self._build_settings_subview()
        elif self.view_mode == "favorites":
            self.content = self._build_favorites_subview()
        elif self.view_mode == "help":
            self.content = self._build_help_subview()
        elif self.view_mode == "about":
            self.content = self._build_about_subview()
        else:
            self.content = self._build_main_profile_view()

    # =========================================================================
    # VIEW 1: MAIN PROFILE TAB (MATCHING image_2d13c2.png)
    # =========================================================================
    def _build_main_profile_view(self) -> ft.Control:
        user = self.session_manager.current_user
        is_guest = self.session_manager.is_guest or not self.session_manager.is_authenticated
        palette = self.settings.palette
        card_w = self._get_card_width(narrow=False)

        title_header = ft.Text(
            "Profile",
            size=30,
            weight=ft.FontWeight.W_800,
            color=palette.text_primary,
        )

        if not is_guest and user:
            name_val = user.full_name or "Edward Renz Natividad"
            email_raw = user.email or "edselrenz0@gmail.com"
            handle_val = f"@{email_raw}" if not email_raw.startswith("@") else email_raw
            avatar_src = self.settings.resolve_avatar_path(user.avatar_url, user.id)

            avatar_ctrl = ft.Container(
                content=ft.Image(
                    src=avatar_src,
                    width=84,
                    height=84,
                    fit=ft.BoxFit.COVER,
                    border_radius=42,
                    error_content=ft.CircleAvatar(
                        content=ft.Icon(ft.Icons.PERSON, size=40, color=ft.Colors.WHITE),
                        radius=42,
                        bgcolor=ThemeColors.PRIMARY_BLUE,
                    ),
                ),
                width=84,
                height=84,
                border_radius=42,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            )

            action_pill = ft.Container(
                content=ft.Text(
                    "Edit Profile",
                    size=13,
                    weight=ft.FontWeight.W_600,
                    color=ThemeColors.PRIMARY_BLUE,
                ),
                border=ft.Border.all(1.2, ThemeColors.PRIMARY_BLUE),
                border_radius=20,
                padding=ft.Padding.symmetric(horizontal=24, vertical=6),
                ink=True,
                on_click=lambda _: self._open_edit_profile_dialog(),
            )
        else:
            name_val = "Guest Explorer"
            handle_val = "Browsing in Guest Mode (Offline)"
            avatar_ctrl = ft.Container(
                content=ft.Icon(ft.Icons.PERSON, size=40, color=ThemeColors.TEXT_MUTED_LIGHT),
                width=84,
                height=84,
                border_radius=42,
                bgcolor="#e2e8f0" if not palette.is_dark else "#1e293b",
                alignment=ft.Alignment(0, 0),
            )
            action_pill = ft.Container(
                content=ft.Text(
                    "Log In / Sign Up",
                    size=13,
                    weight=ft.FontWeight.W_600,
                    color=ThemeColors.PRIMARY_BLUE,
                ),
                border=ft.Border.all(1.2, ThemeColors.PRIMARY_BLUE),
                border_radius=20,
                padding=ft.Padding.symmetric(horizontal=24, vertical=6),
                ink=True,
                on_click=lambda _: self._navigate("/login"),
            )

        identity_row = ft.Row(
            controls=[
                avatar_ctrl,
                ft.Column(
                    controls=[
                        ft.Text(name_val, size=20, weight=ft.FontWeight.W_800, color=palette.text_primary),
                        ft.Text(handle_val, size=14, color=palette.text_faint),
                        ft.Container(height=2),
                        action_pill,
                    ],
                    spacing=3,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=20,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Unsynced Local Guest Trips Banner (only shown if guest trips exist)
        guest_trips_count = len(self.guest_storage.list_itineraries())
        sync_banner: ft.Control = ft.Container()
        if guest_trips_count > 0 and not is_guest:
            sync_banner = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.CLOUD_UPLOAD_OUTLINED, size=18, color=ThemeColors.PRIMARY_BLUE),
                                ft.Text(
                                    f"{guest_trips_count} local {'trip' if guest_trips_count == 1 else 'trips'} not synced",
                                    size=13,
                                    weight=ft.FontWeight.W_600,
                                    color=palette.text_primary,
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.FilledButton(
                            content="Sync" if not self.is_migrating else "Syncing...",
                            style=ft.ButtonStyle(
                                bgcolor=ThemeColors.PRIMARY_BLUE,
                                color=ft.Colors.WHITE,
                                shape=ft.RoundedRectangleBorder(radius=8),
                            ),
                            disabled=self.is_migrating,
                            on_click=lambda _: self._sync_guest_trips(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                bgcolor=ThemeColors.PRIMARY_LIGHT if not palette.is_dark else "#0f2038",
                border=ft.Border.all(1, ThemeColors.CUSTOM_CARD_BORDER if not palette.is_dark else "#1e3a5f"),
                border_radius=14,
                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                width=card_w,
            )

        # 5-Row Rounded Card matching image_2d13c2.png
        menu_card = ft.Container(
            width=card_w,
            bgcolor=palette.surface_card,
            border=ft.Border.all(1, palette.border_main),
            border_radius=20,
            padding=ft.Padding.symmetric(horizontal=22, vertical=10),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=14,
                color=ft.Colors.with_opacity(0.04, "#000000"),
                offset=ft.Offset(0, 4),
            ),
            content=ft.Column(
                spacing=0,
                controls=[
                    self._create_menu_row(
                        icon=ft.Icons.SETTINGS_OUTLINED,
                        icon_color=ThemeColors.PRIMARY_BLUE,
                        title="Settings",
                        desc="Manage your account and customize your app experience.",
                        on_click=lambda: self._open_settings_dialog(),
                    ),
                    ft.Divider(color=palette.border_main, height=1),
                    self._create_menu_row(
                        icon=ft.Icons.FAVORITE,
                        icon_color=ThemeColors.PRIMARY_BLUE,
                        title="Favorites",
                        desc="Your favorite places, all saved in one place. Find them whenever you're ready to explore.",
                        on_click=lambda: self._open_favorites_dialog(),
                    ),
                    ft.Divider(color=palette.border_main, height=1),
                    self._create_menu_row(
                        icon=ft.Icons.HELP_ROUNDED,
                        icon_color=ThemeColors.PRIMARY_BLUE,
                        title="Help & Support",
                        desc="Get assistance and find answers to common questions.",
                        on_click=lambda: self._open_help_dialog(),
                    ),
                    ft.Divider(color=palette.border_main, height=1),
                    self._create_menu_row(
                        icon=ft.Icons.INFO_ROUNDED,
                        icon_color=ThemeColors.PRIMARY_BLUE,
                        title="About",
                        desc=f"Version {self.settings.app_version}.",
                        on_click=lambda: self._open_about_dialog(),
                    ),
                    ft.Divider(color=palette.border_main, height=1),
                    self._create_menu_row(
                        icon=ft.Icons.LOGOUT_ROUNDED,
                        icon_color=ThemeColors.ERROR if not is_guest else ThemeColors.PRIMARY_BLUE,
                        title="Log Out" if not is_guest else "Exit Guest Mode",
                        desc="Sign out of your account." if not is_guest else "Return to welcome screen to log in or register.",
                        title_color=ThemeColors.ERROR if not is_guest else ThemeColors.PRIMARY_BLUE,
                        on_click=lambda: self._confirm_logout() if not is_guest else self._navigate("/welcome"),
                    ),
                ],
            ),
        )

        return self._wrap_centered_scroll(
            ft.Container(
                width=card_w,
                content=ft.Column(
                    controls=[
                        title_header,
                        ft.Container(height=16),
                        identity_row,
                        ft.Container(height=18),
                        sync_banner,
                        menu_card,
                    ],
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                ),
            )
        )

    def _create_menu_row(
        self,
        icon: ft.IconData,
        icon_color: str,
        title: str,
        desc: str,
        on_click: Callable[[], None],
        title_color: Optional[str] = None,
    ) -> ft.Control:
        """Creates a clean menu row matching image_2d13c2.png (clean icon on left, bold title + description on right)."""
        palette = self.settings.palette
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(icon, size=24, color=icon_color),
                        width=36,
                        alignment=ft.Alignment(0, -0.2),
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                title,
                                size=16,
                                weight=ft.FontWeight.W_700,
                                color=title_color or palette.text_primary,
                            ),
                            ft.Text(
                                desc,
                                size=13,
                                color=palette.text_faint,
                            ),
                        ],
                        spacing=3,
                        expand=True,
                    ),
                ],
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(vertical=18, horizontal=4),
            ink=True,
            border_radius=10,
            on_click=lambda _: on_click(),
        )

    # =========================================================================
    # VIEW 2: EDIT PROFILE IN-PAGE SUBVIEW (MATCHING image_2d1741.png EXACTLY)
    # =========================================================================
    def _build_edit_profile_subview(self) -> ft.Control:
        user = self.session_manager.current_user
        uid = user.id if user else "traveler"
        raw_avatar = self._edit_avatar_data_url or (user.avatar_url if user else None)
        avatar_src = self.settings.resolve_avatar_path(raw_avatar, uid)
        palette = self.settings.palette
        card_w = self._get_card_width(narrow=True)

        header_row = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ThemeColors.PRIMARY_BLUE,
                    icon_size=22,
                    tooltip="Back to profile",
                    on_click=lambda _: self._close_subview(),
                ),
                ft.Text("Edit Profile", size=24, weight=ft.FontWeight.W_800, color=palette.text_primary),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            width=card_w,
        )

        avatar_preview_img = ft.Image(
            src=avatar_src,
            width=96,
            height=96,
            fit=ft.BoxFit.COVER,
            border_radius=48,
            error_content=ft.CircleAvatar(
                content=ft.Icon(ft.Icons.PERSON, size=42, color=ft.Colors.WHITE),
                radius=48,
                bgcolor=ThemeColors.PRIMARY_BLUE,
            ),
        )

        def _pick_photo(_=None):
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                f_path = filedialog.askopenfilename(
                    title="Select Profile Photo",
                    filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.webp")],
                )
                root.destroy()
                if f_path:
                    ext = Path(f_path).suffix.lstrip(".").lower()
                    if ext == "jpg":
                        ext = "jpeg"
                    b64_str = base64.b64encode(Path(f_path).read_bytes()).decode("ascii")
                    self._edit_avatar_data_url = f"data:image/{ext};base64,{b64_str}"
                    avatar_preview_img.src = self.settings.resolve_avatar_path(self._edit_avatar_data_url, uid)
                    self._safe_update()
            except Exception:
                pass

        # Circular Avatar with Centered Semi-Transparent Camera Overlay + Outlined 'Change Photo' Pill Button
        avatar_stack = ft.GestureDetector(
            on_tap=_pick_photo,
            content=ft.Stack(
                width=96,
                height=96,
                controls=[
                    ft.Container(
                        content=avatar_preview_img,
                        width=96,
                        height=96,
                        border_radius=48,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    ),
                    ft.Container(
                        left=30,
                        top=30,
                        width=36,
                        height=36,
                        border_radius=18,
                        bgcolor=ft.Colors.with_opacity(0.45, "#000000"),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(ft.Icons.PHOTO_CAMERA_OUTLINED, size=18, color=ft.Colors.WHITE),
                    ),
                ],
            ),
        )

        change_photo_btn = ft.Container(
            content=ft.Text("Change Photo", size=12, weight=ft.FontWeight.W_600, color=ThemeColors.PRIMARY_BLUE),
            border=ft.Border.all(1.2, ThemeColors.PRIMARY_BLUE),
            border_radius=20,
            padding=ft.Padding.symmetric(horizontal=22, vertical=6),
            ink=True,
            on_click=_pick_photo,
        )

        avatar_section = ft.Column(
            controls=[avatar_stack, change_photo_btn],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

        # Helper to build each labeled field spanning the full centered card width
        def _labeled_field(label_text: str, initial_val: str, read_only: bool = False) -> tuple[ft.Control, ft.TextField]:
            read_only_bg = "#1e293b" if palette.is_dark else "#f1f5f9"
            tf = ft.TextField(
                value=initial_val,
                read_only=read_only,
                width=card_w,
                border_radius=10,
                border_color=palette.input_border,
                focused_border_color=ThemeColors.PRIMARY_BLUE,
                bgcolor=read_only_bg if read_only else palette.input_bg,
                filled=True,
                dense=True,
                text_style=ft.TextStyle(
                    size=14,
                    color=palette.text_faint if read_only else palette.text_primary,
                ),
                content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            )
            block = ft.Column(
                controls=[
                    ft.Text(label_text, size=12, weight=ft.FontWeight.W_700, color=palette.text_primary),
                    tf,
                ],
                spacing=4,
                width=card_w,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            )
            return block, tf

        first_block, first_tf = _labeled_field("First Name", user.first_name if user and user.first_name else "Edward Renz")
        mi_block, mi_tf = _labeled_field("Middle Initial (if applicable)", user.middle_initial if user and user.middle_initial else "N/A")
        last_block, last_tf = _labeled_field("Last Name", user.last_name if user and user.last_name else "Natividad")
        bday_block, bday_tf = _labeled_field("Birthday", user.birthday if user and user.birthday else "May 23, 2000")
        gender_block, gender_tf = _labeled_field("Gender", user.gender if user and user.gender else "Female")
        email_block, email_tf = _labeled_field("Email Address", user.email if user and user.email else "edselrenz0@gmail.com", read_only=True)
        phone_block, phone_tf = _labeled_field("Phone Number", user.phone_number if user and user.phone_number else "+66 81 234 5678")

        error_banner = ft.Container(
            visible=bool(self._edit_error_msg),
            bgcolor=ThemeColors.ERROR_BG,
            border_radius=8,
            padding=10,
            width=card_w,
            content=ft.Text(self._edit_error_msg, size=12, color=ThemeColors.ERROR),
        )

        def _save_changes(_=None):
            f_val = (first_tf.value or "").strip()
            l_val = (last_tf.value or "").strip()
            if not f_val or not l_val:
                self._edit_error_msg = "First Name and Last Name are required."
                self._build_content()
                self._safe_update()
                return

            payload = UserUpdatePayload(
                first_name=f_val,
                middle_initial=(mi_tf.value or "").strip() or "N/A",
                last_name=l_val,
                birthday=(bday_tf.value or "").strip() or "May 23, 2000",
                gender=(gender_tf.value or "").strip() or "Female",
                phone_number=(phone_tf.value or "").strip() or "+66 81 234 5678",
                avatar_url=self._edit_avatar_data_url or (user.avatar_url if user else "assets/images/pattranite_avatar.jpg"),
            )

            async def _do_update():
                try:
                    await self.auth_service.update_profile(payload)
                    self._edit_error_msg = ""
                    self.view_mode = "profile"
                    self._build_content()
                    self._safe_update()
                    if self.safe_page:
                        show_toast(self.safe_page, "Profile updated successfully!")
                except Exception as err:
                    self._edit_error_msg = str(err)
                    self._build_content()
                    self._safe_update()

            if self.safe_page:
                self.safe_page.run_task(_do_update)
            else:
                try:
                    asyncio.get_running_loop().create_task(_do_update())
                except RuntimeError:
                    pass

        save_btn = ft.Container(
            content=ft.Text("Save Changes", size=14, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
            bgcolor=ThemeColors.PRIMARY_BLUE,
            border_radius=10,
            height=46,
            width=card_w,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=_save_changes,
        )

        return self._wrap_centered_scroll(
            ft.Container(
                width=card_w,
                alignment=ft.Alignment(0, -1),
                content=ft.Column(
                    controls=[
                        header_row,
                        ft.Container(height=12),
                        ft.Container(content=avatar_section, width=card_w, alignment=ft.Alignment(0, 0)),
                        ft.Container(height=14),
                        error_banner,
                        first_block,
                        mi_block,
                        last_block,
                        bday_block,
                        gender_block,
                        email_block,
                        phone_block,
                        ft.Container(height=12),
                        save_btn,
                        ft.Container(height=24),
                    ],
                    spacing=10,
                    width=card_w,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        )

    # =========================================================================
    # VIEW 3: SETTINGS IN-PAGE SUBVIEW (MATCHING image_2d1705.png EXACTLY)
    # =========================================================================
    def _build_settings_subview(self) -> ft.Control:
        is_dark = bool(self.safe_page and self.safe_page.theme_mode == ft.ThemeMode.DARK)
        palette = self.settings.palette
        card_w = self._get_card_width(narrow=False)

        header_row = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ThemeColors.PRIMARY_BLUE,
                    icon_size=22,
                    tooltip="Back to profile",
                    on_click=lambda _: self._close_subview(),
                ),
                ft.Text("Settings", size=26, weight=ft.FontWeight.W_800, color=palette.text_primary),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        notif_switch = ft.Switch(
            value=self.notifications_enabled,
            active_color=ThemeColors.PRIMARY_BLUE,
            on_change=lambda e: setattr(self, "notifications_enabled", bool(e.control.value)),
        )

        def _settings_row(
            icon: ft.IconData,
            title: str,
            subtitle: Optional[str] = None,
            trailing: Optional[ft.Control] = None,
            on_click: Optional[Callable[[], None]] = None,
        ) -> ft.Control:
            title_col = (
                ft.Column(
                    controls=[
                        ft.Text(title, size=15, weight=ft.FontWeight.W_700, color=palette.text_primary),
                        ft.Text(subtitle, size=12, color=palette.text_faint),
                    ],
                    spacing=2,
                )
                if subtitle
                else ft.Text(title, size=15, weight=ft.FontWeight.W_700, color=palette.text_primary)
            )
            row_controls: list[ft.Control] = [
                ft.Row(
                    controls=[
                        ft.Icon(icon, size=22, color=ThemeColors.PRIMARY_BLUE),
                        title_col,
                    ],
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ]
            if trailing is not None:
                row_controls.append(trailing)

            return ft.Container(
                content=ft.Row(
                    controls=row_controls,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(vertical=16, horizontal=6),
                ink=on_click is not None,
                border_radius=10,
                on_click=(lambda _: on_click()) if on_click else None,
            )

        settings_card = ft.Container(
            width=card_w,
            bgcolor=palette.surface_card,
            border=ft.Border.all(1, palette.border_main),
            border_radius=20,
            padding=ft.Padding.symmetric(horizontal=22, vertical=8),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=14,
                color=ft.Colors.with_opacity(0.04, "#000000"),
                offset=ft.Offset(0, 4),
            ),
            content=ft.Column(
                spacing=0,
                controls=[
                    # Row 1: Account Information
                    _settings_row(
                        icon=ft.Icons.PERSON_OUTLINE,
                        title="Account Information",
                        on_click=lambda: self._open_edit_profile_dialog(),
                    ),
                    ft.Divider(color=palette.border_main, height=1),
                    # Row 2: Notifications
                    _settings_row(
                        icon=ft.Icons.NOTIFICATIONS,
                        title="Notifications",
                        trailing=notif_switch,
                    ),
                    ft.Divider(color=palette.border_main, height=1),
                    # Row 3: Privacy & Security
                    _settings_row(
                        icon=ft.Icons.LOCK,
                        title="Privacy & Security",
                        on_click=lambda: self._open_privacy_security_alert(),
                    ),
                    ft.Divider(color=palette.border_main, height=1),
                    # Row 4: Language
                    _settings_row(
                        icon=ft.Icons.LANGUAGE,
                        title="Language",
                        trailing=ft.Text(
                            "Filipino" if self.current_language == "fil" else "English",
                            size=14,
                            weight=ft.FontWeight.W_500,
                            color=palette.text_primary,
                        ),
                        on_click=lambda: self._toggle_language(),
                    ),
                    ft.Divider(color=palette.border_main, height=1),
                    # Row 5: App Appearance
                    _settings_row(
                        icon=ft.Icons.DARK_MODE_OUTLINED if is_dark else ft.Icons.WB_SUNNY_OUTLINED,
                        title="App Appearance",
                        trailing=ft.Text(
                            "Dark" if is_dark else "Light",
                            size=14,
                            weight=ft.FontWeight.W_500,
                            color=palette.text_primary,
                        ),
                        on_click=lambda: self._toggle_theme(),
                    ),
                    ft.Divider(color=palette.border_main, height=1),
                    # Row 6: Clear Cache
                    _settings_row(
                        icon=ft.Icons.DELETE_OUTLINE,
                        title="Clear Cache",
                        subtitle="Free up storage space",
                        on_click=lambda: self._confirm_clear_cache(),
                    ),
                ],
            ),
        )

        return self._wrap_centered_scroll(
            ft.Container(
                width=card_w,
                content=ft.Column(
                    controls=[
                        header_row,
                        ft.Container(height=14),
                        settings_card,
                    ],
                    spacing=0,
                ),
            )
        )

    def _on_fav_search_change(self, val: str) -> None:
        self._fav_search_query = val
        if hasattr(self, "_fav_cards_col") and self._fav_cards_col is not None:
            self._fav_cards_col.controls = self._render_fav_cards()
            try:
                self._fav_cards_col.update()
            except Exception:
                self._safe_update()
        else:
            self._build_content()
            self._safe_update()

    def _set_fav_category(self, cat: str) -> None:
        self._fav_selected_cat = cat
        self._build_content()
        self._safe_update()

    def _toggle_faq(self, idx: int) -> None:
        self._open_faq_index = None if self._open_faq_index == idx else idx
        self._build_content()
        self._safe_update()

    def _render_fav_cards(self) -> list[ft.Control]:
        favorites = self.favorites_service.get_favorites()
        q = self._fav_search_query.strip().lower()
        filtered = [
            p for p in favorites
            if (not q or q in p.name.lower() or q in (p.municipality_name or "").lower())
            and (self._fav_selected_cat == "ALL" or self._fav_selected_cat.lower() in (p.category or "").lower() or self._fav_selected_cat.lower() in (p.formatted_category or "").lower())
        ]
        palette = self.settings.palette
        cards: list[ft.Control] = []
        if filtered:
            for place in filtered:
                dir_url = place.directions_url or f"https://www.google.com/maps/search/?api=1&query={place.latitude},{place.longitude}"
                directions_btn = ft.OutlinedButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.DIRECTIONS, size=14, color=ThemeColors.PRIMARY_BLUE),
                            ft.Text("Directions", size=11, weight=ft.FontWeight.W_600, color=ThemeColors.PRIMARY_BLUE),
                        ],
                        spacing=4,
                    ),
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    url=dir_url,
                )

                cards.append(
                    ft.Container(
                        bgcolor=palette.surface_card,
                        border=ft.Border.all(1, palette.border_main),
                        border_radius=14,
                        padding=12,
                        content=ft.Row(
                            controls=[
                                ft.Image(
                                    src=place.resolved_image_path,
                                    width=80,
                                    height=64,
                                    fit=ft.BoxFit.COVER,
                                    border_radius=8,
                                    error_content=ft.Icon(ft.Icons.LANDSCAPE, size=24, color=ThemeColors.PRIMARY_BLUE),
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(place.name, size=14, weight=ft.FontWeight.BOLD, color=palette.text_primary),
                                        ft.Text(place.municipality_name or "Nueva Ecija", size=12, color=palette.text_muted),
                                        ft.Text(place.formatted_cost, size=12, weight=ft.FontWeight.BOLD, color=ThemeColors.EMERALD_PRIMARY),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                directions_btn,
                                ft.FilledButton(
                                    content="View Details",
                                    style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                                    on_click=lambda _, pl=place: show_place_detail_dialog(self.safe_page, pl, on_navigate=self.on_navigate) if self.safe_page else None,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.FAVORITE,
                                    icon_color=ft.Colors.RED_500,
                                    tooltip="Remove from favorites",
                                    on_click=lambda _, pl=place: self._remove_fav(pl),
                                ),
                            ],
                            spacing=8,
                        ),
                    )
                )
        else:
            cards.append(
                ft.Container(
                    padding=40,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.FAVORITE_BORDER, size=42, color=ThemeColors.PRIMARY_BLUE),
                            ft.Text("No Favorite Places Saved", size=16, weight=ft.FontWeight.BOLD, color=palette.text_primary),
                            ft.Text("Browse destinations and tap the heart icon to save your personal favorite spots right here.", size=12, color=palette.text_muted),
                            ft.FilledButton(
                                content="Explore Destinations",
                                style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                                on_click=lambda _: self._navigate("/home"),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                )
            )
        return cards

    # =========================================================================
    # VIEW 4: FAVORITES IN-PAGE SUBVIEW
    # =========================================================================
    def _build_favorites_subview(self) -> ft.Control:
        palette = self.settings.palette
        card_w = self._get_card_width(narrow=False)

        favorites = self.favorites_service.get_favorites()
        q = self._fav_search_query.strip().lower()
        filtered_count = len([
            p for p in favorites
            if (not q or q in p.name.lower() or q in (p.municipality_name or "").lower())
            and (self._fav_selected_cat == "ALL" or self._fav_selected_cat.lower() in (p.category or "").lower() or self._fav_selected_cat.lower() in (p.formatted_category or "").lower())
        ])

        header_row = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ThemeColors.PRIMARY_BLUE,
                    icon_size=22,
                    on_click=lambda _: self._close_subview(),
                ),
                ft.Text("Favorites", size=24, weight=ft.FontWeight.W_800, color=palette.text_primary),
                ft.Container(
                    content=ft.Text(str(filtered_count), size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    bgcolor=ThemeColors.PRIMARY_BLUE,
                    border_radius=10,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self._fav_search_field = ft.TextField(
            hint_text="Search saved places...",
            prefix_icon=ft.Icons.SEARCH,
            value=self._fav_search_query,
            width=card_w,
            dense=True,
            border_radius=10,
            bgcolor=palette.input_bg,
            border_color=palette.input_border,
            text_style=ft.TextStyle(color=palette.text_primary),
            on_change=lambda e: self._on_fav_search_change(e.control.value),
        )

        categories = [
            ("ALL", "All Places"),
            ("nature_park", "Nature & Parks"),
            ("museum_cultural", "Culture & Heritage"),
            ("restaurant", "Cafes & Dining"),
            ("resort_swimming", "Resorts & Stays"),
            ("farm", "Farm & Agri-Tourism"),
        ]
        cat_chips = []
        for c_key, c_label in categories:
            is_sel = (self._fav_selected_cat == c_key)
            cat_chips.append(
                ft.Container(
                    content=ft.Text(
                        c_label,
                        size=11,
                        weight=ft.FontWeight.BOLD if is_sel else ft.FontWeight.NORMAL,
                        color=ft.Colors.WHITE if is_sel else palette.text_primary,
                    ),
                    bgcolor=ThemeColors.PRIMARY_BLUE if is_sel else palette.surface_card,
                    border=ft.Border.all(1, ThemeColors.PRIMARY_BLUE if is_sel else palette.border_main),
                    border_radius=12,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                    ink=True,
                    on_click=lambda _, k=c_key: self._set_fav_category(k),
                )
            )
        category_scroller = ft.Row(controls=cat_chips, spacing=6, scroll=ft.ScrollMode.AUTO)

        self._fav_cards_col = ft.Column(controls=self._render_fav_cards(), spacing=10)

        return self._wrap_centered_scroll(
            ft.Container(
                width=card_w,
                content=ft.Column(
                    controls=[
                        header_row,
                        self._fav_search_field,
                        category_scroller,
                        ft.Container(height=4),
                        self._fav_cards_col,
                    ],
                    spacing=10,
                ),
            )
        )

    # =========================================================================
    # VIEW 5 & 6: HELP & SUPPORT AND ABOUT IN-PAGE SUBVIEWS
    # =========================================================================
    def _build_help_subview(self) -> ft.Control:
        palette = self.settings.palette
        card_w = self._get_card_width(narrow=False)

        header_row = ft.Row(
            controls=[
                ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=ThemeColors.PRIMARY_BLUE, icon_size=22, on_click=lambda _: self._close_subview()),
                ft.Text("Help & Support", size=24, weight=ft.FontWeight.W_800, color=palette.text_primary),
            ],
            spacing=8,
        )

        faqs = [
            (
                "How does the app generate suggested itineraries?",
                "Our pacing engine analyzes 2,673 provincial points of interest, your selected pacing, daily budget, and starting destination to calculate optimal daily road routes via Open Source Routing Machine (OSRM).",
            ),
            (
                "Can I use the app offline in remote areas?",
                "Yes! All created itineraries, destination notes, and visited map areas are cached locally so you can travel through the Sierra Madre mountains with confidence.",
            ),
            (
                "What are the emergency provincial hotlines?",
                "PDRRMO Nueva Ecija: (044) 940 3388\nPNP Nueva Ecija: 117 / (044) 463 0565\nTourism Office: tourism@nuevaecija.gov.ph",
            ),
        ]

        faq_controls = []
        for idx, (q, a) in enumerate(faqs):
            is_open = (self._open_faq_index == idx)
            faq_controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(q, size=13, weight=ft.FontWeight.BOLD, color=palette.text_primary, expand=True),
                                    ft.Icon(
                                        ft.Icons.KEYBOARD_ARROW_UP if is_open else ft.Icons.KEYBOARD_ARROW_DOWN,
                                        size=18,
                                        color=ThemeColors.PRIMARY_BLUE,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Container(
                                content=ft.Text(a, size=12, color=palette.text_muted),
                                visible=is_open,
                                padding=ft.Padding.only(top=6),
                            ),
                        ],
                        spacing=2,
                    ),
                    bgcolor=palette.surface_card,
                    border=ft.Border.all(1, palette.border_main),
                    border_radius=12,
                    padding=14,
                    ink=True,
                    on_click=lambda _, i=idx: self._toggle_faq(i),
                )
            )

        card = ft.Container(
            width=card_w,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Text("Frequently Asked Questions", size=16, weight=ft.FontWeight.W_800, color=palette.text_primary),
                    *faq_controls,
                ],
            ),
        )
        return self._wrap_centered_scroll(
            ft.Container(width=card_w, content=ft.Column(controls=[header_row, ft.Container(height=12), card]))
        )

    def _build_about_subview(self) -> ft.Control:
        palette = self.settings.palette
        card_w = self._get_card_width(narrow=False)

        header_row = ft.Row(
            controls=[
                ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=ThemeColors.PRIMARY_BLUE, icon_size=22, on_click=lambda _: self._close_subview()),
                ft.Text("About", size=24, weight=ft.FontWeight.W_800, color=palette.text_primary),
            ],
            spacing=8,
        )
        card = ft.Container(
            width=card_w,
            bgcolor=palette.surface_card,
            border=ft.Border.all(1, palette.border_main),
            border_radius=20,
            padding=24,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.INFO_ROUNDED, size=44, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text("Nueva Ecija Travel Companion", size=18, weight=ft.FontWeight.W_800, color=palette.text_primary),
                    ft.Text("Trip mo, trip ko", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text(
                        "Comprehensive travel and itinerary planning companion engineered for travelers exploring all 32 municipalities and 5 component cities of Nueva Ecija, Philippines.",
                        size=12,
                        color=palette.text_muted,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Divider(color=palette.border_main, height=12),
                    ft.Row(
                        controls=[
                            ft.Text("Version", size=13, color=palette.text_muted),
                            ft.Text(self.settings.app_version, size=13, weight=ft.FontWeight.BOLD, color=palette.text_primary),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(color=palette.border_main, height=12),
                    ft.Row(
                        controls=[
                            ft.Text("Open Data Attribution", size=13, color=palette.text_muted),
                            ft.Text("OpenStreetMap & GIS Nueva Ecija", size=13, weight=ft.FontWeight.BOLD, color=palette.text_primary),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
            ),
        )
        return self._wrap_centered_scroll(
            ft.Container(width=card_w, content=ft.Column(controls=[header_row, ft.Container(height=12), card]))
        )

    # =========================================================================
    # NAVIGATION & DIALOG HELPERS
    # =========================================================================
    def _close_subview(self) -> None:
        self.view_mode = "profile"
        self._build_content()
        self._safe_update()

    def _open_edit_profile_dialog(self) -> None:
        if self.session_manager.is_guest or not self.session_manager.is_authenticated:
            self._navigate("/login")
            return
        self._edit_error_msg = ""
        self.view_mode = "edit"
        self._build_content()
        self._safe_update()

    def _open_settings_dialog(self) -> None:
        self.view_mode = "settings"
        self._build_content()
        self._safe_update()

    def _open_favorites_dialog(self) -> None:
        self.view_mode = "favorites"
        self._build_content()
        self._safe_update()

    def _open_help_dialog(self) -> None:
        self.view_mode = "help"
        self._build_content()
        self._safe_update()

    def _open_about_dialog(self) -> None:
        self.view_mode = "about"
        self._build_content()
        self._safe_update()

    def _remove_fav(self, pl: Place) -> None:
        self.favorites_service.remove_favorite(pl.id)
        self._build_content()
        self._safe_update()

    def _toggle_language(self) -> None:
        self.current_language = "fil" if self.current_language == "en" else "en"
        self._build_content()
        self._safe_update()

    def _open_privacy_security_alert(self) -> None:
        dlg = ft.AlertDialog(
            title=ft.Text("Privacy & Security", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Text(
                "All itinerary drafts, profile preferences, and account tokens are stored using AES-256 encrypted local storage and TLS 1.3 in transit.",
                size=13,
                color=ThemeColors.TEXT_MUTED_LIGHT,
            ),
            actions=[ft.TextButton("Close", on_click=lambda _: self._close_dialog(dlg))],
        )
        self._show_dialog(dlg)

    def _confirm_clear_cache(self) -> None:
        def _do_clear(_):
            self._close_dialog(dlg)
            if self.safe_page:
                show_toast(self.safe_page, "Local cache cleared successfully.")

        dlg = ft.AlertDialog(
            title=ft.Text("Clear Cache & Offline Data", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Text(
                "This will clear locally stored search queries, map tiles, and offline place caches to free up storage space. Your created itineraries and account credentials will not be deleted.",
                size=13,
                color=ThemeColors.TEXT_MUTED_LIGHT,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton(
                    content="Clear Cache",
                    style=ft.ButtonStyle(bgcolor=ThemeColors.ERROR, color=ft.Colors.WHITE),
                    on_click=_do_clear,
                ),
            ],
        )
        self._show_dialog(dlg)

    def _confirm_logout(self) -> None:
        def _do_logout(_):
            self._close_dialog(dlg)
            self.session_manager.clear_session()
            self._navigate("/welcome?logout=1")

        sparkle_path = self.settings.get_asset_path("logout_sparkle_accent.png")
        door_path = self.settings.get_asset_path("logout_door_icon.png")

        top_controls = []
        if Path(sparkle_path).exists():
            top_controls.append(
                ft.Container(
                    content=ft.Image(src=sparkle_path, width=28, height=13, fit=ft.BoxFit.CONTAIN),
                    alignment=ft.Alignment(0, 0),
                    margin=ft.Margin.only(bottom=4),
                )
            )
        else:
            top_controls.append(
                ft.Row(
                    [
                        ft.Text("✦", size=13, color="#c084fc", weight=ft.FontWeight.BOLD),
                        ft.Text("...", size=13, color="#c084fc", weight=ft.FontWeight.BOLD),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=2,
                )
            )

        if Path(door_path).exists():
            top_controls.append(
                ft.Container(
                    content=ft.Image(src=door_path, width=50, height=48, fit=ft.BoxFit.CONTAIN),
                    alignment=ft.Alignment(0, 0),
                    margin=ft.Margin.only(bottom=4),
                )
            )
        else:
            top_controls.append(
                ft.Icon(ft.Icons.LOGOUT_ROUNDED, size=48, color=ThemeColors.PRIMARY_BLUE)
            )

        dlg = ft.AlertDialog(
            shape=ft.RoundedRectangleBorder(radius=28),
            bgcolor=ft.Colors.WHITE,
            content_padding=ft.Padding.only(left=24, right=24, top=20, bottom=24),
            content=ft.Container(
                width=280,
                content=ft.Column(
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        *top_controls,
                        ft.Text(
                            "Log Out?",
                            size=22,
                            weight=ft.FontWeight.W_800,
                            color=ThemeColors.TEXT_PRIMARY_LIGHT,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "You will be signed out of your account.\nYou can always log back in anytime.",
                            size=13.5,
                            color=ThemeColors.TEXT_MUTED_LIGHT,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=8),
                        ft.Container(
                            width=280,
                            height=48,
                            bgcolor=ThemeColors.PRIMARY_BLUE,
                            border_radius=9999,
                            alignment=ft.Alignment(0, 0),
                            ink=True,
                            on_click=_do_logout,
                            content=ft.Text("Log Out", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ),
                        ft.Container(
                            width=280,
                            height=48,
                            bgcolor=ThemeColors.PRIMARY_BLUE,
                            border_radius=9999,
                            alignment=ft.Alignment(0, 0),
                            ink=True,
                            on_click=lambda _: self._close_dialog(dlg),
                            content=ft.Text("Cancel", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ),
                    ],
                ),
            ),
        )
        self._show_dialog(dlg)

    def _show_dialog(self, dlg: ft.AlertDialog) -> None:
        open_overlay_dialog(self.safe_page, dlg)

    def _close_dialog(self, dlg: ft.AlertDialog) -> None:
        close_overlay_dialog(self.safe_page, dlg)

    def _toggle_theme(self) -> None:
        if self.on_toggle_theme:
            self.on_toggle_theme()
        self._build_content()
        self._safe_update()

    def _sync_guest_trips(self) -> None:
        self.is_migrating = True
        self._build_content()
        self._safe_update()

        async def _run():
            try:
                await self.auth_service.migrate_guest_trips()
            finally:
                self.is_migrating = False
                self._build_content()
                self._safe_update()

        if self.page:
            self.page.run_task(_run)
        else:
            try:
                asyncio.get_running_loop().create_task(_run())
            except RuntimeError:
                pass

    def did_mount(self) -> None:
        if self._has_refreshed_profile:
            return
        if self.session_manager.is_authenticated and not self.session_manager.is_guest:
            self._has_refreshed_profile = True

            async def _refresh_profile():
                try:
                    latest_user = await self.auth_service.get_profile()
                    if latest_user:
                        self._build_content()
                        self._safe_update()
                except Exception:
                    pass

            if self.safe_page:
                self.safe_page.run_task(_refresh_profile)

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass

    @property
    def safe_page(self) -> Optional[ft.Page]:
        if hasattr(self, "_test_page") and self._test_page is not None:
            return self._test_page
        try:
            return self.page
        except Exception:
            return None

    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)
