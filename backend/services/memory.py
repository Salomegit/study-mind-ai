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
                updated_at  TEXT NOT NULL
            )
        """)
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

def save_turn(session_id: str, role: str, content: str) -> None:
    """
    Append one turn (user or assistant) to the session history.
    Creates the session row if it does not exist.
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
            INSERT INTO sessions (session_id, history, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                history    = excluded.history,
                updated_at = excluded.updated_at
        """, (session_id, json.dumps(history), now))
        conn.commit()


def get_history(session_id: str) -> list[dict]:
    """
    Return the full message list for a session.
    Returns an empty list if the session does not exist.
    """
    with _connect() as conn:
        row = conn.execute(
            "SELECT history FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
    if not row:
        return []
    return json.loads(row["history"])


def clear_session(session_id: str) -> None:
    """Delete all history for a session (e.g. user starts a new chat)."""
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
