"""SQLAlchemy 2.0 database engine, declarative base, and session dependency."""

from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)
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
