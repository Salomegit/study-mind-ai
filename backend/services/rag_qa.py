# backend/services/rag_qa.py

"""
RAG Q&A pipeline — orchestration only.

This file no longer handles:
- Collection CRUD  → collection_manager.py
- Similarity search / context building → retriever.py
- Session memory → memory.py

What remains here is the pipeline: retrieve → filter → build context
→ build prompt → call Gemini → sanitise output → save to memory → return.
"""

import logging
import google.generativeai as genai
from chromadb.utils import embedding_functions

from config import settings
from .collection_manager import CollectionManager
from .retriever import Retriever
from .prompts import build_prompt
from .input_guard import sanitise_output
from . import memory as session_memory

logger = logging.getLogger(__name__)


class RAGQABot:
    def __init__(self, api_key: str, chroma_path: str = "./chroma_db"):
        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel("gemini-2.5-flash")

        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
        self.collection_manager = CollectionManager(chroma_path, embedding_fn)
        self.retriever = Retriever(self.collection_manager)

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------

    def ask(
        self,
        question: str,
        collection_name: str,
        session_id: str | None = None,
        top_k: int = 8,
    ) -> dict:
        """
        Full RAG pipeline:
        1. Load session history (if session_id provided)
        2. Retrieve top_k chunks from ChromaDB
        3. Filter chunks below similarity threshold
        4. Build context string
        5. Build structured prompt with history injected
        6. Send to Gemini
        7. Sanitise output (Layer 4)
        8. Save both turns to session memory
        9. Return structured response (matches QuestionResponse schema)
        """
        # Step 1 — Load history
        history = session_memory.get_history(session_id) if session_id else []

        # Step 2 — Retrieve
        chunks = self.retriever.search(question, collection_name, top_k=top_k)

        if not chunks:
            return {
                "question": question,
                "answer": "No relevant information found in the document.",
                "session_id": session_id,
                "history": history,
                "sources": [],
                "num_chunks_retrieved": 0,
                "error": "No chunks retrieved from ChromaDB",
            }

        # Step 3 — Filter
        filtered = self.retriever.filter_by_threshold(chunks)

        if not filtered:
            best = chunks[0]["similarity_score"]
            logger.info("All chunks below threshold. Best score: %.4f", best)
            return {
                "question": question,
                "answer": (
                    "I couldn't find sufficiently relevant information for that question "
                    "in your study materials. Try rephrasing or uploading more materials."
                ),
                "session_id": session_id,
                "history": history,
                "sources": [],
                "num_chunks_retrieved": 0,
                "top_similarity_score": best,
            }

        # Step 4 — Build context
        context = self.retriever.build_context(filtered)
        best_score = filtered[0]["similarity_score"]

        # Step 5 — Build prompt with history
        prompt = build_prompt(question, context, best_score, history=history)

        try:
            # Step 6 — Call Gemini
            response = self.gemini_model.generate_content(prompt)
            raw_answer = response.text

            # Step 7 — Sanitise output
            answer = sanitise_output(raw_answer)

            # Step 8 — Persist both turns to session memory
            if session_id:
                session_memory.save_turn(session_id, "user", question)
                session_memory.save_turn(session_id, "assistant", answer)

            # Reload history so response reflects the just-saved turns
            updated_history = session_memory.get_history(session_id) if session_id else []

            logger.info(
                "Answer generated — collection: %s | chunks: %d | top_score: %.4f",
                collection_name, len(filtered), best_score,
            )

            return {
                "question": question,
                "answer": answer,
                "session_id": session_id,
                "history": updated_history,
                "sources": [
                    {
                        "chunk_id": c["chunk_id"],
                        "text_preview": c["text"][:200] + "..." if len(c["text"]) > 200 else c["text"],
                        "similarity_score": c["similarity_score"],
                        "metadata": c["metadata"],
                    }
                    for c in filtered
                ],
                "num_chunks_retrieved": len(filtered),
                "top_similarity_score": best_score,
            }

        except Exception as e:
            logger.exception("Gemini API call failed for collection %s", collection_name)
            return {
                "question": question,
                "answer": "An error occurred while generating the answer. Please try again.",
                "session_id": session_id,
                "history": history,
                "sources": [
                    {
                        "chunk_id": c["chunk_id"],
                        "text_preview": c["text"][:200] + "..." if len(c["text"]) > 200 else c["text"],
                        "similarity_score": c["similarity_score"],
                        "metadata": c["metadata"],
                    }
                    for c in filtered
                ],
                "num_chunks_retrieved": len(filtered),
                "error": str(e),
            }
