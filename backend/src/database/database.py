"""
src/database/database.py
========================
SQLAlchemy 2.0 database connection layer.

Provides:
  - engine        : SQLAlchemy Engine connected to the SQLite database.
  - SessionLocal  : Session factory (call SessionLocal() to get a session).
  - Base          : Declarative base class for all ORM models.
  - get_db()      : FastAPI / dependency-injection compatible session generator.

SQLite-specific notes:
  - Foreign key enforcement is OFF by default in SQLite. We enable it on
    every new connection via the "connect" event hook (PRAGMA foreign_keys=ON).
  - check_same_thread=False is required when SQLite is used with FastAPI
    (which runs handlers in multiple threads).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import DATABASE_URL

# ─────────────────────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────────────────────

engine: Engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + FastAPI
    echo=False,                                  # Set True to log all SQL statements
)


# ─────────────────────────────────────────────────────────────
# SQLite Foreign Key Enforcement
# ─────────────────────────────────────────────────────────────
# SQLite silently ignores FK violations unless PRAGMA foreign_keys=ON
# is issued for every connection (it resets on each new connection).

@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # noqa: ANN001
    """Enable foreign key enforcement for every SQLite connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ─────────────────────────────────────────────────────────────
# Session Factory
# ─────────────────────────────────────────────────────────────

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # Prevents lazy-load errors after commit
)


# ─────────────────────────────────────────────────────────────
# Declarative Base
# ─────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """
    Shared declarative base for all ORM models.

    All model classes must inherit from this Base so that
    ``Base.metadata.create_all(engine)`` picks them up.
    """


# ─────────────────────────────────────────────────────────────
# Session Utilities
# ─────────────────────────────────────────────────────────────

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and
    guarantees the session is closed afterwards.

    Usage in a FastAPI route::

        @router.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context-manager wrapper for use outside FastAPI (scripts, tests, CLI).

    Usage::

        with get_db_context() as db:
            db.add(some_object)
            db.commit()
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def verify_foreign_keys(db: Session) -> bool:
    """
    Confirm that SQLite foreign key enforcement is active on this session.

    Returns True if foreign_keys PRAGMA is ON, False otherwise.
    """
    result = db.execute(text("PRAGMA foreign_keys")).fetchone()
    return result is not None and result[0] == 1
