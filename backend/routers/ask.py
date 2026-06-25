# backend/routers/ask.py

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from schemas import QuestionRequest, QuestionResponse
from services.input_guard import validate_question, validate_collection_name, InputValidationError

logger = logging.getLogger(__name__)

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
def ask_question(request: QuestionRequest):
    """
    Ask a question about an uploaded document.

    Security layers:
    - Layer 2a: Pydantic (QuestionRequest) validates non-empty fields
    - Layer 2b: input_guard.validate_question() checks length + injection patterns
    - Layer 3: prompts.py uses XML delimiters to isolate user input
    - Layer 4: rag_qa.py calls sanitise_output() on Gemini's response
    """
    try:
        clean_question = validate_question(request.question)
        clean_collection = validate_collection_name(request.collection)
    except InputValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    logger.info(
        "Question received — collection: %s | question: %s | session: %s",
        clean_collection,
        clean_question[:60] + "..." if len(clean_question) > 60 else clean_question,
        request.session_id or "none",
    )

    try:
        result = get_qa_bot().ask(
            question=clean_question,
            collection_name=clean_collection,
            session_id=request.session_id,
        )
        logger.info("Answer generated — chunks_retrieved: %d", result.get("num_chunks_retrieved", 0))
        return JSONResponse(status_code=200, content=result)

    except Exception:
        logger.exception("Q&A processing failed for collection %s", clean_collection)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your question. Please try again.",
        )
