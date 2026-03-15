"""
app/database/repository.py
All database read/write for users and analyses.
No raw SQL anywhere outside this file.
"""

import json
import hashlib
from datetime import datetime
from typing import Optional
from app.database.connection import db_session


# ── User Repository ───────────────────────────────────────────────────────────

class UserRepository:
    def __init__(self, db_path=None):
        self.db_path = db_path

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def get_by_id(self, user_id: int) -> Optional[dict]:
        with db_session(self.db_path) as conn:
            row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    def get_by_username(self, username: str) -> Optional[dict]:
        with db_session(self.db_path) as conn:
            row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        return dict(row) if row else None

    def verify_password(self, username: str, password: str) -> Optional[dict]:
        """Return user dict if credentials match, else None."""
        user = self.get_by_username(username)
        if user and user["password_hash"] == self._hash(password):
            return user
        return None

    def update_last_login(self, user_id: int) -> None:
        with db_session(self.db_path) as conn:
            conn.execute(
                "UPDATE users SET last_login=? WHERE id=?",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id)
            )

    def get_all(self) -> list:
        with db_session(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id,username,role,full_name,created_at,last_login FROM users ORDER BY id"
            ).fetchall()
        return [dict(r) for r in rows]

    def create(self, username: str, password: str, role: str = "analyst", full_name: str = "") -> int:
        with db_session(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO users (username,password_hash,role,full_name) VALUES (?,?,?,?)",
                (username, self._hash(password), role, full_name)
            )
        return cur.lastrowid

    def change_password(self, user_id: int, new_password: str) -> None:
        with db_session(self.db_path) as conn:
            conn.execute("UPDATE users SET password_hash=? WHERE id=?",
                         (self._hash(new_password), user_id))

    def update_full_name(self, user_id: int, full_name: str) -> None:
        with db_session(self.db_path) as conn:
            conn.execute("UPDATE users SET full_name=? WHERE id=?", (full_name, user_id))

    def delete(self, user_id: int) -> bool:
        with db_session(self.db_path) as conn:
            cur = conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        return cur.rowcount > 0


# ── Analysis Repository ───────────────────────────────────────────────────────

class AnalysisRepository:
    def __init__(self, db_path=None):
        self.db_path = db_path

    def save(self, result: dict, user_id: int = None) -> int:
        """
        Persist a full analysis result.
        result dict must have keys: sentiments, themes, insights, total_feedback, source, filename
        Returns the new analysis id.
        """
        sentiments = result.get("sentiments", {})
        themes     = result.get("themes", {})
        insights   = result.get("insights", {})

        counts   = sentiments.get("counts", {})
        keywords = [kw["word"] for kw in themes.get("top_keywords", [])[:10]]

        with db_session(self.db_path) as conn:
            cur = conn.execute(
                """INSERT INTO analyses
                   (source, filename, total, pos_count, neg_count, neu_count,
                    avg_polarity, top_keywords, summary, created_by, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    result.get("source", "text"),
                    result.get("filename"),
                    result.get("total_feedback", 0),
                    counts.get("Positive", 0),
                    counts.get("Negative", 0),
                    counts.get("Neutral", 0),
                    sentiments.get("average_polarity", 0.0),
                    json.dumps(keywords),
                    insights.get("summary", ""),
                    user_id,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
            )
            analysis_id = cur.lastrowid

            # Save individual items
            items = sentiments.get("items", [])
            conn.executemany(
                "INSERT INTO feedback_items (analysis_id, text, label, polarity, subjectivity) VALUES (?,?,?,?,?)",
                [
                    (analysis_id, item["text"], item["label"],
                     item["polarity"], item["subjectivity"])
                    for item in items
                ]
            )

            self._log(conn, "INSERT", analysis_id, user_id,
                      f"Saved analysis: {result.get('total_feedback',0)} items")

        return analysis_id

    def get_all(self, user_id: int = None, limit: int = 100) -> list:
        """Return analyses — admin sees all, analyst sees own only."""
        with db_session(self.db_path) as conn:
            if user_id is None:
                rows = conn.execute(
                    """SELECT a.*, u.username FROM analyses a
                       LEFT JOIN users u ON u.id = a.created_by
                       ORDER BY a.created_at DESC LIMIT ?""", (limit,)
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT a.*, u.username FROM analyses a
                       LEFT JOIN users u ON u.id = a.created_by
                       WHERE a.created_by = ?
                       ORDER BY a.created_at DESC LIMIT ?""", (user_id, limit)
                ).fetchall()
        return [dict(r) for r in rows]

    def get_by_id(self, analysis_id: int) -> Optional[dict]:
        with db_session(self.db_path) as conn:
            row = conn.execute("SELECT * FROM analyses WHERE id=?", (analysis_id,)).fetchone()
            if not row:
                return None
            result = dict(row)
            result["top_keywords"] = json.loads(result["top_keywords"] or "[]")
            items = conn.execute(
                "SELECT * FROM feedback_items WHERE analysis_id=?", (analysis_id,)
            ).fetchall()
            result["items"] = [dict(i) for i in items]
        return result

    def delete(self, analysis_id: int, user_id: int = None) -> bool:
        with db_session(self.db_path) as conn:
            cur = conn.execute("DELETE FROM analyses WHERE id=?", (analysis_id,))
            if cur.rowcount:
                self._log(conn, "DELETE", analysis_id, user_id, "Deleted analysis")
        return cur.rowcount > 0

    def get_stats(self, user_id: int = None) -> dict:
        with db_session(self.db_path) as conn:
            if user_id is None:
                total = conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
                pos   = conn.execute("SELECT SUM(pos_count) FROM analyses").fetchone()[0] or 0
                neg   = conn.execute("SELECT SUM(neg_count) FROM analyses").fetchone()[0] or 0
                neu   = conn.execute("SELECT SUM(neu_count) FROM analyses").fetchone()[0] or 0
                items = conn.execute("SELECT COUNT(*) FROM feedback_items").fetchone()[0]
            else:
                total = conn.execute("SELECT COUNT(*) FROM analyses WHERE created_by=?", (user_id,)).fetchone()[0]
                pos   = conn.execute("SELECT SUM(pos_count) FROM analyses WHERE created_by=?", (user_id,)).fetchone()[0] or 0
                neg   = conn.execute("SELECT SUM(neg_count) FROM analyses WHERE created_by=?", (user_id,)).fetchone()[0] or 0
                neu   = conn.execute("SELECT SUM(neu_count) FROM analyses WHERE created_by=?", (user_id,)).fetchone()[0] or 0
                items = conn.execute(
                    "SELECT COUNT(*) FROM feedback_items fi JOIN analyses a ON a.id=fi.analysis_id WHERE a.created_by=?",
                    (user_id,)
                ).fetchone()[0]
        return {"total_analyses": total, "total_items": items,
                "total_positive": pos, "total_negative": neg, "total_neutral": neu}

    def get_audit_log(self, limit: int = 50, user_id: int = None) -> list:
        with db_session(self.db_path) as conn:
            if user_id is not None:
                rows = conn.execute(
                    """SELECT al.*, u.username FROM audit_log al
                       LEFT JOIN users u ON u.id = al.user_id
                       WHERE al.user_id = ?
                       ORDER BY al.created_at DESC LIMIT ?""",
                    (user_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT al.*, u.username FROM audit_log al
                       LEFT JOIN users u ON u.id = al.user_id
                       ORDER BY al.created_at DESC LIMIT ?""",
                    (limit,)
                ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def _log(conn, action, analysis_id, user_id, details):
        conn.execute(
            "INSERT INTO audit_log (action, analysis_id, user_id, details) VALUES (?,?,?,?)",
            (action, analysis_id, user_id, details)
        )
