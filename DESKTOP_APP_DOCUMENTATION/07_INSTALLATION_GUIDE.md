# Installation & Setup Guide: Nueva Ecija Travel Desktop Client

**Client:** Python Flet Desktop Application  
**Target OS:** Windows 10/11 (Primary), macOS, Ubuntu / Debian Linux  
**Document Ref:** `DESKTOP_APP_DOCUMENTATION/07_INSTALLATION_GUIDE.md`

---

## 1. System Requirements

### 1.1 Hardware Specifications
- **Processor:** 64-bit dual-core Intel/AMD or Apple Silicon (M1/M2/M3)
- **RAM:** Minimum 4 GB (8 GB recommended)
- **Disk Space:** ~500 MB free space (for Python runtime, Flet Flutter engine, and local storage cache)
- **Display Resolution:** Minimum 1024x720 pixels (1280x820 or higher recommended)

### 1.2 Software Prerequisites
- **Python:** 3.10, 3.11, 3.12, 3.13, or 3.14 (Tested on Python 3.14.3 64-bit)
- **Pip:** Package installer for Python (`pip --version`)
- **FastAPI Backend:** Running on `http://127.0.0.1:8000` (Docker PostgreSQL 16 or SQLite fallback)

---

## 2. Step-by-Step Installation

### Step 1: Clone or Navigate to the Repository
```powershell
# Open terminal or PowerShell
cd c:\Users\Edward\Desktop\CaseStudy

# Verify git branch is feature/flet-desktop-app
git status
```

### Step 2: Set Up Python Virtual Environment (Optional but Recommended)
```powershell
# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate on Linux/macOS
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```powershell
pip install -r desktop_client/requirements.txt
```

Verify installed core packages:
```powershell
python -c "import flet as ft, httpx; print('Flet:', ft.__version__, '| Httpx:', httpx.__version__)"
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env` in `desktop_client/`:
```powershell
cd desktop_client
copy .env.example .env
```

Ensure `API_BASE_URL` points to your backend instance:
```ini
API_BASE_URL=http://127.0.0.1:8000/api/v1
APP_TITLE=Nueva Ecija Travel — Desktop Client
APP_ENV=development
API_TIMEOUT_SECONDS=15
ITINERARY_GEN_TIMEOUT_SECONDS=45
DEBUG=False
```

### Step 5: Start the FastAPI Backend
Ensure the backend is running in a separate terminal:
```powershell
cd c:\Users\Edward\Desktop\CaseStudy\backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Verify backend health in browser or curl:
```powershell
curl http://127.0.0.1:8000/docs
```

### Step 6: Launch the Desktop Client
From the project root:
```powershell
python -m desktop_client.main
```
Or from inside the `desktop_client/` folder:
```powershell
cd desktop_client
python main.py
```

The native Flet window will initialize displaying the **Nueva Ecija Travel** desktop interface.

---

## 3. Troubleshooting & Common Issues

### Issue 1: "Cannot connect to server at http://127.0.0.1:8000"
- **Cause:** Backend server is stopped or running on a different port.
- **Fix:** Verify `uvicorn app.main:app` is running and accessible on port 8000. The desktop client status pill will show green ("Backend Online") once connection is established.

### Issue 2: Flet Desktop Window Fails to Open on Headless Environments
- **Cause:** Running in a purely headless CI/CD environment without graphical display.
- **Fix:** Flet supports web rendering for CI/CD:
  ```powershell
  python -c "import flet as ft; from desktop_client.main import main; ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550)"
  ```

### Issue 3: Git Branch or Permission Warnings on Windows
- **Cause:** Locked handles by another process.
- **Fix:** Run PowerShell with Administrator privileges or use `git checkout -f feature/flet-desktop-app`.
