# Codebase QA Review & Remediation Plan — Commit `0a3e2c515b732ebcc0030093506db866fab14d2f` (`v0.58.0`)

**Repository Audited**: `edselrenz/Itinerary-App` (Commit `0a3e2c515b732ebcc0030093506db866fab14d2f`, Version `0.58.0`)
**Audited Scope**: Phase 60 (`v0.57.0` Desktop Map Web Parity `MAP-QA-01` through `MAP-QA-10`) & Phase 61 (`v0.58.0` Multi-Platform Packaging, Android APK, Inno Setup & GitHub Actions Release Pipeline)

## 1. Executive Summary & Verification Matrix

A line-by-line audit of Commit `0a3e2c515b732ebcc0030093506db866fab14d2f` confirms that **all 10 Desktop Map Web Parity defects (`MAP-QA-01` through `MAP-QA-10`)** and the core **Phase 61 Multi-Platform Packaging & Release Pipeline** have been implemented and verified. Out of 16 audited subsystems, **12 pass 100% with zero issues**, while **4 residual defects (`PKG-REV-01` through `PKG-REV-04`)** were identified for final production hardening.

| Audit ID | Subsystem / Requirement | Target File(s) | Status in `0a3e2c5` | Verification Notes |
| :--- | :--- | :--- | :--- | :--- |
| **`MAP-QA-01`** | POI Bottom Sheet Commute Guide Crash Fix | `desktop_client/views/places_view.py:1351–1363` | **PASS** | Safely handles both `CommuteInfo` dataclass (`getattr`) and `dict` fallback; verified by `TC-31`. |
| **`MAP-QA-02`** | Favorite Toggle Contract in Map Bottom Sheet | `desktop_client/views/places_view.py:1214–1219` | **PASS** | Passes `p_obj` (`Place` instance) to `fav_svc.toggle_favorite(p_obj)`; verified by `TC-31`. |
| **`MAP-QA-03`** | Linear Pan Math & Zero-Delta (`0.0`) Preservation | `desktop_client/components/slippy_map_canvas.py:98–125, 1000–1085` | **PASS** | Explicit `is None` checks preserve `0.0` axis deltas; `_drag_origin_lat/lng` + 220px rebase eliminate quadratic pan drift (`TC-32`). |
| **`MAP-QA-04`** | 16 Web Category Colors & 30×30 Teardrop Pins | `desktop_client/components/slippy_map_canvas.py:309–340, 1413–1460` | **PASS** | Exact hex parity with `Project/src/global.scss:4732–4744`; rotated `-45deg` teardrop anchored at `(sx, sy)`. |
| **`MAP-QA-05`** | Web-Identical `<app-place-detail-sheet>` Card | `desktop_client/views/places_view.py:1200–1515` | **PASS** | 150px hero banner, overlaid Favorite/Close/Category/Open badges, rating chips, green commute box, and `/suggested?destination=...&placeId=...` (`TC-33`). |
| **`MAP-QA-06`** | OSRM Polyline Decoding & Floating Stop Tooltips | `desktop_client/views/places_view.py:377–413`, `slippy_map_canvas.py:1462–1528` | **PASS** | Decodes `day_overview_polyline` and `route_polyline_from_prev`; renders `.route-stop-tooltip` pill above numbered badge. |
| **`MAP-QA-07`** | Compact Drawer Rows & Auto-Close on Selection | `desktop_client/views/places_view.py:783–853` | **PASS** | `_build_drawer_row` renders 60×60 thumbnail + metadata row and closes drawer on click (`TC-34`). |
| **`MAP-QA-08`** | Initial Route Query Filter & Bounds Auto-Focus | `desktop_client/views/places_view.py:109, 148–151` | **PASS** | Calls `self._apply_filters()` in `__init__()` and `fit_bounds()` in `did_mount()` (`TC-33`). |
| **`MAP-QA-09` / `10`** | `public_facility` Icon & Map Dark Mode Sync | `desktop_client/views/places_view.py:53, 424–437` | **PASS** | Adds `ft.Icons.FLAG_OUTLINED` and passes `dark_mode=get_settings().is_dark_mode` to `SlippyMapCanvas`. |
| **Phase 61.1** | Capacitor Android CORS (`https://localhost`) | `cloudflare-worker/worker.js:9–17`, `backend/app/core/config.py:21–38` | **PASS** | Both `http://localhost` and `https://localhost` whitelisted per [Capacitor Android Documentation](https://capacitorjs.com/docs/android). |
| **Phase 61.2** | Native Service Worker Guard & Hardware Back Button | `Project/src/main.ts:59–62`, `Project/src/app/app.component.ts:48–75` | **PASS** | Disables `ngsw-worker.js` on native platforms and wires `@capacitor/app` `backButton` + `StatusBar`. |
| **Phase 61.3** | Android Release Signing & Local APK Script | `Project/android/app/build.gradle:21–42`, `scripts/build_android_apk.ps1` | **PASS** | Reads `keystore.properties` when present ([Sign your app](https://developer.android.com/studio/publish/app-signing)) and automates APK builds. |
| **Phase 61.4** | Writable `%LOCALAPPDATA%` Storage Fallback | `desktop_client/config/settings.py:204–217` | **PASS** | `.write_probe` check cleanly relocates `storage_dir` to `%LOCALAPPDATA%\NuevaEcijaTravel\storage` when read-only. |
| **Phase 61.5** | GitHub Actions Release Pipeline & Inno Setup | `.github/workflows/release-builds.yml`, `installer/NuevaEcijaTravel.iss` | **PASS** | Automates Ubuntu APK + Windows [Inno Setup](https://jrsoftware.org/inno-setup/documentation/) builds and [softprops/action-gh-release](https://github.com/softprops/action-gh-release) publishing. |
| **`PKG-REV-01`** | Frozen PyInstaller `_ASSETS_DIR` & Tile Cache Path | `desktop_client/components/slippy_map_canvas.py:50–53` | **NEEDS FIX (High)** | Still uses `Path(__file__).resolve().parent.parent / "assets"` instead of `get_settings().assets_dir`, breaking live tile resolution in compiled `_internal` builds and risking `PermissionError` in read-only installs. |
| **`PKG-REV-02`** | Standalone `build_standalone_exe.py` Flet Auto-Cache | `scripts/build_standalone_exe.py:66–72` | **NEEDS FIX (Medium)** | Missing `flet_desktop.ensure_client_cached()` fallback ([flet-desktop on PyPI](https://pypi.org/project/flet-desktop/)) when run outside GitHub Actions on a fresh machine. |
| **`PKG-REV-03`** | In-App Route Launch Missing `trip_data` Argument | `desktop_client/views/trip_detail_view.py:470` | **NEEDS FIX (Medium)** | `_launch_in_app_nav` omits `self.itinerary` and `dayNumber={day_num}`, unlike `_open_full_map` on line 928. |
| **`PKG-REV-04`** | Dark Mode Tokens in Map Drawer/Sheet & `.gitignore` | `desktop_client/views/places_view.py:783–853, 1390–1490`, `.gitignore:130` | **NEEDS FIX (Low)** | `_build_drawer_row` and `_build_poi_bottom_sheet` hardcode light-mode hex colors (`#f8fafc`, `#ffffff`), and `.gitignore` has a stray `for_updates` entry at EOF. |

## 2. Detailed Root-Cause Analysis of Remaining Findings (`PKG-REV-01` to `PKG-REV-04`)

### 2.1 `PKG-REV-01` (High): `slippy_map_canvas.py` Hardcodes `_ASSETS_DIR` via `__file__` Instead of `get_settings().assets_dir`

- **Location**: `desktop_client/components/slippy_map_canvas.py` (Lines 50–53)
- **Current Code in `0a3e2c5`**:
  ```python
  _ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
  _BUNDLED_TILES_DIR = _ASSETS_DIR / "tiles"
  _CACHE_TILES_DIR = _ASSETS_DIR / "tiles_cache"
  _CACHE_TILES_DIR.mkdir(parents=True, exist_ok=True)
  ```
- **Root Cause**:
  1. When compiled with [PyInstaller](https://www.pyinstaller.org/) 6 (`--onedir`), `slippy_map_canvas.pyc` resides inside `dist/NuevaEcijaTravel/_internal/desktop_client/components/`, so `Path(__file__).resolve().parent.parent / "assets"` points to `dist/NuevaEcijaTravel/_internal/desktop_client/assets` (which does not exist—`scripts/build_standalone_exe.py` copies `assets` to `dist/NuevaEcijaTravel/assets` and `dist/NuevaEcijaTravel/_internal/assets`). Meanwhile, `desktop_client/main.py:558` launches Flet with `assets_dir=str(_st.assets_dir)` (`dist/NuevaEcijaTravel/assets`). Consequently, in the compiled `.exe`, newly fetched tiles are written into `_internal/desktop_client/assets/tiles_cache/` while Flet's `ft.Image(src=f"/tiles_cache/{tile_key}.png")` looks in `dist/NuevaEcijaTravel/assets/tiles_cache/`, causing live-cached tiles not to render!
  2. In addition, line 53 calls `_CACHE_TILES_DIR.mkdir(parents=True, exist_ok=True)` at module import time without a `try...except` guard or write-probe check. If a user overrides the Inno Setup installation directory to `C:\Program Files\NuevaEcijaTravel` (read-only for non-elevated users), `_CACHE_TILES_DIR.mkdir()` or `_fetch_and_cache_tile()` (`tmp_file.write_bytes(data)` on line 266) will fail with `PermissionError`.
- **Remediation**:
  Resolve `_ASSETS_DIR = get_settings().assets_dir`, test write access on `_ASSETS_DIR / "tiles_cache"`, and if `_ASSETS_DIR` is read-only, fall back to `get_settings().storage_dir / "tiles_cache"` (returning the full absolute file path when `tiles_cache` is outside `assets_dir` so `ft.Image` renders it directly from disk).

### 2.2 `PKG-REV-02` (Medium): `scripts/build_standalone_exe.py` Lacks `flet_desktop.ensure_client_cached()` Provisioning

- **Location**: `scripts/build_standalone_exe.py` (Lines 66–72)
- **Current Code in `0a3e2c5`**:
  ```python
  print(f"Flet Runtime Source: {flet_cache}")
  if not flet_cache or not (flet_cache / "flet.exe").is_file():
      print(
          "ERROR: flet.exe not found in workspace cache or ~/.flet. "
          "Run `python desktop_client/main.py` once first so Flet caches the desktop engine."
      )
      sys.exit(1)
  ```
- **Root Cause**:
  While `.github/workflows/release-builds.yml` (line 119) explicitly runs `python -c "import flet_desktop; print('Cached Flet Client:', flet_desktop.ensure_client_cached())"` before calling `python scripts/build_standalone_exe.py`, running `python scripts/build_standalone_exe.py` or `.\scripts\build_desktop_installer.ps1` directly on a fresh machine where `flet` has not yet been launched will still exit with code 1.
- **Remediation**:
  Embed the `flet_desktop.ensure_client_cached()` call directly inside `scripts/build_standalone_exe.py` whenever `flet_cache` is `None`.

### 2.3 `PKG-REV-03` (Medium): `TripDetailView._launch_in_app_nav` Omits `self.itinerary` and `dayNumber`

- **Location**: `desktop_client/views/trip_detail_view.py` (Lines 468–471)
- **Current Code in `0a3e2c5`**:
  ```python
  def _launch_in_app_nav(self, day: Optional[ItineraryDay]) -> None:
      if self.on_navigate and self.itinerary:
          day_num = day.day_number if day else 1
          self.on_navigate(f"/map?itineraryId={self.itinerary.id}&day={day_num}&followRoute=true")
  ```
- **Root Cause**:
  Compare this with `_open_full_map()` on line 928 of the same file (`self.on_navigate(f"/map?followRoute=true&itineraryId={self.itinerary.id}&day={day_num}&dayNumber={day_num}", self.itinerary)`). Because `_launch_in_app_nav` does not pass `self.itinerary` as the second positional argument (`trip_data`), navigating to `/map` from the per-day "Follow Route" button relies on `selected_trip` already being populated in `main.py`. Passing `self.itinerary` and `dayNumber={day_num}` ensures 100% consistency across both entry points.

### 2.4 `PKG-REV-04` (Low): Hardcoded Light-Mode Colors in Map Drawer Rows & POI Bottom Sheet + `.gitignore` Cleanup

- **Location**: `desktop_client/views/places_view.py` (Lines 783–853 and Lines 1390–1490) & `.gitignore` (Line 130)
- **Root Cause**:
  1. In `PlacesView._build_drawer_row` (lines 783–853) and `PlacesView._build_poi_bottom_sheet` (lines 1390–1490), surface backgrounds (`#f8fafc`, `#ffffff`), borders (`#e2e8f0`), and titles (`#0f172a`, `ThemeColors.TEXT_BLACK`) are hardcoded to light-mode colors instead of reading `get_settings().palette`. When Dark Mode is active (`is_dark_mode = True`), the drawer container and zoom controls switch to dark slate, but the individual place rows inside the drawer and the POI bottom sheet remain bright white.
  2. `.gitignore` line 130 has an unformatted trailing token `for_updates` without a trailing newline.

## 3. Phased File-by-File Implementation Plan (Ready for Antigravity Execution)

### Step 1: Fix `_ASSETS_DIR` & Writable Tile Cache Resolution in `desktop_client/components/slippy_map_canvas.py`

In `desktop_client/components/slippy_map_canvas.py`:

1. Replace lines 50–53:
```python
_ASSETS_DIR = get_settings().assets_dir
_BUNDLED_TILES_DIR = _ASSETS_DIR / "tiles"


def _resolve_writable_tile_cache_dir() -> Tuple[Path, bool]:
    """Returns (cache_dir, is_inside_assets_dir) with automatic fallback to storage_dir when read-only."""
    cand = _ASSETS_DIR / "tiles_cache"
    try:
        cand.mkdir(parents=True, exist_ok=True)
        probe = cand / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return cand, True
    except Exception:
        fallback = get_settings().storage_dir / "tiles_cache"
        try:
            fallback.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return fallback, False


_CACHE_TILES_DIR, _CACHE_IN_ASSETS = _resolve_writable_tile_cache_dir()
```

2. In `_get_or_schedule_tile` (`desktop_client/components/slippy_map_canvas.py`, lines 212–217 and lines 267–273), return `f"/tiles_cache/{tile_key}.png"` when `_CACHE_IN_ASSETS` is `True`, or `str(cache_file)` when using the `%LOCALAPPDATA%` storage fallback:
```python
    # 2. Check local disk cache
    cache_file = _CACHE_TILES_DIR / f"{tile_key}.png"
    if cache_file.exists():
        try:
            if cache_file.stat().st_size >= 67:
                return f"/tiles_cache/{tile_key}.png" if _CACHE_IN_ASSETS else str(cache_file)
        except OSError:
            pass
```
And inside `_fetch_and_cache_tile` (line 272):
```python
                                if _is_valid_osm_png(data):
                                    tmp_file = _CACHE_TILES_DIR / f"{tile_key}.tmp"
                                    tmp_file.write_bytes(data)
                                    tmp_file.replace(cache_file)
                                    saved_asset_path = (
                                        f"/tiles_cache/{tile_key}.png" if _CACHE_IN_ASSETS else str(cache_file)
                                    )
                                    break
```

### Step 2: Add `flet_desktop.ensure_client_cached()` Fallback in `scripts/build_standalone_exe.py`

In `scripts/build_standalone_exe.py` (right above `print(f"Flet Runtime Source: {flet_cache}")` around line 65), insert:
```python
    if not flet_cache or not (flet_cache / "flet.exe").is_file():
        print("flet.exe not found in local cache; provisioning via flet_desktop.ensure_client_cached()...")
        try:
            import flet_desktop
            cached_dir = Path(flet_desktop.ensure_client_cached())
            if (cached_dir / "flet" / "flet.exe").is_file():
                flet_cache = cached_dir / "flet"
            elif (cached_dir / "flet.exe").is_file():
                flet_cache = cached_dir
        except Exception as exc:
            print(f"Warning: flet_desktop.ensure_client_cached() failed: {exc}")
```

### Step 3: Normalize `_launch_in_app_nav` in `desktop_client/views/trip_detail_view.py`

In `desktop_client/views/trip_detail_view.py` (lines 468–471), update `_launch_in_app_nav`:
```python
    def _launch_in_app_nav(self, day: Optional[ItineraryDay]) -> None:
        if self.on_navigate and self.itinerary:
            day_num = day.day_number if day else 1
            self.on_navigate(
                f"/map?followRoute=true&itineraryId={self.itinerary.id}&day={day_num}&dayNumber={day_num}",
                self.itinerary,
            )
```

### Step 4: Wire Dark-Mode Palette Tokens in `PlacesView._build_drawer_row` & `_build_poi_bottom_sheet` and Clean `.gitignore`

1. In `desktop_client/views/places_view.py` (`_build_drawer_row`, lines 780–853), use `palette = get_settings().palette`:
```python
    def _build_drawer_row(self, p: Place) -> ft.Control:
        """Compact horizontal row matching Web .drawer-place-card with Dark Mode parity."""
        palette = get_settings().palette
        return ft.Container(
            bgcolor=palette.surface_card_hover if palette.is_dark else "#f8fafc",
            border=ft.Border.all(1, palette.border_main),
            border_radius=12,
            padding=ft.Padding.all(8),
            ink=True,
            on_click=lambda _, pl=p: self._focus_place_and_open_dialog(pl),
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Image(
                        src=p.resolved_image_path,
                        width=60,
                        height=60,
                        fit=ft.BoxFit.COVER,
                        border_radius=8,
                    ),
                    ft.Column(
                        spacing=2,
                        tight=True,
                        expand=True,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        p.formatted_category.upper(),
                                        size=10,
                                        weight=ft.FontWeight.W_700,
                                        color="#38bdf8" if palette.is_dark else "#0084ff",
                                    ),
                                    ft.Text(
                                        p.formatted_cost,
                                        size=10,
                                        weight=ft.FontWeight.W_700,
                                        color="#10b981" if palette.is_dark else "#059669",
                                    ),
                                ],
                            ),
                            ft.Text(
                                p.name,
                                size=13,
                                weight=ft.FontWeight.W_700,
                                color=palette.text_primary,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Row(
                                spacing=3,
                                tight=True,
                                controls=[
                                    ft.Icon(ft.Icons.LOCATION_ON_OUTLINED, size=12, color=palette.text_muted),
                                    ft.Text(
                                        p.municipality_name or "Nueva Ecija",
                                        size=11,
                                        color=palette.text_muted,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Icon(ft.Icons.NEAR_ME_OUTLINED, size=16, color=palette.text_faint),
                ],
            ),
        )
```

2. In `desktop_client/views/places_view.py` (`_build_poi_bottom_sheet`, around line 1390), read `palette = get_settings().palette` and replace hardcoded `#ffffff` / `ThemeColors.TEXT_BLACK` with `palette.surface_card`, `palette.border_main`, and `palette.text_primary`.

3. In `.gitignore`, remove the stray `for_updates` line at the end of the file and add `dist_apk/` and `dist_installer/` under the build outputs section so generated installer/APK artifacts are never accidentally staged in Git:
```gitignore
# --- Installer & APK Output Directories ---
dist_apk/
dist_installer/
```

## 4. Regression Test Cases (`TC-35` & `TC-36`) to Add to `desktop_client/tests/test_cycle2_regressions.py`

Append these two tests to `desktop_client/tests/test_cycle2_regressions.py` to lock in `PKG-REV-01` and `PKG-REV-03`:

```python
def test_tc_35_slippy_map_assets_dir_uses_settings_and_writable_cache():
    """TC-35: Verifies SlippyMapCanvas resolves _ASSETS_DIR via get_settings().assets_dir (PKG-REV-01)."""
    from desktop_client.components import slippy_map_canvas
    from desktop_client.config.settings import get_settings

    assert slippy_map_canvas._ASSETS_DIR == get_settings().assets_dir
    assert slippy_map_canvas._CACHE_TILES_DIR.exists()


def test_tc_36_trip_detail_in_app_nav_passes_itinerary_and_day_number():
    """TC-36: Verifies TripDetailView._launch_in_app_nav passes both route query and itinerary object (PKG-REV-03)."""
    from desktop_client.models.itinerary import Itinerary, ItineraryDay
    from desktop_client.views.trip_detail_view import TripDetailView

    itin = Itinerary(
        id="draft",
        title="Gabaldon Nature Escape",
        destination="Gabaldon",
        days=[ItineraryDay(id="d1", day_number=2, travel_date="2026-11-20", items=[])],
    )
    captured = []
    view = TripDetailView(
        itinerary=itin,
        on_back=lambda: None,
        on_navigate=lambda route, trip=None, *args: captured.append((route, trip)),
    )
    view._launch_in_app_nav(itin.days[0])
    assert len(captured) == 1
    route_str, passed_trip = captured[0]
    assert "followRoute=true" in route_str
    assert "dayNumber=2" in route_str
    assert passed_trip is itin
```
