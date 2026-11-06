#!/usr/bin/env python3
"""Database initialization and verification script for PostgreSQL and SQLite.

Checks if configured database is up, runs schema setup / Alembic migrations,
verifies seed data, and outputs verification stats.

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
from app.core.database import Base
from app.models.entities import Municipality, Place, Itinerary, User


def is_sqlite() -> bool:
    return settings.database_url.startswith("sqlite")


def check_database_connection(max_retries: int = 5, retry_interval: float = 2.0) -> bool:
    """Check whether configured database is reachable at settings.database_url."""
    db_url = settings.database_url
    print(f"Connecting to database: {db_url.split('@')[-1] if '@' in db_url else db_url} ...")
    
    engine = create_engine(db_url, pool_pre_ping=True)
    check_query = text("SELECT sqlite_version();") if is_sqlite() else text("SELECT version();")
    db_type = "SQLite" if is_sqlite() else "PostgreSQL"
    
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                result = conn.execute(check_query).scalar()
                print(f"[OK] Connected to {db_type}: {result}")
                return True
        except Exception as e:
            print(f"[Attempt {attempt}/{max_retries}] Waiting for database... ({e})")
            if attempt < max_retries:
                time.sleep(retry_interval)
    return False


def run_migrations() -> bool:
    """Run alembic upgrade head for PostgreSQL or Base.metadata.create_all for SQLite."""
    print("\n--- Running Database Schema Setup / Migrations ---")
    if is_sqlite():
        engine = create_engine(settings.database_url)
        Base.metadata.create_all(bind=engine)
        print("[OK] SQLite schema verified and up to date.")
        return True

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
    """Run scripts/seed_featured_places.py if seed data is missing."""
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        try:
            place_count = conn.execute(text("SELECT count(*) FROM places;")).scalar() or 0
        except Exception:
            place_count = 0

    if place_count >= 17:
        print(f"\n--- Seed Data Check ---")
        print(f"[OK] Database already populated with {place_count} destinations.")
        return True

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
    db_type = "SQLite" if is_sqlite() else "PostgreSQL"
    print(f"\n[SUCCESS] Local {db_type} database is fully configured and ready for the backend!")


def main():
    print("=" * 60)
    db_label = "SQLite" if is_sqlite() else "PostgreSQL"
    print(f"  Nueva Ecija Travel App — {db_label} Setup")
    print("=" * 60)
    
    if not check_database_connection():
        if is_sqlite():
            print("\n[!] Could not connect to SQLite database.")
        else:
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


