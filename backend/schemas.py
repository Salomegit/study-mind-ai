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


# ── Quiz Question ──────────────────────────────────────────────────────────

class QuizQuestion(BaseModel):
    """A single quiz question with options."""
    question_id: int
    question_text: str
    question_type: str  # "multiple_choice", "true_false", "short_answer"
    options: list[str] | None = None  # For multiple choice / true_false
    correct_answer: str | int | None = None  # The correct answer (optional in request)
    explanation: str | None = None  # Why this is correct


# ── /quiz/generate request ──────────────────────────────────────────────────

class QuizGenerationRequest(BaseModel):
    """Request to generate a quiz from a document collection."""
    collection: str
    num_questions: int = 5  # How many questions to generate
    difficulty: str = "medium"  # "easy", "medium", "hard"
    quiz_type: str = "mixed"  # "mixed", "multiple_choice_only", "true_false_only"

    @field_validator("num_questions")
    @classmethod
    def validate_num_questions(cls, v: int) -> int:
        if not 1 <= v <= 20:
            raise ValueError("Number of questions must be between 1 and 20.")
        return v

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        if v not in ["easy", "medium", "hard"]:
            raise ValueError("Difficulty must be 'easy', 'medium', or 'hard'.")
        return v

    @field_validator("quiz_type")
    @classmethod
    def validate_quiz_type(cls, v: str) -> str:
        if v not in ["mixed", "multiple_choice_only", "true_false_only"]:
            raise ValueError("Quiz type must be 'mixed', 'multiple_choice_only', or 'true_false_only'.")
        return v


# ── /quiz/generate response ────────────────────────────────────────────────

class QuizGenerationResponse(BaseModel):
    """Response with generated quiz questions."""
    quiz_id: str
    collection: str
    questions: list[QuizQuestion]
    num_questions: int
    difficulty: str
    quiz_type: str
    error: str | None = None


# ── /quiz/check-answer request ─────────────────────────────────────────────

class AnswerSubmission(BaseModel):
    """A user's answer to a quiz question."""
    question_id: int
    user_answer: str | int


class QuizAnswerRequest(BaseModel):
    """Request to check answers for a quiz."""
    quiz_id: str
    answers: list[AnswerSubmission]


# ── /quiz/check-answer response ────────────────────────────────────────────

class AnswerResult(BaseModel):
    """Result for a single answer."""
    question_id: int
    question_text: str
    user_answer: str | int
    correct_answer: str | int
    is_correct: bool
    explanation: str
    question_type: str


class QuizResultResponse(BaseModel):
    """Complete quiz results."""
    quiz_id: str
    total_questions: int
    correct_count: int
    score_percentage: float
    results: list[AnswerResult]
    error: str | None = None
