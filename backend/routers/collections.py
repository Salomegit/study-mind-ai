# backend/routers/collections.py

import logging
from fastapi import APIRouter, HTTPException

from services.utils import sanitise_collection_name

logger = logging.getLogger(__name__)

router = APIRouter()


def get_processor():
    from main import processor
    return processor


@router.get("/collections/{collection_name}")
def collection_info(collection_name: str):
    try:
        safe_name = sanitise_collection_name(collection_name)
        collection = get_processor().client.get_collection(name=safe_name)
        return {"collection_name": safe_name, "chunks": collection.count()}
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Collection '{collection_name}' not found",
        )


@router.delete("/collections/{collection_name}")
def delete_collection(collection_name: str):
    try:
        safe_name = sanitise_collection_name(collection_name)
        get_processor().client.delete_collection(name=safe_name)
        return {"deleted": safe_name}
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Collection '{collection_name}' not found",
        )
