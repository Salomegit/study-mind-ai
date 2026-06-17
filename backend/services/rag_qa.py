# backend/services/rag_qa.py

import logging
import google.generativeai as genai
from chromadb.utils import embedding_functions
import chromadb

from config import settings
from .utils import sanitise_collection_name
from .prompts import build_prompt
from .input_guard import sanitise_output  # Layer 4: output post-processing

logger = logging.getLogger(__name__)

# Minimum similarity score — chunks below this are filtered before Gemini sees them
MIN_SIMILARITY = 0.30  # Lowered from 0.65 to handle structural questions


class RAGQABot:
    def __init__(self, api_key: str, chroma_path: str = "./chroma_db"):
        """
        Initialize RAG Q&A bot with:
        - Persistent ChromaDB (data survives restarts)
        - Cosine similarity for better text matching
        - SentenceTransformer embedding function registered with ChromaDB
        - Gemini as the LLM for answer generation
        """
        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel("gemini-2.5-flash")

        self.chroma_client = chromadb.PersistentClient(path=chroma_path)

        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def get_or_create_collection(self, collection_name: str):
        safe_name = sanitise_collection_name(collection_name)
        return self.chroma_client.get_or_create_collection(
            name=safe_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedding_function
        )

    def delete_collection(self, collection_name: str) -> dict:
        try:
            safe_name = sanitise_collection_name(collection_name)
            self.chroma_client.delete_collection(safe_name)
            return {"success": True, "message": f"Collection '{safe_name}' deleted."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_collections(self) -> list[str]:
        return [col.name for col in self.chroma_client.list_collections()]

    # ------------------------------------------------------------------
    # Document ingestion
    # ------------------------------------------------------------------

    def add_chunks(
        self,
        collection_name: str,
        chunks: list[str],
        ids: list[str],
        metadatas: list[dict] | None = None
    ) -> dict:
        try:
            collection = self.get_or_create_collection(collection_name)
            collection.add(
                documents=chunks,
                ids=ids,
                metadatas=metadatas or [{} for _ in chunks]
            )
            return {
                "success": True,
                "chunks_added": len(chunks),
                "collection": collection_name
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Similarity search
    # ------------------------------------------------------------------

    def search_chunks(
        self,
        question: str,
        collection_name: str,
        top_k: int = 8,  # Increased from 5 for better recall
    ) -> list[dict]:
        """
        Search ChromaDB for chunks most similar to the question.
        Returns list of dicts with chunk text, similarity score, and metadata.
        """
        try:
            collection = self.get_or_create_collection(collection_name)

            results = collection.query(
                query_texts=[question],
                n_results=top_k,
                include=["documents", "distances", "metadatas"]
            )

            if not results or not results["ids"] or len(results["ids"][0]) == 0:
                return []

            formatted = []
            for i in range(len(results["ids"][0])):
                similarity_score = 1 - results["distances"][0][i]
                formatted.append({
                    "chunk_id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "similarity_score": round(similarity_score, 4),
                    "distance": round(results["distances"][0][i], 4),
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
                })

            formatted.sort(key=lambda x: x["similarity_score"], reverse=True)
            return formatted

        except Exception as e:
            logger.error("Error searching ChromaDB: %s", e)
            return []

    # ------------------------------------------------------------------
    # Context builder
    # ------------------------------------------------------------------

    def build_context(self, chunks: list[dict]) -> str:
        """Combine retrieved chunks into a single labelled context string."""
        context_parts = []
        for i, chunk in enumerate(chunks):
            score = chunk["similarity_score"]
            source = chunk["metadata"].get("filename",
                     chunk["metadata"].get("source", "Unknown source"))
            page = chunk["metadata"].get("page_number",
                   chunk["metadata"].get("page", ""))
            page_info = f" | Page {page}" if page else ""
            context_parts.append(
                f"[Chunk {i + 1} | Source: {source}{page_info} | Relevance: {score}]\n{chunk['text']}"
            )
        return "\n\n".join(context_parts)

    # ------------------------------------------------------------------
    # Main Q&A method
    # ------------------------------------------------------------------

    def ask(self, question: str, collection_name: str, top_k: int = 8) -> dict:
        """
        Full RAG pipeline:
        1. Retrieve top_k most similar chunks from ChromaDB
        2. Filter chunks below similarity threshold
        3. Build context from chunks
        4. Build structured prompt (with injection-resistant delimiters)
        5. Send to Gemini
        6. Post-process output to redact sensitive patterns (Layer 4)
        7. Return structured response

        NOTE: Input validation (Layer 2) happens upstream in main.py
        before this method is called.
        """
        # Step 1 — Retrieve
        chunks = self.search_chunks(question, collection_name, top_k=top_k)

        if not chunks:
            return {
                "question": question,
                "answer": "No relevant information found in the document.",
                "sources": [],
                "num_chunks_retrieved": 0,
                "error": "No chunks retrieved from ChromaDB"
            }

        # Step 2 — Filter low-relevance chunks
        filtered_chunks = [c for c in chunks if c["similarity_score"] >= MIN_SIMILARITY]

        if not filtered_chunks:
            best = chunks[0]["similarity_score"]
            logger.info(
                "All chunks below threshold. Best score: %.4f, question: %s",
                best, question[:60]
            )
            return {
                "question": question,
                "answer": (
                    "I couldn't find sufficiently relevant information for that question "
                    "in your study materials. Try rephrasing or uploading more materials."
                ),
                "sources": [],
                "num_chunks_retrieved": 0,
                "top_similarity_score": best
            }

        # Step 3 — Build context
        context = self.build_context(filtered_chunks)

        # Step 4 — Build injection-resistant structured prompt
        best_score = filtered_chunks[0]["similarity_score"]
        prompt = build_prompt(question, context, best_score)

        try:
            # Step 5 — Call Gemini
            response = self.gemini_model.generate_content(prompt)
            raw_answer = response.text

            # Step 6 — Post-process output (Layer 4: redact sensitive patterns)
            answer = sanitise_output(raw_answer)

            logger.info(
                "Answer generated — collection: %s | chunks: %d | top_score: %.4f",
                collection_name, len(filtered_chunks), best_score
            )

            return {
                "question": question,
                "answer": answer,
                "sources": [
                    {
                        "chunk_id": c["chunk_id"],
                        "text_preview": c["text"][:200] + "..." if len(c["text"]) > 200 else c["text"],
                        "similarity_score": c["similarity_score"],
                        "metadata": c["metadata"]
                    }
                    for c in filtered_chunks
                ],
                "num_chunks_retrieved": len(filtered_chunks),
                "top_similarity_score": best_score
            }

        except Exception as e:
            logger.exception("Gemini API call failed for collection %s", collection_name)
            return {
                "question": question,
                "answer": "An error occurred while generating the answer. Please try again.",
                "sources": [
                    {
                        "chunk_id": c["chunk_id"],
                        "text_preview": c["text"][:200] + "..." if len(c["text"]) > 200 else c["text"],
                        "similarity_score": c["similarity_score"],
                        "metadata": c["metadata"]
                    }
                    for c in filtered_chunks
                ],
                "num_chunks_retrieved": len(filtered_chunks),
                "error": str(e)
            }