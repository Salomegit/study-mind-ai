# backend/process_document.py

"""
Full ingestion pipeline for PDF and DOCX files.

Flow:
    load_document()        →  List[Document]   (loaders.py)
    chunk_documents()      →  List[Document]   (smaller pieces, metadata preserved)
    embed_chunks()         →  List[List[float]]
    store_in_chromadb()    →  chromadb.Collection
"""

import logging
import uuid
from typing import Optional

import chromadb
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from config import settings
from backend.loaders import load_document

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Document Processor
# -----------------------------------------------------------------------------

class DocumentProcessor:
    """
    Handles ingestion of PDF and DOCX files into ChromaDB.

    Usage:
        processor = DocumentProcessor()

        # PDF
        result = processor.process("report.pdf", collection_name="finance")

        # DOCX
        result = processor.process("notes.docx", collection_name="meetings")

        # Returns:
        # {
        #     "document_id":      "abc-123",
        #     "collection_name":  "finance",
        #     "source_file":      "report.pdf",
        #     "file_type":        "pdf",
        #     "elements_loaded":  42,     ← pages (PDF) or elements (DOCX)
        #     "chunks_stored":    87,
        # }
    """

    def __init__(self):
        logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)

        logger.info("Initializing ChromaDB at: %s", settings.CHROMA_DB_PATH)
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
        )

    # -------------------------------------------------------------------------
    # Step 1 — Load
    # -------------------------------------------------------------------------

    def load(self, file_path: str) -> list[Document]:
        """
        Load a PDF or DOCX file. Returns a list of LangChain Documents.
        File type is detected automatically from the extension.
        """
        return load_document(file_path)

    # -------------------------------------------------------------------------
    # Step 2 — Chunk
    # -------------------------------------------------------------------------

    def chunk_documents(self, docs: list[Document]) -> list[Document]:
        """
        Split documents into smaller chunks using RecursiveCharacterTextSplitter.

        Tries to break on: paragraphs → sentences → words → characters.
        Metadata from the parent Document is carried forward into every chunk.

        Example chunk metadata (PDF):
            {"source": "report.pdf", "page": 3}

        Example chunk metadata (DOCX):
            {"source": "notes.docx", "page_number": 2, "category": "NarrativeText"}
        """
        chunks = self.splitter.split_documents(docs)

        if not chunks:
            raise ValueError("Chunking produced no output — document may be empty")

        logger.info(
            "Split %d element(s) into %d chunk(s)",
            len(docs),
            len(chunks),
        )
        return chunks

    # -------------------------------------------------------------------------
    # Step 3 — Embed
    # -------------------------------------------------------------------------

    def embed_chunks(self, chunks: list[Document]) -> list[list[float]]:
        """
        Generate embeddings for each chunk's text content.
        """
        texts = [chunk.page_content for chunk in chunks]

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=settings.EMBEDDING_BATCH_SIZE,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            return embeddings.tolist()

        except Exception as e:
            logger.exception("Embedding generation failed")
            raise RuntimeError(f"Embedding failed: {e}") from e

    # -------------------------------------------------------------------------
    # Step 4 — Store
    # -------------------------------------------------------------------------

    def store_in_chromadb(
        self,
        collection_name: str,
        document_id: str,
        chunks: list[Document],
        embeddings: list[list[float]],
    ) -> chromadb.Collection:
        """
        Persist chunks + embeddings in ChromaDB.

        Each stored record includes:
            - The chunk text
            - Its embedding vector
            - Metadata: document_id, filename, chunk_index,
                        page_number (PDF) or element category (DOCX)
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunk/embedding count mismatch: "
                f"{len(chunks)} chunks vs {len(embeddings)} embeddings"
            )

        try:
            collection = self.client.get_or_create_collection(name=collection_name)

            ids = [f"{document_id}_{uuid.uuid4()}" for _ in chunks]

            metadatas = []
            for idx, chunk in enumerate(chunks):
                meta = chunk.metadata or {}

                record = {
                    "document_id":  document_id,
                    "filename":     str(meta.get("source", "unknown")),
                    "chunk_index":  idx,
                }

                # PDF — page is 0-indexed, store as 1-indexed for humans
                if "page" in meta:
                    record["page_number"] = meta["page"] + 1

                # DOCX — page_number is already 1-indexed from Unstructured
                if "page_number" in meta:
                    record["page_number"] = meta["page_number"]

                # DOCX — structural category e.g. "Title", "NarrativeText"
                if "category" in meta:
                    record["category"] = meta["category"]

                metadatas.append(record)

            collection.add(
                ids=ids,
                documents=[c.page_content for c in chunks],
                embeddings=embeddings,
                metadatas=metadatas,
            )

            logger.info(
                "Stored %d chunks in collection '%s'",
                len(chunks),
                collection_name,
            )
            return collection

        except Exception as e:
            logger.exception("Failed to store vectors in ChromaDB")
            raise RuntimeError(f"Vector storage failed: {e}") from e

    # -------------------------------------------------------------------------
    # Main Pipeline
    # -------------------------------------------------------------------------

    def process(
        self,
        file_path: str,
        collection_name: str,
        document_id: Optional[str] = None,
    ) -> dict:
        """
        Full ingestion pipeline: load → chunk → embed → store.

        Args:
            file_path:        Path to a .pdf or .docx file.
            collection_name:  ChromaDB collection to store chunks in.
            document_id:      Optional stable ID; auto-generated if omitted.

        Returns a summary dict.
        """
        from pathlib import Path

        document_id = document_id or str(uuid.uuid4())
        file_name   = Path(file_path).name
        file_type   = Path(file_path).suffix.lower().lstrip(".")

        logger.info(
            "Starting pipeline — file: %s | collection: %s | doc_id: %s",
            file_name,
            collection_name,
            document_id,
        )

        # 1. Load
        docs = self.load(file_path)
        logger.info("Loaded %d element(s)", len(docs))

        # 2. Chunk
        chunks = self.chunk_documents(docs)
        logger.info("Created %d chunk(s)", len(chunks))

        # 3. Embed
        embeddings = self.embed_chunks(chunks)
        logger.info("Generated %d embedding(s)", len(embeddings))

        # 4. Store
        self.store_in_chromadb(
            collection_name=collection_name,
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings,
        )

        logger.info("Pipeline complete — document_id: %s", document_id)

        return {
            "document_id":     document_id,
            "collection_name": collection_name,
            "source_file":     file_name,
            "file_type":       file_type,
            "elements_loaded": len(docs),
            "chunks_stored":   len(chunks),
        }
