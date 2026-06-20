# backend/services/collection_manager.py

"""
ChromaDB collection CRUD — completely separate from the RAG pipeline.

Separating this means:
- rag_qa.py only imports what it needs for answering questions
- Collection management can be tested and changed independently
- DocumentProcessor and RAGQABot can both use this without coupling to each other
"""

import logging
import chromadb
from chromadb.utils import embedding_functions

from config import settings
from .utils import sanitise_collection_name

logger = logging.getLogger(__name__)


class CollectionManager:
    def __init__(self, chroma_path: str, embedding_function):
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.embedding_function = embedding_function

    def get_or_create(self, collection_name: str):
        safe_name = sanitise_collection_name(collection_name)
        return self.client.get_or_create_collection(
            name=safe_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedding_function,
        )

    def delete(self, collection_name: str) -> dict:
        try:
            safe_name = sanitise_collection_name(collection_name)
            self.client.delete_collection(safe_name)
            return {"success": True, "message": f"Collection '{safe_name}' deleted."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_names(self) -> list[str]:
        return [col.name for col in self.client.list_collections()]

    def add_chunks(
        self,
        collection_name: str,
        chunks: list[str],
        ids: list[str],
        metadatas: list[dict] | None = None,
    ) -> dict:
        try:
            collection = self.get_or_create(collection_name)
            collection.add(
                documents=chunks,
                ids=ids,
                metadatas=metadatas or [{} for _ in chunks],
            )
            return {
                "success": True,
                "chunks_added": len(chunks),
                "collection": collection_name,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
