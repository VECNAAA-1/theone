"""
app/database/schema.py
Tables:
    users        — login accounts (username, password hash, role)
    analyses     — each feedback analysis session
    feedback_items — individual feedback rows per session
    audit_log    — every write operation logged

Run standalone:  python app/database/schema.py
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from app.database.connection import db_session, get_db_path

CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'analyst',  -- 'admin' | 'analyst'
    full_name     TEXT    NOT NULL DEFAULT '',
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login    TIMESTAMP
);
"""

CREATE_ANALYSES = """
CREATE TABLE IF NOT EXISTS analyses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    source       TEXT    NOT NULL DEFAULT 'text',   -- 'text' | 'file'
    filename     TEXT,
    total        INTEGER NOT NULL DEFAULT 0,
    pos_count    INTEGER NOT NULL DEFAULT 0,
    neg_count    INTEGER NOT NULL DEFAULT 0,
    neu_count    INTEGER NOT NULL DEFAULT 0,
    avg_polarity REAL    NOT NULL DEFAULT 0.0,
    top_keywords TEXT    NOT NULL DEFAULT '[]',     -- JSON
    summary      TEXT    NOT NULL DEFAULT '',
    created_by   INTEGER,                           -- FK → users.id
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
"""

CREATE_FEEDBACK_ITEMS = """
CREATE TABLE IF NOT EXISTS feedback_items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id  INTEGER NOT NULL,
    text         TEXT    NOT NULL,
    label        TEXT    NOT NULL,    -- Positive | Negative | Neutral
    polarity     REAL    NOT NULL DEFAULT 0.0,
    subjectivity REAL    NOT NULL DEFAULT 0.0,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);
"""

CREATE_AUDIT_LOG = """
CREATE TABLE IF NOT EXISTS audit_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    action     TEXT    NOT NULL,
    analysis_id INTEGER,
    user_id    INTEGER,
    details    TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_users_username    ON users(username);",
    "CREATE INDEX IF NOT EXISTS idx_analyses_user     ON analyses(created_by);",
    "CREATE INDEX IF NOT EXISTS idx_analyses_date     ON analyses(created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_items_analysis    ON feedback_items(analysis_id);",
    "CREATE INDEX IF NOT EXISTS idx_items_label       ON feedback_items(label);",
    "CREATE INDEX IF NOT EXISTS idx_audit_date        ON audit_log(created_at DESC);",
]

ALL_DDL = [CREATE_USERS, CREATE_ANALYSES, CREATE_FEEDBACK_ITEMS, CREATE_AUDIT_LOG] + CREATE_INDEXES


def init_db(db_path: str = None) -> None:
    """Create all tables/indexes (idempotent — safe to call on every startup)."""
    with db_session(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        for stmt in ALL_DDL:
            conn.execute(stmt)
        _seed_default_users(conn)
    print(f"[DB] Schema ready: {get_db_path(db_path)}")


def _seed_default_users(conn) -> None:
    """Insert default admin + analyst accounts if users table is empty."""
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        import hashlib
        def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()
        conn.executemany(
            "INSERT INTO users (username, password_hash, role, full_name) VALUES (?,?,?,?)",
            [
                ("admin",    _hash("admin123"),    "admin",    "System Administrator"),
                ("analyst1", _hash("analyst123"),  "analyst",  "Analyst One"),
                ("analyst2", _hash("analyst456"),  "analyst",  "Analyst Two"),
            ]
        )
        print("[DB] Default users seeded  (admin/admin123 · analyst1/analyst123 · analyst2/analyst456)")


def get_schema_info(db_path: str = None) -> list:
    with db_session(db_path) as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        return [
            {"table": r["name"],
             "columns": [dict(c) for c in conn.execute(f"PRAGMA table_info({r['name']})").fetchall()]}
            for r in tables
        ]


if __name__ == "__main__":
    init_db()
    print([t["table"] for t in get_schema_info()])
