# backend/services/memory.py

"""
Chat session memory backed by SQLite.

Why SQLite and not in-memory dict:
- Survives server restarts (student doesn't lose their session)
- Zero extra services to run locally
- Standard library — no new dependency
- Swap to Redis for production by replacing this file only;
  the interface (save_turn / get_history / clear_session) stays the same.

Security:
- History is stored server-side only, keyed by session_id (UUID)
- The client sends session_id, never raw history
- A client cannot inject or tamper with prior turns
- Sessions expire after SESSION_TTL_HOURS of inactivity
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# Sessions inactive longer than this are pruned on next startup
SESSION_TTL_HOURS = 24

# SQLite file lives next to chroma_db — one data directory
DB_PATH = Path("./session_memory.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Create the sessions table if it does not exist.
    Call this once at app startup (in main.py lifespan).
    """
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id  TEXT PRIMARY KEY,
                history     TEXT NOT NULL DEFAULT '[]',
                collection  TEXT,
                user_id     TEXT,
                updated_at  TEXT NOT NULL
            )
        """)
        # Older DBs created before these columns existed.
        existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(sessions)")}
        if "collection" not in existing_columns:
            conn.execute("ALTER TABLE sessions ADD COLUMN collection TEXT")
        if "user_id" not in existing_columns:
            conn.execute("ALTER TABLE sessions ADD COLUMN user_id TEXT")
        conn.commit()
    _prune_expired()
    logger.info("Session memory DB ready at %s", DB_PATH)


def _prune_expired() -> None:
    """Delete sessions not updated within SESSION_TTL_HOURS."""
    cutoff = (datetime.utcnow() - timedelta(hours=SESSION_TTL_HOURS)).isoformat()
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE updated_at < ?", (cutoff,))
        conn.commit()


# ── Public interface ───────────────────────────────────────────────────────

def save_turn(
    session_id: str,
    role: str,
    content: str,
    collection: str | None = None,
    user_id: str | None = None,
) -> None:
    """
    Append one turn (user or assistant) to the session history.
    Creates the session row if it does not exist.

    `collection` and `user_id` are stamped on the row so recent sessions can
    be listed with a human-readable label, scoped to their owner (see
    list_sessions()). Pass them on every call — COALESCE keeps whatever was
    already stored if omitted.
    """
    now = datetime.utcnow().isoformat()
    with _connect() as conn:
        row = conn.execute(
            "SELECT history FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()

        if row:
            history = json.loads(row["history"])
        else:
            history = []

        history.append({"role": role, "content": content})

        conn.execute("""
            INSERT INTO sessions (session_id, history, collection, user_id, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                history    = excluded.history,
                collection = COALESCE(excluded.collection, sessions.collection),
                user_id    = COALESCE(excluded.user_id, sessions.user_id),
                updated_at = excluded.updated_at
        """, (session_id, json.dumps(history), collection, user_id, now))
        conn.commit()


def get_history(session_id: str, user_id: str | None = None) -> list[dict]:
    """
    Return the full message list for a session.
    Returns an empty list if the session does not exist, or if it belongs
    to a different user_id than the one given (sessions with no owner
    stamped — e.g. pre-auth data — remain readable by anyone, matching the
    original no-auth trust model).
    """
    with _connect() as conn:
        row = conn.execute(
            "SELECT history, user_id AS owner FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
    if not row:
        return []
    if row["owner"] is not None and row["owner"] != user_id:
        return []
    return json.loads(row["history"])


def clear_session(session_id: str, user_id: str | None = None) -> None:
    """
    Delete all history for a session (e.g. user starts a new chat).
    Scoped the same way as get_history: a session with an owner stamped can
    only be cleared by that owner.
    """
    with _connect() as conn:
        conn.execute(
            "DELETE FROM sessions WHERE session_id = ? AND (user_id IS NULL OR user_id = ?)",
            (session_id, user_id),
        )
        conn.commit()


def list_sessions(limit: int = 20, user_id: str | None = None) -> list[dict]:
    """
    Return recent non-empty sessions belonging to `user_id`, most recently
    active first. Sessions with no owner stamped (pre-auth data) are
    included for everyone, same trust model as get_history/clear_session.
    Each entry has a `preview` (first user turn, truncated) so the frontend
    can render a human-readable "recent chats" list instead of raw UUIDs.
    """
    with _connect() as conn:
        rows = conn.execute("""
            SELECT session_id, collection, history, updated_at
            FROM sessions
            WHERE history != '[]' AND (user_id IS NULL OR user_id = ?)
            ORDER BY updated_at DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()

    sessions = []
    for row in rows:
        history = json.loads(row["history"])
        first_user_turn = next((t["content"] for t in history if t["role"] == "user"), "")
        preview = first_user_turn[:80] + "..." if len(first_user_turn) > 80 else first_user_turn
        sessions.append({
            "session_id": row["session_id"],
            "collection": row["collection"],
            "preview": preview,
            "turns": len(history),
            "updated_at": row["updated_at"],
        })
    return sessions
