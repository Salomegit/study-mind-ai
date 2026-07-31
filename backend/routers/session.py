# backend/routers/session.py

"""
Session memory endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from services import memory as session_memory
from services.auth import require_user_id

router = APIRouter()


@router.get("/sessions")
def list_recent_sessions(limit: int = 20, user_id: str = Depends(require_user_id)):
    """
    Return the caller's recent chat sessions (most recently active first) so
    the frontend can render a "recent chats" list. Each entry includes the
    collection name and a short preview instead of a bare session_id.

    Requires auth — this lists chat content, so it's scoped to the Clerk
    user_id embedded in the caller's token. Sessions with no owner stamped
    (created before this was added) are visible to anyone, same as before.
    """
    return {"sessions": session_memory.list_sessions(limit=limit, user_id=user_id)}


@router.delete("/session/{session_id}")
def clear_session(session_id: str, user_id: str = Depends(require_user_id)):
    """
    Clear all chat history for a session.
    Call this when the student clicks 'New Chat' on the frontend.
    A session owned by a different user is silently a no-op (idempotent
    delete — doesn't leak whether the session_id exists).
    """
    try:
        session_memory.clear_session(session_id, user_id=user_id)
        return {"cleared": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/history")
def get_session_history(session_id: str, user_id: str = Depends(require_user_id)):
    """Return the full history for a session — useful for debug or UI restore."""
    history = session_memory.get_history(session_id, user_id=user_id)
    return {"session_id": session_id, "history": history, "turns": len(history)}

