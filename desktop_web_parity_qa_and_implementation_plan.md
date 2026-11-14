# Nueva Ecija Travel Itinerary App ("Trip mo, trip ko") — Desktop (`desktop_client/`) vs. Web (`Project/`) QA Audit v3 & Antigravity Remediation Specification

**Repository**: [https://github.com/Edselrenz/Itinerary-App](https://www.google.com/search?q=https://github.com/Edselrenz/Itinerary-App)  
**Target Desktop Package**: `desktop_client/` (Python 3.12+ / Flet `>=1.1.2` / `httpx` / `pytest`)  
**Reference Web Application**: `Project/` (Ionic 9 / Angular 22 / Leaflet 1.9 / TypeScript) & [https://edselrenz.github.io/Itinerary-App](https://www.google.com/search?q=https://edselrenz.github.io/Itinerary-App)  
**Backend API Reference**: `backend/app/schemas/user.py` & `backend/app/schemas/itinerary.py` (FastAPI / SQLAlchemy / PostGIS)  
**Applied Engineering & Design Standards**: `@coding-and-system-development` & `@anti-generic-frontend-design`

---

## 1. Executive Summary & Root-Cause Analysis of the 4 Reported Failures (QA v3)

Following the previous iteration, hands-on testing of the Flet `1.1.2` desktop application exposed **4 critical functional and layout regressions** compared to the Web App (`Project/`). Below is the exact technical root cause of each defect and its required fix:

| # | User-Reported Issue | Root Cause in Flet `1.1.2` & FastAPI Contract | Exact Fix Required |
| :--- | :--- | :--- | :--- |
| **1** | **"The `'You are offline'` notice spans the whole application"** | In Flet `1.1.2`, placing `OfflineHostBanner` (an `ft.Container` with `bgcolor="#0f172a"`) as an unpositioned child inside `main.py`'s root `ft.Stack(expand=True)` (or without `expand=False` and fixed `height=52`) causes Flutter's `StackFit.expand` behavior to stretch the dark `#0f172a` background across the **entire 1280×840 application window**, covering the UI. | **Never** place `OfflineHostBanner` as an unpositioned child of `ft.Stack(expand=True)`. Render `OfflineHostBanner` as the first non-expanding child (`expand=False`, fixed `height=52`) inside the root `ft.Column(spacing=0, expand=True)` directly above `content_area`, wrapped in a centered floating pill (`width=620, height=44, border_radius=12`), with a working `[✕]` dismiss button (`self.visible = False; self.page.update()`). |
| **2** | **"The map is not working properly, it does not display the places like the website, it does not show the routing"** | 1) **`flet_map` Incompatibility**: `flet_map` is either absent or incompatible with Flet `1.1.2`'s control tree, and `ft.canvas` shapes (`cv.Circle`) **do not support click handlers** in Flet.<br>2) **Missing 2,673 OSM Places**: `PlaceService` failed to resolve the relative path to `Project/src/assets/data/osm_places.json` (`2,673` POIs) when launched from `desktop_client/` and did not implement zoom-aware marker clustering (`zoom < 14` → `#0084ff` numbered cluster circles; `zoom >= 14` → category-colored teardrop pins).<br>3) **Missing Route Polyline & Stop Projection**: `ItineraryRouteMap` and `MapView` failed to extract `(lat, lng)` from both `item.place.latitude/longitude` and `item.custom_lat/custom_lng`, failed to query OSRM (`https://router.project-osrm.org/route/v1/driving/...?overview=full&geometries=polyline`) or decode `day_overview_polyline` / geodesic spline fallback, and failed to project `(lat, lng)` into Web-Mercator pixel coordinates `(x, y)` on an `ft.canvas.Canvas` layer over 256×256 OpenStreetMap tiles (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`). | Build a **100% Pure-Flet `1.1.2` Web-Mercator Slippy Map Engine (`desktop_client/components/slippy_map_canvas.py`)** that layers:<br>• **Layer 1**: 256×256 OpenStreetMap `ft.Image` tiles positioned via Web-Mercator math with drag-to-pan (`ft.GestureDetector`) and zoom (`+`/`-`).<br>• **Layer 2**: `ft.canvas.Canvas` with `cv.Path` drawing the `#0284c7` / `#2563eb` (`stroke_width=5`) OSRM road polyline (plus white casing `stroke_width=8`) and dashed walk connectors.<br>• **Layer 3**: Clickable `ft.Container` controls positioned at `(px, py)` for **Blue Marker Clusters (`#0084ff`)**, **Category Teardrop Pins**, and **Numbered Route Stop Badges (`1..N`)**. |
| **3** | **"The edit profile does not really work properly"** | **Backend Schema Mismatch (`backend/app/schemas/user.py` vs. `desktop_client/models/user.py`)**:<br>• FastAPI `UserOut` returns `first_name`, `last_name`, `username_normalized`, `email_normalized` — it **never** returns `full_name` or `email`!<br>• FastAPI `UserUpdateIn` (`PATCH /api/v1/auth/me`) accepts `first_name`, `last_name`, `username`, `current_password`, `new_password` — it **ignores** `full_name` and `avatar_url`!<br>• `User.from_dict()` read `data.get("full_name", "")`, wiping out the user's name after login or update, and Guest/Offline mode lacked local persistence (`profile_extra.json`) for `first_name`, `last_name`, `middle_initial`, `birthday`, `gender`, `phone_number`, and `avatar_url` (plus native file picker for `Change Photo`). | 1) Update `desktop_client/models/user.py` so `User.from_dict()` reads `first_name`, `last_name`, `username_normalized`, and `email_normalized` (computing `full_name` dynamically), and `UserUpdatePayload.to_dict()` sends `first_name`, `last_name`, `username`.<br>2) Persist extended profile fields (`middle_initial`, `birthday`, `gender`, `phone_number`, `avatar_url`) and Guest profile edits locally in `LocalStorage` (`profile_extra_{user_id}`), merging them on load and save.<br>3) Wire `[Change Photo]` in `ProfileView` to open a native file dialog (`tkinter.filedialog` / `ft.FilePicker`) with preset avatar fallbacks. |
| **4** | **"Both the custom and suggested itinerary also does not work the same as the web"** | • **`SuggestedWizardView`** used a single static view instead of the Web App's **3-View State Machine (`view_mode = "form" | "itinerary" | "nearby"`)** in `suggested-wizard.page.html/.ts`, missing the pre-save preview mode (`save_immediately=False`), `set_active_draft_itinerary(plan)` (needed for `[Full Map]` handoff), collapsible `Travel Notes & Planning Assumptions`, embedded `ItineraryRouteMap`, inter-stop leg commute badges (`🚗 X.X km • ~X mins drive • Y mins tricycle • Est. Fare ₱XX–₱YY`), `Nearby Places in [Municipality]` view (`Restaurants | Hospital & Pharmacies | Stores` with `[+ Add to Day X]`), and `[Customize in Builder]` handoff.<br>• **`CustomBuilderView`** used a cramped 2-column split-pane instead of the Web App's **3-View State Machine (`active_view = "form" | "browse" | "timeline"`)** in `custom-builder.page.html/.ts` with the top segmented switcher (`[+ Add Places]` \| `[📅 Your Itinerary (N)]`), target day selector (`Scheduling for: Day 1 (0) | Day 2 (0) | [+]`), stateful `[+ Add]` / `[✓ Added]` place cards, editable Trip Settings header (`syncDaysWithDateRange`), `[🕒 Auto-Schedule]`, embedded `ItineraryRouteMap`, inter-stop commute leg badges, `[Edit Stop]` modal with `Move to Day` dropdown, and `[+ Add Off-Grid Custom Venue]` modal with Nueva Ecija geofence validation (`Lat 15.15–16.15, Lng 120.70–121.40`). | Rewrite `SuggestedWizardView` and `CustomBuilderView` to mirror `suggested-wizard.page.html/.ts` and `custom-builder.page.html/.ts` 1:1, including their exact 3-view state machines, top view switcher, embedded `ItineraryRouteMap`, inter-stop leg commute calculator, draft itinerary handoff to `MapView` (`itineraryId="draft"`), and `[Customize in Builder]` handoff. |

---

## 2. Mandatory Fix 1: Non-Blocking `OfflineHostBanner` & Root App Shell (`main.py`)

### 2.1 Why the Offline Notice Covered the Entire Window
In Flet `1.1.2`, if a container with `bgcolor="#0f172a"` is placed inside `ft.Stack(expand=True)` without explicit `top`, `left`, `right`, `height` coordinates—or if its parent wrapper has `expand=True`—Flutter expands that container to fill the entire `1280×840` window.

### 2.2 Complete Replacement for `desktop_client/components/offline_banner.py`
Replace `desktop_client/components/offline_banner.py` with this strictly bounded (`expand=False`, fixed `height=52`) top notification bar that **never** stretches across the application:

```python
"""Compact, non-blocking top connectivity banner matching Project/src/app/app.component.html."""

from __future__ import annotations

from typing import Callable, Optional
import flet as ft

from desktop_client.services.connectivity_service import ConnectivityService, ConnectivityState


class OfflineHostBanner(ft.Container):
    """Floating pill banner (`.offline-host-banner`) rendered at the top of the root Column.

    CRITICAL FLET 1.1.2 LAYOUT RULE:
    - `expand` MUST be `False` and `height` MUST be fixed (`52`) when visible (`0` when hidden)
      so it NEVER stretches across the application viewport.
    """

    def __init__(
        self,
        connectivity_service: ConnectivityService,
        on_retry: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__()
        self._connectivity = connectivity_service
        self._on_retry = on_retry

        # Strictly non-expanding top bar wrapper
        self.expand = False
        self.height = 52
        self.visible = False
        self.alignment = ft.Alignment(0, 0)
        self.padding = ft.Padding.only(top=6, bottom=2, left=16, right=16)
        self.bgcolor = ft.Colors.TRANSPARENT

        self._title_text = ft.Text(
            "You are offline",
            size=12,
            weight=ft.FontWeight.W_700,
            color="#f8fafc",
        )
        self._sub_text = ft.Text(
            "Showing cached Nueva Ecija places & saved itineraries",
            size=11,
            color="#94a3b8",
        )
        self._retry_btn = ft.TextButton(
            content=ft.Text("Retry", size=11, weight=ft.FontWeight.W_700, color="#38bdf8"),
            on_click=self._handle_retry,
            style=ft.ButtonStyle(
                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                bgcolor="#1e293b",
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )
        self._dismiss_btn = ft.IconButton(
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_size=15,
            icon_color="#94a3b8",
            tooltip="Dismiss offline notice",
            on_click=self._handle_dismiss,
            style=ft.ButtonStyle(padding=ft.Padding.all(4)),
        )

        # Inner dark pill card matching Web App `.offline-banner-content` (max-width 620px, height 42px)
        self.content = ft.Container(
            width=620,
            height=42,
            bgcolor="#0f172a",
            border=ft.Border.all(1, "#334155"),
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=14, vertical=6),
            shadow=ft.BoxShadow(
                blur_radius=12,
                color=ft.Colors.with_opacity(0.18, "#0f172a"),
                offset=ft.Offset(0, 4),
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.CLOUD_OFF_ROUNDED, color="#f59e0b", size=18),
                            ft.Column(
                                spacing=0,
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[self._title_text, self._sub_text],
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[self._retry_btn, self._dismiss_btn],
                    ),
                ],
            ),
        )

        self._connectivity.subscribe(self.sync_state)

    def sync_state(self, state: ConnectivityState) -> None:
        should_show = (not state.is_online) and (not state.banner_dismissed)
        self.visible = should_show
        self.height = 52 if should_show else 0
        if state.is_checking:
            self._title_text.value = "Reconnecting to server..."
        else:
            self._title_text.value = "You are offline"
        try:
            if self.page:
                self.update()
        except Exception:
            pass

    def _handle_retry(self, _e: ft.ControlEvent) -> None:
        if self._on_retry:
            self._on_retry()

    def _handle_dismiss(self, _e: ft.ControlEvent) -> None:
        self._connectivity.dismiss_banner()
        self.visible = False
        self.height = 0
        try:
            if self.page:
                self.page.update()
        except Exception:
            pass
```

### 2.3 Root Layout Structure in `desktop_client/main.py`
In `desktop_client/main.py`, do **not** put `OfflineHostBanner` inside an unpositioned `ft.Stack`. Use a clean vertical `ft.Column(spacing=0, expand=True)`:

```python
# Inside ItineraryDesktopApp._build_layout() in desktop_client/main.py:
self._offline_banner = OfflineHostBanner(
    connectivity_service=self.connectivity_service,
    on_retry=self._trigger_connectivity_check,
)
self._content_area = ft.Container(expand=True, bgcolor="#f8f9fa")
self._bottom_tab_bar = BottomTabBar(
    current_route=self._current_route,
    on_navigate=self.navigate,
)

self._root = ft.Column(
    spacing=0,
    expand=True,
    controls=[
        self._offline_banner,   # Fixed height=52 when offline, height=0 when online/dismissed
        self._content_area,     # expand=True main router outlet
        self._bottom_tab_bar,   # Fixed height=68 bottom navigation bar
    ],
)
self.page.add(self._root)
```

---

## 3. Mandatory Fix 2: `Edit Profile` & Backend `UserOut` / `UserUpdateIn` Schema Alignment

### 3.1 Exact FastAPI Schema Contract (`backend/app/schemas/user.py`)
Inspecting `backend/app/schemas/user.py` reveals why `Edit Profile` failed:
- **`UserOut` (returned by `GET /api/v1/auth/me` and `PATCH /api/v1/auth/me`)**:
  ```python
  class UserOut(BaseModel):
      id: uuid.UUID
      first_name: str
      last_name: str
      username_normalized: str
      email_normalized: str
      is_active: bool
      created_at: datetime
  ```
- **`UserUpdateIn` (expected by `PATCH /api/v1/auth/me`)**:
  ```python
  class UserUpdateIn(BaseModel):
      first_name: str | None = Field(default=None, min_length=1, max_length=100)
      last_name: str | None = Field(default=None, min_length=1, max_length=100)
      username: str | None = Field(default=None, min_length=3, max_length=100)
      current_password: str | None = Field(default=None, min_length=8, max_length=128)
      new_password: str | None = Field(default=None, min_length=8, max_length=128)
  ```
- **Why the Desktop App Broke**:
  1. `desktop_client/models/user.py` looked for `data.get("full_name")` and `data.get("email")`, which do not exist in `UserOut`, causing the user's name and email to become blank (`""`) or revert after saving!
  2. `desktop_client/models/user.py` sent `{"full_name": ...}` in `PATCH /api/v1/auth/me`, which FastAPI silently ignored because `UserUpdateIn` only accepts `first_name`, `last_name`, and `username`!
  3. Extended profile fields from the Web App (`middle_initial`, `birthday`, `gender`, `phone_number`, `avatar_url`, `default_daily_budget`) and Guest Mode profile edits must be saved in `LocalStorage` (`profile_extra_{user_id}`) and merged into the active `User` object, exactly like `Project/src/app/features/auth/profile/profile.page.ts` (`ne_profile_extra_${user.id}`).

### 3.2 Complete Replacement for `desktop_client/models/user.py`

```python
"""User and authentication domain models aligned 1:1 with backend/app/schemas/user.py and Web App."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class User:
    """Represents an authenticated or guest user with backend + local extended profile fields."""

    id: str
    first_name: str = ""
    last_name: str = ""
    middle_initial: str = ""
    username: str = ""
    email: str = ""
    birthday: str = ""
    gender: str = ""
    phone_number: str = ""
    avatar_url: Optional[str] = None
    is_active: bool = True
    is_guest: bool = False
    created_at: Optional[str] = None
    preferences: list[str] = field(default_factory=list)
    default_daily_budget: float = 3000.0

    @property
    def full_name(self) -> str:
        """Construct display name from first_name, middle_initial, and last_name."""
        parts: list[str] = []
        if self.first_name.strip():
            parts.append(self.first_name.strip())
        if self.middle_initial.strip():
            mi = self.middle_initial.strip().rstrip(".")
            parts.append(f"{mi}.")
        if self.last_name.strip():
            parts.append(self.last_name.strip())
        joined = " ".join(parts).strip()
        if joined:
            return joined
        if self.username.strip():
            return self.username.strip()
        if self.email.strip():
            return self.email.split("@")[0]
        return "Guest Explorer" if self.is_guest else "Traveler"

    @classmethod
    def from_dict(cls, data: dict[str, Any], extra: Optional[dict[str, Any]] = None) -> "User":
        extra = extra or {}
        raw_first = str(data.get("first_name") or extra.get("first_name") or "").strip()
        raw_last = str(data.get("last_name") or extra.get("last_name") or "").strip()

        # Fallback if legacy data only stored full_name
        if not raw_first and not raw_last and data.get("full_name"):
            tokens = str(data.get("full_name")).strip().split(" ", 1)
            raw_first = tokens[0]
            raw_last = tokens[1] if len(tokens) > 1 else ""

        email_val = str(
            data.get("email_normalized")
            or data.get("email")
            or extra.get("email")
            or ""
        ).strip()
        username_val = str(
            data.get("username_normalized")
            or data.get("username")
            or extra.get("username")
            or (email_val.split("@")[0] if email_val else "")
        ).strip()

        prefs = extra.get("preferences", data.get("preferences", []))
        if isinstance(prefs, str):
            prefs = [p.strip() for p in prefs.split(",") if p.strip()]

        return cls(
            id=str(data.get("id", "guest-local")),
            first_name=raw_first,
            last_name=raw_last,
            middle_initial=str(extra.get("middle_initial") or data.get("middle_initial") or "").strip(),
            username=username_val,
            email=email_val,
            birthday=str(extra.get("birthday") or data.get("birthday") or "").strip(),
            gender=str(extra.get("gender") or data.get("gender") or "").strip(),
            phone_number=str(extra.get("phone_number") or data.get("phone_number") or "").strip(),
            avatar_url=extra.get("avatar_url") or data.get("avatar_url"),
            is_active=bool(data.get("is_active", True)),
            is_guest=bool(data.get("is_guest", False)),
            created_at=data.get("created_at"),
            preferences=list(prefs) if isinstance(prefs, list) else [],
            default_daily_budget=float(
                extra.get("default_daily_budget", data.get("default_daily_budget", 3000.0)) or 3000.0
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_initial": self.middle_initial,
            "username": self.username,
            "username_normalized": self.username,
            "email": self.email,
            "email_normalized": self.email,
            "full_name": self.full_name,
            "birthday": self.birthday,
            "gender": self.gender,
            "phone_number": self.phone_number,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "is_guest": self.is_guest,
            "created_at": self.created_at,
            "preferences": self.preferences,
            "default_daily_budget": self.default_daily_budget,
        }

    @classmethod
    def create_guest(cls, extra: Optional[dict[str, Any]] = None) -> "User":
        extra = extra or {}
        return cls(
            id="guest-local",
            first_name=str(extra.get("first_name") or "Guest"),
            last_name=str(extra.get("last_name") or "Explorer"),
            middle_initial=str(extra.get("middle_initial") or ""),
            username=str(extra.get("username") or "guest_explorer"),
            email=str(extra.get("email") or "guest@local.offline"),
            birthday=str(extra.get("birthday") or ""),
            gender=str(extra.get("gender") or ""),
            phone_number=str(extra.get("phone_number") or ""),
            avatar_url=extra.get("avatar_url"),
            is_active=True,
            is_guest=True,
            preferences=list(extra.get("preferences", ["Nature & Parks", "Food Trip", "Culture & History"])),
            default_daily_budget=float(extra.get("default_daily_budget", 2500.0)),
        )


@dataclass
class AuthTokens:
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuthTokens":
        return cls(
            access_token=str(data.get("access_token", "")),
            refresh_token=data.get("refresh_token"),
            token_type=str(data.get("token_type", "bearer")),
        )


@dataclass
class UserUpdatePayload:
    """Payload for updating profile across FastAPI PATCH /api/v1/auth/me + LocalStorage extended metadata."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_initial: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    birthday: Optional[str] = None
    gender: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[list[str]] = None
    default_daily_budget: Optional[float] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

    def to_backend_dict(self) -> dict[str, Any]:
        """Exact fields accepted by FastAPI `UserUpdateIn` (`backend/app/schemas/user.py`)."""
        payload: dict[str, Any] = {}
        if self.first_name is not None and len(self.first_name.strip()) >= 1:
            payload["first_name"] = self.first_name.strip()
        if self.last_name is not None and len(self.last_name.strip()) >= 1:
            payload["last_name"] = self.last_name.strip()
        if self.username is not None and len(self.username.strip()) >= 3:
            payload["username"] = self.username.strip()
        if self.current_password and self.new_password:
            payload["current_password"] = self.current_password
            payload["new_password"] = self.new_password
        return payload

    def to_extra_dict(self) -> dict[str, Any]:
        """Extended profile fields persisted locally in `profile_extra_{user_id}`."""
        extra: dict[str, Any] = {}
        for key in (
            "first_name",
            "last_name",
            "middle_initial",
            "username",
            "email",
            "birthday",
            "gender",
            "phone_number",
            "avatar_url",
            "preferences",
            "default_daily_budget",
        ):
            val = getattr(self, key)
            if val is not None:
                extra[key] = val
        return extra
```

### 3.3 Updating `AuthService.update_profile` (`desktop_client/services/auth_service.py`)
Ensure `AuthService.update_profile(payload: UserUpdatePayload)` works in **both Authenticated Mode, Offline Mode, and Guest Mode**:
1. Save `payload.to_extra_dict()` into `self._storage.load_json("profile_extra.json", default={})[user_id]` immediately.
2. If the user is authenticated (`not current_user.is_guest`) and `payload.to_backend_dict()` is non-empty, send `PATCH /api/v1/auth/me` with `payload.to_backend_dict()`. If the backend responds with `200 OK`, parse `User.from_dict(resp, extra=saved_extra)`. If the backend is offline (`ApiError` with status `0`), fall back gracefully to updating the local `User` session object and persist it so edits are never lost.
3. If the user is in **Guest Mode** (`current_user.is_guest`), update the guest `User` in `self._session` and save to `profile_extra.json["guest-local"]` so Guest travelers can also customize their name, avatar photo, default daily budget, and travel preferences.

### 3.4 Working `Edit Profile` Modal & Native Photo Picker (`desktop_client/views/profile_view.py`)
In `desktop_client/views/profile_view.py`:
- **Never** check `if user.is_guest: return` to block opening the Edit Profile dialog or changing preferences/budget.
- Provide the exact Web App Edit Profile fields (`Project/src/app/features/auth/profile/profile.page.html`):
  - **Profile Photo Preview** (`ft.CircleAvatar` or `68×68` rounded `ft.Image`) + **`[Change Photo]`** button (uses Python's standard `tkinter.filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp")])` in a helper or preset avatar chips so it works reliably on Windows/macOS/Linux without Flet `FilePicker` overlay bugs) + **`[Remove Photo]`** button.
  - **First Name** (`first_name`, required), **Last Name** (`last_name`, required), **Middle Initial** (`middle_initial`, max 2 chars).
  - **Username** (`username`, min 3 chars) and **Email** (`email`, read-only for registered accounts, editable for guest).
  - **Birthday** (`YYYY-MM-DD`), **Gender** (`ft.Dropdown`: `Male`, `Female`, `Non-binary`, `Prefer not to say`), **Phone Number** (`+63 9XX XXX XXXX`).
  - **Default Daily Budget (PHP)** (`default_daily_budget`).
- When `[Save Changes]` is clicked:
  - Validate that `first_name` is non-empty.
  - Call `self._auth_service.update_profile(payload)`.
  - Close the dialog (`self.page.pop_dialog()` or `dialog.open = False`), call `self._refresh_profile_ui()`, show a green toast (`"Profile updated successfully!"`), and call `self.page.update()`.

---

## 4. Mandatory Fix 3: Pure-Flet `1.1.2` Interactive Slippy Map, Marker Clustering & Road Routing Engine

### 4.1 Why the Previous Map Failed
1. **`flet_map` is not reliable in Flet `1.1.2`**, and drawing markers as `ft.canvas.Circle` shapes makes them **unclickable** because Flet canvas shapes do not emit pointer events.
2. **Dataset Path Resolution**: When running `python -m desktop_client.main` or `flet run desktop_client/main.py`, relative paths like `"Project/src/assets/data/osm_places.json"` fail if the working directory is `desktop_client/`. You **must** resolve the repository root via `Path(__file__).resolve().parents[2] / "Project" / "src" / "assets" / "data" / "osm_places.json"`.
3. **Missing Web-Mercator Tile + Canvas + Overlay Stack Architecture**: To display places and routes exactly like Leaflet on the Web App (`map.page.ts` and `itinerary-route-map.component.ts`), the map component must layer **3 synchronized coordinate planes** inside a clipped `ft.Stack`:
   - **Plane 1 (Tile Layer)**: 256×256 OpenStreetMap `ft.Image` tiles (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`) positioned using exact Web-Mercator math (`latlon_to_world_px(lat, lon, zoom)`), wrapped in an `ft.GestureDetector` that supports smooth mouse drag panning (`on_pan_update`) and scroll-wheel / button zooming (`zoom 9..18`).
   - **Plane 2 (Vector Route Polyline Layer)**: An `ft.canvas.Canvas` filling the viewport that projects every `(lat, lng)` vertex of the active day's OSRM road route (`https://router.project-osrm.org/route/v1/driving/{lng1},{lat1};{lng2},{lat2}?overview=full&geometries=polyline` or `generate_geodesic_arc` fallback) into viewport pixel coordinates `(px, py)` and draws:
     - Outer white route casing (`cv.Paint(color="#ffffff", stroke_width=8, style=ft.PaintingStyle.STROKE, stroke_cap=ft.StrokeCap.ROUND, stroke_join=ft.StrokeJoin.ROUND)`)
     - Inner road route line (`cv.Paint(color="#0284c7", stroke_width=5, style=ft.PaintingStyle.STROKE, stroke_cap=ft.StrokeCap.ROUND, stroke_join=ft.StrokeJoin.ROUND)`)
   - **Plane 3 (Interactive Marker & Cluster Layer)**: Positioned `ft.Container` controls (`left=px - radius, top=py - radius`) placed on top of the canvas so every marker has a real `on_click` handler and `tooltip`:
     - **At Zoom `< 14` (Discovery Mode)**: Grid-based spatial clustering (`cluster_radius_px = 55`) groups nearby POIs into **Web-App-identical Blue Numbered Cluster Circles (`#0084ff` outer ring, `#0066cc` inner core, white bold count)** that zoom into the cluster center by `+2` levels on click!
     - **At Zoom `>= 14` (or singleton clusters)**: Category-colored circular/teardrop pins (`#10b981` Nature, `#f97316` Food, `#8b5cf6` Culture, `#ec4899` Shopping, `#06b6d4` Resort, `#64748b` Essential) with category icons that open the **`PlaceDetailSheet`** on click!
     - **In Route Mode (`ItineraryRouteMap` & `MapView` Follow-Route Mode)**: Clickable **Numbered Stop Badges (`1`, `2`, `3`... in `#2563eb` or `#f97316` when active, `30×30px`, `2.5px` white border)** with a floating white pill label showing `1. [Stop Name]`!

### 4.2 Complete Implementation for `desktop_client/components/slippy_map_canvas.py`
Create `desktop_client/components/slippy_map_canvas.py` with the complete Web-Mercator slippy map, OSRM road router, spatial marker clusterer, and interactive pin overlay:

```python
"""Pure-Flet 1.1.2 Web-Mercator Slippy Map with OSM tiles, spatial marker clustering, and OSRM road routing."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional
import flet as ft
import flet.canvas as cv
import httpx

from desktop_client.models.place import Place
from desktop_client.utils.polyline import decode_polyline, generate_geodesic_arc


# Category Pin Palette matching Project/src/app/features/map/map.page.scss (.pin-cat-*)
CATEGORY_PIN_STYLE: dict[str, tuple[str, ft.IconData]] = {
    "tourist_attraction": ("#10b981", ft.Icons.LANDSCAPE_ROUNDED),
    "nature_park": ("#10b981", ft.Icons.PARK_ROUNDED),
    "attraction": ("#10b981", ft.Icons.PHOTO_CAMERA_ROUNDED),
    "restaurant": ("#f97316", ft.Icons.RESTAURANT_ROUNDED),
    "cafe": ("#f97316", ft.Icons.LOCAL_CAFE_ROUNDED),
    "fast_food": ("#f97316", ft.Icons.FASTFOOD_ROUNDED),
    "church_religious": ("#8b5cf6", ft.Icons.ACCOUNT_BALANCE_ROUNDED),
    "museum_cultural": ("#8b5cf6", ft.Icons.MUSEUM_ROUNDED),
    "shopping_market": ("#ec4899", ft.Icons.SHOPPING_BAG_ROUNDED),
    "supermarket": ("#ec4899", ft.Icons.SHOPPING_CART_ROUNDED),
    "convenience_store": ("#ec4899", ft.Icons.STOREFRONT_ROUNDED),
    "resort_swimming": ("#06b6d4", ft.Icons.POOL_ROUNDED),
    "hotel_accommodation": ("#06b6d4", ft.Icons.HOTEL_ROUNDED),
}


@dataclass
class RouteStopPin:
    """Represents a numbered itinerary stop on the route map."""

    index: int          # 0-based index (displayed as index + 1)
    title: str
    lat: float
    lng: float
    planned_time: str = ""
    category: str = "attraction"
    place: Optional[Place] = None


def latlon_to_world_px(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    """Project (lat, lon) in degrees to global Web-Mercator pixel coordinates at integer zoom."""
    lat = max(-85.05112878, min(85.05112878, float(lat)))
    lon = float(lon)
    scale = 256.0 * (2 ** zoom)
    x = (lon + 180.0) / 360.0 * scale
    sin_lat = math.sin(math.radians(lat))
    y = (0.5 - math.log((1.0 + sin_lat) / (1.0 - sin_lat)) / (4.0 * math.pi)) * scale
    return x, y


def world_px_to_latlon(wx: float, wy: float, zoom: int) -> tuple[float, float]:
    """Inverse project global Web-Mercator pixel coordinates (wx, wy) back to (lat, lon)."""
    scale = 256.0 * (2 ** zoom)
    lon = (wx / scale) * 360.0 - 180.0
    n = math.pi - 2.0 * math.pi * (wy / scale)
    lat = math.degrees(math.atan(0.5 * (math.exp(n) - math.exp(-n))))
    return lat, lon


def fetch_osrm_road_geometry(coords: list[tuple[float, float]], timeout: float = 3.0) -> list[tuple[float, float]]:
    """Fetch road-following geometry from public OSRM API for a sequence of (lat, lng) stops.
    Falls back to smooth 24-point geodesic arcs if offline or OSRM times out.
    """
    valid = [(float(lat), float(lng)) for lat, lng in coords if lat and lng]
    if len(valid) < 2:
        return valid

    coord_str = ";".join(f"{lng:.6f},{lat:.6f}" for lat, lng in valid)
    url = f"https://router.project-osrm.org/route/v1/driving/{coord_str}?overview=full&geometries=polyline"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                routes = data.get("routes") or []
                if routes and routes[0].get("geometry"):
                    decoded = decode_polyline(routes[0]["geometry"])
                    if len(decoded) >= 2:
                        return decoded
    except Exception:
        pass

    # Offline / fallback: stitch smooth geodesic splines between consecutive stops
    fallback_pts: list[tuple[float, float]] = []
    for i in range(len(valid) - 1):
        arc = generate_geodesic_arc(valid[i], valid[i + 1], num_points=24)
        if i > 0 and arc:
            arc = arc[1:]
        fallback_pts.extend(arc)
    return fallback_pts


class SlippyMapCanvas(ft.Container):
    """Interactive OpenStreetMap slippy map with marker clustering, category pins, and OSRM road polylines."""

    def __init__(
        self,
        width: int = 860,
        height: int = 520,
        center_lat: float = 15.58,
        center_lng: float = 121.00,
        zoom: int = 10,
        places: Optional[list[Place]] = None,
        route_stops: Optional[list[RouteStopPin]] = None,
        route_polyline_points: Optional[list[tuple[float, float]]] = None,
        active_stop_index: Optional[int] = None,
        user_location: Optional[tuple[float, float]] = None,
        on_place_click: Optional[Callable[[Place], None]] = None,
        on_stop_click: Optional[Callable[[int, RouteStopPin], None]] = None,
        border_radius: int = 16,
    ) -> None:
        super().__init__()
        self._map_w = max(320, int(width))
        self._map_h = max(220, int(height))
        self.width = self._map_w
        self.height = self._map_h
        self.border_radius = border_radius
        self.clip_behavior = ft.ClipBehavior.HARD_EDGE
        self.bgcolor = "#e2e8f0"
        self.border = ft.Border.all(1, "#cbd5e1")

        self.center_lat = float(center_lat)
        self.center_lng = float(center_lng)
        self.zoom = max(8, min(18, int(zoom)))

        self._places: list[Place] = list(places or [])
        self._route_stops: list[RouteStopPin] = list(route_stops or [])
        self._route_pts: list[tuple[float, float]] = list(route_polyline_points or [])
        self._active_stop_index = active_stop_index
        self._user_location = user_location
        self._on_place_click = on_place_click
        self._on_stop_click = on_stop_click

        self._tile_stack = ft.Stack(width=self._map_w, height=self._map_h)
        self._vector_canvas = cv.Canvas(width=self._map_w, height=self._map_h, shapes=[])
        self._marker_stack = ft.Stack(width=self._map_w, height=self._map_h)

        # Attribution & Zoom Controls
        self._zoom_label = ft.Text(f"Z{self.zoom}", size=10, weight=ft.FontWeight.W_700, color="#334155")
        controls_overlay = ft.Container(
            right=12,
            bottom=28,
            bgcolor=ft.Colors.with_opacity(0.94, "#ffffff"),
            border_radius=10,
            border=ft.Border.all(1, "#cbd5e1"),
            padding=ft.Padding.symmetric(horizontal=4, vertical=4),
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.12, "#0f172a")),
            content=ft.Column(
                spacing=2,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ADD_ROUNDED,
                        icon_size=16,
                        icon_color="#0f172a",
                        tooltip="Zoom in",
                        on_click=lambda _: self.set_zoom(self.zoom + 1),
                        style=ft.ButtonStyle(padding=ft.Padding.all(4)),
                    ),
                    self._zoom_label,
                    ft.IconButton(
                        icon=ft.Icons.REMOVE_ROUNDED,
                        icon_size=16,
                        icon_color="#0f172a",
                        tooltip="Zoom out",
                        on_click=lambda _: self.set_zoom(self.zoom - 1),
                        style=ft.ButtonStyle(padding=ft.Padding.all(4)),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.FIT_SCREEN_ROUNDED,
                        icon_size=15,
                        icon_color="#0284c7",
                        tooltip="Fit markers / route",
                        on_click=lambda _: self.fit_to_content(),
                        style=ft.ButtonStyle(padding=ft.Padding.all(4)),
                    ),
                ],
            ),
        )

        attribution_badge = ft.Container(
            left=8,
            bottom=6,
            bgcolor=ft.Colors.with_opacity(0.82, "#ffffff"),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            content=ft.Text("© OpenStreetMap contributors • OSRM Routing", size=9, color="#475569"),
        )

        # Gesture detector handles click-and-drag panning across the map
        gesture_layer = ft.GestureDetector(
            on_pan_update=self._handle_pan_update,
            drag_interval=16,
            content=ft.Stack(
                width=self._map_w,
                height=self._map_h,
                controls=[
                    self._tile_stack,
                    self._vector_canvas,
                    self._marker_stack,
                ],
            ),
        )

        self.content = ft.Stack(
            width=self._map_w,
            height=self._map_h,
            controls=[
                gesture_layer,
                controls_overlay,
                attribution_badge,
            ],
        )

        self.redraw()

    def set_places(self, places: list[Place], auto_fit: bool = False) -> None:
        self._places = list(places or [])
        if auto_fit and self._places:
            self.fit_bounds([(p.latitude, p.longitude) for p in self._places if p.latitude and p.longitude])
        else:
            self.redraw()

    def set_route(
        self,
        stops: list[RouteStopPin],
        polyline_points: Optional[list[tuple[float, float]]] = None,
        active_stop_index: Optional[int] = None,
        auto_fit: bool = True,
    ) -> None:
        self._route_stops = list(stops or [])
        self._active_stop_index = active_stop_index
        if polyline_points is not None:
            self._route_pts = list(polyline_points)
        elif len(self._route_stops) >= 2:
            self._route_pts = fetch_osrm_road_geometry([(s.lat, s.lng) for s in self._route_stops])
        else:
            self._route_pts = []

        if auto_fit and self._route_stops:
            self.fit_bounds([(s.lat, s.lng) for s in self._route_stops if s.lat and s.lng])
        else:
            self.redraw()

    def set_center_and_zoom(self, lat: float, lng: float, zoom: Optional[int] = None) -> None:
        self.center_lat = float(lat)
        self.center_lng = float(lng)
        if zoom is not None:
            self.zoom = max(8, min(18, int(zoom)))
        self.redraw()

    def set_zoom(self, new_zoom: int) -> None:
        self.zoom = max(8, min(18, int(new_zoom)))
        self.redraw()

    def fit_to_content(self) -> None:
        if self._route_stops:
            self.fit_bounds([(s.lat, s.lng) for s in self._route_stops if s.lat and s.lng])
        elif self._places:
            self.fit_bounds([(p.latitude, p.longitude) for p in self._places if p.latitude and p.longitude])
        else:
            self.set_center_and_zoom(15.58, 121.00, 10)

    def fit_bounds(self, coords: list[tuple[float, float]], padding_px: int = 56) -> None:
        valid = [(lat, lng) for lat, lng in coords if lat and lng and -90 <= lat <= 90 and -180 <= lng <= 180]
        if not valid:
            self.redraw()
            return
        if len(valid) == 1:
            self.center_lat, self.center_lng = valid[0]
            self.zoom = 14
            self.redraw()
            return

        min_lat = min(c[0] for c in valid)
        max_lat = max(c[0] for c in valid)
        min_lng = min(c[1] for c in valid)
        max_lng = max(c[1] for c in valid)

        self.center_lat = (min_lat + max_lat) / 2.0
        self.center_lng = (min_lng + max_lng) / 2.0

        usable_w = max(120, self._map_w - 2 * padding_px)
        usable_h = max(120, self._map_h - 2 * padding_px)

        best_z = 10
        for z in range(16, 8, -1):
            x1, y1 = latlon_to_world_px(max_lat, min_lng, z)
            x2, y2 = latlon_to_world_px(min_lat, max_lng, z)
            if abs(x2 - x1) <= usable_w and abs(y2 - y1) <= usable_h:
                best_z = z
                break
        self.zoom = best_z
        self.redraw()

    def _handle_pan_update(self, e: ft.DragUpdateEvent) -> None:
        dx = float(getattr(e, "delta_x", 0.0) or 0.0)
        dy = float(getattr(e, "delta_y", 0.0) or 0.0)
        cx, cy = latlon_to_world_px(self.center_lat, self.center_lng, self.zoom)
        self.center_lat, self.center_lng = world_px_to_latlon(cx - dx, cy - dy, self.zoom)
        self.redraw()

    def _latlon_to_viewport(self, lat: float, lng: float) -> tuple[float, float]:
        cx, cy = latlon_to_world_px(self.center_lat, self.center_lng, self.zoom)
        px, py = latlon_to_world_px(lat, lng, self.zoom)
        return (self._map_w / 2.0) + (px - cx), (self._map_h / 2.0) + (py - cy)

    def redraw(self) -> None:
        self._zoom_label.value = f"Z{self.zoom}"
        self._render_tiles()
        self._render_route_Vectors()
        self._render_markers_and_clusters()
        try:
            if self.page:
                self.update()
        except Exception:
            pass

    def _render_tiles(self) -> None:
        cx, cy = latlon_to_world_px(self.center_lat, self.center_lng, self.zoom)
        top_left_wx = cx - (self._map_w / 2.0)
        top_left_wy = cy - (self._map_h / 2.0)

        min_tx = int(math.floor(top_left_wx / 256.0))
        max_tx = int(math.floor((top_left_wx + self._map_w) / 256.0))
        min_ty = int(math.floor(top_left_wy / 256.0))
        max_ty = int(math.floor((top_left_wy + self._map_h) / 256.0))

        num_tiles = 2 ** self.zoom
        tiles: list[ft.Control] = []
        for tx in range(min_tx, max_tx + 1):
            for ty in range(min_ty, max_ty + 1):
                if ty < 0 or ty >= num_tiles:
                    continue
                wrapped_tx = tx % num_tiles
                left_px = (tx * 256.0) - top_left_wx
                top_px = (ty * 256.0) - top_left_wy
                tile_url = f"https://tile.openstreetmap.org/{self.zoom}/{wrapped_tx}/{ty}.png"
                tiles.append(
                    ft.Container(
                        left=left_px,
                        top=top_px,
                        width=256,
                        height=256,
                        content=ft.Image(
                            src=tile_url,
                            width=256,
                            height=256,
                            fit=ft.ImageFit.COVER,
                            gapless_playback=True,
                        ),
                    )
                )
        self._tile_stack.controls = tiles

    def _render_route_Vectors(self) -> None:
        shapes: list[cv.Shape] = []
        if len(self._route_pts) >= 2:
            screen_pts = [self._latlon_to_viewport(lat, lng) for lat, lng in self._route_pts]
            path_elements: list[cv.PathElement] = [cv.Path.MoveTo(screen_pts[0][0], screen_pts[0][1])]
            for vx, vy in screen_pts[1:]:
                path_elements.append(cv.Path.LineTo(vx, vy))

            # Outer white route casing
            shapes.append(
                cv.Path(
                    elements=path_elements,
                    paint=ft.Paint(
                        color="#ffffff",
                        stroke_width=8,
                        style=ft.PaintingStyle.STROKE,
                        stroke_cap=ft.StrokeCap.ROUND,
                        stroke_join=ft.StrokeJoin.ROUND,
                    ),
                )
            )
            # Inner primary road line (#0284c7 / #2563eb matching Web App)
            shapes.append(
                cv.Path(
                    elements=path_elements,
                    paint=ft.Paint(
                        color="#0284c7",
                        stroke_width=5,
                        style=ft.PaintingStyle.STROKE,
                        stroke_cap=ft.StrokeCap.ROUND,
                        stroke_join=ft.StrokeJoin.ROUND,
                    ),
                )
            )
        self._vector_canvas.shapes = shapes

    def _render_markers_and_clusters(self) -> None:
        controls: list[ft.Control] = []

        # 1. User GPS / Cabanatuan Anchor Dot (if present)
        if self._user_location:
            ux, uy = self._latlon_to_viewport(self._user_location[0], self._user_location[1])
            if -20 <= ux <= self._map_w + 20 and -20 <= uy <= self._map_h + 20:
                controls.append(
                    ft.Container(
                        left=ux - 10,
                        top=uy - 10,
                        width=20,
                        height=20,
                        bgcolor="#3b82f6",
                        border=ft.Border.all(3, "#ffffff"),
                        border_radius=10,
                        tooltip="Your Location",
                        shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.4, "#3b82f6")),
                    )
                )

        # 2. Discovery Place Markers (with Web-App-identical Marker Clustering when zoom < 14)
        visible_places: list[tuple[Place, float, float]] = []
        for p in self._places:
            if not p.latitude or not p.longitude:
                continue
            px, py = self._latlon_to_viewport(p.latitude, p.longitude)
            if -32 <= px <= self._map_w + 32 and -32 <= py <= self._map_h + 32:
                visible_places.append((p, px, py))

        if self.zoom < 14 and len(visible_places) > 18:
            # Grid spatial clustering (cell size 58px) matching Leaflet.markercluster (.marker-cluster)
            grid: dict[tuple[int, int], list[tuple[Place, float, float]]] = {}
            cell_size = 58.0
            for item in visible_places:
                gx = int(item[1] // cell_size)
                gy = int(item[2] // cell_size)
                grid.setdefault((gx, gy), []).append(item)

            for bucket in grid.values():
                if len(bucket) == 1:
                    p, px, py = bucket[0]
                    controls.append(self._build_place_pin(p, px, py))
                else:
                    avg_x = sum(b[1] for b in bucket) / len(bucket)
                    avg_y = sum(b[2] for b in bucket) / len(bucket)
                    avg_lat = sum(b[0].latitude for b in bucket) / len(bucket)
                    avg_lng = sum(b[0].longitude for b in bucket) / len(bucket)
                    count = len(bucket)
                    controls.append(self._build_cluster_pin(count, avg_x, avg_y, avg_lat, avg_lng))
        else:
            for p, px, py in visible_places[:250]:
                controls.append(self._build_place_pin(p, px, py))

        # 3. Numbered Itinerary Route Stop Badges (1..N) on top of everything
        for stop in self._route_stops:
            if not stop.lat or not stop.lng:
                continue
            sx, sy = self._latlon_to_viewport(stop.lat, stop.lng)
            if -40 <= sx <= self._map_w + 40 and -40 <= sy <= self._map_h + 40:
                controls.append(self._build_route_stop_badge(stop, sx, sy))

        self._marker_stack.controls = controls

    def _build_cluster_pin(
        self, count: int, px: float, py: float, center_lat: float, center_lng: float
    ) -> ft.Control:
        """Web-App-identical blue marker cluster circle (`.marker-cluster` in `map.page.scss`)."""
        size = 38 if count < 25 else (44 if count < 100 else 50)
        return ft.Container(
            left=px - size / 2,
            top=py - size / 2,
            width=size,
            height=size,
            border_radius=size / 2,
            bgcolor=ft.Colors.with_opacity(0.28, "#0084ff"),
            padding=ft.Padding.all(4),
            tooltip=f"{count} places in this area — Click to zoom in",
            on_click=lambda _: self.set_center_and_zoom(center_lat, center_lng, min(17, self.zoom + 2)),
            content=ft.Container(
                alignment=ft.Alignment(0, 0),
                border_radius=(size - 8) / 2,
                bgcolor="#0084ff",
                border=ft.Border.all(2, "#ffffff"),
                content=ft.Text(
                    str(count),
                    size=12,
                    weight=ft.FontWeight.W_800,
                    color="#ffffff",
                ),
            ),
        )

    def _build_place_pin(self, place: Place, px: float, py: float) -> ft.Control:
        """Category-colored teardrop/circular marker pin that opens PlaceDetailSheet on click."""
        color_hex, icon_data = CATEGORY_PIN_STYLE.get(
            place.category, ("#2563eb", ft.Icons.LOCATION_ON_ROUNDED)
        )
        return ft.Container(
            left=px - 15,
            top=py - 15,
            width=30,
            height=30,
            bgcolor=color_hex,
            border=ft.Border.all(2, "#ffffff"),
            border_radius=15,
            alignment=ft.Alignment(0, 0),
            tooltip=f"{place.name} ({place.municipality_name or 'Nueva Ecija'})",
            shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.28, "#0f172a")),
            on_click=lambda _, p=place: self._on_place_click(p) if self._on_place_click else None,
            content=ft.Icon(icon_data, size=15, color="#ffffff"),
        )

    def _build_route_stop_badge(self, stop: RouteStopPin, sx: float, sy: float) -> ft.Control:
        """Numbered circular stop badge (`1`, `2`, `3`...) with floating stop name pill."""
        is_active = self._active_stop_index == stop.index
        badge_bg = "#f97316" if is_active else "#2563eb"
        badge_size = 34 if is_active else 30

        return ft.Container(
            left=sx - badge_size / 2,
            top=sy - badge_size / 2,
            on_click=lambda _, s=stop: self._on_stop_click(s.index, s) if self._on_stop_click else None,
            tooltip=f"Stop {stop.index + 1}: {stop.title} ({stop.planned_time or 'Scheduled'})",
            content=ft.Row(
                spacing=4,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=badge_size,
                        height=badge_size,
                        bgcolor=badge_bg,
                        border=ft.Border.all(2.5, "#ffffff"),
                        border_radius=badge_size / 2,
                        alignment=ft.Alignment(0, 0),
                        shadow=ft.BoxShadow(
                            blur_radius=8,
                            color=ft.Colors.with_opacity(0.35, "#0f172a"),
                            offset=ft.Offset(0, 2),
                        ),
                        content=ft.Text(
                            str(stop.index + 1),
                            size=13,
                            weight=ft.FontWeight.W_800,
                            color="#ffffff",
                        ),
                    ),
                    ft.Container(
                        bgcolor=ft.Colors.with_opacity(0.95, "#ffffff"),
                        border=ft.Border.all(1, "#cbd5e1"),
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=7, vertical=3),
                        shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.12, "#0f172a")),
                        content=ft.Text(
                            stop.title[:22] + ("…" if len(stop.title) > 22 else ""),
                            size=10,
                            weight=ft.FontWeight.W_700,
                            color="#0f172a",
                        ),
                    ),
                ],
            ),
        )
```

### 4.3 Loading All 2,673 OSM Places in `desktop_client/services/place_service.py`
In `desktop_client/services/place_service.py`, ensure `load_osm_places()` resolves the exact repository path to `Project/src/assets/data/osm_places.json` regardless of the current working directory:

```python
from pathlib import Path

def _find_osm_places_json() -> Optional[Path]:
    """Locate Project/src/assets/data/osm_places.json from any working directory."""
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "Project" / "src" / "assets" / "data" / "osm_places.json",
        Path.cwd() / "Project" / "src" / "assets" / "data" / "osm_places.json",
        Path.cwd().parent / "Project" / "src" / "assets" / "data" / "osm_places.json",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None
```
When `PlaceService` initializes, merge `CANONICAL_OFFLINE_PLACES` (curated landmarks with photos & entrance fees) with all **2,673 records** from `osm_places.json` so:
- `MapView` displays the full province-wide POI clusters and category pins just like the Web App (`map.page.ts` with `limit=3000`).
- `CustomBuilderView` and `SuggestedWizardView` have instant access to every municipality's attractions, restaurants, resorts, churches, markets, hospitals, and pharmacies even when offline!

### 4.4 Updating `ItineraryRouteMap` (`desktop_client/components/itinerary_route_map.py`)
`ItineraryRouteMap` is embedded inside **all 3 itinerary views** (`SuggestedWizardView`, `CustomBuilderView`, and `ItineraryDetailView`), matching `Project/src/app/shared/components/itinerary-route-map/itinerary-route-map.component.html`:
- Renders `SlippyMapCanvas(width=760, height=280)` populated with `RouteStopPin` objects extracted from `day.items`:
  ```python
  lat = (item.place.latitude if item.place and item.place.latitude else None) or item.custom_lat
  lng = (item.place.longitude if item.place and item.place.longitude else None) or item.custom_lng
  ```
- Computes the road polyline using `day.day_overview_polyline` if present, or calls `fetch_osrm_road_geometry([(s.lat, s.lng) for s in stops])` (which automatically falls back to `generate_geodesic_arc` when offline).
- Renders a top-right **`[🗺️ Full Map]`** pill button (`"Open in Full Map"`):
  - When clicked, if `itinerary_id == "draft"` (unsaved Suggested Wizard preview or unsaved Custom Builder draft), it stores the current draft in `itinerary_service.set_active_draft_itinerary(draft_itinerary)` and navigates to `/map?itineraryId=draft&day={day.day_number}`!
  - If `itinerary_id` is a saved trip ID, it navigates to `/map?itineraryId={itinerary_id}&day={day.day_number}`!
- Renders a bottom-left route metrics pill (`"🚗 {len(stops)} stops • {total_km:.1f} km • ~{total_mins} min drive"`).

---

## 5. Mandatory Fix 4: `SuggestedWizardView` & `CustomBuilderView` Exact Web Workflow Parity

### 5.1 Why Suggested & Custom Itinerary Felt Different from the Web App
On the Web App (`Project/src/app/features/itinerary/`):
1. **Suggested Itinerary (`suggested-wizard.page.html/.ts`)** is a **3-View State Machine (`view_mode = "form" | "itinerary" | "nearby"`)**:
   - **View 1 (`form` — `"Tell us your travel preferences"`)**:
     - `DestinationAutocomplete` combobox (`🌏 All of Nueva Ecija (Province-Wide Corridor)`, `32 Municipalities` with district tags & POI counts, `12 Top Landmarks`) + **`[🗺️ All 32 Towns]`** regional modal (`All | Central | North | South | East` tabs) + Quick Destination Chips (`Cabanatuan City`, `Gabaldon`, `General Tinio`, `Pantabangan`, `San Jose City`, `Science City of Muñoz`, `Bongabon`, `Gapan City`, `Palayan City`).
     - Clickable **Travel Dates** box (`From` / `To`) opening the **Popup Date Picker Modal** with quick duration pills (`2 Days (1N)`, `3 Days (2N)`, `4 Days (3N)`, `1 Week`) and dynamic duration banner (`"X Days, Y Nights in Nueva Ecija"`).
     - **Daily Budget (PHP)** numeric input + quick preset pills (`₱1,500`, `₱2,500`, `₱4,000`, `₱6,000`).
     - **Preferences** multi-select icon pills (`Nature & Parks`, `Food Trip`, `Culture & History`, `Shopping`, `Resort`).
     - **Travel Mode** pills (`🚗 Drive / Car`, `🛵 Motorcycle / Tricycle`, `🚶 Walking / Transit`).
     - **Minimum Place Rating** chips (`All Ratings`, `4.0+ ★`, `4.5+ ★`).
     - **`[Find Itinerary]`** primary CTA button (`save_immediately=False`).
   - **View 2 (`itinerary` — `"Here's an itinerary just for you!"`)**:
     - Stores the generated preview in `itinerary_service.set_active_draft_itinerary(plan)` immediately so clicking `[Full Map]` on the route map opens the unsaved preview in `MapView` Follow-Route Mode (`itineraryId="draft"`), and returning from `MapView` restores the draft!
     - **Trip Summary Card (`.figma-trip-card`)**: Destination, Date Range, Budget (`₱X,XXX`), and Preference tags.
     - **Verified Place Costs Card (`.verified-budget-card`)**: Shows verified min–max total (`₱X,XXX – ₱Y,YYY`), count of unpriced stops, and honest pricing footnote.
     - **Collapsible `Travel Notes & Planning Assumptions` (`.assumptions-info-box`)**: Expandable accordion parsing each assumption into categorized tags (`Pacing`, `Routing`, `Budget`, `Schedule`).
     - **Day Capsule Bar (`.figma-day-capsule-bar`)**: Horizontal day pills showing `Day 1` / `[Municipality]` (`getDayLocationName(day)`).
     - **Embedded `ItineraryRouteMap`**: Interactive slippy map for `generatedPlan.days[activeDayIndex]` with OSRM road polyline, numbered stop pins (`1..N`), and **`[Full Map]`** button.
     - **Stop Cards with Inter-Stop Leg Commute Badges**:
       - Between Stop `i-1` and Stop `i`, displays the blue commute connector pill (`🚗 {km} km • ~{drive_mins} mins drive • {trike_mins} mins tricycle • Est. Fare ₱{min_fare}–₱{max_fare}`).
       - Each stop card shows thumbnail photo, stop title, category badge, `getTimingTime(stop)` (`"9:00 AM - 10:30 AM"`), `getTimingDuration(stop)` (`"1.5 hrs"`), and `getStopCost(stop)`. Clicking a stop card opens **`PlaceDetailSheet`** with `stop_notes` and `get_commute_info_for_municipality()`!
     - **Nearby Essentials Trigger Banner (`.nearby-banner-trigger`)**: `"Nearby Places in [Municipality] — Find restaurants, hospitals, pharmacies & stores near your stops"` → switches to `view_mode = "nearby"`.
     - **Bottom Action Buttons**:
       - **`[✓ Accept & Save Itinerary]`**: Calls `itinerary_service.create_itinerary(payload)`, clears active draft, shows success toast, and opens `/trips/{saved.id}`!
       - **`[✏️ Customize in Builder]`**: Stores `generatedPlan` in `itinerary_service.set_active_draft_itinerary(generatedPlan)` and navigates to `/custom-builder?draft=true`, opening `CustomBuilderView` directly in `active_view = "timeline"` pre-populated with all generated days and stops!
   - **View 3 (`nearby` — `"Nearby Places in [Municipality]"`)**:
     - Segmented capsule bar: **`[🍽️ Restaurants]`** | **`[🏥 Hospital & Pharmacies]`** | **`[🛒 Stores]`**.
     - Lists nearby essentials for the active day's municipality (`place_service.get_nearby_places(municipality)`) with opening hours, category badge, **`[Maps]`** button, and **`[+ Add to Day X]`** button (which appends the place as a stop to `generatedPlan.days[activeDayIndex]`, recalculates leg metrics & budget summary, and shows a confirmation toast!).

2. **Custom Itinerary (`custom-builder.page.html/.ts`)** is **NOT** a static side-by-side split screen! It is a **3-View State Machine (`active_view = "form" | "browse" | "timeline"`)** with a top segmented mode switcher (`[+ Add Places]` | `[📅 Your Itinerary (N)]`) once past Step 1:
   - **View 0 (`form` — `"Tell us your travel details"`)**:
     - Collects `Trip Title` (`"Nueva Ecija Getaway"`), `Destination` (32-LGU `DestinationAutocomplete` + `[🗺️ All 32 Towns]` modal + Quick Destination Chips), `Travel Dates` (clickable `From`/`To` box opening the Popup Date Picker Modal), `Daily Budget (PHP)` + presets (`₱1,500`, `₱2,500`, `₱4,000`, `₱6,000`), and `Preferences` pills.
     - Clicking **`[Start Building Itinerary →]`** calls `sync_days_with_date_range()` (creating `Day 1..N` matching the exact date range) and transitions to `active_view = "browse"`!
     - *(Note: If opened via `/custom-builder/{id}` to edit an existing trip, or via `[Customize in Builder]` from Suggested Wizard, or with `?addPlaceId=...` from Home/Map, it skips `form` and opens directly in `active_view = "timeline"`!)*
   - **View 1 (`browse` — `"Add the places you want to visit"`)**:
     - **Top Segmented View Switcher**: **`[+ Add Places]`** (active) | **`[📅 Your Itinerary ({total_stops})]`**.
     - **Target Day Selector Bar**: `"Scheduling for:"` `[Day 1 (2)]` `[Day 2 (0)]` `[+]` (allows selecting which day new places are added to, or adding a new day on the fly).
     - **Search & Category Filter Bar**: Instant search input + category pills (`All`, `✨ Recommended for You` when preferences are selected, `Tourist Spots`, `Food`, `Resorts & Stays`, `Culture & Heritage`, `Shopping`, `Transit & Essentials`, `Other`). Places matching the chosen destination municipality are prioritized at the top.
     - **Responsive Place Card Grid**: Each place card displays thumbnail photo, category pill, rating badge, municipality & cost, **`[ℹ️ Details]`** (opens `PlaceDetailSheet`), and a stateful **`[+ Add]` / `[✓ Added]`** toggle button! Clicking `[+ Add]` adds the stop to `current_day`, auto-calculates `planned_time = calculate_next_stop_time()` (accounting for Haversine driving transit buffer between stops!), and flips the button to green `[✓ Added]`.
     - **Sticky Bottom Bar**: **`[View my Itinerary ({total_stops} places) →]`** (switches to `active_view = "timeline"`).
   - **View 2 (`timeline` — `"Your Custom Itinerary"`)**:
     - **Top Bar**: Back button, title, **`[✓ Save]`** header button, and the **Segmented View Switcher** (`[+ Add Places]` | `[📅 Your Itinerary ({total_stops})]` active).
     - **Editable Trip Settings Card**: Inline fields for `Trip Title`, `Daily Budget (₱)`, and clickable `Travel Dates` (changing dates dynamically adds or trims days via `sync_days_with_date_range()`, prompting confirmation if shortening would discard stops).
     - **Verified Place Costs Card (`.verified-budget-card`)**: Shows verified min–max total (`₱X,XXX – ₱Y,YYY`), daily budget comparison (`₱X,XXX / day × N days`), and unpriced stop count.
     - **Day Capsule Switcher**: `[Day 1 - Cabanatuan City]`, `[Day 2 - Gabaldon]`, ..., **`[+ Add Day]`**.
     - **Active Day Header**: Shows `Day X - [Municipality]`, travel date, **`[🕒 Auto-Schedule]`** button (`auto_optimize_day_schedule()` recalculates sequential times starting at `09:00 AM` with Haversine driving buffers), and **`[🗑 Delete Day]`** button.
     - **Embedded `ItineraryRouteMap`**: Live slippy map showing the active day's OSRM road polyline and numbered stop badges (`1..N`) with **`[Full Map]`** button. Clicking a numbered pin on the map opens the Edit Stop modal for that stop!
     - **Ordered Timeline Stop Cards with Inter-Stop Leg Commute Badges**:
       - Displays the inter-stop commute leg badge (`🚗 {km} km • ~{drive_mins} mins drive • {trike_mins} mins tricycle • Est. Fare ₱{min_fare}–₱{max_fare}`) between consecutive stops.
       - Each stop card shows step number badge (`1`, `2`...), thumbnail photo, title, category & municipality badge, `planned_time (duration)`, cost range, notes preview, and action buttons: **`[↑]`** (`move_stop_up`), **`[↓]`** (`move_stop_down`), **`[✏️ Edit]`** (`open_edit_stop_modal`), and **`[🗑 Remove]`** (`remove_stop`).
     - **Edit Scheduled Stop Modal (`open_edit_stop_modal`)**:
       - Allows editing **Planned Time** (`09:00 AM`), **Duration (minutes)** (`30..360`), **Min Cost (₱)**, **Max Cost (₱)** (validating `min <= max`), **Notes**, and **Move to Day (`Day 1..N` dropdown)**!
     - **Bottom Add Actions**:
       - **`[+ Browse & Add Places to Day X]`** (switches to `active_view = "browse"`).
       - **`[+ Add Off-Grid Custom Venue]`** (opens modal with Venue Name, Municipality/Address, Planned Time, Duration, Min/Max Cost, Notes, and optional GPS Coordinates validated against the Nueva Ecija bounding box `Lat 15.15–16.15, Lng 120.70–121.40`).
     - **Sticky Footer CTA**: **`[💾 Save Custom Itinerary]`** (validates `total_stops > 0`, calls `create_itinerary` or `update_itinerary`, and navigates to `/trips/{saved.id}`).

---

## 6. Step-by-Step Implementation Plan for Antigravity

Execute the following 6 implementation steps in order inside `desktop_client/`:

### Step 1: Fix `OfflineHostBanner` & Root Layout (`desktop_client/components/offline_banner.py` & `desktop_client/main.py`)
1. Replace `desktop_client/components/offline_banner.py` with the bounded `OfflineHostBanner` implementation in **Section 2.2** (`expand=False`, fixed `height=52` when visible, `height=0` when hidden/dismissed, inner `width=620, height=42` dark pill).
2. In `desktop_client/main.py`, ensure the root layout is an `ft.Column(spacing=0, expand=True, controls=[self._offline_banner, self._content_area, self._bottom_tab_bar])` (**not** an unpositioned child inside `ft.Stack(expand=True)`).
3. Verify that clicking `[✕]` on the offline notice immediately sets `self._offline_banner.visible = False` and `self._offline_banner.height = 0` without blocking any screen.

### Step 2: Fix `User` Model, `AuthService`, and `ProfileView` (`desktop_client/models/user.py`, `services/auth_service.py`, `views/profile_view.py`)
1. Replace `desktop_client/models/user.py` with the schema-aligned implementation in **Section 3.2** so `User.from_dict()` reads `first_name`, `last_name`, `username_normalized`, and `email_normalized` from FastAPI `UserOut`, and `UserUpdatePayload.to_backend_dict()` sends `first_name`, `last_name`, `username`, `current_password`, `new_password` to `PATCH /api/v1/auth/me`.
2. Update `AuthService.update_profile()` in `desktop_client/services/auth_service.py` to persist extended profile fields (`middle_initial`, `birthday`, `gender`, `phone_number`, `avatar_url`, `preferences`, `default_daily_budget`) in `LocalStorage` (`profile_extra.json` keyed by `user.id`), call `PATCH /api/v1/auth/me` when authenticated and online, and update `self._session.user` in both Authenticated and Guest/Offline modes.
3. Update `ProfileView._open_edit_profile_modal()` in `desktop_client/views/profile_view.py` to edit `first_name`, `last_name`, `middle_initial`, `username`, `birthday`, `gender`, `phone_number`, `default_daily_budget`, and `avatar_url` (with a working native image file picker via `tkinter.filedialog.askopenfilename` + preset avatar options).

### Step 3: Load All 2,673 OSM Places & Build Pure-Flet Slippy Map + Clustering + Road Routing (`services/place_service.py`, `components/slippy_map_canvas.py`, `components/itinerary_route_map.py`, `views/map_view.py`)
1. Update `desktop_client/services/place_service.py` using `_find_osm_places_json()` (**Section 4.3**) so all **2,673 POIs** from `Project/src/assets/data/osm_places.json` are loaded and merged with `CANONICAL_OFFLINE_PLACES` on startup.
2. Create `desktop_client/components/slippy_map_canvas.py` (**Section 4.2**) implementing:
   - OpenStreetMap 256×256 tile rendering with drag-to-pan and zoom controls (`Z8..Z18`).
   - Spatial marker clustering at `zoom < 14` (`.marker-cluster` blue numbered badges `#0084ff` that zoom in by `+2` on click).
   - Category-colored POI pins at `zoom >= 14` that open `PlaceDetailSheet` on click.
   - Vector `ft.canvas.Path` rendering of OSRM road polylines (`fetch_osrm_road_geometry`) and geodesic fallback splines (`generate_geodesic_arc`).
   - Clickable numbered stop badges (`1..N`) with stop title pills.
3. Update `desktop_client/components/itinerary_route_map.py` and `desktop_client/views/map_view.py` to use `SlippyMapCanvas` in both **Discovery Mode** (search + category pills + municipality dropdown + `Near Me (10 km)` filter + cluster/pin inspection) and **Follow-Route Mode** (`?itineraryId=...&day=...`, including `itineraryId="draft"`, day switcher pills, OSRM road route line, numbered stop badges, `Simulate Next Stop` / GPS distance & ETA HUD, and bottom horizontal stop carousel).

### Step 4: Upgrade `SuggestedWizardView` to the Exact 3-View Web Workflow (`desktop_client/views/suggested_wizard_view.py`)
1. Implement the 3-view state machine (`self.view_mode = "form" | "itinerary" | "nearby"`) matching `Project/src/app/features/itinerary/suggested-wizard/suggested-wizard.page.html/.ts`:
   - **`form` view**: `DestinationAutocomplete` (with `[All 32 Towns]` regional modal + Quick Destination Chips), clickable `Travel Dates` box opening the **Popup Date Picker Modal** (`From`/`To` + `2D/1N`, `3D/2N`, `4D/3N`, `1 Week` presets), `Daily Budget` + presets (`₱1,500`, `₱2,500`, `₱4,000`, `₱6,000`), `Preferences` pills, `Travel Mode` pills (`Drive / Car`, `Motorcycle / Tricycle`, `Walking / Transit`), `Minimum Place Rating` chips (`All Ratings`, `4.0+ ★`, `4.5+ ★`), and `[Find Itinerary]`.
   - **`itinerary` view**: Calls `suggest_itinerary(..., save_immediately=False)`, stores the result in `itinerary_service.set_active_draft_itinerary(plan)`, renders the Trip Summary card, Verified Place Costs card, collapsible `Travel Notes & Planning Assumptions`, Day Capsule Bar (`Day 1 / [Municipality]`), embedded `ItineraryRouteMap` (with live road route & `[Full Map]` button), stop cards with **Inter-Stop Leg Commute Badges (`get_leg_commute`)** and click-to-inspect `PlaceDetailSheet`, `"Nearby Places in [Municipality]"` banner button, **`[✓ Accept & Save Itinerary]`**, and **`[✏️ Customize in Builder]`**.
   - **`nearby` view**: Segmented bar (`Restaurants` | `Hospital & Pharmacies` | `Stores`) for the active day's municipality with **`[+ Add to Day X]`** and **`[Maps]`**.

### Step 5: Upgrade `CustomBuilderView` to the Exact 3-View Web Workflow (`desktop_client/views/custom_builder_view.py`)
1. Replace the static split-pane layout with the Web App's 3-view state machine (`self.active_view = "form" | "browse" | "timeline"`) matching `Project/src/app/features/itinerary/custom-builder/custom-builder.page.html/.ts`:
   - **`form` view**: Collects `Trip Title`, `Destination` (`DestinationAutocomplete` + `[All 32 Towns]` modal + Quick Chips), `Travel Dates` (Popup Date Picker Modal), `Daily Budget` + presets, and `Preferences`. Clicking **`[Start Building Itinerary →]`** runs `sync_days_with_date_range()` and switches to `active_view = "browse"`.
   - **`browse` view**: Top segmented switcher (`[+ Add Places]` active | `[📅 Your Itinerary (N)]`), Target Day Selector (`Scheduling for: Day 1 (0) | Day 2 (0) | [+]`), search input + category filter pills (`All`, `✨ Recommended for You`, `Tourist Spots`, `Food`, `Resorts & Stays`, `Culture & Heritage`, `Shopping`, `Transit & Essentials`, `Other`), responsive place cards with photos and stateful **`[+ Add]` / `[✓ Added]`** toggle buttons, and sticky footer **`[View my Itinerary (N places) →]`**.
   - **`timeline` view**: Top segmented switcher (`[+ Add Places]` | `[📅 Your Itinerary (N)]` active) + header `[✓ Save]` button, editable Trip Settings card (`Trip Title`, `Daily Budget`, `Travel Dates` with `sync_days_with_date_range`), Verified Place Costs card, Day Switcher pills + `[+ Add Day]`, Day Header with **`[🕒 Auto-Schedule]`** and **`[🗑 Delete Day]`**, embedded **`ItineraryRouteMap`** (with OSRM road polyline + numbered stop pins + `[Full Map]` button), ordered stop cards with **Inter-Stop Leg Commute Badges**, `[↑]`, `[↓]`, **`[✏️ Edit]`** (modal with Planned Time, Duration, Min/Max Cost, Notes, and **`Move to Day` dropdown**), `[🗑 Remove]`, bottom **`[+ Browse & Add Places to Day X]`** and **`[+ Add Off-Grid Custom Venue]`** (geofenced `Lat 15.15–16.15, Lng 120.70–121.40`), and sticky footer **`[💾 Save Custom Itinerary]`**.

### Step 6: Automated Verification & QA Test Suite (`pytest desktop_client/tests/`)
Run `pytest desktop_client/tests/ -v` and verify all tests pass, covering:
1. **`test_offline_banner_bounds`**: Verifies `OfflineHostBanner.expand is False`, `height == 52` when offline, and `height == 0` / `visible is False` when online or dismissed.
2. **`test_user_model_and_edit_profile`**: Verifies `User.from_dict()` parses FastAPI `UserOut` (`first_name`, `last_name`, `username_normalized`, `email_normalized`), `UserUpdatePayload.to_backend_dict()` emits `first_name`, `last_name`, `username`, and `AuthService.update_profile()` persists both backend and extended local fields (`middle_initial`, `birthday`, `gender`, `phone_number`, `avatar_url`) in Authenticated, Offline, and Guest modes.
3. **`test_slippy_map_places_and_routing`**: Verifies `PlaceService` loads 2,600+ POIs from `osm_places.json`, `SlippyMapCanvas` clusters markers at `zoom < 14`, renders individual pins at `zoom >= 14`, and projects OSRM/geodesic polyline coordinates onto `cv.Path` with numbered `RouteStopPin` badges.
4. **`test_suggested_and_custom_itinerary_parity`**: Verifies `SuggestedWizardView` (`form` → `itinerary` → `nearby` + `[Customize in Builder]` handoff) and `CustomBuilderView` (`form` → `browse` → `timeline` + `[Auto-Schedule]` + `Move to Day` + `ItineraryRouteMap` draft handoff).
