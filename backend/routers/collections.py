# backend/routers/collections.py

import logging
from fastapi import APIRouter, Depends, HTTPException

from services.auth import require_user_id
from services.utils import user_collection_name, user_collection_prefix

logger = logging.getLogger(__name__)

router = APIRouter()


def get_processor():
    from main import processor
    return processor


@router.get("/collections")
def list_collections(user_id: str = Depends(require_user_id)):
    """List only the authenticated user's collections."""
    try:
        from main import qa_bot
        prefix = user_collection_prefix(user_id)
        collections = sorted(
            name.removeprefix(prefix)
            for name in qa_bot.collection_manager.list_names()
            if name.startswith(prefix)
        )
        return {"collections": collections}
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch collections"
        )


@router.get("/collections/{collection_name}")
def collection_info(collection_name: str, user_id: str = Depends(require_user_id)):
    try:
        physical_name = user_collection_name(user_id, collection_name)
        collection = get_processor().client.get_collection(name=physical_name)
        return {"collection_name": collection_name, "chunks": collection.count()}
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Collection '{collection_name}' not found",
        )


