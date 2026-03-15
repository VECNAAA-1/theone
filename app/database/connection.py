"""
app/database/connection.py
SQLite connection manager — thread-safe context manager approach.
All database files live in the instance/ folder at project root.
"""

import sqlite3
import os
from contextlib import contextmanager

_BASE_DIR     = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INSTANCE_DIR  = os.path.join(_BASE_DIR, "instance")
DEFAULT_DB    = os.path.join(INSTANCE_DIR, "feedbackiq.db")


def get_db_path(db_path: str = None) -> str:
    path = db_path or DEFAULT_DB
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def get_connection(db_path: str = None) -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path(db_path))
    conn.row_factory = sqlite3.Row          # access columns by name
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def db_session(db_path: str = None):
    """
    Usage:
        with db_session() as conn:
            conn.execute("SELECT ...")
    Commits on success, rolls back on exception, always closes.
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
