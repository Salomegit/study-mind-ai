# backend/main.py

import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from config import settings
from services.process_document import DocumentProcessor
from services.rag_qa import RAGQABot
from services.utils import sanitise_collection_name
from services.input_guard import (   # ← Layer 2: input validation
    validate_question,
    validate_collection_name,
    InputValidationError,
)

# -----------------------------------------------------------------------------
# App Setup
# -----------------------------------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

# CORS — lock this down to your production domain before deploying
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

processor = DocumentProcessor()

gemini_api_key = settings.GEMINI_API_KEY
if not gemini_api_key:
    raise ValueError(
        "GEMINI_API_KEY environment variable not set. Define it in .env or export it."
    )

qa_bot = RAGQABot(api_key=gemini_api_key, chroma_path=settings.CHROMA_DB_PATH)

SUPPORTED_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


# -----------------------------------------------------------------------------
# Pydantic Models
# -----------------------------------------------------------------------------

class QuestionRequest(BaseModel):
    """
    Request model for Q&A endpoint.
    Pydantic validators run before the route handler —
    this is the first validation gate.
    """
    collection: str
    question: str

    @field_validator('question')
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Question cannot be empty.")
        return v.strip()

    @field_validator('collection')
    @classmethod
    def collection_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Collection name cannot be empty.")
        return v.strip()


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    document_id: str = Form(None),
):
    # ── Validate content type ──────────────────────────────────────────────
    if file.content_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. Accepted: PDF, DOCX",
        )

    # ── Validate collection name ───────────────────────────────────────────
    try:
        validate_collection_name(collection_name)
    except InputValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    ext = SUPPORTED_TYPES[file.content_type]
    upload_dir = Path(settings.UPLOAD_DIR)
    safe_name = f"{uuid.uuid4()}{ext}"
    save_path = upload_dir / safe_name

    try:
        contents = await file.read()

        size_mb = len(contents) / (1024 * 1024)
        if size_mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"File size {size_mb:.1f} MB exceeds the {settings.MAX_FILE_SIZE_MB} MB limit",
            )

        save_path.write_bytes(contents)
        logger.info("Saved upload to %s", save_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to save uploaded file")
        raise HTTPException(status_code=500, detail=f"File save failed: {e}")

    try:
        result = processor.process(
            file_path=str(save_path),
            collection_name=collection_name,
            document_id=document_id,
            original_filename=file.filename,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Processing failed for %s", save_path)
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")
    finally:
        if save_path.exists():
            save_path.unlink()
            logger.info("Cleaned up temp file %s", save_path)

    return JSONResponse(status_code=200, content=result)


@app.post("/ask")
def ask_question(request: QuestionRequest):
    """
    Ask a question about an uploaded document.

    Security layers applied here:
    - Layer 2a: Pydantic model validates non-empty fields (above)
    - Layer 2b: input_guard.validate_question() checks length + injection patterns
    - Layer 3: prompts.py uses XML delimiters to isolate user input
    - Layer 4: rag_qa.py calls sanitise_output() on Gemini's response
    """

    # ── Layer 2b: Deep input validation ───────────────────────────────────
    try:
        clean_question = validate_question(request.question)
        clean_collection = validate_collection_name(request.collection)
    except InputValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    logger.info(
        "Question received — collection: %s | question: %s",
        clean_collection,
        clean_question[:60] + "..." if len(clean_question) > 60 else clean_question,
    )

    try:
        result = qa_bot.ask(clean_question, clean_collection)

        logger.info(
            "Answer generated — chunks_retrieved: %d",
            result.get("num_chunks_retrieved", 0),
        )

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        logger.exception("Q&A processing failed for collection %s", clean_collection)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your question. Please try again.",
            # NOTE: never expose str(e) to the client in production —
            # it can leak internal paths, model names, or ChromaDB details
        )


@app.get("/collections/{collection_name}")
def collection_info(collection_name: str):
    try:
        safe_name = sanitise_collection_name(collection_name)
        collection = processor.client.get_collection(name=safe_name)
        return {"collection_name": safe_name, "chunks": collection.count()}
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Collection '{collection_name}' not found",
        )


@app.delete("/collections/{collection_name}")
def delete_collection(collection_name: str):
    try:
        safe_name = sanitise_collection_name(collection_name)
        processor.client.delete_collection(name=safe_name)
        return {"deleted": safe_name}
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Collection '{collection_name}' not found",
        )