import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Embedding models are already cached locally (~/.cache/huggingface/hub).
# Skip the network round-trip to huggingface.co so we don't hit the
# connect-error/retry bug in huggingface_hub's http_backoff (it closes the
# shared httpx client on a ConnectError, then reuses the closed client on
# the next retry attempt, crashing instead of surfacing the real error).
os.environ.setdefault("HF_HUB_OFFLINE", "1")


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    """

    # App
    APP_NAME: str = "PDF RAG API"
    DEBUG: bool = False

    # ChromaDB
    CHROMA_DB_PATH: str = "./chroma_db"

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_BATCH_SIZE: int = 32

    # Chunking
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 20
    GEMINI_API_KEY: str = ""

    # Auth — same publishable key the frontend uses (NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY).
    # It's safe to share: the Frontend API domain it encodes is public information,
    # used here only to look up Clerk's JWKS endpoint to verify request tokens.
    CLERK_PUBLISHABLE_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# Create directories automatically
Path(settings.CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)