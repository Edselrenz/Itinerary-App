# Build & Distribution Guide: Nueva Ecija Travel Desktop Client

**Client:** Python Flet Desktop Application  
**Target Output:** Windows Executable (`.exe`), Standalone Installer, macOS App Bundle (`.app`), Linux AppImage  
**Document Ref:** `DESKTOP_APP_DOCUMENTATION/08_BUILD_AND_DISTRIBUTION.md`

---

## 1. Overview of Packaging Strategies

Flet provides two primary approaches for packaging desktop applications:
1. **Flet CLI Build (`flet build windows`)**: Packages the application into a native Flutter binary bundled with Python CPython runtime. Best for production distribution.
2. **PyInstaller Standalone Packaging (`pyinstaller`)**: Freezes the Python scripts, dependencies, and Flutter engine into a standalone directory or single executable. Ideal for rapid internal distribution and testing.

---

## 2. Packaging with PyInstaller (Recommended for Windows)

### Step 1: Install PyInstaller
```powershell
pip install pyinstaller
```

### Step 2: Create Build Specification (`build.spec`)
From the `desktop_client/` directory:
```powershell
pyinstaller --name "NuevaEcijaTravel" `
  --windowed `
  --noconfirm `
  --add-data "config;config" `
  --add-data "storage;storage" `
  --hidden-import "flet" `
  --hidden-import "httpx" `
  --hidden-import "pydantic" `
  main.py
```

### Step 3: Output Directory Structure
PyInstaller produces the standalone distribution inside `desktop_client/dist/NuevaEcijaTravel/`:
```text
dist/
└── NuevaEcijaTravel/
    ├── NuevaEcijaTravel.exe     # Standalone application executable
    ├── python314.dll             # Embedded Python runtime
    ├── lib/                      # Bundled dependencies
    ├── data/flutter_assets/      # Flutter engine UI assets
    └── storage/                  # Default local storage folder
```

Users can double-click `NuevaEcijaTravel.exe` to run the application on any 64-bit Windows machine without requiring a pre-installed Python interpreter.

---

## 3. Packaging with Native Flet CLI (`flet build`)

The Flet CLI creates optimized native binaries via the Flutter toolchain.

### Prerequisites:
- Flutter SDK 3.22+
- Visual Studio 2022 with "Desktop development with C++" workload

### Execution:
```powershell
cd desktop_client
flet build windows --org ph.nuevaecijatravel --project "Nueva Ecija Travel"
```

The resulting build is compiled into `desktop_client/build/windows/x64/runner/Release/`.

---

## 4. Creating an Inno Setup Windows Installer

To distribute the application as a professional Windows setup wizard (`NuevaEcijaTravel_Setup_v1.0.0.exe`):

1. Download and install [Inno Setup](https://jrsoftware.org/isdl.php).
2. Create `installer.iss`:
```pascal
[Setup]
AppName=Nueva Ecija Travel
AppVersion=1.0.0
DefaultDirName={autopf}\NuevaEcijaTravel
DefaultGroupName=Nueva Ecija Travel
OutputBaseFilename=NuevaEcijaTravel_Setup_v1.0.0
Compression=lzma
SolidCompression=yes
OutputDir=.\dist_installer

[Files]
Source: "dist\NuevaEcijaTravel\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Nueva Ecija Travel"; Filename: "{app}\NuevaEcijaTravel.exe"
Name: "{autodesktop}\Nueva Ecija Travel"; Filename: "{app}\NuevaEcijaTravel.exe"

[Run]
Filename: "{app}\NuevaEcijaTravel.exe"; Description: "Launch Nueva Ecija Travel"; Flags: nowait postinstall skipifsilent
```
3. Compile with Inno Setup Compiler (`ISCC.exe installer.iss`).

---

## 5. Code Signing & Release Checklist

Before public release:
- [ ] Code sign `NuevaEcijaTravel.exe` using a valid Microsoft Authenticode certificate (`signtool.exe sign /a /tr http://timestamp.digicert.com ...`).
- [ ] Verify default API endpoint points to production backend (`https://api.nuevaecijatravel.ph/api/v1`).
- [ ] Test clean installation on a fresh Windows sandbox without Python installed.
- [ ] Verify export to `.ics` writes properly into the user's `Downloads` or `Documents` folder.
- [ ] Confirm local guest storage permissions restrict write access to the executing user.
