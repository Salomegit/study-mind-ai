# backend/routers/upload.py

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from config import settings
from services.input_guard import validate_collection_name, InputValidationError

logger = logging.getLogger(__name__)

router = APIRouter()

SUPPORTED_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


def get_processor():
    from main import processor
    return processor


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    document_id: str = Form(None),
):
    if file.content_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. Accepted: PDF, DOCX",
        )

    try:
        validate_collection_name(collection_name)
    except InputValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    ext = SUPPORTED_TYPES[file.content_type]
    upload_dir = Path(settings.UPLOAD_DIR)
    save_path = upload_dir / f"{uuid.uuid4()}{ext}"

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
        result = get_processor().process(
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
