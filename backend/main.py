# backend/main.py

import logging
import os
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import settings
from services.process_document import DocumentProcessor
from services.rag_qa import RAGQABot

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

# Single shared processor instance — loads the embedding model once on startup
processor = DocumentProcessor()

# Initialize RAG Q&A Bot with Gemini API key
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set!")

qa_bot = RAGQABot(api_key=gemini_api_key)

SUPPORTED_TYPES = {
    "application/pdf":                                                   ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


# -----------------------------------------------------------------------------
# Pydantic Models
# -----------------------------------------------------------------------------

class QuestionRequest(BaseModel):
    """Request model for Q&A endpoint."""
    collection: str
    question: str


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@app.get("/health")
def health():
    """Quick liveness check."""
    return {"status": "ok", "app": settings.APP_NAME}


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    document_id: str = Form(None),
):
    """
    Upload a PDF or DOCX file and ingest it into ChromaDB.

    Form fields:
        file            — the document (.pdf or .docx)
        collection_name — ChromaDB collection to store chunks in
        document_id     — optional stable ID; auto-generated if omitted
    """

    # ── Validate content type ──────────────────────────────────────────────
    if file.content_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type '{file.content_type}'. "
                f"Accepted: PDF, DOCX"
            ),
        )

    ext = SUPPORTED_TYPES[file.content_type]

    # ── Save upload to disk ────────────────────────────────────────────────
    upload_dir = Path(settings.UPLOAD_DIR)
    safe_name  = f"{uuid.uuid4()}{ext}"
    save_path  = upload_dir / safe_name

    try:
        contents = await file.read()

        # Enforce size limit before writing
        size_mb = len(contents) / (1024 * 1024)
        if size_mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File size {size_mb:.1f} MB exceeds "
                    f"the {settings.MAX_FILE_SIZE_MB} MB limit"
                ),
            )

        save_path.write_bytes(contents)
        logger.info("Saved upload to %s", save_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to save uploaded file")
        raise HTTPException(status_code=500, detail=f"File save failed: {e}")

    # ── Run ingestion pipeline ─────────────────────────────────────────────
    try:
        result = processor.process(
            file_path=str(save_path),
            collection_name=collection_name,
            document_id=document_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Processing failed for %s", save_path)
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")
    finally:
        # Always clean up the temp file whether processing succeeded or not
        if save_path.exists():
            save_path.unlink()
            logger.info("Cleaned up temp file %s", save_path)

    return JSONResponse(status_code=200, content=result)


@app.post("/ask")
def ask_question(request: QuestionRequest):
    """
    Ask a question about an uploaded document.
    
    The system will:
    1. Search the collection for relevant chunks
    2. Send them + your question to Gemini
    3. Return a grounded answer with sources
    
    Request body:
        collection — name of the ChromaDB collection (from /upload)
        question   — your question about the document
    """
    logger.info(
        "Question received - collection: %s, question: %s",
        request.collection,
        request.question[:50] + "..." if len(request.question) > 50 else request.question
    )
    
    try:
        # Call the RAG Q&A bot
        result = qa_bot.ask(request.question, request.collection)
        
        # Log success
        logger.info(
            "Answer generated - chunks_retrieved: %d",
            result.get("num_chunks_retrieved", 0)
        )
        
        return JSONResponse(status_code=200, content=result)
    
    except Exception as e:
        logger.exception("Q&A processing failed for collection %s", request.collection)
        raise HTTPException(
            status_code=500,
            detail=f"Q&A processing failed: {str(e)}"
        )


@app.get("/collections/{collection_name}")
def collection_info(collection_name: str):
    """
    Return the number of chunks stored in a collection.
    """
    try:
        collection = processor.client.get_collection(name=collection_name)
        return {
            "collection_name": collection_name,
            "chunks": collection.count(),
        }
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Collection '{collection_name}' not found",
        )


@app.delete("/collections/{collection_name}")
def delete_collection(collection_name: str):
    """
    Delete a collection and all its vectors.
    """
    try:
        processor.client.delete_collection(name=collection_name)
        return {"deleted": collection_name}
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Collection '{collection_name}' not found",
        )