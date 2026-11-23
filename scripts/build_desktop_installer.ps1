<#
.SYNOPSIS
    Compiles the Flet Python desktop app via PyInstaller and packages it into a
    single-file Windows installer (NuevaEcijaTravel_Setup_v1.0.0.exe) using Inno Setup.
.DESCRIPTION
    1. Installs/verifies PyInstaller, Pillow, and desktop_client/requirements.txt
    2. Executes scripts/build_standalone_exe.py -> dist/NuevaEcijaTravel/
    3. Generates Install_And_Launch.bat inside dist/NuevaEcijaTravel/
    4. Invokes Inno Setup Compiler (ISCC.exe) on installer/NuevaEcijaTravel.iss
       to produce dist_installer/NuevaEcijaTravel_Setup_v1.0.0.exe (or falls back
       to a self-contained portable installer archive if Inno Setup is not installed).
#>
param(
    [switch]$SkipPyInstaller = $false
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot
$DistDir = Join-Path $RootDir "dist\NuevaEcijaTravel"
$OutDir  = Join-Path $RootDir "dist_installer"
$IssFile = Join-Path $RootDir "installer\NuevaEcijaTravel.iss"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Trip Mo, Trip Ko - Desktop Standalone and Installer Builder" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

if (-not $SkipPyInstaller) {
    Write-Host "`n[1/3] Installing Python packaging dependencies..." -ForegroundColor Yellow
    python -m pip install --upgrade pip pyinstaller pillow
    python -m pip install -r (Join-Path $RootDir "desktop_client\requirements.txt")

    Write-Host "`n[2/3] Running PyInstaller standalone build (scripts/build_standalone_exe.py)..." -ForegroundColor Yellow
    python (Join-Path $RootDir "scripts\build_standalone_exe.py")
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed with exit code $LASTEXITCODE."
    }
}

if (-not (Test-Path (Join-Path $DistDir "NuevaEcijaTravel.exe"))) {
    throw "dist\NuevaEcijaTravel\NuevaEcijaTravel.exe not found. Ensure PyInstaller completed."
}

# Remove any temporary .old hot-swap files from dist/NuevaEcijaTravel before packaging
Get-ChildItem -Path $DistDir -Recurse -Filter "*.old" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

# Embed one-click fallback installer batch file inside dist/NuevaEcijaTravel
$InstallBatLines = @(
    '@echo off',
    'title Installing Trip Mo, Trip Ko - Nueva Ecija Travel',
    'set "TARGET_DIR=%LOCALAPPDATA%\Programs\NuevaEcijaTravel"',
    'echo Unpacking Trip Mo, Trip Ko to "%TARGET_DIR%"...',
    'if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"',
    'xcopy /E /I /Y "%~dp0*" "%TARGET_DIR%\" >nul',
    'powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath(''Desktop'') + ''\Trip Mo, Trip Ko.lnk''); $s.TargetPath = ''%TARGET_DIR%\NuevaEcijaTravel.exe''; $s.WorkingDirectory = ''%TARGET_DIR%''; $s.IconLocation = ''%TARGET_DIR%\NuevaEcijaTravel.exe,0''; $s.Save()"',
    'echo Installation complete! Launching Trip Mo, Trip Ko...',
    'start "" "%TARGET_DIR%\NuevaEcijaTravel.exe"'
)
$InstallBat = $InstallBatLines -join "`r`n"
Set-Content -Path (Join-Path $DistDir "Install_And_Launch.bat") -Value $InstallBat -Encoding ASCII

Write-Host "`n[3/3] Building single-file Windows Setup.exe via Inno Setup..." -ForegroundColor Yellow
$IsccCandidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)

$IsccExe = $null
foreach ($Candidate in $IsccCandidates) {
    if (Test-Path $Candidate) {
        $IsccExe = $Candidate
        break
    }
}

if ($IsccExe) {
    Write-Host "Found Inno Setup Compiler: $IsccExe" -ForegroundColor Green
    & $IsccExe $IssFile
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup compilation failed with exit code $LASTEXITCODE."
    }
    Write-Host "`n==========================================================" -ForegroundColor Green
    Write-Host " SUCCESS! Single-File Installer Created:" -ForegroundColor Green
    Write-Host " $OutDir\NuevaEcijaTravel_Setup_v1.0.0.exe" -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
} else {
    Write-Warning "Inno Setup 6 (ISCC.exe) was not found. Install it via: winget install -e --id JRSoftware.InnoSetup"
}

$ZipOut = Join-Path $OutDir "NuevaEcijaTravel_Portable_Installer_v1.0.0.zip"
Write-Host "Refreshing portable installer archive at: $ZipOut" -ForegroundColor Yellow
python -c "import zipfile; from pathlib import Path; dist_dir = Path(r'$DistDir'); zip_out = Path(r'$ZipOut'); zf = zipfile.ZipFile(zip_out, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6); [zf.write(p, p.relative_to(dist_dir)) for p in dist_dir.rglob('*') if p.is_file() and not p.name.endswith('.old')]; zf.close()"
Write-Host "Created $ZipOut (contains Install_And_Launch.bat + full standalone build)." -ForegroundColor Green
