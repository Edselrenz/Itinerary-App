# Antigravity Autonomous Execution Plan: Android APK & Windows Desktop Installer Packaging (`v0.58.1`)

**Target Agent**: [Google Antigravity](https://antigravity.google/docs/skills/) (Operating in Autonomous Implementation & Packaging Mode per [Google Antigravity Rules Documentation](https://antigravity.google/docs/rules/))
**Target Repository**: `edselrenz/Itinerary-App` (Commit `9221e67fe98e78910427ef7bd19b78185c69e1ca`, Version `0.58.1`)
**Target Host OS**: Windows 11 (64-bit) with PowerShell, Python 3.11+, Node.js 20/22+, and Android Studio / JDK 21

## Agent Directives & Execution Rules for Antigravity

You are tasked with compiling, verifying, and exporting both redistributable application packages for **Trip Mo, Trip Ko — Nueva Ecija Travel Itinerary** so the user can immediately copy and test them on external Android phones and external Windows 10/11 PCs:

1. **Windows 64-bit Single-File Desktop Installer**: `dist_installer\NuevaEcijaTravel_Setup_v1.0.0.exe` (plus fallback portable archive `dist_installer\NuevaEcijaTravel_Portable_Installer_v1.0.0.zip`).
2. **Android Installable APK**: `dist_apk\TripMoTripKo-debug.apk` (and `dist_apk\TripMoTripKo-release.apk`).

Execute **Step 1 through Step 6** strictly in sequential order. Inspect every command's exit code and terminal output before advancing to the next step. Do **not** skip verification gates, and do **not** commit `.jks` keystore files or `keystore.properties` to [Git](https://git-scm.com/docs).

## Overview of Execution Phases

| Phase | Step Name | Primary Script / Tool Executed | Expected Deliverable / Acceptance Gate |
| :--- | :--- | :--- | :--- |
| **Step 1** | Pre-Flight Test & Environment Gate | `pytest` (Desktop + Backend) | **115/115** desktop tests and **21/21** backend tests pass (`0` failures). |
| **Step 2** | Provision Desktop Packaging Tooling | `pip`, [flet-desktop on PyPI](https://pypi.org/project/flet-desktop/), [Inno Setup Downloads](https://jrsoftware.org/inno-setup/downloads) (`winget`) | `pyinstaller`, `pillow`, cached `flet.exe` engine, and `ISCC.exe` verified available. |
| **Step 3** | Compile Standalone Flet Desktop App & Single-File `Setup.exe` | `scripts\build_standalone_exe.py` + `scripts\build_desktop_installer.ps1` ([PyInstaller Manual](https://www.pyinstaller.org/) & [Inno Setup Documentation](https://jrsoftware.org/inno-setup/documentation/)) | `dist\NuevaEcijaTravel\NuevaEcijaTravel.exe` and `dist_installer\NuevaEcijaTravel_Setup_v1.0.0.exe` exist and are non-empty. |
| **Step 4** | Provision Android SDK & JDK 21 Environment | [Oracle Java Documentation](https://docs.oracle.com/en/java/) (`JAVA_HOME` JDK 21) & [Android Studio CLI](https://developer.android.com/build/building-cmdline) (`ANDROID_HOME`) | `java -version` reports JDK 21; Android SDK Platform 36 (`compileSdk = 36`) resolved. |
| **Step 5** | Build Ionic Angular Production Bundle & Compile Android APK | `scripts\build_android_apk.ps1` ([Capacitor Android Documentation](https://capacitorjs.com/docs/android) & [CLI Command - cap build](https://capacitorjs.com/docs/cli/commands/build)) | `dist_apk\TripMoTripKo-debug.apk` (and `dist_apk\TripMoTripKo-release.apk` if signed) generated and verified. |
| **Step 6** | Compute SHA-256 Checksums, Sync Docs & Trigger Optional Cloud Release | PowerShell `Get-FileHash`, `docs/PROJECT_STATE.md`, `.github/workflows/release-builds.yml` ([softprops/action-gh-release](https://github.com/softprops/action-gh-release)) | Checksums logged, documentation synchronized, and final artifact paths reported. |

## Step 1: Pre-Flight Verification & Automated Test Gate

Before compiling binaries, verify that the working tree is clean and all Phase 60, 61, and 61.1 fixes (`PKG-REV-01` through `PKG-REV-04`, `TC-31` through `TC-36`) pass 100%.

### 1.1 Run Automated Test Suites from Repository Root
Execute in PowerShell at the repository root:

```powershell
# 1. Verify Desktop Client Regression & Parity Suite (Expected: 115 passed)
python -m pytest desktop_client/tests -q

# 2. Verify FastAPI Backend Suite (Expected: 21 passed)
python -m pytest backend/tests -q
```

### 1.2 Gate Criteria
- Both `pytest` commands must exit with code `0`.
- Confirm `desktop_client/assets/icon/app_icon.ico` and `desktop_client/assets/data/osm_places.json` exist on disk.

## Step 2: Provision Windows Desktop Packaging Tooling (PyInstaller, Flet Runtime & Inno Setup 6)

Ensure the Python packaging packages, the Flet Flutter Windows engine (`flet.exe`), and the [Inno Setup Command-Line Parameters](https://jrsoftware.org/ishelp/topic_setupcmdline.htm) compiler (`ISCC.exe`) are present on the machine.

### 2.1 Verify Python Dependencies & Cache Flet Desktop Runtime
Execute in PowerShell at the repository root:

```powershell
# 1. Install/upgrade PyInstaller, Pillow, and desktop client requirements
python -m pip install --upgrade pip pyinstaller pillow
python -m pip install -r desktop_client/requirements.txt

# 2. Ensure the Flet Windows desktop client binary (flet.exe) is cached locally
python -c "import flet_desktop; print('Cached Flet Client:', flet_desktop.ensure_client_cached())"
```

### 2.2 Locate or Install Inno Setup 6 (`ISCC.exe`)
Check whether `ISCC.exe` is already installed; if not, install it silently via `winget`:

```powershell
$IsccPaths = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)
$FoundIscc = $IsccPaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $FoundIscc) {
    Write-Host "Installing Inno Setup 6 via winget..."
    winget install -e --id JRSoftware.InnoSetup --accept-package-agreements --accept-source-agreements
}
```

## Step 3: Compile the Flet Desktop Standalone Bundle & Single-File `Setup.exe` Installer

Compile the Python Flet desktop application ([Packaging with PyInstaller](https://flet.dev/docs/publish/using-pyinstaller/)) into `dist\NuevaEcijaTravel\` and wrap it into a single executable installer `dist_installer\NuevaEcijaTravel_Setup_v1.0.0.exe` that unpacks everything required to run on another Windows 10/11 PC.

### 3.1 Execute the Desktop Installer Build Pipeline
Run `scripts\build_desktop_installer.ps1` from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_desktop_installer.ps1
```

### 3.2 Also Generate the Portable ZIP Archive (For USB / No-Installer Testing)
Ensure both the single-file `.exe` installer and a portable `.zip` archive (containing `Install_And_Launch.bat`) are present inside `dist_installer\`:

```powershell
if (Test-Path "dist\NuevaEcijaTravel\NuevaEcijaTravel.exe") {
    Compress-Archive -Path "dist\NuevaEcijaTravel\*" -DestinationPath "dist_installer\NuevaEcijaTravel_Portable_Installer_v1.0.0.zip" -Force
}
Get-ChildItem dist_installer
```

### 3.3 Step 3 Verification Gate
Verify all of the following before proceeding to Step 4:
1. `dist\NuevaEcijaTravel\NuevaEcijaTravel.exe` exists (~15 MB).
2. `dist\NuevaEcijaTravel\flet\flet.exe` and `dist\NuevaEcijaTravel\assets\data\osm_places.json` exist inside the distribution folder.
3. `dist\NuevaEcijaTravel\.env` exists and points to `API_BASE_URL=https://ne-itinerary-api.edselrenz0.workers.dev/api/v1`.
4. `dist_installer\NuevaEcijaTravel_Setup_v1.0.0.exe` exists (or `NuevaEcijaTravel_Portable_Installer_v1.0.0.zip` if `winget` was blocked).

## Step 4: Configure Android SDK, JDK 21 & Optional Release Keystore

`Project/android/app/capacitor.build.gradle` requires **Java 21**, and `Project/android/variables.gradle` targets **Android SDK 36**.

### 4.1 Auto-Detect and Export `JAVA_HOME` and `ANDROID_HOME`
Run in PowerShell to configure the current session and generate `Project/android/local.properties` so Gradle knows the exact SDK path on Windows:

```powershell
# 1. Resolve JDK 21 (Android Studio bundled JBR or system JDK 21)
$JbrCandidates = @(
    "C:\Program Files\Android\Android Studio\jbr",
    "$env:LOCALAPPDATA\Programs\Android Studio\jbr",
    $env:JAVA_HOME
) | Where-Object { $_ -and (Test-Path (Join-Path $_ "bin\java.exe")) }

if ($JbrCandidates) {
    $env:JAVA_HOME = $JbrCandidates[0]
    $env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
    Write-Host "Using JAVA_HOME: $env:JAVA_HOME"
    java -version
} else {
    Write-Warning "JDK 21 not found locally. Install Android Studio or Temurin JDK 21 (`winget install EclipseAdoptium.Temurin.21.JDK`), or use Step 6 Cloud Build."
}

# 2. Resolve Android SDK and write Project/android/local.properties
$SdkPath = if ($env:ANDROID_HOME -and (Test-Path $env:ANDROID_HOME)) {
    $env:ANDROID_HOME
} else {
    Join-Path $env:LOCALAPPDATA "Android\Sdk"
}

if (Test-Path $SdkPath) {
    $env:ANDROID_HOME = $SdkPath
    $env:PATH = "$SdkPath\platform-tools;$env:PATH"
    $EscapedSdk = $SdkPath.Replace("\", "\\")
    Set-Content -Path "Project\android\local.properties" -Value "sdk.dir=$EscapedSdk" -Encoding UTF8
    Write-Host "Configured Project\android\local.properties with sdk.dir=$EscapedSdk"
} else {
    Write-Warning "Android SDK not found at $SdkPath. If Android Studio is not installed locally, proceed to Step 6 to trigger the GitHub Actions cloud APK build."
}
```

### 4.2 (Optional) Generate Local Release Keystore for Signed Release APK
If `JAVA_HOME` is available and `Project\nueva-ecija-travel-release.jks` does not exist yet, generate a self-signed release keystore ([Sign your app](https://developer.android.com/studio/publish/app-signing)) so you can build both `TripMoTripKo-debug.apk` and a signed `TripMoTripKo-release.apk`:

```powershell
$KeystoreFile = "Project\nueva-ecija-travel-release.jks"
$KeystoreProps = "Project\android\keystore.properties"

if ((Test-Path "$env:JAVA_HOME\bin\keytool.exe") -and (-not (Test-Path $KeystoreFile))) {
    & "$env:JAVA_HOME\bin\keytool.exe" -genkeypair -v `
        -keystore $KeystoreFile `
        -alias nuevaecijatravel `
        -keyalg RSA -keysize 2048 -validity 10000 `
        -storepass "NuevaEcijaTravel2026!" `
        -keypass "NuevaEcijaTravel2026!" `
        -dname "CN=Edward Renz Natividad, OU=BSIT, O=NuevaEcijaTravel, L=Cabanatuan, ST=Nueva Ecija, C=PH"

    $PropsContent = @"
storeFile=../nueva-ecija-travel-release.jks
storePassword=NuevaEcijaTravel2026!
keyAlias=nuevaecijatravel
keyPassword=NuevaEcijaTravel2026!
"@
    Set-Content -Path $KeystoreProps -Value $PropsContent -Encoding UTF8
    Write-Host "Generated local release keystore and Project\android\keystore.properties (excluded by .gitignore)."
}
```

## Step 5: Compile the Ionic Angular Bundle & Android `.apk` Files

### 5.1 Execute the Automated Android APK Build Script
If `JAVA_HOME` and `ANDROID_HOME` were resolved in Step 4, run `scripts\build_android_apk.ps1` to compile both the Debug APK and (if `keystore.properties` exists) the Signed Release APK:

```powershell
# 1. Build Debug APK (dist_apk\TripMoTripKo-debug.apk)
powershell -ExecutionPolicy Bypass -File .\scripts\build_android_apk.ps1 -BuildType debug

# 2. If keystore.properties exists, also build Signed Release APK (dist_apk\TripMoTripKo-release.apk)
if (Test-Path "Project\android\keystore.properties") {
    powershell -ExecutionPolicy Bypass -File .\scripts\build_android_apk.ps1 -BuildType release -SkipNpmInstall
}

Get-ChildItem dist_apk
```

### 5.2Fallback When Android SDK / JDK 21 Is Not Installed Locally
If the local laptop does not have the Android SDK (`%LOCALAPPDATA%\Android\Sdk`) installed:
1. still run the Angular production build + Capacitor sync in `Project/` to verify 0 frontend compilation errors:
   ```powershell
   Push-Location Project
   npm ci
   npx ng build --configuration production --service-worker=false
   npx cap sync android
   Pop-Location
   ```
2. Then execute **Step 6.2** below to let GitHub Actions compile `TripMoTripKo-debug.apk` on `ubuntu-latest` and download the finished `.apk` directly into `dist_apk\`.

## Step 6: Compute Checksums, Trigger Cloud Release (If Needed) & Update Documentation

### 6.1 Compute File Sizes and SHA-256 Checksums of All Generated Deliverables
Run in PowerShell to inspect and verify all generated installer and APK artifacts:

```powershell
$Artifacts = @()
if (Test-Path "dist_installer") { $Artifacts += Get-ChildItem "dist_installer\*" -File }
if (Test-Path "dist_apk")       { $Artifacts += Get-ChildItem "dist_apk\*" -File }

foreach ($Item in $Artifacts) {
    $Hash = (Get-FileHash -Path $Item.FullName -Algorithm SHA256).Hash
    $SizeMB = [math]::Round($Item.Length / 1MB, 2)
    Write-Host ("{0,-48} | {1,8} MB | SHA256: {2}" -f $Item.Name, $SizeMB, $Hash)
}
```

### 6.2 (Optional / Fallback) Trigger GitHub Actions Cloud Build & Download APK / Setup.exe via `gh` CLI
If GitHub CLI (`gh`) is authenticated on the machine—or if Android SDK was not installed locally in Step 4—trigger `.github/workflows/release-builds.yml` in the cloud and download the compiled artifacts into `dist_apk\` and `dist_installer\`:

```powershell
# Check if GitHub CLI is available and authenticated
gh auth status
if ($LASTEXITCODE -eq 0) {
    Write-Host "Triggering .github/workflows/release-builds.yml on GitHub Actions..."
    gh workflow run release-builds.yml -f version_tag=v1.0.0 -f publish_release=true
    Write-Host "Use 'gh run watch' to monitor progress, then 'gh run download' to pull android-apk-artifacts and windows-desktop-installer."
}
```

### 6.3 Synchronize Continuous Documentation (`docs/PROJECT_STATE.md` & `docs/DEVELOPMENT_LOG.md`)
1. Record the final compiled artifact filenames, byte/MB sizes, and SHA-256 checksums in `docs/PROJECT_STATE.md` and `docs/DEVELOPMENT_LOG.md`.
2. Run `git status` to verify that no untracked secrets (`*.jks`, `keystore.properties`, `.env`) are staged.

## Final Output Report Format Required from Antigravity

Upon completing Steps 1–6, report to the user:
1. **Test Gate Summary**: Exact pass counts for `desktop_client/tests` (`115/115`) and `backend/tests` (`21/21`).
2. **Generated Desktop Installer Paths & Sizes**:
   - Single-File Installer: `dist_installer\NuevaEcijaTravel_Setup_v1.0.0.exe` (size in MB + SHA-256).
   - Portable Installer Zip: `dist_installer\NuevaEcijaTravel_Portable_Installer_v1.0.0.zip` (size in MB + SHA-256).
3. **Generated Android APK Paths & Sizes**:
   - Debug APK: `dist_apk\TripMoTripKo-debug.apk` (size in MB + SHA-256).
   - Signed Release APK: `dist_apk\TripMoTripKo-release.apk` (size in MB + SHA-256, or cloud workflow status if built via GitHub Actions).
4. **Device Transfer Instructions**: One-line summary of which file to copy to another Windows PC (`dist_installer\NuevaEcijaTravel_Setup_v1.0.0.exe`) and which file to copy to an Android phone (`dist_apk\TripMoTripKo-debug.apk` or `TripMoTripKo-release.apk`).
