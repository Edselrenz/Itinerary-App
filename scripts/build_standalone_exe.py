"""Build script compiling Nueva Ecija Travel desktop application into a standalone Windows .exe."""

import os
import shutil
import subprocess
import sys
from pathlib import Path


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

    # Locate flet runtime in user cache
    flet_cache = Path.home() / ".flet" / "client" / "flet-desktop-full-1.1.2" / "flet"
    if not flet_cache.exists():
        # Fallback search in ~/.flet
        flet_base = Path.home() / ".flet" / "client"
        if flet_base.exists():
            for sub in flet_base.iterdir():
                cand = sub / "flet"
                if (cand / "flet.exe").is_file():
                    flet_cache = cand
                    break

    print(f"Flet Runtime Source: {flet_cache}")
    if not (flet_cache / "flet.exe").is_file():
        print("ERROR: flet.exe not found in cache. Please run flet_desktop.ensure_client_cached() first.")
        sys.exit(1)

    # Clean previous builds
    if dist_dir.exists():
        shutil.rmtree(dist_dir, ignore_errors=True)
    if build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)

    # Assemble PyInstaller command
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
        str(dist_dir),
        "--workpath",
        str(build_dir),
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
        # Hidden imports
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
        "desktop_client.components",
        "--hidden-import",
        "desktop_client.views",
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
        str(entrypoint),
    ]

    print(f"\nExecuting PyInstaller: {' '.join(cmd[:10])} ...")
    res = subprocess.run(cmd, cwd=str(root_dir))
    if res.returncode != 0:
        print(f"PyInstaller failed with code {res.returncode}")
        sys.exit(res.returncode)

    out_app_dir = dist_dir / "NuevaEcijaTravel"
    print(f"\nPyInstaller build completed: {out_app_dir}")

    # Copy bundled Flet Flutter runtime directly into the distribution folder
    target_flet_dir = out_app_dir / "flet"
    print(f"Bundling Flet Flutter engine from {flet_cache} -> {target_flet_dir} ...")
    shutil.copytree(flet_cache, target_flet_dir, dirs_exist_ok=True)

    # Copy also to _internal/flet if PyInstaller placed internals there
    internal_dir = out_app_dir / "_internal"
    if internal_dir.exists():
        internal_flet = internal_dir / "flet"
        shutil.copytree(flet_cache, internal_flet, dirs_exist_ok=True)

    # Create local storage directory
    storage_dir = out_app_dir / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    exports_dir = storage_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)

    # Copy .env.example
    env_example = desktop_dir / ".env.example"
    if env_example.exists():
        shutil.copy(env_example, out_app_dir / ".env")

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
