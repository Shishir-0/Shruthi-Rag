"""
FastAPI Main Application Entrypoint for SHRUTI Multilingual Voice-First RAG System.
OpenAI Realtime API & HH Goa RAG Architecture.
"""
import time
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.config import settings
from backend.app.api.endpoints import router as api_router
from backend.app.api.ws_voice import router as ws_router
from backend.app.api.realtime_session import router as realtime_session_router
from backend.app.pipeline.retrieval import hybrid_retriever
from backend.app.pipeline.http_client import close_http_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Pre-warming
    hybrid_retriever.initialize()
    yield
    # Shutdown Cleanup
    await close_http_client()

app = FastAPI(
    title=settings.APP_NAME,
    description="HH Goa 2026 Task #2 Production Submission — OpenAI Realtime API & Qdrant + BM25 RAG",
    version="3.0.0",
    lifespan=lifespan
)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(realtime_session_router, prefix="/api/v1")
app.include_router(ws_router)

@app.get("/")
def read_root():
    return {
        "system": "SHRUTI — OpenAI Realtime Voice RAG System",
        "task": "HH Goa 2026 Task #2 Submission",
        "voice_stack": "OpenAI Realtime API (Speech-to-Speech)",
        "rag_stack": "Qdrant + BM25 Hybrid Retrieval with Grounding & Citations",
        "status": "OPERATIONAL",
        "docs": "/docs"
    }

@app.get("/health/live")
def health_live():
    return {
        "status": "ALIVE",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }

@app.get("/health/ready")
def health_ready():
    hybrid_retriever.initialize()
    chunks_count = len(hybrid_retriever.chunks_lookup)
    is_ready = chunks_count > 0
    return {
        "status": "READY" if is_ready else "DEGRADED",
        "indexed_chunks": chunks_count,
        "bm25_ready": hybrid_retriever.bm25 is not None or bool(hybrid_retriever.chunks_lookup),
        "vector_matrix_ready": hybrid_retriever.vector_matrix is not None or hybrid_retriever.qdrant_client is not None,
        "test_mode": settings.SHRUTI_TEST_MODE
    }

@app.get("/health/providers")
async def health_providers():
    has_openai_key = bool(settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 5)
    openai_reachable = False

    if has_openai_key and not settings.SHRUTI_TEST_MODE:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
                )
                openai_reachable = (resp.status_code == 200)
        except Exception:
            openai_reachable = False
    elif settings.SHRUTI_TEST_MODE:
        openai_reachable = True

    return {
        "voice_provider": "OpenAI Realtime API",
        "realtime_model": settings.OPENAI_REALTIME_MODEL,
        "stt_provider": "OpenAI Whisper / Realtime STT",
        "tts_provider": "OpenAI Audio / Realtime Speech",
        "llm_provider": "OpenAI GPT-4o / GPT-4o-mini",
        "openai_authenticated": has_openai_key or settings.SHRUTI_TEST_MODE,
        "openai_reachable": openai_reachable,
        "vector_db": "Qdrant",
        "keyword_db": "BM25",
        "test_mode": settings.SHRUTI_TEST_MODE
    }

@app.get("/health")
def legacy_health():
    return health_ready()
