"""Engine / session factory for the relational store (Layers 1 & 2)."""

from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from chatapp.config import DATABASE_URL


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""


_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    # SQLite (dev fallback) needs this to be usable from FastAPI's threadpool.
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)

if _is_sqlite:
    # SQLite ignores FK constraints unless told otherwise; Postgres enforces
    # them natively, so this only applies to the dev fallback.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_fks(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def init_db() -> None:
    """Create all tables. In production, replace with Alembic migrations."""
    # Import for side effect: registers models on Base.metadata.
    from chatapp.db import models  # noqa: F401

    Base.metadata.create_all(engine)
