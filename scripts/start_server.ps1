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

# 3. Locate and Launch Persistent Tunnel (ngrok permanent tunnel with Cloudflare fallback)
$tunnelProcess = $null
$tunnelUrl = $null
$toolsDir = Join-Path $ProjectRoot "tools"

if (-not $NoTunnel) {
    # Check for ngrok permanent domain
    $ngrokDomain = "anybody-cube-surprise.ngrok-free.dev"
    if (Test-Path (Join-Path $ProjectRoot ".env")) {
        $envLines = Get-Content (Join-Path $ProjectRoot ".env")
        foreach ($line in $envLines) {
            if ($line -match '^NGROK_DOMAIN\s*=\s*(.+)$') {
                $ngrokDomain = $matches[1].Trim()
            }
        }
    }

    $ngrokBin = Join-Path $toolsDir "ngrok.exe"
    if (-not (Test-Path $ngrokBin)) {
        $systemNgrok = Get-Command ngrok -ErrorAction SilentlyContinue
        if ($systemNgrok) {
            $ngrokBin = $systemNgrok.Source
        }
    }

    if ($ngrokBin -and (Test-Path $ngrokBin) -and $ngrokDomain) {
        Write-Host "`n[3/4] Launching Permanent ngrok Tunnel ($ngrokDomain)..." -ForegroundColor Cyan
        $tunnelLog = Join-Path $env:TEMP "ne_ngrok.log"
        if (Test-Path $tunnelLog) {
            Remove-Item $tunnelLog -Force -ErrorAction SilentlyContinue
        }

        $tunnelProcess = Start-Process -FilePath $ngrokBin `
            -ArgumentList "http --domain=$ngrokDomain 8000" `
            -RedirectStandardError $tunnelLog `
            -PassThru -NoNewWindow

        Start-Sleep -Seconds 2
        $tunnelUrl = "https://$ngrokDomain"

        Write-Host "`n+----------------------------------------------------------------------+" -ForegroundColor Green
        Write-Host "|  PERMANENT NGROK HTTPS TUNNEL ACTIVE!                                |" -ForegroundColor Green
        Write-Host "+----------------------------------------------------------------------+" -ForegroundColor Green
        Write-Host "  Fixed Backend URL: $tunnelUrl/api/v1" -ForegroundColor Cyan
        Write-Host "  Live GitHub Pages: https://edselrenz.github.io/Itinerary-App/" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  AUTOMATIC CONNECTION: ACTIVE" -ForegroundColor Green
        Write-Host "  GitHub Pages and mobile devices connect automatically without" -ForegroundColor Green
        Write-Host "  copying or pasting any URLs!" -ForegroundColor Green
        Write-Host "+----------------------------------------------------------------------+`n" -ForegroundColor Green
    } else {
        Write-Host "`n[3/4] Preparing Cloudflare Tunnel fallback for GitHub Pages..." -ForegroundColor Cyan

        $cloudflaredBin = $null
        $systemCloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
        if ($systemCloudflared) {
            $cloudflaredBin = $systemCloudflared.Source
        }

        $localCloudflared = Join-Path $toolsDir "cloudflared.exe"
        if (-not $cloudflaredBin -and (Test-Path $localCloudflared)) {
            $cloudflaredBin = $localCloudflared
        }

        if (-not $cloudflaredBin) {
            Write-Host "Downloading portable cloudflared.exe to tools/..." -ForegroundColor Yellow
            try {
                if (-not (Test-Path $toolsDir)) {
                    New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null
                }
                $downloadUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
                Invoke-WebRequest -Uri $downloadUrl -OutFile $localCloudflared -UseBasicParsing -TimeoutSec 30
                if (Test-Path $localCloudflared) {
                    $cloudflaredBin = $localCloudflared
                }
            } catch {
                Write-Host "[!] Auto-download failed: $($_.Exception.Message)" -ForegroundColor Yellow
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
                Write-Host "+----------------------------------------------------------------------+`n" -ForegroundColor Green
            }
        }
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
        Write-Host "`nStopping Tunnel process..." -ForegroundColor Gray
        Stop-Process -Id $tunnelProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
