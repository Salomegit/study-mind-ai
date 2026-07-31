# backend/routers/ask.py

import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from schemas import QuestionRequest, QuestionResponse
from services.input_guard import validate_question, validate_collection_name, InputValidationError
from services.auth import verify_clerk_auth
from services.utils import user_collection_name
from services import memory as session_memory

logger = logging.getLogger(__name__)
DAILY_ASK_LIMIT = 50

router = APIRouter()


def get_qa_bot():
    """
    Import here (not at module level) to avoid circular imports
    when main.py registers this router before qa_bot is created.
    Override this in tests to inject a mock.
    """
    from main import qa_bot
    return qa_bot


@router.post("/ask", response_model=QuestionResponse)
def ask_question(request: QuestionRequest, user_id: str = Depends(verify_clerk_auth)):
    """
    Ask a question about an uploaded document.
    
    Requires Clerk authentication.

    Security layers:
    - Layer 1: Clerk authentication (verify_clerk_auth) — user must be signed in
    - Layer 2a: Pydantic (QuestionRequest) validates non-empty fields
    - Layer 2b: input_guard.validate_question() checks length + injection patterns
    - Layer 3: prompts.py uses XML delimiters to isolate user input
    - Layer 4: rag_qa.py calls sanitise_output() on Gemini's response

    A valid Clerk session is required; its user ID is passed to the Q&A
    service so saved session history remains scoped to its owner.
    """
    try:
        clean_question = validate_question(request.question)
        clean_collection = user_collection_name(
            user_id,
            validate_collection_name(request.collection),
        )
    except InputValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    logger.info(
        "Question received — user: %s | collection: %s | question: %s | session: %s",
        user_id,
        clean_collection,
        clean_question[:60] + "..." if len(clean_question) > 60 else clean_question,
        request.session_id or "none",
    )

    if request.session_id and not session_memory.session_is_accessible(request.session_id, user_id):
        raise HTTPException(status_code=404, detail="Session not found.")

    if not session_memory.consume_daily_quota(user_id, "ask", DAILY_ASK_LIMIT):
        raise HTTPException(
            status_code=429,
            detail=f"Daily Ask limit reached ({DAILY_ASK_LIMIT} requests). Try again tomorrow.",
        )

    try:
        result = get_qa_bot().ask(
            question=clean_question,
            collection_name=clean_collection,
            session_id=request.session_id,
            user_id=user_id,
            collection_label=validate_collection_name(request.collection),
        )
        logger.info("Answer generated — chunks_retrieved: %d", result.get("num_chunks_retrieved", 0))
        return JSONResponse(status_code=200, content=result)

    except PermissionError as error:
        raise HTTPException(status_code=404, detail="Session not found.") from error
    except Exception:
        logger.exception("Q&A processing failed for collection %s", clean_collection)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your question. Please try again.",
        )
