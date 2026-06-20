# backend/schemas.py

"""
All Pydantic request and response models for StudyMind.

Keeping schemas in one place means:
- main.py and routers stay focused on routing logic only
- Response shapes are documented and validated automatically in /docs
- Adding a field to a response is one change here, not scattered across files
"""

from pydantic import BaseModel, field_validator


# ── Chat history ───────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    """A single turn in a conversation."""
    role: str        # "user" or "assistant"
    content: str


# ── Source chunk returned in Q&A responses ─────────────────────────────────

class SourceChunk(BaseModel):
    chunk_id: str
    text_preview: str
    similarity_score: float
    metadata: dict


# ── /ask request ───────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    """
    Request model for /ask.
    Pydantic validators here are the first gate — they run before
    the route handler and before input_guard.
    session_id is optional: if omitted, no memory is stored or used.
    """
    collection: str
    question: str
    session_id: str | None = None

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Question cannot be empty.")
        return v.strip()

    @field_validator("collection")
    @classmethod
    def collection_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Collection name cannot be empty.")
        return v.strip()


# ── /ask response ──────────────────────────────────────────────────────────

class QuestionResponse(BaseModel):
    """
    Response model for /ask.
    All fields are always present — None where not applicable.
    This gives the frontend a stable contract regardless of code path.
    """
    question: str
    answer: str
    session_id: str | None = None
    history: list[ChatMessage] = []
    sources: list[SourceChunk] = []
    num_chunks_retrieved: int = 0
    top_similarity_score: float | None = None
    error: str | None = None


# ── /upload response ───────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    success: bool
    message: str | None = None
    collection: str | None = None
    chunks_added: int | None = None
    error: str | None = None
