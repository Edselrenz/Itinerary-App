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
    """Resolves relative SQLite URLs to the canonical project root database."""
    if raw_url.startswith("sqlite:///./nueva_ecija_travel.db"):
        return f"sqlite:///{ROOT_DB.as_posix()}"
    return raw_url

db_url = resolve_db_url(settings.database_url)
connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

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
