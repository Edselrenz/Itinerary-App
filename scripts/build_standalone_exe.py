"""Build script compiling Nueva Ecija Travel desktop application into a standalone Windows .exe."""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _ensure_ico_file(desktop_dir: Path) -> Path | None:
    """Ensures desktop_client/assets/icon/app_icon.ico exists by converting favicon.png if needed."""
    ico_path = desktop_dir / "assets" / "icon" / "app_icon.ico"
    if ico_path.is_file():
        return ico_path
    png_icon = desktop_dir / "assets" / "icon" / "favicon.png"
    if not png_icon.is_file():
        return None
    try:
        from PIL import Image

        img = Image.open(png_icon).convert("RGBA")
        img.save(
            ico_path,
            format="ICO",
            sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
        )
        print(f"Generated Windows application icon: {ico_path}")
        return ico_path
    except Exception as exc:
        print(f"Note: Could not convert favicon.png to .ico ({exc}); proceeding without custom .ico.")
        return None


def build():
    root_dir = Path(__file__).resolve().parent.parent
    desktop_dir = root_dir / "desktop_client"
    dist_dir = root_dir / "dist"
    build_dir = root_dir / "build_temp"

    print("==================================================")
    print(" Compiling Nueva Ecija Travel Standalone Windows App")
    print("==================================================")
    print(f"Root: {root_dir}")
    print(f"Source: {desktop_dir}")

    # Locate flet runtime
    flet_cache = None
    workspace_cache = root_dir / "build_cache" / "flet_runtime"
    existing_dist = dist_dir / "NuevaEcijaTravel" / "flet"

    if (workspace_cache / "flet.exe").is_file():
        flet_cache = workspace_cache
    elif (existing_dist / "flet.exe").is_file():
        workspace_cache.mkdir(parents=True, exist_ok=True)
        shutil.copytree(existing_dist, workspace_cache, dirs_exist_ok=True)
        flet_cache = workspace_cache
    else:
        try:
            cand = Path.home() / ".flet" / "client" / "flet-desktop-full-1.1.2" / "flet"
            if (cand / "flet.exe").is_file():
                flet_cache = cand
            else:
                flet_base = Path.home() / ".flet" / "client"
                if flet_base.exists():
                    for sub in sorted(flet_base.iterdir(), reverse=True):
                        cand = sub / "flet"
                        if (cand / "flet.exe").is_file():
                            flet_cache = cand
                            break
        except Exception:
            pass

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

    print(f"Flet Runtime Source: {flet_cache}")
    if not flet_cache or not (flet_cache / "flet.exe").is_file():
        print(
            "ERROR: flet.exe not found in workspace cache or ~/.flet. "
            "Run `python desktop_client/main.py` once first so Flet caches the desktop engine."
        )
        sys.exit(1)

    # Terminate any running instances of NuevaEcijaTravel.exe or flet.exe holding file locks in dist/
    if os.name == "nt":
        for proc_name in ("NuevaEcijaTravel.exe", "flet.exe"):
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", proc_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=3,
                )
            except Exception:
                pass

    # Clean previous build_temp; stage PyInstaller output in build_temp/dist_stage first
    # so dist/NuevaEcijaTravel is NEVER partially deleted if a running instance holds a lock
    if build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)
    stage_dist_dir = build_dir / "dist_stage"
    stage_dist_dir.mkdir(parents=True, exist_ok=True)

    ico_file = _ensure_ico_file(desktop_dir)
    entrypoint = desktop_dir / "main.py"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        "NuevaEcijaTravel",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(stage_dist_dir),
        "--workpath",
        str(build_dir / "work"),
    ]
    if ico_file and ico_file.is_file():
        cmd.extend(["--icon", str(ico_file)])

    cmd.extend([
        # Add source packages
        "--add-data",
        f"{desktop_dir / 'config'}{os.pathsep}desktop_client/config",
        "--add-data",
        f"{desktop_dir / 'core'}{os.pathsep}desktop_client/core",
        "--add-data",
        f"{desktop_dir / 'models'}{os.pathsep}desktop_client/models",
        "--add-data",
        f"{desktop_dir / 'services'}{os.pathsep}desktop_client/services",
        "--add-data",
        f"{desktop_dir / 'components'}{os.pathsep}desktop_client/components",
        "--add-data",
        f"{desktop_dir / 'views'}{os.pathsep}desktop_client/views",
        "--add-data",
        f"{desktop_dir / 'assets'}{os.pathsep}assets",
        "--add-data",
        f"{desktop_dir / 'assets'}{os.pathsep}desktop_client/assets",
        # Hidden imports and package data collection
        "--collect-all",
        "flet",
        "--collect-all",
        "flet_desktop",
        "--hidden-import",
        "desktop_client",
        "--hidden-import",
        "desktop_client.config",
        "--hidden-import",
        "desktop_client.config.settings",
        "--hidden-import",
        "desktop_client.core",
        "--hidden-import",
        "desktop_client.core.api_client",
        "--hidden-import",
        "desktop_client.core.session",
        "--hidden-import",
        "desktop_client.core.storage",
        "--hidden-import",
        "desktop_client.core.export",
        "--hidden-import",
        "desktop_client.core.connectivity_service",
        "--hidden-import",
        "desktop_client.core.offline_data",
        "--hidden-import",
        "desktop_client.core.polyline",
        "--hidden-import",
        "desktop_client.core.geo",
        "--hidden-import",
        "desktop_client.core.commute_guide",
        "--hidden-import",
        "desktop_client.models",
        "--hidden-import",
        "desktop_client.models.user",
        "--hidden-import",
        "desktop_client.models.place",
        "--hidden-import",
        "desktop_client.models.itinerary",
        "--hidden-import",
        "desktop_client.services",
        "--hidden-import",
        "desktop_client.services.auth_service",
        "--hidden-import",
        "desktop_client.services.place_service",
        "--hidden-import",
        "desktop_client.services.itinerary_service",
        "--hidden-import",
        "desktop_client.services.favorites_service",
        "--hidden-import",
        "desktop_client.components",
        "--hidden-import",
        "desktop_client.components.bottom_tab_bar",
        "--hidden-import",
        "desktop_client.components.date_range_dialog",
        "--hidden-import",
        "desktop_client.components.destination_picker",
        "--hidden-import",
        "desktop_client.components.dialogs",
        "--hidden-import",
        "desktop_client.components.itinerary_route_map",
        "--hidden-import",
        "desktop_client.components.offline_banner",
        "--hidden-import",
        "desktop_client.components.place_card",
        "--hidden-import",
        "desktop_client.components.slippy_map_canvas",
        "--hidden-import",
        "desktop_client.components.splash_overlay",
        "--hidden-import",
        "desktop_client.components.stop_card",
        "--hidden-import",
        "desktop_client.components.workflow_header",
        "--hidden-import",
        "desktop_client.views",
        "--hidden-import",
        "desktop_client.views.custom_builder_view",
        "--hidden-import",
        "desktop_client.views.dashboard_view",
        "--hidden-import",
        "desktop_client.views.guest_view",
        "--hidden-import",
        "desktop_client.views.login_view",
        "--hidden-import",
        "desktop_client.views.places_view",
        "--hidden-import",
        "desktop_client.views.profile_view",
        "--hidden-import",
        "desktop_client.views.saved_trips_view",
        "--hidden-import",
        "desktop_client.views.signup_view",
        "--hidden-import",
        "desktop_client.views.suggested_wizard_view",
        "--hidden-import",
        "desktop_client.views.trip_detail_view",
        "--hidden-import",
        "desktop_client.views.welcome_view",
        "--hidden-import",
        "flet",
        "--hidden-import",
        "flet_desktop",
        "--hidden-import",
        "httpx",
        "--hidden-import",
        "pydantic",
        "--hidden-import",
        "anyio",
        "--hidden-import",
        "msgpack",
        "--hidden-import",
        "repath",
        "--hidden-import",
        "oauthlib",
        "--hidden-import",
        "dotenv",
        str(entrypoint),
    ])

    print(f"\nExecuting PyInstaller: {' '.join(cmd[:10])} ...")
    res = subprocess.run(cmd, cwd=str(root_dir))
    if res.returncode != 0:
        print(f"PyInstaller failed with code {res.returncode}")
        sys.exit(res.returncode)

    staged_app_dir = stage_dist_dir / "NuevaEcijaTravel"
    out_app_dir = dist_dir / "NuevaEcijaTravel"
    print(f"\nPyInstaller staging completed: {staged_app_dir}")

    # Copy bundled Flet Flutter runtime directly into the staged distribution folder
    target_flet_dir = staged_app_dir / "flet"
    print(f"Bundling Flet Flutter engine from {flet_cache} -> {target_flet_dir} ...")
    shutil.copytree(flet_cache, target_flet_dir, dirs_exist_ok=True)

    # Copy also to _internal/flet if PyInstaller placed internals there
    internal_dir = staged_app_dir / "_internal"
    if internal_dir.exists():
        internal_flet = internal_dir / "flet"
        shutil.copytree(flet_cache, internal_flet, dirs_exist_ok=True)

    # Ensure flet package data (icons.json, cupertino_icons.json) is present in _internal
    try:
        import flet

        flet_pkg_dir = Path(flet.__file__).parent
        if (flet_pkg_dir / "controls").exists() and internal_dir.exists():
            internal_controls = internal_dir / "flet" / "controls"
            internal_controls.mkdir(parents=True, exist_ok=True)
            shutil.copytree(flet_pkg_dir / "controls", internal_controls, dirs_exist_ok=True)
            print("Successfully copied flet/controls package data (icons.json, etc.)")
    except Exception as e:
        print("Warning copying flet package data:", e)

    # Copy desktop_client/assets into staged_app_dir/assets so osm_places.json (2,673 POIs) & photos are always present
    target_assets_dir = staged_app_dir / "assets"
    shutil.copytree(desktop_dir / "assets", target_assets_dir, dirs_exist_ok=True)
    if internal_dir.exists():
        shutil.copytree(desktop_dir / "assets", internal_dir / "assets", dirs_exist_ok=True)
    print("Successfully copied desktop_client/assets (2,673 OSM places + photos) to output distribution")

    # Create local storage directory
    storage_dir = staged_app_dir / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    exports_dir = storage_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)

    # Copy .env.example or write default production .env pointing to the Cloudflare Worker gateway
    env_example = desktop_dir / ".env.example"
    env_target = staged_app_dir / ".env"
    if env_example.exists():
        shutil.copy(env_example, env_target)
    elif not env_target.exists():
        env_target.write_text(
            "API_BASE_URL=https://ne-itinerary-api.edselrenz0.workers.dev/api/v1\n"
            "DEBUG=False\n"
            "API_TIMEOUT_SECONDS=15.0\n"
            "ITINERARY_GEN_TIMEOUT_SECONDS=45.0\n",
            encoding="utf-8",
        )

    # Sync complete staged build into dist/NuevaEcijaTravel (using NTFS .old rename fallback for any locked binary)
    out_app_dir.mkdir(parents=True, exist_ok=True)
    for old_file in out_app_dir.rglob("*.old"):
        try:
            old_file.unlink()
        except Exception:
            pass
    for src_item in staged_app_dir.rglob("*"):
        rel = src_item.relative_to(staged_app_dir)
        dst_item = out_app_dir / rel
        if src_item.is_dir():
            dst_item.mkdir(parents=True, exist_ok=True)
        elif src_item.is_file():
            dst_item.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src_item, dst_item)
            except PermissionError:
                old_dst = dst_item.with_suffix(dst_item.suffix + ".old")
                try:
                    if old_dst.exists():
                        old_dst.unlink()
                    dst_item.rename(old_dst)
                    shutil.copy2(src_item, dst_item)
                except Exception:
                    pass

    # Verify NuevaEcijaTravel.exe exists
    exe_file = out_app_dir / "NuevaEcijaTravel.exe"
    if not exe_file.is_file():
        print("ERROR: Output executable not found!")
        sys.exit(1)

    exe_size_mb = exe_file.stat().st_size / (1024 * 1024)
    total_size_mb = sum(f.stat().st_size for f in out_app_dir.rglob("*") if f.is_file()) / (1024 * 1024)

    print("\n==================================================")
    print(" BUILD SUCCESSFUL!")
    print("==================================================")
    print(f"Executable: {exe_file}")
    print(f"Executable Size: {exe_size_mb:.2f} MB")
    print(f"Total Standalone Distribution Size: {total_size_mb:.2f} MB")
    print(f"To run: Double-click '{exe_file}'")
    print("==================================================")


if __name__ == "__main__":
    build()