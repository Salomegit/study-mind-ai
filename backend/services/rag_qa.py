# backend/services/rag_qa.py

import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions
from config import settings

# 🔴 FIX 2: Minimum similarity threshold — chunks below this score are filtered out
MIN_SIMILARITY = 0.65


class RAGQABot:
    def __init__(self, api_key: str, chroma_path: str = "./chroma_db"):
        """
        Initialize RAG Q&A bot with:
        - Persistent ChromaDB (data survives restarts)
        - Cosine similarity for better text matching
        - SentenceTransformer embedding function registered with ChromaDB
        - Gemini as the LLM for answer generation
        """
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel("gemini-2.5-flash")

        # Persistent ChromaDB client — data is saved to disk
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)

        # Register embedding function with ChromaDB using configured model
        # This ensures the same model is used for both storing and querying
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def get_or_create_collection(self, collection_name: str):
        """
        Get an existing collection or create a new one with:
        - Cosine similarity (better for text than default L2)
        - Registered embedding function (auto-embeds on add and query)
        """
        return self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedding_function
        )

    def delete_collection(self, collection_name: str) -> dict:
        """Delete a collection and all its documents."""
        try:
            self.chroma_client.delete_collection(collection_name)
            return {"success": True, "message": f"Collection '{collection_name}' deleted."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_collections(self) -> list[str]:
        """List all available collections."""
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
        """
        Add document chunks to a collection.
        ChromaDB auto-embeds the chunks using the registered embedding function.

        Args:
            collection_name: Target collection
            chunks:          List of text chunks from your document processor
            ids:             Unique ID per chunk e.g. ["doc1_chunk_0", "doc1_chunk_1"]
            metadatas:       Optional list of dicts with extra info per chunk
                             e.g. [{"filename": "notes.pdf", "page_number": 1}, ...]
        """
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
        top_k: int = 5
    ) -> list[dict]:
        """
        Search ChromaDB for chunks most similar to the question.
        Returns list of dicts with chunk text, similarity score, and metadata.

        Uses cosine similarity — direction-based, not magnitude-based,
        so short questions can still match long document chunks correctly.
        """
        try:
            # 🟡 FIX 3: Use get_or_create_collection instead of get_collection
            # to guarantee the same embedding function is used at query time
            # as was used at ingestion time — prevents silent vector space mismatch
            collection = self.get_or_create_collection(collection_name)

            results = collection.query(
                query_texts=[question],  # ChromaDB auto-embeds this
                n_results=top_k,
                include=["documents", "distances", "metadatas"]
            )

            if not results or not results["ids"] or len(results["ids"][0]) == 0:
                return []

            # Format results — convert cosine distance to similarity score
            formatted = []
            for i in range(len(results["ids"][0])):
                similarity_score = 1 - results["distances"][0][i]  # higher = more similar
                formatted.append({
                    "chunk_id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "similarity_score": round(similarity_score, 4),
                    "distance": round(results["distances"][0][i], 4),
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
                })

            # Sort by similarity score descending (best match first)
            formatted.sort(key=lambda x: x["similarity_score"], reverse=True)
            return formatted

        except Exception as e:
            print(f"Error searching ChromaDB: {e}")
            return []

    # ------------------------------------------------------------------
    # Context builder
    # ------------------------------------------------------------------

    def build_context(self, chunks: list[dict]) -> str:
        """
        Combine retrieved chunks into a single context string for the LLM.
        Labels each chunk so Gemini can cite sources in its answer.
        Also includes similarity score so you can see relevance at a glance.
        """
        context_parts = []
        for i, chunk in enumerate(chunks):
            score = chunk["similarity_score"]

            # 🔴 FIX 1: Match actual metadata keys used during ingestion
            # Fallback chain: filename → source → "Unknown source"
            source = chunk["metadata"].get("filename",
                     chunk["metadata"].get("source", "Unknown source"))
            # Fallback chain: page_number → page → ""
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

    def ask(self, question: str, collection_name: str, top_k: int = 5) -> dict:
        """
        Full RAG pipeline:
        1. Embed the question
        2. Retrieve top_k most similar chunks from ChromaDB
        3. Filter chunks below similarity threshold
        4. Build context from chunks
        5. Send context + question to Gemini
        6. Return structured response

        Args:
            question:        The user's question
            collection_name: ChromaDB collection to search in
            top_k:           Number of chunks to retrieve (default 5)
        """
        # Step 1 & 2 — Retrieve relevant chunks
        chunks = self.search_chunks(question, collection_name, top_k=top_k)

        if not chunks:
            return {
                "question": question,
                "answer": "No relevant information found in the document.",
                "sources": [],
                "num_chunks_retrieved": 0,
                "error": "No chunks retrieved from ChromaDB"
            }

        # 🔴 FIX 2: Filter out low-relevance chunks before sending to Gemini
        # Chunks below MIN_SIMILARITY are noise and produce wrong answers
        filtered_chunks = [c for c in chunks if c["similarity_score"] >= MIN_SIMILARITY]

        if not filtered_chunks:
            return {
                "question": question,
                "answer": (
                    f"No sufficiently relevant information found. "
                    f"Best match score was {chunks[0]['similarity_score']:.2f} "
                    f"(minimum required: {MIN_SIMILARITY})."
                ),
                "sources": [],
                "num_chunks_retrieved": 0,
                "top_similarity_score": chunks[0]["similarity_score"]
            }

        # Step 3 — Build context from filtered chunks only
        context = self.build_context(filtered_chunks)

        # Step 4 — Build prompt and call Gemini
        prompt = f"""You are a study assistant helping KCSE students, university students, and researchers.
Answer questions based ONLY on the provided document chunks below.

Rules:
- If the answer is not in the provided chunks, say "This information is not in the provided document."
- Always cite which chunk(s) your answer came from e.g. (Chunk 1) or (Chunk 2, Chunk 3).
- Keep answers clear, accurate, and easy to understand.
- For KCSE students, use simple language. For university/research, be more detailed.

Document chunks:
{context}

Question: {question}

Answer:"""

        try:
            response = self.gemini_model.generate_content(prompt)
            answer = response.text

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
                "top_similarity_score": filtered_chunks[0]["similarity_score"]
            }

        except Exception as e:
            return {
                "question": question,
                "answer": f"Error calling Gemini API: {str(e)}",
                # Fixed: return structured sources, not raw text
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