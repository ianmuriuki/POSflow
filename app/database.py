"""
app/database.py
---------------
Creates the SQLAlchemy engine and session factory.
All database access in the app goes through get_session().

Usage:
    from app.database import get_session

    with get_session() as session:
        session.add(some_model)
        session.commit()
"""

import os
import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from app.config import CONFIG

logger = logging.getLogger(__name__)

# ── Resolve DB path ─────────────────────────────────────────────
_DB_PATH = os.path.abspath(CONFIG.get("db_path", "posflow.db"))
_DB_URL  = f"sqlite:///{_DB_PATH}"

# ── Engine ──────────────────────────────────────────────────────
engine = create_engine(
    _DB_URL,
    echo=False,           # Set True to print raw SQL (debugging only)
    connect_args={"check_same_thread": False},  # Required for SQLite + threads
)

# Enable WAL mode for better concurrent read performance
@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, _connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")  # Enforce FK constraints
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.close()

# ── Session factory ─────────────────────────────────────────────
_SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@contextmanager
def get_session() -> Session:
    """
    Context manager that provides a database session.
    Automatically commits on success and rolls back on any exception.

    Example:
        with get_session() as session:
            product = session.get(Product, product_id)
    """
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_path() -> str:
    """Return the absolute path to the database file."""
    return _DB_PATH
