# ==============================================================================
# Nueva Ecija Travel App - Server Startup & Dual Tunnel Script (ngrok + Cloudflare)
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
Write-Host "  Nueva Ecija Travel App - Local Server & Dual Tunnel       " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Start or Verify Database
Write-Host "`n[1/4] Checking PostgreSQL Database..." -ForegroundColor Yellow
$pgListening = $false
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $iar = $tcp.BeginConnect("127.0.0.1", 5432, $null, $null)
    $success = $iar.AsyncWaitHandle.WaitOne(1000)
    if ($success -and $tcp.Connected) {
        $tcp.EndConnect($iar)
        $pgListening = $true
    }
    $tcp.Close()
} catch {}

if (-not $pgListening) {
    Write-Host "PostgreSQL is not listening on port 5432. Checking Docker..." -ForegroundColor Gray
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerCmd) {
        Write-Host "Starting PostgreSQL container via Docker Compose..." -ForegroundColor Gray
        docker compose up -d 2>$null
        Start-Sleep -Seconds 3
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $iar = $tcp.BeginConnect("127.0.0.1", 5432, $null, $null)
            $success = $iar.AsyncWaitHandle.WaitOne(1000)
            if ($success -and $tcp.Connected) {
                $tcp.EndConnect($iar)
                $pgListening = $true
            }
            $tcp.Close()
        } catch {}
    }
}

if ($pgListening) {
    Write-Host "[OK] PostgreSQL is active on port 5432." -ForegroundColor Green
    Write-Host "`n[2/4] Verifying database schema & seed data..." -ForegroundColor Yellow
    python scripts/setup_postgres.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARNING] Database setup returned non-zero code. Proceeding with server start..." -ForegroundColor Yellow
    }
} else {
    Write-Host "[INFO] PostgreSQL not available on port 5432. Falling back to local SQLite database (nueva_ecija_travel.db)..." -ForegroundColor Yellow
    $env:DATABASE_URL = "sqlite:///./nueva_ecija_travel.db"
    Write-Host "[OK] Using seeded SQLite database (nueva_ecija_travel.db)." -ForegroundColor Green
}

# 2. Check if FastAPI backend on port 8000 is already active
$serverAlreadyRunning = $false
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $iar = $tcp.BeginConnect("127.0.0.1", 8000, $null, $null)
    $success = $iar.AsyncWaitHandle.WaitOne(1000)
    if ($success -and $tcp.Connected) {
        $tcp.EndConnect($iar)
        $serverAlreadyRunning = $true
    }
    $tcp.Close()
} catch {}

if ($serverAlreadyRunning) {
    Write-Host "`n[+] FastAPI backend is already running on http://127.0.0.1:8000." -ForegroundColor Green
}

# 3. Locate and Launch Tunnels (ngrok and Cloudflare Tunnel)
$tunnelProcesses = @()
$ngrokUrl = $null
$cfUrl = $null
$toolsDir = Join-Path $ProjectRoot "tools"

if (-not $NoTunnel) {
    # 3a. Start ngrok tunnel
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

    if ($ngrokBin -and (Test-Path $ngrokBin)) {
        Write-Host "`n[3/4] Launching ngrok Tunnel ($ngrokDomain)..." -ForegroundColor Cyan
        $ngrokLog = Join-Path $env:TEMP "ne_ngrok.log"
        if (Test-Path $ngrokLog) { Remove-Item $ngrokLog -Force -ErrorAction SilentlyContinue }

        $ngrokProcess = Start-Process -FilePath $ngrokBin `
            -ArgumentList "http --url=https://$ngrokDomain 8000 --log=stdout" `
            -RedirectStandardOutput $ngrokLog `
            -RedirectStandardError (Join-Path $env:TEMP "ne_ngrok_err.log") `
            -PassThru -NoNewWindow
        
        $tunnelProcesses += $ngrokProcess
        $ngrokUrl = "https://$ngrokDomain"
        Write-Host "  [OK] ngrok tunnel process launched." -ForegroundColor Green
    }

    # 3b. Start Cloudflare Tunnel
    $cloudflaredBin = Join-Path $toolsDir "cloudflared.exe"
    if (-not (Test-Path $cloudflaredBin)) {
        $systemCloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
        if ($systemCloudflared) {
            $cloudflaredBin = $systemCloudflared.Source
        }
    }

    if ($cloudflaredBin -and (Test-Path $cloudflaredBin)) {
        Write-Host "Launching Cloudflare Tunnel (High-resilience fallback)..." -ForegroundColor Cyan
        $cfLog = Join-Path $env:TEMP "ne_cloudflared.log"
        if (Test-Path $cfLog) { Remove-Item $cfLog -Force -ErrorAction SilentlyContinue }

        $cfProcess = Start-Process -FilePath $cloudflaredBin `
            -ArgumentList "tunnel --url http://127.0.0.1:8000 --no-autoupdate" `
            -RedirectStandardError $cfLog `
            -PassThru -NoNewWindow

        $tunnelProcesses += $cfProcess
        Write-Host "Connecting to Cloudflare edge network..." -ForegroundColor Gray
        for ($i = 0; $i -lt 15; $i++) {
            Start-Sleep -Milliseconds 600
            if (Test-Path $cfLog) {
                $logContent = Get-Content $cfLog -Raw -ErrorAction SilentlyContinue
                if ($logContent -match '(https://[a-zA-Z0-9-]+\.trycloudflare\.com)') {
                    $cfUrl = $matches[1]
                    break
                }
            }
        }
        if ($cfUrl) {
            Write-Host "  [OK] Cloudflare Tunnel established: $cfUrl" -ForegroundColor Green
        }
    }

    Write-Host "`n+----------------------------------------------------------------------+" -ForegroundColor Green
    Write-Host "|  ONLINE CONNECTION OPTIONS FOR GITHUB PAGES & MOBILE                 |" -ForegroundColor Green
    Write-Host "+----------------------------------------------------------------------+" -ForegroundColor Green
    if ($ngrokUrl) {
        Write-Host "  1. Fixed ngrok URL:      $ngrokUrl/api/v1" -ForegroundColor Cyan
    }
    if ($cfUrl) {
        Write-Host "  2. Cloudflare Tunnel:    $cfUrl/api/v1" -ForegroundColor Cyan
    }
    Write-Host "  Live GitHub Pages:       https://edselrenz.github.io/Itinerary-App/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  HOW TO CONNECT:" -ForegroundColor Yellow
    Write-Host "  - The GitHub Pages app defaults to ngrok automatically." -ForegroundColor Gray
    Write-Host "  - If your Wi-Fi router (e.g. Tenda/PLDT) has DNS issues resolving ngrok:" -ForegroundColor Gray
    Write-Host "    A) In Chrome/Edge: Settings > Privacy > Use secure DNS > Choose 'Cloudflare'" -ForegroundColor Gray
    Write-Host "    B) Or in the App: Tap the [Settings] gear on the Offline banner and paste the" -ForegroundColor Gray
    Write-Host "       Cloudflare Tunnel URL ($cfUrl) directly!" -ForegroundColor Gray
    Write-Host "+----------------------------------------------------------------------+`n" -ForegroundColor Green
} else {
    Write-Host "`n[3/4] Tunnel disabled (-NoTunnel passed)." -ForegroundColor Gray
}

# 4. Optional: Start Ionic Frontend
if ($WithFrontend) {
    Write-Host "[+] Starting Ionic Angular Frontend..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot/Project'; npm start"
}

# 5. Start or Monitor FastAPI Backend
if (-not $serverAlreadyRunning) {
    Write-Host "[4/4] Starting FastAPI Server on http://127.0.0.1:8000 ..." -ForegroundColor Green
    Write-Host "  * Swagger UI:    http://127.0.0.1:8000/docs" -ForegroundColor Gray
    Write-Host "  * Health Check:  http://127.0.0.1:8000/api/v1/health" -ForegroundColor Gray
    Write-Host "`nPress Ctrl+C in this window to stop Server and Tunnels.`n" -ForegroundColor Yellow

    try {
        python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
    } finally {
        Write-Host "`nStopping Tunnel processes..." -ForegroundColor Gray
        foreach ($proc in $tunnelProcesses) {
            if ($proc -and -not $proc.HasExited) {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            }
        }
    }
} else {
    Write-Host "[4/4] FastAPI Server is already listening on http://127.0.0.1:8000." -ForegroundColor Green
    Write-Host "Tunnels are running. Press Ctrl+C in this window to stop tunnels.`n" -ForegroundColor Yellow

    try {
        while ($true) {
            Start-Sleep -Seconds 2
        }
    } finally {
        Write-Host "`nStopping Tunnel processes..." -ForegroundColor Gray
        foreach ($proc in $tunnelProcesses) {
            if ($proc -and -not $proc.HasExited) {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            }
        }
    }
}
