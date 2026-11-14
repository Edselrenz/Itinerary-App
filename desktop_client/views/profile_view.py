"""Profile, Edit Profile, Settings, Favorites, Help & Support, and About In-Page Views mirroring Ionic tabs/profile."""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from typing import Callable, Optional
import flet as ft

from desktop_client.components.dialogs import show_place_detail_dialog
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
        self.bgcolor = ThemeColors.BG_LIGHT

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

        self._build_content()

    def handle_back(self) -> bool:
        """Allows back navigation from subviews ('edit', 'settings', 'favorites', 'help', 'about') back to 'profile'."""
        if self.view_mode != "profile":
            self.view_mode = "profile"
            self._build_content()
            self._safe_update()
            return True
        return False

    def _build_content(self) -> None:
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

        title_header = ft.Text(
            "Profile",
            size=30,
            weight=ft.FontWeight.W_800,
            color=ThemeColors.TEXT_BLACK,
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
                bgcolor="#e2e8f0",
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
                        ft.Text(name_val, size=20, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                        ft.Text(handle_val, size=14, color=ThemeColors.TEXT_FAINT_LIGHT),
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
                                    color=ThemeColors.TEXT_BLACK,
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
                bgcolor=ThemeColors.PRIMARY_LIGHT,
                border=ft.Border.all(1, ThemeColors.CUSTOM_CARD_BORDER),
                border_radius=14,
                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                width=560,
            )

        # 5-Row Rounded White Card matching image_2d13c2.png verbatim
        menu_card = ft.Container(
            width=560,
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
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
                    ft.Divider(color="#f1f5f9", height=1),
                    self._create_menu_row(
                        icon=ft.Icons.FAVORITE,
                        icon_color=ThemeColors.PRIMARY_BLUE,
                        title="Favorites",
                        desc="Your favorite places, all saved in one place. Find them whenever you're ready to explore.",
                        on_click=lambda: self._open_favorites_dialog(),
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
                    self._create_menu_row(
                        icon=ft.Icons.HELP_ROUNDED,
                        icon_color=ThemeColors.PRIMARY_BLUE,
                        title="Help & Support",
                        desc="Get assistance and find answers to common questions.",
                        on_click=lambda: self._open_help_dialog(),
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
                    self._create_menu_row(
                        icon=ft.Icons.INFO_ROUNDED,
                        icon_color=ThemeColors.PRIMARY_BLUE,
                        title="About",
                        desc=f"Version {self.settings.app_version}.",
                        on_click=lambda: self._open_about_dialog(),
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
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

        return ft.Column(
            controls=[
                ft.Container(
                    width=560,
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
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
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
                                color=title_color or ThemeColors.TEXT_BLACK,
                            ),
                            ft.Text(
                                desc,
                                size=13,
                                color=ThemeColors.TEXT_FAINT_LIGHT,
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

        header_row = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ThemeColors.PRIMARY_BLUE,
                    icon_size=22,
                    tooltip="Back to profile",
                    on_click=lambda _: self._close_subview(),
                ),
                ft.Text("Edit Profile", size=24, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
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

        # Helper to build each labeled field matching image_2d1741.png
        def _labeled_field(label_text: str, initial_val: str, read_only: bool = False) -> tuple[ft.Control, ft.TextField]:
            tf = ft.TextField(
                value=initial_val,
                read_only=read_only,
                border_radius=10,
                border_color="#cbd5e1",
                focused_border_color=ThemeColors.PRIMARY_BLUE,
                bgcolor="#f1f5f9" if read_only else ft.Colors.WHITE,
                filled=True,
                dense=True,
                text_style=ft.TextStyle(
                    size=14,
                    color=ThemeColors.TEXT_FAINT_LIGHT if read_only else ThemeColors.TEXT_BLACK,
                ),
                content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            )
            block = ft.Column(
                controls=[
                    ft.Text(label_text, size=12, weight=ft.FontWeight.W_700, color=ThemeColors.TEXT_BLACK),
                    tf,
                ],
                spacing=4,
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
                        self.safe_page.snack_bar = ft.SnackBar(
                            content=ft.Text("Profile updated successfully!", color=ft.Colors.WHITE),
                            bgcolor=ThemeColors.SUCCESS,
                            open=True,
                        )
                        self.safe_page.update()
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
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=_save_changes,
        )

        return ft.Column(
            controls=[
                ft.Container(
                    width=440,
                    content=ft.Column(
                        controls=[
                            header_row,
                            ft.Container(height=12),
                            ft.Container(content=avatar_section, alignment=ft.Alignment(0, 0)),
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
                    ),
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =========================================================================
    # VIEW 3: SETTINGS IN-PAGE SUBVIEW (MATCHING image_2d1705.png EXACTLY)
    # =========================================================================
    def _build_settings_subview(self) -> ft.Control:
        is_dark = bool(self.safe_page and self.safe_page.theme_mode == ft.ThemeMode.DARK)

        header_row = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ThemeColors.PRIMARY_BLUE,
                    icon_size=22,
                    tooltip="Back to profile",
                    on_click=lambda _: self._close_subview(),
                ),
                ft.Text("Settings", size=26, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
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
                        ft.Text(title, size=15, weight=ft.FontWeight.W_700, color=ThemeColors.TEXT_BLACK),
                        ft.Text(subtitle, size=12, color=ThemeColors.TEXT_FAINT_LIGHT),
                    ],
                    spacing=2,
                )
                if subtitle
                else ft.Text(title, size=15, weight=ft.FontWeight.W_700, color=ThemeColors.TEXT_BLACK)
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
            width=560,
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
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
                    ft.Divider(color="#f1f5f9", height=1),
                    # Row 2: Notifications
                    _settings_row(
                        icon=ft.Icons.NOTIFICATIONS,
                        title="Notifications",
                        trailing=notif_switch,
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
                    # Row 3: Privacy & Security
                    _settings_row(
                        icon=ft.Icons.LOCK,
                        title="Privacy & Security",
                        on_click=lambda: self._open_privacy_security_alert(),
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
                    # Row 4: Language
                    _settings_row(
                        icon=ft.Icons.LANGUAGE,
                        title="Language",
                        trailing=ft.Text(
                            "Filipino" if self.current_language == "fil" else "English",
                            size=14,
                            weight=ft.FontWeight.W_500,
                            color=ThemeColors.TEXT_BLACK,
                        ),
                        on_click=lambda: self._toggle_language(),
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
                    # Row 5: App Appearance
                    _settings_row(
                        icon=ft.Icons.DARK_MODE_OUTLINED if is_dark else ft.Icons.WB_SUNNY_OUTLINED,
                        title="App Appearance",
                        trailing=ft.Text(
                            "Dark" if is_dark else "Light",
                            size=14,
                            weight=ft.FontWeight.W_500,
                            color=ThemeColors.TEXT_BLACK,
                        ),
                        on_click=lambda: self._toggle_theme(),
                    ),
                    ft.Divider(color="#f1f5f9", height=1),
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

        return ft.Column(
            controls=[
                ft.Container(
                    width=560,
                    content=ft.Column(
                        controls=[
                            header_row,
                            ft.Container(height=14),
                            settings_card,
                        ],
                        spacing=0,
                    ),
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =========================================================================
    # VIEW 4: FAVORITES IN-PAGE SUBVIEW
    # =========================================================================
    def _build_favorites_subview(self) -> ft.Control:
        favorites = self.favorites_service.get_favorites()
        q = self._fav_search_query.strip().lower()
        filtered = [
            p for p in favorites
            if (not q or q in p.name.lower() or q in (p.municipality_name or "").lower())
            and (self._fav_selected_cat == "ALL" or self._fav_selected_cat.lower() in (p.category or "").lower() or self._fav_selected_cat.lower() in (p.formatted_category or "").lower())
        ]

        header_row = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ThemeColors.PRIMARY_BLUE,
                    icon_size=22,
                    on_click=lambda _: self._close_subview(),
                ),
                ft.Text("Favorites", size=24, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
                ft.Container(
                    content=ft.Text(str(len(filtered)), size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    bgcolor=ThemeColors.PRIMARY_BLUE,
                    border_radius=10,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        cards: list[ft.Control] = []
        if filtered:
            for place in filtered:
                cards.append(
                    ft.Container(
                        bgcolor=ThemeColors.SURFACE_LIGHT,
                        border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
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
                                        ft.Text(place.name, size=14, weight=ft.FontWeight.BOLD),
                                        ft.Text(place.municipality_name or "Nueva Ecija", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                                        ft.Text(place.formatted_cost, size=12, weight=ft.FontWeight.BOLD, color=ThemeColors.EMERALD_PRIMARY),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.FAVORITE,
                                    icon_color=ft.Colors.RED_500,
                                    tooltip="Remove from favorites",
                                    on_click=lambda _, pl=place: self._remove_fav(pl),
                                ),
                                ft.FilledButton(
                                    content="View Details",
                                    style=ft.ButtonStyle(bgcolor=ThemeColors.PRIMARY_BLUE, color=ft.Colors.WHITE),
                                    on_click=lambda _, pl=place: show_place_detail_dialog(self.safe_page, pl, on_navigate=self.on_navigate) if self.safe_page else None,
                                ),
                            ],
                            spacing=12,
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
                            ft.Text("No Favorite Places Saved", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("Browse destinations and tap the heart icon to save your personal favorite spots right here.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
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

        return ft.Column(
            controls=[
                ft.Container(
                    width=560,
                    content=ft.Column(controls=[header_row, ft.Container(height=12), *cards], spacing=10),
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =========================================================================
    # VIEW 5 & 6: HELP & SUPPORT AND ABOUT IN-PAGE SUBVIEWS
    # =========================================================================
    def _build_help_subview(self) -> ft.Control:
        header_row = ft.Row(
            controls=[
                ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=ThemeColors.PRIMARY_BLUE, icon_size=22, on_click=lambda _: self._close_subview()),
                ft.Text("Help & Support", size=24, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
            ],
            spacing=8,
        )
        card = ft.Container(
            width=560,
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=20,
            padding=22,
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Text("Frequently Asked Questions", size=16, weight=ft.FontWeight.W_800),
                    ft.Text("How does the app generate suggested itineraries?", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text("Our pacing engine analyzes 2,673 provincial points of interest, your selected pacing, daily budget, and starting destination to calculate optimal daily road routes via Open Source Routing Machine (OSRM).", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ft.Divider(color="#f1f5f9", height=1),
                    ft.Text("Can I use the app offline in remote areas?", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text("Yes! All created itineraries, destination notes, and visited map areas are cached locally so you can travel through the Sierra Madre mountains with confidence.", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                    ft.Divider(color="#f1f5f9", height=1),
                    ft.Text("What are the emergency provincial hotlines?", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text("PDRRMO Nueva Ecija: (044) 940 3388\nPNP Nueva Ecija: 117 / (044) 463 0565\nTourism Office: tourism@nuevaecija.gov.ph", size=12, color=ThemeColors.TEXT_MUTED_LIGHT),
                ],
            ),
        )
        return ft.Column(
            controls=[ft.Container(width=560, content=ft.Column(controls=[header_row, ft.Container(height=12), card]))],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_about_subview(self) -> ft.Control:
        header_row = ft.Row(
            controls=[
                ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=ThemeColors.PRIMARY_BLUE, icon_size=22, on_click=lambda _: self._close_subview()),
                ft.Text("About", size=24, weight=ft.FontWeight.W_800, color=ThemeColors.TEXT_BLACK),
            ],
            spacing=8,
        )
        card = ft.Container(
            width=560,
            bgcolor=ThemeColors.SURFACE_LIGHT,
            border=ft.Border.all(1, ThemeColors.BORDER_LIGHT),
            border_radius=20,
            padding=24,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.INFO_ROUNDED, size=44, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text("Nueva Ecija Travel Companion", size=18, weight=ft.FontWeight.W_800),
                    ft.Text("Trip mo, trip ko", size=13, weight=ft.FontWeight.BOLD, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text(
                        "Comprehensive travel and itinerary planning companion engineered for travelers exploring all 32 municipalities and 5 component cities of Nueva Ecija, Philippines.",
                        size=12,
                        color=ThemeColors.TEXT_MUTED_LIGHT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Divider(color="#f1f5f9", height=12),
                    ft.Row(
                        controls=[
                            ft.Text("Version", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ft.Text(self.settings.app_version, size=13, weight=ft.FontWeight.BOLD),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(color="#f1f5f9", height=12),
                    ft.Row(
                        controls=[
                            ft.Text("Open Data Attribution", size=13, color=ThemeColors.TEXT_MUTED_LIGHT),
                            ft.Text("OpenStreetMap & GIS Nueva Ecija", size=13, weight=ft.FontWeight.BOLD),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
            ),
        )
        return ft.Column(
            controls=[ft.Container(width=560, content=ft.Column(controls=[header_row, ft.Container(height=12), card]))],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
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
                self.safe_page.snack_bar = ft.SnackBar(
                    content=ft.Text("Local cache cleared successfully."),
                    open=True,
                )
                self.safe_page.update()

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

        dlg = ft.AlertDialog(
            title=ft.Text("Log Out?", size=20, weight=ft.FontWeight.W_800, text_align=ft.TextAlign.CENTER),
            content=ft.Column(
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Icon(ft.Icons.LOGOUT_ROUNDED, size=44, color=ThemeColors.PRIMARY_BLUE),
                    ft.Text(
                        "You will be signed out of your account. You can always log back in anytime.",
                        size=13,
                        color=ThemeColors.TEXT_MUTED_LIGHT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(
                        width=260,
                        height=42,
                        bgcolor=ThemeColors.PRIMARY_BLUE,
                        border_radius=20,
                        alignment=ft.Alignment(0, 0),
                        ink=True,
                        on_click=_do_logout,
                        content=ft.Text("Log Out", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ),
                    ft.Container(
                        width=260,
                        height=42,
                        bgcolor=ThemeColors.PRIMARY_BLUE,
                        border_radius=20,
                        alignment=ft.Alignment(0, 0),
                        ink=True,
                        on_click=lambda _: self._close_dialog(dlg),
                        content=ft.Text("Cancel", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ),
                ],
            ),
        )
        self._show_dialog(dlg)

    def _show_dialog(self, dlg: ft.AlertDialog) -> None:
        if self.page:
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()

    def _close_dialog(self, dlg: ft.AlertDialog) -> None:
        dlg.open = False
        if self.page:
            self.page.update()

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
