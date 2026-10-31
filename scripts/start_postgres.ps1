# PowerShell helper to start PostgreSQL via Docker and run setup
Write-Host "Starting Nueva Ecija PostgreSQL via Docker..." -ForegroundColor Cyan

# Check if Docker engine is reachable
$dockerRunning = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Docker Desktop is not currently running." -ForegroundColor Yellow
    Write-Host "Starting Docker Desktop..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    Write-Host "Please wait 10-15 seconds for Docker Desktop to finish booting, then re-run this script." -ForegroundColor Yellow
    exit 1
}

# Run docker-compose
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Failed to start Docker container." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] PostgreSQL container started!" -ForegroundColor Green
Write-Host "Running migrations and seeding database..." -ForegroundColor Cyan
python scripts/setup_postgres.py

