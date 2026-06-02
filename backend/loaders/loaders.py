# backend/loaders.py

"""
Document loaders for PDF and DOCX files.

Each loader returns a list of LangChain Document objects so the rest of
the pipeline (chunking → embedding → storage) stays identical regardless
of the source file type.
"""

import logging
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_core.documents import Document

from config import settings

logger = logging.getLogger(__name__)

# Supported extensions and their human-readable label
SUPPORTED_EXTENSIONS = {
    ".pdf": "PDF",
    ".docx": "Word Document",
}


# -----------------------------------------------------------------------------
# Shared validation
# -----------------------------------------------------------------------------

def _validate_file(file_path: str) -> Path:
    """
    Run common checks before loading any document.
    Raises FileNotFoundError, ValueError on failure.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{path.suffix}'. "
            f"Supported types: {', '.join(SUPPORTED_EXTENSIONS.keys())}"
        )

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise ValueError(
            f"File size {size_mb:.1f} MB exceeds the "
            f"{settings.MAX_FILE_SIZE_MB} MB limit"
        )

    return path


def _filter_empty_docs(docs: list[Document], file_path: str) -> list[Document]:
    """
    Remove blank documents and warn about them.
    Raises ValueError if nothing survives the filter.
    """
    valid = []

    for doc in docs:
        if doc.page_content.strip():
            valid.append(doc)
        else:
            page = doc.metadata.get("page")
            location = f"page {page + 1}" if page is not None else "unknown location"
            logger.warning(
                "%s — blank content at %s (possibly image-based). Skipping.",
                file_path,
                location,
            )

    if not valid:
        raise ValueError(
            "No text could be extracted. "
            "The file may be scanned, image-based, or password-protected."
        )

    return valid


# -----------------------------------------------------------------------------
# PDF Loader
# -----------------------------------------------------------------------------

def load_pdf(file_path: str) -> list[Document]:
    """
    Load a PDF using LangChain's PyPDFLoader.

    Returns one Document per page. Each Document carries:
        doc.page_content          → page text
        doc.metadata["source"]    → file path
        doc.metadata["page"]      → 0-indexed page number
    """
    path = _validate_file(file_path)

    logger.info("Loading PDF: %s", path.name)

    try:
        loader = PyPDFLoader(str(path))
        docs = loader.load()
    except Exception as e:
        logger.exception("PyPDFLoader failed on %s", file_path)
        raise RuntimeError(f"PDF loading failed: {e}") from e

    docs = _filter_empty_docs(docs, file_path)

    logger.info("Loaded %d pages from %s", len(docs), path.name)
    return docs


# -----------------------------------------------------------------------------
# DOCX Loader
# -----------------------------------------------------------------------------

def load_docx(file_path: str) -> list[Document]:
    """
    Load a Word document using UnstructuredWordDocumentLoader in 'elements' mode.

    Returns one Document per structural element (heading, paragraph, table cell …).
    Each Document carries:
        doc.page_content              → element text
        doc.metadata["source"]        → file path
        doc.metadata["page_number"]   → 1-indexed page number (when detectable)
        doc.metadata["category"]      → element type e.g. "Title", "NarrativeText"
    """
    path = _validate_file(file_path)

    logger.info("Loading DOCX: %s", path.name)

    try:
        loader = UnstructuredWordDocumentLoader(str(path), mode="elements")
        docs = loader.load()
    except Exception as e:
        logger.exception("UnstructuredWordDocumentLoader failed on %s", file_path)
        raise RuntimeError(f"DOCX loading failed: {e}") from e

    docs = _filter_empty_docs(docs, file_path)

    logger.info("Loaded %d elements from %s", len(docs), path.name)
    return docs


# -----------------------------------------------------------------------------
# Unified entry point
# -----------------------------------------------------------------------------

def load_document(file_path: str) -> list[Document]:
    """
    Auto-detect file type and delegate to the correct loader.

    Supported: .pdf, .docx
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return load_pdf(file_path)

    if ext == ".docx":
        return load_docx(file_path)

    raise ValueError(
        f"Unsupported file type '{ext}'. "
        f"Supported: {', '.join(SUPPORTED_EXTENSIONS.keys())}"
    )