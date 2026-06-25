# backend/routers/session.py

"""
Session memory endpoints.
Kept minimal — one route to clear a session when the student starts a new chat.
"""

from fastapi import APIRouter, HTTPException
from services import memory as session_memory

router = APIRouter()


@router.delete("/session/{session_id}")
def clear_session(session_id: str):
    """
    Clear all chat history for a session.
    Call this when the student clicks 'New Chat' on the frontend.
    """
    try:
        session_memory.clear_session(session_id)
        return {"cleared": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/history")
def get_session_history(session_id: str):
    """Return the full history for a session — useful for debug or UI restore."""
    history = session_memory.get_history(session_id)
    return {"session_id": session_id, "history": history, "turns": len(history)}

