#!/usr/bin/env python3
"""PostgreSQL local database initialization and verification script.

Checks if local PostgreSQL is up, runs Alembic migrations, seeds
all curated Nueva Ecija places, and outputs verification stats.

Usage:
    python scripts/setup_postgres.py
"""

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, select, text
from app.core.config import settings
from app.models.entities import Municipality, Place, Itinerary, User


def check_postgres_connection(max_retries: int = 5, retry_interval: float = 2.0) -> bool:
    """Check whether PostgreSQL is reachable at settings.database_url."""
    db_url = settings.database_url
    print(f"Connecting to database: {db_url.split('@')[-1] if '@' in db_url else db_url} ...")
    
    # Try connecting to the target database first
    engine = create_engine(db_url, pool_pre_ping=True)
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version();")).scalar()
                print(f"[OK] Connected to PostgreSQL: {result}")
                return True
        except Exception as e:
            print(f"[Attempt {attempt}/{max_retries}] Waiting for database... ({e})")
            if attempt < max_retries:
                time.sleep(retry_interval)
    return False


def run_migrations() -> bool:
    """Run alembic upgrade head."""
    print("\n--- Running Alembic Migrations ---")
    res = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(BACKEND_DIR),
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        print("[ERROR] Alembic migration failed:")
        print(res.stderr)
        return False
    print(res.stdout.strip() if res.stdout else "[OK] Migrations up to date.")
    return True


def run_seed() -> bool:
    """Run scripts/seed_featured_places.py."""
    print("\n--- Seeding Municipalities & Featured Places ---")
    seed_script = ROOT_DIR / "scripts" / "seed_featured_places.py"
    res = subprocess.run(
        [sys.executable, str(seed_script)],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        print("[ERROR] Seeding failed:")
        print(res.stderr)
        return False
    print(res.stdout.strip())
    return True


def verify_database():
    """Verify record counts across tables."""
    print("\n--- Database Health & Verification Summary ---")
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        mun_count = conn.execute(text("SELECT count(*) FROM municipalities;")).scalar()
        place_count = conn.execute(text("SELECT count(*) FROM places;")).scalar()
        user_count = conn.execute(text("SELECT count(*) FROM users;")).scalar()
        itin_count = conn.execute(text("SELECT count(*) FROM itineraries;")).scalar()
        
        print(f"  * Municipalities: {mun_count}")
        print(f"  * Places:         {place_count}")
        print(f"  * Users:          {user_count}")
        print(f"  * Itineraries:    {itin_count}")
    print("\n[SUCCESS] Local PostgreSQL is fully configured and ready for the backend!")


def main():
    print("=" * 60)
    print("  Nueva Ecija Travel App — PostgreSQL Setup")
    print("=" * 60)
    
    if not check_postgres_connection():
        print("\n[!] Could not connect to PostgreSQL on 127.0.0.1:5432.")
        print("\nPlease make sure PostgreSQL is running on your machine.")
        print("Option 1 (Docker): Run 'docker compose up -d' in the project directory.")
        print("Option 2 (Native Windows Service): Ensure PostgreSQL service is started.")
        sys.exit(1)
        
    if not run_migrations():
        sys.exit(1)
        
    if not run_seed():
        sys.exit(1)
        
    verify_database()


if __name__ == "__main__":
    main()

