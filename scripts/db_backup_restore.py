"""Database Backup & Restore Drill Utility for the Nueva Ecija Travel Itinerary.

Supports PostgreSQL (via pg_dump/psql) and SQLite (via online backup/iterdump)
for local development, CI automated testing, and pilot deployments.
"""

from __future__ import annotations

import argparse
import datetime
import os
import shutil
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse

# Ensure repository root and backend are in path
ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
for p in [str(ROOT_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.core.config import settings
from app.models.entities import Municipality, Place, User
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_BACKUP_DIR = ROOT_DIR / "backups"


def is_sqlite_binary_file(path: Path) -> bool:
    """Checks whether a file begins with the SQLite format 3 magic header."""
    try:
        with open(path, "rb") as f:
            return f.read(16).startswith(b"SQLite format 3")
    except Exception:
        return False


def parse_db_url(db_url: str) -> dict[str, str | int]:
    """Parses database connection URL into distinct components."""
    clean_url = db_url
    if "+psycopg" in clean_url:
        clean_url = clean_url.replace("+psycopg", "")

    parsed = urlparse(clean_url)
    return {
        "scheme": parsed.scheme,
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 5432,
        "dbname": parsed.path.lstrip("/"),
    }


def create_backup(target_path: Path | None = None, db_url: str | None = None) -> Path:
    """Creates a database backup snapshot and returns the path to the backup file."""
    url = db_url or settings.database_url
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")

    if target_path is None:
        DEFAULT_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        ext = "sqlite" if "sqlite" in url else "sql"
        target_path = DEFAULT_BACKUP_DIR / f"ne_backup_{timestamp}.{ext}"
    else:
        target_path.parent.mkdir(parents=True, exist_ok=True)

    if url.startswith("sqlite"):
        db_file = url.replace("sqlite:///", "")
        if target_path.suffix == ".sql":
            # Generate plain text SQL dump
            conn = sqlite3.connect(db_file)
            with open(target_path, "w", encoding="utf-8") as f:
                for line in conn.iterdump():
                    f.write(f"{line}\n")
            conn.close()
        else:
            # Binary SQLite online backup
            src = sqlite3.connect(db_file)
            dst = sqlite3.connect(str(target_path))
            with dst:
                src.backup(dst)
            src.close()
            dst.close()
    else:
        # PostgreSQL database backup via pg_dump
        info = parse_db_url(url)
        cmd = [
            "pg_dump",
            "-h",
            str(info["host"]),
            "-p",
            str(info["port"]),
            "-U",
            str(info["user"]),
            "-F",
            "p",  # plain SQL format
            "-b",
            "-v",
            "-f",
            str(target_path),
            str(info["dbname"]),
        ]
        env = os.environ.copy()
        if info["password"]:
            env["PGPASSWORD"] = str(info["password"])

        if not shutil.which("pg_dump"):
            raise RuntimeError(
                "pg_dump binary is not found in system PATH. Please ensure PostgreSQL client tools are installed."
            )

        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"pg_dump failed (exit code {result.returncode}): {result.stderr}")

    return target_path


def verify_backup(backup_path: Path) -> dict[str, str | int | bool]:
    """Verifies that a backup file exists, is non-empty, and contains expected database entities."""
    if not backup_path.exists():
        return {"valid": False, "error": f"Backup file not found: {backup_path}"}

    file_size = backup_path.stat().st_size
    if file_size == 0:
        return {"valid": False, "error": "Backup file is empty (0 bytes)"}

    # Binary SQLite file
    if is_sqlite_binary_file(backup_path):
        try:
            conn = sqlite3.connect(str(backup_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()

            required = ["municipalities", "places", "users"]
            missing = [t for t in required if t not in tables]
            if missing:
                return {
                    "valid": False,
                    "error": f"Missing critical tables in backup: {missing}",
                    "tables_found": tables,
                }
            return {
                "valid": True,
                "file_size_bytes": file_size,
                "tables_found": tables,
                "type": "sqlite_binary",
            }
        except Exception as e:
            return {"valid": False, "error": f"Corrupt SQLite backup: {e}"}

    # Plain text SQL dump
    try:
        with open(backup_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(50000)

        required_keywords = ["CREATE TABLE", "users"]
        missing = [k for k in required_keywords if k not in content]
        if missing:
            return {
                "valid": False,
                "error": f"SQL dump missing expected keywords: {missing}",
            }

        return {
            "valid": True,
            "file_size_bytes": file_size,
            "type": "sql_text",
        }
    except Exception as e:
        return {"valid": False, "error": f"Unable to read SQL dump: {e}"}


def restore_backup(backup_path: Path, db_url: str | None = None) -> bool:
    """Restores a database snapshot from a backup file."""
    url = db_url or settings.database_url
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    if url.startswith("sqlite"):
        db_file = url.replace("sqlite:///", "")
        if is_sqlite_binary_file(backup_path):
            if db_file != ":memory:":
                shutil.copy2(backup_path, db_file)
            else:
                raise ValueError("Cannot restore file-based backup directly into :memory: SQLite URL")
        else:
            with open(backup_path, "r", encoding="utf-8", errors="ignore") as f:
                sql_script = f.read()
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF;")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall()]
            for t in tables:
                cursor.execute(f'DROP TABLE IF EXISTS "{t}";')
            conn.commit()
            conn.executescript(sql_script)
            conn.commit()
            conn.close()
        return True
    else:
        info = parse_db_url(url)
        cmd = [
            "psql",
            "-h",
            str(info["host"]),
            "-p",
            str(info["port"]),
            "-U",
            str(info["user"]),
            "-d",
            str(info["dbname"]),
            "-f",
            str(backup_path),
        ]
        env = os.environ.copy()
        if info["password"]:
            env["PGPASSWORD"] = str(info["password"])

        if not shutil.which("psql"):
            raise RuntimeError(
                "psql binary is not found in system PATH. Please ensure PostgreSQL client tools are installed."
            )

        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"psql restore failed (exit code {result.returncode}): {result.stderr}")
        return True


def run_drill(db_url: str | None = None, drill_dir: Path | None = None) -> bool:
    """Executes a full, automated backup-and-restore drill:
    1. Seeds a canary record into the active database.
    2. Takes a backup snapshot.
    3. Verifies the backup snapshot integrity.
    4. Mutates/deletes the canary record to simulate data loss.
    5. Restores database from backup snapshot.
    6. Confirms that canary record is faithfully restored.
    7. Cleans up canary and reports success.
    """
    url = db_url or settings.database_url
    drill_folder = drill_dir or (DEFAULT_BACKUP_DIR / "drills")
    drill_folder.mkdir(parents=True, exist_ok=True)

    canary_id = uuid.uuid4()
    canary_username = f"canary_drill_{canary_id.hex[:8]}"
    canary_email = f"{canary_username}@drill.local"

    print("==================================================")
    print("STARTING DATABASE BACKUP & RESTORE DRILL")
    print(f"Target Database URL: {url.split('@')[-1] if '@' in url else url}")
    print("==================================================")

    engine = create_engine(url)
    Session = sessionmaker(bind=engine)

    # Step 1: Create Canary
    print("\n[Step 1/6] Seeding canary user record into database...")
    with Session() as session:
        canary_user = User(
            id=canary_id,
            first_name="Canary",
            last_name="Drill",
            username_normalized=canary_username.lower(),
            email_normalized=canary_email.lower(),
            password_hash="argon2id$drill_hash",
            is_active=True,
        )
        session.add(canary_user)
        session.commit()
    print(f"Canary record seeded: {canary_username} (ID: {canary_id})")

    # Step 2: Create Backup
    print("\n[Step 2/6] Generating backup snapshot...")
    snapshot_path = drill_folder / f"drill_snapshot_{canary_id.hex[:8]}.sql"
    snapshot_file = create_backup(target_path=snapshot_path, db_url=url)
    print(f"Backup snapshot generated: {snapshot_file} ({snapshot_file.stat().st_size} bytes)")

    # Step 3: Verify Backup
    print("\n[Step 3/6] Verifying snapshot integrity...")
    verification = verify_backup(snapshot_file)
    if not verification.get("valid"):
        raise RuntimeError(f"Backup verification failed: {verification.get('error')}")
    print(f"Snapshot verified: valid={verification['valid']}, size={verification.get('file_size_bytes')} bytes")

    # Step 4: Simulate Catastrophic Data Loss
    print("\n[Step 4/6] Simulating data loss (deleting canary record)...")
    with Session() as session:
        user_to_delete = session.scalar(select(User).where(User.id == canary_id))
        if user_to_delete:
            session.delete(user_to_delete)
            session.commit()

    # Confirm deletion
    with Session() as session:
        lost_user = session.scalar(select(User).where(User.id == canary_id))
        if lost_user is not None:
            raise RuntimeError("Failed to simulate data loss: canary record still exists.")
    print("Data loss simulated: Canary record successfully eliminated from database.")

    # Dispose engine connection pool before restoring database file
    engine.dispose()

    # Step 5: Restore from Backup
    print("\n[Step 5/6] Restoring database from snapshot...")
    restore_backup(snapshot_file, db_url=url)
    print("Restore operation completed.")

    # Reconnect fresh engine
    engine = create_engine(url)
    Session = sessionmaker(bind=engine)

    # Step 6: Verify Canary Restoration
    print("\n[Step 6/6] Verifying canary restoration...")
    with Session() as session:
        restored_user = session.scalar(select(User).where(User.id == canary_id))
        if restored_user is None:
            raise RuntimeError("Drill failed: Canary user record was NOT restored from snapshot!")
        print(f"Canary record successfully verified: {restored_user.username_normalized} (ID: {restored_user.id})")

        # Cleanup canary
        session.delete(restored_user)
        session.commit()
        print("Canary cleanup completed.")

    engine.dispose()

    print("\n==================================================")
    print("DATABASE BACKUP & RESTORE DRILL COMPLETED: SUCCESS (100%)")
    print("==================================================")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Nueva Ecija Itinerary Database Backup & Restore Utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup_parser = subparsers.add_parser("backup", help="Create a database backup snapshot")
    backup_parser.add_argument("--output", "-o", type=Path, help="Target backup file path")
    backup_parser.add_argument("--db-url", type=str, help="Database connection URL")

    verify_parser = subparsers.add_parser("verify", help="Verify integrity of an existing backup file")
    verify_parser.add_argument("file", type=Path, help="Path to the backup file to inspect")

    restore_parser = subparsers.add_parser("restore", help="Restore database from a backup file")
    restore_parser.add_argument("file", type=Path, help="Path to the backup file to restore")
    restore_parser.add_argument("--db-url", type=str, help="Database connection URL")

    drill_parser = subparsers.add_parser("drill", help="Execute an automated backup and restore drill")
    drill_parser.add_argument("--db-url", type=str, help="Database connection URL")

    args = parser.parse_args()

    if args.command == "backup":
        path = create_backup(target_path=args.output, db_url=args.db_url)
        print(f"Backup created successfully: {path}")
    elif args.command == "verify":
        res = verify_backup(args.file)
        print(f"Verification result: {res}")
        if not res.get("valid"):
            sys.exit(1)
    elif args.command == "restore":
        restore_backup(args.file, db_url=args.db_url)
        print(f"Restore from {args.file} completed successfully.")
    elif args.command == "drill":
        success = run_drill(db_url=args.db_url)
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
