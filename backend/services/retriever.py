# backend/services/retriever.py

"""
Similarity search and context building — no Gemini dependency here.

Separating retrieval from generation means:
- You can swap ChromaDB for another vector store without touching rag_qa.py
- Retrieval logic can be tested with just ChromaDB, no LLM needed
- top_k, MIN_SIMILARITY, and context format can all be tuned in one place
"""

import logging

logger = logging.getLogger(__name__)

MIN_SIMILARITY = 0.30


class Retriever:
    def __init__(self, collection_manager):
        self.cm = collection_manager

    def search(
        self,
        question: str,
        collection_name: str,
        top_k: int = 8,
    ) -> list[dict]:
        """
        Query ChromaDB and return chunks with similarity scores.
        Returns an empty list if nothing is found.
        """
        try:
            collection = self.cm.get_or_create(collection_name)
            results = collection.query(
                query_texts=[question],
                n_results=top_k,
                include=["documents", "distances", "metadatas"],
            )

            if not results or not results["ids"] or not results["ids"][0]:
                return []

            formatted = []
            for i in range(len(results["ids"][0])):
                similarity_score = 1 - results["distances"][0][i]
                formatted.append({
                    "chunk_id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "similarity_score": round(similarity_score, 4),
                    "distance": round(results["distances"][0][i], 4),
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                })

            formatted.sort(key=lambda x: x["similarity_score"], reverse=True)
            return formatted

        except Exception as e:
            logger.error("ChromaDB search error: %s", e)
            return []

    def filter_by_threshold(self, chunks: list[dict]) -> list[dict]:
        return [c for c in chunks if c["similarity_score"] >= MIN_SIMILARITY]

    def build_context(self, chunks: list[dict]) -> str:
        """Combine chunks into a labelled context string for the prompt."""
        parts = []
        for i, chunk in enumerate(chunks):
            score = chunk["similarity_score"]
            source = chunk["metadata"].get(
                "filename", chunk["metadata"].get("source", "Unknown source")
            )
            page = chunk["metadata"].get(
                "page_number", chunk["metadata"].get("page", "")
            )
            page_info = f" | Page {page}" if page else ""
            parts.append(
                f"[Chunk {i + 1} | Source: {source}{page_info} | Relevance: {score}]\n{chunk['text']}"
            )
        return "\n\n".join(parts)
