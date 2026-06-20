# backend/main.py

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from services.process_document import DocumentProcessor
from services.rag_qa import RAGQABot
from services import memory as session_memory

from routers import ask, upload, collections, session

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Shared service instances (imported by routers via get_qa_bot / get_processor)
# -----------------------------------------------------------------------------

gemini_api_key = settings.GEMINI_API_KEY
if not gemini_api_key:
    raise ValueError(
        "GEMINI_API_KEY environment variable not set. Define it in .env or export it."
    )

processor = DocumentProcessor()
qa_bot = RAGQABot(api_key=gemini_api_key, chroma_path=settings.CHROMA_DB_PATH)

# -----------------------------------------------------------------------------
# Lifespan — runs once on startup and shutdown
# -----------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    session_memory.init_db()   # creates SQLite table, prunes expired sessions
    logger.info("StudyMind started")
    yield
    logger.info("StudyMind shutting down")

# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS — lock this down to your production domain before deploying
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Routers
# -----------------------------------------------------------------------------

app.include_router(ask.router)
app.include_router(upload.router)
app.include_router(collections.router)
app.include_router(session.router)


# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}
