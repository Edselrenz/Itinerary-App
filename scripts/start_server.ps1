# ==============================================================================
# Nueva Ecija Travel App - Server Startup & Cloudflare Tunnel Script
# ==============================================================================
param (
    [switch]$WithTunnel = $true,
    [switch]$WithFrontend = $false,
    [switch]$NoTunnel
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

# 3. Locate or Install Cloudflare Tunnel
$tunnelProcess = $null
$tunnelUrl = $null

if (-not $NoTunnel) {
    Write-Host "`n[3/4] Preparing Cloudflare Tunnel for GitHub Pages..." -ForegroundColor Cyan

    $cloudflaredBin = $null
    $systemCloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($systemCloudflared) {
        $cloudflaredBin = $systemCloudflared.Source
    }

    $toolsDir = Join-Path $ProjectRoot "tools"
    $localCloudflared = Join-Path $toolsDir "cloudflared.exe"

    if (-not $cloudflaredBin -and (Test-Path $localCloudflared)) {
        $cloudflaredBin = $localCloudflared
    }

    # If not found, attempt automatic download of portable cloudflared.exe
    if (-not $cloudflaredBin) {
        Write-Host "Cloudflared not found on system. Downloading portable binary to tools/..." -ForegroundColor Yellow
        try {
            if (-not (Test-Path $toolsDir)) {
                New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null
            }
            $downloadUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
            Invoke-WebRequest -Uri $downloadUrl -OutFile $localCloudflared -UseBasicParsing -TimeoutSec 30
            if (Test-Path $localCloudflared) {
                $cloudflaredBin = $localCloudflared
                Write-Host "[OK] Downloaded portable cloudflared.exe successfully!" -ForegroundColor Green
            }
        } catch {
            Write-Host "[!] Auto-download failed: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "Trying winget install..." -ForegroundColor Gray
            Start-Process winget -ArgumentList "install Cloudflare.cloudflared --accept-package-agreements --accept-source-agreements" -Wait -NoNewWindow
            $systemCloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
            if ($systemCloudflared) {
                $cloudflaredBin = $systemCloudflared.Source
            }
        }
    }

    if ($cloudflaredBin) {
        Write-Host "Launching Cloudflare Tunnel..." -ForegroundColor Gray
        $tunnelLog = Join-Path $env:TEMP "ne_cloudflared.log"
        if (Test-Path $tunnelLog) {
            Remove-Item $tunnelLog -Force -ErrorAction SilentlyContinue
        }

        $tunnelProcess = Start-Process -FilePath $cloudflaredBin `
            -ArgumentList "tunnel --url http://127.0.0.1:8000 --no-autoupdate" `
            -RedirectStandardError $tunnelLog `
            -PassThru -NoNewWindow

        Write-Host "Connecting to Cloudflare edge network..." -ForegroundColor Gray
        for ($i = 0; $i -lt 30; $i++) {
            Start-Sleep -Milliseconds 500
            if (Test-Path $tunnelLog) {
                $logContent = Get-Content $tunnelLog -Raw -ErrorAction SilentlyContinue
                if ($logContent -match '(https://[a-zA-Z0-9-]+\.trycloudflare\.com)') {
                    $tunnelUrl = $matches[1]
                    break
                }
            }
            if ($tunnelProcess.HasExited) {
                break
            }
        }

        if ($tunnelUrl) {
            try {
                Set-Clipboard -Value $tunnelUrl
                $copiedMsg = " [COPIED TO CLIPBOARD]"
            } catch {
                $copiedMsg = ""
            }

            Write-Host "`n+----------------------------------------------------------------------+" -ForegroundColor Green
            Write-Host "|  CLOUDFLARE PUBLIC HTTPS TUNNEL CREATED!                             |" -ForegroundColor Green
            Write-Host "+----------------------------------------------------------------------+" -ForegroundColor Green
            Write-Host "  Public URL: $tunnelUrl$copiedMsg" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "  To connect GitHub Pages to this machine:" -ForegroundColor Yellow
            Write-Host "  1. Open your live app: https://edselrenz.github.io/Itinerary-App/" -ForegroundColor Yellow
            Write-Host "  2. In the top offline banner, click: [Set Server]" -ForegroundColor Yellow
            Write-Host "  3. Paste: $tunnelUrl (or press Ctrl+V)" -ForegroundColor Green
            Write-Host "+----------------------------------------------------------------------+`n" -ForegroundColor Green
        } else {
            Write-Host "[WARNING] Could not parse Cloudflare tunnel URL yet. Check $tunnelLog" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`n[!] Notice: cloudflared is not installed." -ForegroundColor Yellow
        Write-Host "To enable remote HTTPS tunneling, run:" -ForegroundColor Yellow
        Write-Host "  winget install Cloudflare.cloudflared`n" -ForegroundColor Cyan
    }
} else {
    Write-Host "`n[3/4] Tunnel disabled (-NoTunnel passed)." -ForegroundColor Gray
}

# 4. Optional: Start Ionic Frontend
if ($WithFrontend) {
    Write-Host "[+] Starting Ionic Angular Frontend..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot/Project'; npm start"
}

# 5. Start FastAPI Backend (Foreground)
Write-Host "[4/4] Starting FastAPI Server on http://127.0.0.1:8000 ..." -ForegroundColor Green
Write-Host "  * Swagger UI:    http://127.0.0.1:8000/docs" -ForegroundColor Gray
Write-Host "  * Health Check:  http://127.0.0.1:8000/api/v1/health" -ForegroundColor Gray
Write-Host "  * GitHub Pages:  https://edselrenz.github.io/Itinerary-App/" -ForegroundColor Gray
if ($tunnelUrl) {
    Write-Host "  * Live Tunnel:   $tunnelUrl" -ForegroundColor Cyan
}
Write-Host "`nPress Ctrl+C in this window to stop both the Server and Tunnel.`n" -ForegroundColor Yellow

try {
    python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
} finally {
    if ($tunnelProcess -and -not $tunnelProcess.HasExited) {
        Write-Host "`nStopping Cloudflare Tunnel..." -ForegroundColor Gray
        Stop-Process -Id $tunnelProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
