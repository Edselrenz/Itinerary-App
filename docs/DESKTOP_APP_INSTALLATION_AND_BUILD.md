# Desktop Application Installation, Build & Distribution Guide

**Target Application**: Nueva Ecija Travel Desktop Client ("Trip mo, trip ko")  
**Framework**: Python Flet >= 1.1.2  
**Executable Target**: Windows 64-bit Standalone Executable (`NuevaEcijaTravel.exe`)  
**Specification File**: `NuevaEcijaTravel.spec`  
**Document Ref**: `docs/DESKTOP_APP_INSTALLATION_AND_BUILD.md`  

---

## 1. Development Environment Setup

### System Prerequisites
* **Operating System**: Windows 10/11 (64-bit), macOS 13+, or Ubuntu 22.04+
* **Python Runtime**: Python 3.11, 3.12, 3.13, or **Python 3.14.3**
* **Git**: Installed and configured

### Installation Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-org/CaseStudy.git
   cd CaseStudy
   ```

2. **Verify Python & Install Dependencies**:
   ```powershell
   # Windows PowerShell
   python -m pip install --upgrade pip
   python -m pip install flet httpx pydantic python-dotenv pytest pyinstaller
   ```

3. **Verify Environment Configuration**:
   Ensure `.env` exists in the repository root (or copy `.env.example`):
   ```env
   API_BASE_URL=http://127.0.0.1:8000/api/v1
   DEBUG=False
   API_TIMEOUT_SECONDS=15.0
   ITINERARY_GEN_TIMEOUT_SECONDS=45.0
   ```

---

## 2. Running in Development Mode

The desktop client can be launched immediately using the provided Windows batch launcher or directly through Python:

### Option A: Using the Launcher Script
Double-click [run_desktop_app.bat](file:///C:/Users/Edward/Desktop/CaseStudy/run_desktop_app.bat) in the repository root, which executes:
```cmd
@echo off
title Nueva Ecija Travel - Desktop Application
cd /d "%~dp0"
python desktop_client\main.py
```

### Option B: Using the Terminal
```powershell
# From repository root
python desktop_client/main.py
```

### Hot-Reloading Mode
To run with automatic UI hot-reloading enabled during development:
```powershell
flet run desktop_client/main.py -d
```

---

## 3. Production Packaging with PyInstaller

The desktop client compiles into a standalone, portable Windows distribution requiring **no pre-installed Python runtime, no pip packages, and no external dependencies**.

### 3.1 PyInstaller Specification (`NuevaEcijaTravel.spec`)

The specification bundles all core modules, views, components, and authentic local photography:

```python
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [
    ('desktop_client/config', 'desktop_client/config'),
    ('desktop_client/core', 'desktop_client/core'),
    ('desktop_client/models', 'desktop_client/models'),
    ('desktop_client/services', 'desktop_client/services'),
    ('desktop_client/components', 'desktop_client/components'),
    ('desktop_client/views', 'desktop_client/views'),
    ('desktop_client/assets', 'desktop_client/assets'),
    ('desktop_client/assets', 'assets'),
]

binaries = []
hiddenimports = [
    'desktop_client', 'desktop_client.config', 'desktop_client.config.settings',
    'desktop_client.core', 'desktop_client.core.api_client', 'desktop_client.core.session',
    'desktop_client.core.storage', 'desktop_client.core.export', 'desktop_client.core.async_utils',
    'desktop_client.core.commute_guide', 'desktop_client.core.offline_data',
    'desktop_client.models', 'desktop_client.models.user', 'desktop_client.models.place',
    'desktop_client.models.itinerary', 'desktop_client.services', 'desktop_client.services.auth_service',
    'desktop_client.services.place_service', 'desktop_client.services.itinerary_service',
    'desktop_client.services.favorites_service', 'desktop_client.components',
    'desktop_client.views', 'flet', 'flet_desktop', 'httpx', 'pydantic', 'anyio',
]

tmp_ret = collect_all('flet')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('flet_desktop')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

a = Analysis(
    ['desktop_client/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NuevaEcijaTravel',
    debug=False,
    console=False,
    upx=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name='NuevaEcijaTravel',
)
```

### 3.2 Executing the Standalone Build

To compile a fresh standalone distribution:
```powershell
pyinstaller NuevaEcijaTravel.spec --clean --noconfirm
```

Output directory structure:
```text
dist/
└── NuevaEcijaTravel/
    ├── NuevaEcijaTravel.exe       # Standalone binary
    ├── python314.dll              # Embedded runtime
    ├── assets/                    # 47 bundled authentic photos, brand logos, and datasets
    │   ├── popular_destinations/
    │   ├── logout_skyscrapers_blob.png
    │   ├── welcome_hero_buildings.png
    │   ├── pattranite_avatar.jpg
    │   └── data/osm_places.json
    └── _internal/                 # Compiled bytecode and shared libraries
```

---

## 4. Launching the Standalone Distribution

The compiled distribution can be launched directly using the root launcher:
* **Double-click**: [Run_NuevaEcijaTravel_EXE.bat](file:///C:/Users/Edward/Desktop/CaseStudy/Run_NuevaEcijaTravel_EXE.bat)
* **Direct Path**: `dist\NuevaEcijaTravel\NuevaEcijaTravel.exe`

The standalone client starts in **under 1.5 seconds**, connects to the local or remote FastAPI backend, and renders all photography and design system tokens cleanly.

---

## 5. Troubleshooting & Common Issues

| Symptom | Cause | Resolution |
| :--- | :--- | :--- |
| **Window fails to open on click** | Missing assets directory in `dist/` | Ensure `desktop_client/assets` is copied to `dist/NuevaEcijaTravel/assets`. |
| **Backend offline indicator on startup** | FastAPI backend server not running | Start backend via [start_server.bat](file:///C:/Users/Edward/Desktop/CaseStudy/start_server.bat) or run in offline guest mode. |
| **`RuntimeError: Event loop is running`** | Calling `asyncio.run()` directly in UI | Wrap all async task dispatches in `run_async(coro, page)`. |
| **Missing destination photos** | Offline places looking for HTTP URLs | Photos are resolved locally via `resolve_place_image()`. |
