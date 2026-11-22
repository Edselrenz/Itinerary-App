<#
.SYNOPSIS
    Builds the Ionic Angular web app (Project/) into an Android APK using Capacitor and Gradle.
.PARAMETER BuildType
    'debug' (default, no keystore required) or 'release' (uses Project/android/keystore.properties if present).
.PARAMETER InstallToDevice
    If set, runs `adb install -r` to deploy the compiled APK directly to a connected Android phone.
#>
param(
    [ValidateSet("debug", "release")]
    [string]$BuildType = "debug",
    [switch]$SkipNpmInstall = $false,
    [switch]$InstallToDevice = $false
)

$ErrorActionPreference = "Stop"
$RootDir    = Split-Path -Parent $PSScriptRoot
$ProjectDir = Join-Path $RootDir "Project"
$AndroidDir = Join-Path $ProjectDir "android"
$OutApkDir  = Join-Path $RootDir "dist_apk"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Trip Mo, Trip Ko — Capacitor Android APK Builder ($BuildType)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Auto-detect JAVA_HOME (JDK 21 required by Project/android/app/capacitor.build.gradle)
if (-not $env:JAVA_HOME -or -not (Test-Path (Join-Path $env:JAVA_HOME "bin\java.exe"))) {
    $JbrCandidates = @(
        "C:\Program Files\Android\Android Studio\jbr",
        "$env:LOCALAPPDATA\Programs\Android Studio\jbr"
    )
    foreach ($Cand in $JbrCandidates) {
        if (Test-Path (Join-Path $Cand "bin\java.exe")) {
            $env:JAVA_HOME = $Cand
            $env:PATH = "$Cand\bin;$env:PATH"
            Write-Host "Auto-detected JAVA_HOME: $env:JAVA_HOME" -ForegroundColor Green
            break
        }
    }
}

# 2. Auto-detect ANDROID_HOME
if (-not $env:ANDROID_HOME) {
    $DefaultSdk = Join-Path $env:LOCALAPPDATA "Android\Sdk"
    if (Test-Path $DefaultSdk) {
        $env:ANDROID_HOME = $DefaultSdk
        $env:PATH = "$DefaultSdk\platform-tools;$env:PATH"
        Write-Host "Auto-detected ANDROID_HOME: $env:ANDROID_HOME" -ForegroundColor Green
    }
}

Push-Location $ProjectDir
try {
    if (-not $SkipNpmInstall) {
        Write-Host "`n[1/4] Installing npm dependencies (npm ci)..." -ForegroundColor Yellow
        npm ci
        if ($LASTEXITCODE -ne 0) { throw "npm ci failed." }
    }

    Write-Host "`n[2/4] Building production Ionic Angular bundle (--no-service-worker)..." -ForegroundColor Yellow
    npx ng build --configuration production --no-service-worker
    if ($LASTEXITCODE -ne 0) { throw "Angular production build failed." }

    Write-Host "`n[3/4] Syncing web assets and native plugins to Android (npx cap sync android)..." -ForegroundColor Yellow
    npx cap sync android
    if ($LASTEXITCODE -ne 0) { throw "Capacitor sync failed." }

    Write-Host "`n[4/4] Compiling Android APK via Gradle Wrapper..." -ForegroundColor Yellow
    Push-Location $AndroidDir
    try {
        if ($BuildType -eq "release") {
            .\gradlew.bat assembleRelease
            $BuiltApk = Join-Path $AndroidDir "app\build\outputs\apk\release\app-release.apk"
            $UnsignedApk = Join-Path $AndroidDir "app\build\outputs\apk\release\app-release-unsigned.apk"
            if (-not (Test-Path $BuiltApk) -and (Test-Path $UnsignedApk)) {
                $BuiltApk = $UnsignedApk
            }
            $TargetApkName = "TripMoTripKo-release.apk"
        } else {
            .\gradlew.bat assembleDebug
            $BuiltApk = Join-Path $AndroidDir "app\build\outputs\apk\debug\app-debug.apk"
            $TargetApkName = "TripMoTripKo-debug.apk"
        }
        if ($LASTEXITCODE -ne 0) { throw "Gradle APK build failed." }
    } finally {
        Pop-Location
    }

    New-Item -ItemType Directory -Force -Path $OutApkDir | Out-Null
    $FinalApkPath = Join-Path $OutApkDir $TargetApkName
    Copy-Item -Path $BuiltApk -Destination $FinalApkPath -Force

    Write-Host "`n==========================================================" -ForegroundColor Green
    Write-Host " APK BUILD SUCCESSFUL!" -ForegroundColor Green
    Write-Host " Gradle Output : $BuiltApk" -ForegroundColor Green
    Write-Host " Copied To     : $FinalApkPath" -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green

    if ($InstallToDevice) {
        Write-Host "Installing APK onto connected Android device via ADB..." -ForegroundColor Yellow
        adb install -r $FinalApkPath
    }
} finally {
    Pop-Location
}
