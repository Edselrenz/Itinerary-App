# ==============================================================================
# Nueva Ecija Travel App - Server Startup & Cloudflare Tunnel Script
# ==============================================================================
param (
    [switch]$WithTunnel,
    [switch]$WithFrontend
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Nueva Ecija Travel App - Local Server & Database Launcher " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Start PostgreSQL Database
Write-Host "`n[1/4] Checking PostgreSQL Database..." -ForegroundColor Yellow
$pgListening = Test-NetConnection -ComputerName 127.0.0.1 -Port 5432 -InformationLevel Quiet -WarningAction SilentlyContinue

if (-not $pgListening) {
    Write-Host "PostgreSQL is not listening on port 5432. Checking Docker..." -ForegroundColor Gray
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerCmd) {
        Write-Host "Starting PostgreSQL container via Docker Compose..." -ForegroundColor Gray
        docker compose up -d
        Start-Sleep -Seconds 3
    } else {
        Write-Host "[!] Docker not detected in PATH. If using native PostgreSQL, ensure the service is running." -ForegroundColor Yellow
    }
} else {
    Write-Host "[OK] PostgreSQL is active on port 5432." -ForegroundColor Green
}

# 2. Run Database Migrations & Seeding
Write-Host "`n[2/4] Verifying database schema & seed data..." -ForegroundColor Yellow
python scripts/setup_postgres.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Database setup returned non-zero code. Proceeding with server start..." -ForegroundColor Yellow
}

# 3. Optional: Start Cloudflare Tunnel for GitHub Pages
$tunnelProcess = $null
$cloudflaredCmd = Get-Command cloudflared -ErrorAction SilentlyContinue

if ($WithTunnel -or ($cloudflaredCmd -and -not $env:NO_TUNNEL)) {
    if ($cloudflaredCmd) {
        Write-Host "`n[3/4] Launching Cloudflare Tunnel for GitHub Pages HTTPS connectivity..." -ForegroundColor Cyan
        $tunnelProcess = Start-Process cloudflared -ArgumentList "tunnel --url http://127.0.0.1:8000" -PassThru -NoNewWindow
        Write-Host "[OK] Tunnel process started (PID: $($tunnelProcess.Id))." -ForegroundColor Green
        Write-Host "Cloudflare will output a public HTTPS URL (e.g. https://*.trycloudflare.com)." -ForegroundColor Green
        Write-Host "You can paste that HTTPS URL into the app's offline banner on GitHub Pages!" -ForegroundColor Green
    } else {
        Write-Host "`n[3/4] Notice: 'cloudflared' not found." -ForegroundColor Gray
        Write-Host "To allow GitHub Pages to reach your local server from the internet:" -ForegroundColor Gray
        Write-Host "Run: winget install Cloudflare.cloudflared" -ForegroundColor Gray
    }
} else {
    Write-Host "`n[3/4] Cloudflare Tunnel skipped (pass -WithTunnel to enable)." -ForegroundColor Gray
}

# 4. Optional: Start Ionic Frontend in background
if ($WithFrontend) {
    Write-Host "`n[+] Starting Ionic Angular Frontend..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot/Project'; npm start"
}

# 5. Start FastAPI Backend (Foreground)
Write-Host "`n[4/4] Starting FastAPI Server on http://127.0.0.1:8000 ..." -ForegroundColor Green
Write-Host "  * Swagger UI:    http://127.0.0.1:8000/docs" -ForegroundColor Gray
Write-Host "  * Health Check:  http://127.0.0.1:8000/api/v1/health" -ForegroundColor Gray
Write-Host "  * CORS Allowed:  Localhost & https://*.github.io" -ForegroundColor Gray
Write-Host "`nPress Ctrl+C to stop the server.`n" -ForegroundColor Yellow

try {
    python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
} finally {
    if ($tunnelProcess -and -not $tunnelProcess.HasExited) {
        Write-Host "`nStopping Cloudflare Tunnel..." -ForegroundColor Gray
        Stop-Process -Id $tunnelProcess.Id -Force -ErrorAction SilentlyContinue
    }
}

