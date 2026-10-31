"""Automated test for database backup, verification, and disaster-recovery drill."""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"
for d in [str(ROOT_DIR), str(BACKEND_DIR), str(SCRIPTS_DIR)]:
    if d not in sys.path:
        sys.path.insert(0, d)

from app.core.database import Base
from db_backup_restore import create_backup, run_drill, verify_backup


def test_backup_restore_drill(tmp_path: Path):
    """Executes a full, isolated backup-and-restore drill against a temporary database."""
    test_db_file = tmp_path / "test_drill.sqlite"
    test_db_url = f"sqlite:///{test_db_file.as_posix()}"

    # Initialize tables
    engine = create_engine(test_db_url)
    Base.metadata.create_all(bind=engine)
    engine.dispose()

    # Execute automated drill
    drill_dir = tmp_path / "drills"
    success = run_drill(db_url=test_db_url, drill_dir=drill_dir)
    assert success is True

    # Check that a backup file was generated and verified
    drill_files = list(drill_dir.glob("*.sql"))
    assert len(drill_files) >= 1

    verification = verify_backup(drill_files[0])
    assert verification["valid"] is True
    assert verification["file_size_bytes"] > 0
