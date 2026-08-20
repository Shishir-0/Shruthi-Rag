"""
SHRUTI FastAPI REST API Endpoints
"""
import time
import base64
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional, Dict, Any

from backend.app.schemas import (
    QueryRequest, QueryResponse, TranscriptionResponse, SynthesisRequest, SynthesisResponse
)
from backend.app.pipeline.stt import stt_engine
from backend.app.pipeline.tts import tts_engine
from backend.app.pipeline.orchestrator import orchestrator
from backend.app.pipeline.retrieval import hybrid_retriever

router = APIRouter(tags=["SHRUTI Voice RAG"])

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "SHRUTI Voice-First Multilingual RAG",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }

@router.post("/voice/transcribe", response_model=TranscriptionResponse)
async def transcribe_voice(
    file: Optional[UploadFile] = File(None),
    audio_base64: Optional[str] = Form(None),
    language_hint: Optional[str] = Form("hi-IN")
):
    if file:
        audio_bytes = await file.read()
    elif audio_base64:
        try:
            audio_bytes = base64.b64decode(audio_base64.split(",")[-1])
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 audio data.")
    else:
        raise HTTPException(status_code=400, detail="Must provide audio file or base64 data.")

    res = await stt_engine.transcribe_audio(audio_bytes, language_hint=language_hint or "hi-IN")
    return res

@router.post("/query", response_model=QueryResponse)
async def process_text_query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")
    return await orchestrator.process_query(req)

@router.post("/voice/query", response_model=QueryResponse)
async def process_voice_query(
    file: Optional[UploadFile] = File(None),
    audio_base64: Optional[str] = Form(None),
    language_hint: Optional[str] = Form("hi-IN")
):
    # Step 1: Transcribe Voice
    t0 = time.perf_counter()
    if file:
        audio_bytes = await file.read()
    elif audio_base64:
        try:
            audio_bytes = base64.b64decode(audio_base64.split(",")[-1])
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 audio data.")

    else:
        raise HTTPException(status_code=400, detail="Must provide audio file or base64 data.")

    stt_res = await stt_engine.transcribe_audio(audio_bytes, language_hint=language_hint or "hi-IN")
    stt_ms = (time.perf_counter() - t0) * 1000.0

    # Step 2: Orchestrate RAG Pipeline
    query_req = QueryRequest(query=stt_res.text, language=stt_res.language, stream_tts=True)
    resp = await orchestrator.process_query(query_req)

    # Attach STT Telemetry
    resp.telemetry.stt_ms = round(stt_res.duration_ms or stt_ms, 2)
    resp.telemetry.total_voice_ms = round(resp.telemetry.total_voice_ms + resp.telemetry.stt_ms, 2)

    return resp

@router.post("/voice/synthesize", response_model=SynthesisResponse)
async def synthesize_voice(req: SynthesisRequest):
    return await tts_engine.synthesize_speech(req.text, req.language, req.voice)

@router.get("/sources/{chunk_id}")
async def get_source_by_id(chunk_id: str):
    hybrid_retriever.initialize()
    chk = hybrid_retriever.chunks_lookup.get(chunk_id)
    if not chk:
        raise HTTPException(status_code=404, detail=f"Source chunk '{chunk_id}' not found.")
    return chk

@router.get("/metrics")
async def get_system_metrics():
    hybrid_retriever.initialize()
    return {
        "indexed_chunks_count": len(hybrid_retriever.chunks_lookup),
        "target_rag_core_ms": 50.0,
        "supported_languages": ["hi", "gu", "bn", "ta", "en", "te", "mr", "pa"],
        "stt_provider": "OpenAI Realtime / Whisper",
        "tts_provider": "OpenAI Realtime / Speech",
        "vector_database": "Qdrant",
        "keyword_index": "BM25"
    }
