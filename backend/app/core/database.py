"""SQLAlchemy 2.0 database engine, declarative base, and session dependency."""

from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.core.config import settings

"""SQLAlchemy 2.0 database engine, declarative base, and session dependency."""

import logging
from collections.abc import Generator
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.core.config import settings

logger = logging.getLogger(__name__)

ROOT_DB = Path(__file__).resolve().parents[3] / "nueva_ecija_travel.db"

def resolve_db_url(raw_url: str) -> str:
    """Resolves relative SQLite URLs and enforces short connect timeouts for unreachable Postgres."""
    if raw_url.startswith("sqlite:///./nueva_ecija_travel.db"):
        return f"sqlite:///{ROOT_DB.as_posix()}"
    if raw_url.startswith("postgresql") and "connect_timeout" not in raw_url:
        separator = "&" if "?" in raw_url else "?"
        return f"{raw_url}{separator}connect_timeout=2"
    return raw_url

db_url = resolve_db_url(settings.database_url)
connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {"connect_timeout": 2}

try:
    engine = create_engine(db_url, pool_pre_ping=True, connect_args=connect_args)
    if not db_url.startswith("sqlite"):
        with engine.connect() as test_conn:
            pass
except Exception as exc:
    logger.warning(
        "Configured database '%s' connection failed (%s). Falling back to canonical SQLite at %s",
        db_url,
        exc,
        ROOT_DB,
    )
    fallback_url = f"sqlite:///{ROOT_DB.as_posix()}"
    engine = create_engine(fallback_url, pool_pre_ping=True, connect_args={"check_same_thread": False})


def ensure_user_profile_columns(target_engine) -> None:
    """Ensures extended user profile columns exist across both PostgreSQL and SQLite."""
    try:
        from sqlalchemy import inspect, text
        insp = inspect(target_engine)
        if not insp.has_table("users"):
            return
        existing_cols = {c["name"] for c in insp.get_columns("users")}
        cols_to_add = [
            ("middle_initial", "VARCHAR(16)"),
            ("phone_number", "VARCHAR(40)"),
            ("birthday", "VARCHAR(40)"),
            ("gender", "VARCHAR(32)"),
            ("avatar_url", "TEXT"),
            ("default_daily_budget", "NUMERIC(10, 2) DEFAULT 3000.0"),
        ]
        with target_engine.begin() as conn:
            for col_name, col_type in cols_to_add:
                if col_name not in existing_cols:
                    if target_engine.dialect.name == "postgresql":
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                    else:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};"))
            # Backfill NULL profile metadata on existing accounts so login loads complete profile & avatar from DB
            conn.execute(
                text(
                    "UPDATE users SET "
                    "middle_initial = COALESCE(NULLIF(middle_initial, ''), 'N/A'), "
                    "birthday = COALESCE(NULLIF(birthday, ''), 'May 23, 2000'), "
                    "gender = COALESCE(NULLIF(gender, ''), 'Female'), "
                    "phone_number = COALESCE(NULLIF(phone_number, ''), '+66 81 234 5678'), "
                    "avatar_url = COALESCE(NULLIF(avatar_url, ''), 'assets/images/pattranite_avatar.jpg'), "
                    "default_daily_budget = COALESCE(default_daily_budget, 3000.0);"
                )
            )
    except Exception as e:
        logger.warning("Auto-migration check for user profile columns skipped/failed: %s", e)


ensure_user_profile_columns(engine)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy ORM models."""


def get_db() -> Generator[Session, None, None]:
    """Yields a database session per request and ensures deterministic closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
