# backend/process_pdf.py

import logging
import uuid
from pathlib import Path
from typing import List
from config import settings

import chromadb
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

self.model = SentenceTransformer(
    settings.EMBEDDING_MODEL
)

self.client = chromadb.PersistentClient(
    path=settings.CHROMA_DB_PATH
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# PDF Processor
# -----------------------------------------------------------------------------

class PDFProcessor:
    def __init__(self):
        logger.info("Loading embedding model...")
        self.model = SentenceTransformer(EMBEDDING_MODEL)

        logger.info("Initializing ChromaDB...")
        self.client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH
        )

    # -------------------------------------------------------------------------
    # PDF Extraction
    # -------------------------------------------------------------------------

    def extract_pdf_text(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file.
        """

        pdf_file = Path(pdf_path)

        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        try:
            reader = PdfReader(pdf_path)

            text_parts = []

            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""

                if page_text.strip():
                    text_parts.append(page_text)

            text = "\n".join(text_parts)

            if not text.strip():
                raise ValueError("No text could be extracted from PDF")

            return text

        except Exception as e:
            logger.exception("Failed to extract PDF text")
            raise RuntimeError(f"PDF extraction failed: {e}")

    # -------------------------------------------------------------------------
    # Chunking
    # -------------------------------------------------------------------------

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> List[str]:
        """
        Character-based chunking.

        For even better retrieval quality consider replacing this
        with RecursiveCharacterTextSplitter from LangChain.
        """

        chunks = []

        start = 0

        while start < len(text):
            end = start + chunk_size

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            start = end - overlap

        return chunks

    # -------------------------------------------------------------------------
    # Embeddings
    # -------------------------------------------------------------------------

    def embed_chunks(
        self,
        chunks: List[str],
        batch_size: int = 32,
    ) -> List[List[float]]:
        """
        Generate embeddings in batches.
        """

        try:
            embeddings = self.model.encode(
                chunks,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
            )

            return embeddings.tolist()

        except Exception as e:
            logger.exception("Embedding generation failed")
            raise RuntimeError(f"Embedding failed: {e}")

    # -------------------------------------------------------------------------
    # Storage
    # -------------------------------------------------------------------------

    def store_in_chromadb(
        self,
        collection_name: str,
        document_id: str,
        filename: str,
        chunks: List[str],
        embeddings: List[List[float]],
    ):
        """
        Store embeddings and chunks in ChromaDB.
        """

        try:
            collection = self.client.get_or_create_collection(
                name=collection_name
            )

            ids = [
                f"{document_id}_{uuid.uuid4()}"
                for _ in chunks
            ]

            metadatas = [
                {
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_index": idx,
                }
                for idx in range(len(chunks))
            ]

            collection.add(
                ids=ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            logger.info(
                "Stored %s chunks in collection '%s'",
                len(chunks),
                collection_name,
            )

            return collection

        except Exception as e:
            logger.exception("Failed to store vectors")
            raise RuntimeError(f"Vector storage failed: {e}")

    # -------------------------------------------------------------------------
    # Main Pipeline
    # -------------------------------------------------------------------------

    def process_pdf(
        self,
        pdf_path: str,
        collection_name: str,
        document_id: str | None = None,
    ):
        """
        Full ingestion pipeline.
        """

        document_id = document_id or str(uuid.uuid4())

        logger.info("Processing PDF: %s", pdf_path)

        text = self.extract_pdf_text(pdf_path)

        logger.info(
            "Extracted %s characters",
            len(text),
        )

        chunks = self.chunk_text(
            text=text,
            chunk_size=1000,
            overlap=200,
        )

        logger.info(
            "Created %s chunks",
            len(chunks),
        )

        embeddings = self.embed_chunks(chunks)

        logger.info(
            "Generated %s embeddings",
            len(embeddings),
        )

        collection = self.store_in_chromadb(
            collection_name=collection_name,
            document_id=document_id,
            filename=Path(pdf_path).name,
            chunks=chunks,
            embeddings=embeddings,
        )

        logger.info(
            "PDF processing complete. Document ID: %s",
            document_id,
        )

        return {
            "document_id": document_id,
            "collection": collection,
            "chunks": len(chunks),
        }


# -----------------------------------------------------------------------------
# Example Usage
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    processor = PDFProcessor()

    result = processor.process_pdf(
        pdf_path="sample_pdf.pdf",
        collection_name="biology_101",
    )

    print(result)