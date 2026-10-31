# ==============================================================================
# Nueva Ecija Travel App - Server & Database Shutdown Script
# ==============================================================================
param (
    [switch]$KeepDatabase = $false
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  Nueva Ecija Travel App - Server Shutdown Tool             " -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta

function Stop-ProcessOnPort {
    param ([int]$Port, [string]$ServiceName)
    Write-Host "Checking for $ServiceName on port $Port..." -ForegroundColor Gray
    $found = $false
    try {
        $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($conns) {
            $procIds = $conns | Select-Object -ExpandProperty OwningProcess -Unique
            foreach ($p in $procIds) {
                if ($p -gt 0) {
                    $pName = (Get-Process -Id $p -ErrorAction SilentlyContinue).ProcessName
                    Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
                    Write-Host "[OK] Stopped $ServiceName (PID: $p, Name: $pName) on port $Port." -ForegroundColor Green
                    $found = $true
                }
            }
        }
    } catch {
        # Fallback using netstat
        $lines = netstat -ano | Select-String ":$Port\s"
        foreach ($line in $lines) {
            $parts = ($line -replace '\s+', ' ').Trim().Split(' ')
            $pidToKill = $parts[-1]
            if ($pidToKill -match '^\d+$' -and [int]$pidToKill -gt 0) {
                Stop-Process -Id [int]$pidToKill -Force -ErrorAction SilentlyContinue
                Write-Host "[OK] Stopped $ServiceName (PID: $pidToKill) on port $Port." -ForegroundColor Green
                $found = $true
            }
        }
    }
    if (-not $found) {
        Write-Host "No active service found on port $Port." -ForegroundColor DarkGray
    }
}

# 1. Terminate Cloudflare Tunnel processes
Write-Host "`n[1/4] Stopping Cloudflare Tunnel..." -ForegroundColor Yellow
$cloudflaredProcs = Get-Process -Name "*cloudflared*" -ErrorAction SilentlyContinue
if ($cloudflaredProcs) {
    foreach ($proc in $cloudflaredProcs) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] Stopped Cloudflare Tunnel process (PID: $($proc.Id))." -ForegroundColor Green
    }
} else {
    Write-Host "No active Cloudflare Tunnel processes found." -ForegroundColor DarkGray
}

# Clean up temporary tunnel log
$tunnelLog = Join-Path $env:TEMP "ne_cloudflared.log"
if (Test-Path $tunnelLog) {
    Remove-Item $tunnelLog -Force -ErrorAction SilentlyContinue
}

# 2. Stop FastAPI Backend (Port 8000)
Write-Host "`n[2/4] Stopping FastAPI Backend Server..." -ForegroundColor Yellow
Stop-ProcessOnPort -Port 8000 -ServiceName "FastAPI Backend"

# 3. Stop Frontend Dev Servers (Port 4200 / 8100) if running
Write-Host "`n[3/4] Stopping Frontend Dev Servers..." -ForegroundColor Yellow
Stop-ProcessOnPort -Port 4200 -ServiceName "Angular Dev Server"
Stop-ProcessOnPort -Port 8100 -ServiceName "Ionic Dev Server"

# 4. Stop PostgreSQL Container (Docker)
Write-Host "`n[4/4] Checking PostgreSQL Docker Container..." -ForegroundColor Yellow
if ($KeepDatabase) {
    Write-Host "Skipping database shutdown (-KeepDatabase specified)." -ForegroundColor DarkGray
} else {
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerCmd) {
        Write-Host "Stopping PostgreSQL container..." -ForegroundColor Gray
        & docker compose stop *>$null
        & docker stop ne_postgres *>$null
        Write-Host "[OK] PostgreSQL container stopped." -ForegroundColor Green
    } else {
        Write-Host "Docker not in PATH; skipping Docker container stop." -ForegroundColor DarkGray
    }
}

Write-Host "`n============================================================" -ForegroundColor Magenta
Write-Host "  All servers and tunnels have been successfully stopped.   " -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Magenta
