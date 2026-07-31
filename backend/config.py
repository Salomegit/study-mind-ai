import os
import os
from pathlib import Path

from pydantic import field_validator, model_validator
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

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalise_debug_value(cls, value):
        if isinstance(value, str):
            environment_values = {
                "development": True,
                "dev": True,
                "production": False,
                "prod": False,
                "release": False,
            }
            return environment_values.get(value.strip().lower(), value)
        return value

    # Shared persistent data location for Railway volumes
    DATA_DIR: str = "./data"

    # Storage paths
    SQLITE_DB_PATH: str = ""
    CHROMA_DB_PATH: str = ""

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_BATCH_SIZE: int = 32

    # Chunking
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 7
    GEMINI_API_KEY: str = ""

    # Clerk (server-side env surface for deployment)
    CLERK_SECRET_KEY: str = ""
    CLERK_PUBLISHABLE_KEY: str = ""
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: str = ""
    CLERK_WEBHOOK_SECRET: str = ""
    CLERK_JWT_ISSUER: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def resolve_storage_paths(self):
        data_dir = os.environ.get("DATA_DIR", self.DATA_DIR)

        if not self.SQLITE_DB_PATH:
            self.SQLITE_DB_PATH = str(Path(data_dir) / "sessions.db")

        if not self.CHROMA_DB_PATH:
            self.CHROMA_DB_PATH = str(Path(data_dir) / "chroma_db")

        Path(data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)
        Path(self.SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        return self


settings = Settings()
