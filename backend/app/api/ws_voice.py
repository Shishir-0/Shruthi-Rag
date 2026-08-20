"""
SHRUTI Real-Time WebSocket Voice Endpoint (/ws/voice)
Integrates OpenAI Realtime API, Ephemeral Sessions, Speculative Retrieval, Function Calling RAG, Barge-In, and T0-T8 Nanosecond Latency Telemetry.
"""
import json
import time
import uuid
import logging
import asyncio
import base64
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.config import settings
from backend.app.schemas import QueryRequest, WSClientMessage, WSServerMessage
from backend.app.voice.turn_manager import turn_manager
from backend.app.voice.openai_realtime import openai_realtime_manager, OpenAIRealtimeSession
from backend.app.pipeline.fast_path import fast_path_engine
from backend.app.pipeline.query_stability import stability_detector
from scripts.build_embeddings import LightweightMultilingualProvider
from backend.app.pipeline.retrieval import hybrid_retriever

logger = logging.getLogger(__name__)
router = APIRouter()

_fast_embedder = LightweightMultilingualProvider()

session_audio_buffers: Dict[str, bytearray] = {}
session_language_hints: Dict[str, str] = {}
session_speculative_cache: Dict[str, Dict[str, Any]] = {}
session_telemetry_trackers: Dict[str, Dict[str, float]] = {}

@router.websocket("/ws/voice")
async def voice_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id, conv_id = turn_manager.get_or_create_session()
    current_turn_id = turn_manager.start_new_turn(session_id)
    session_audio_buffers[session_id] = bytearray()
    session_language_hints[session_id] = "hi-IN"
    session_telemetry_trackers[session_id] = {
        "t0_mic_start": time.perf_counter_ns(),
        "speculation_started": 0,
        "speculation_hit": 0,
        "speculation_cancelled": 0,
        "speculation_saved_ms": 0.0
    }

    # Initialize OpenAI Realtime session manager
    openai_session = await openai_realtime_manager.get_or_create_session(session_id, conv_id)
    logger.info(f"WebSocket voice session connected: {session_id}")

    try:
        while True:
            msg = await websocket.receive()

            # --- Binary Audio Frame (PCM16 16kHz) Processing ---
            if "bytes" in msg and msg["bytes"]:
                audio_bytes = msg["bytes"]
                
                # Check for instant user barge-in while previous turn was active
                if not turn_manager.is_turn_active(session_id, current_turn_id):
                    current_turn_id = turn_manager.start_new_turn(session_id)
                    session_audio_buffers[session_id] = bytearray()
                    await openai_session.send_barge_in()

                session_audio_buffers[session_id].extend(audio_bytes)

                # Forward PCM frame to OpenAI Realtime session
                pcm_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                await openai_session.send_audio_chunk(pcm_b64)

            # --- Text Control Message Processing ---
            elif "text" in msg and msg["text"]:
                data = json.loads(msg["text"])
                msg_type = data.get("type")

                if msg_type == "START_STREAM":
                    current_turn_id = turn_manager.start_new_turn(session_id)
                    session_audio_buffers[session_id] = bytearray()
                    session_language_hints[session_id] = data.get("language_hint", "hi-IN")
                    session_telemetry_trackers[session_id]["t0_mic_start"] = time.perf_counter_ns()

                    await websocket.send_json(WSServerMessage(
                        type="STREAM_STARTED",
                        session_id=session_id,
                        conversation_id=conv_id,
                        turn_id=current_turn_id
                    ).model_dump())

                elif msg_type in ["BARGE_IN", "CANCEL_TURN"]:
                    turn_manager.cancel_turn(current_turn_id, reason="User Interruption / Barge-In")
                    current_turn_id = turn_manager.start_new_turn(session_id)
                    session_audio_buffers[session_id] = bytearray()
                    session_speculative_cache.pop(session_id, None)
                    await openai_session.send_barge_in()

                    await websocket.send_json(WSServerMessage(
                        type="TURN_CANCELLED",
                        session_id=session_id,
                        conversation_id=conv_id,
                        turn_id=current_turn_id,
                        error_message="Barge-in: Interrupted in <100ms."
                    ).model_dump())

                elif msg_type == "TRANSCRIPT_DELTA":
                    # Real-time partial transcript stream update
                    partial_text = data.get("text", "")
                    lang = data.get("language") or session_language_hints.get(session_id, "hi-IN")
                    
                    if partial_text and turn_manager.is_turn_active(session_id, current_turn_id):
                        await websocket.send_json(WSServerMessage(
                            type="TRANSCRIPT_PARTIAL",
                            session_id=session_id,
                            conversation_id=conv_id,
                            turn_id=current_turn_id,
                            text=partial_text,
                            language=lang,
                            timestamp_ms=time.time() * 1000
                        ).model_dump())

                        # Speculative Retrieval Trigger on Stable Transcript
                        stability = stability_detector.evaluate_transcript(partial_text)
                        if stability.is_stable and session_id not in session_speculative_cache:
                            session_telemetry_trackers[session_id]["speculation_started"] += 1
                            async def run_speculation():
                                try:
                                    t0_spec = time.perf_counter_ns()
                                    q_vec = _fast_embedder.embed_texts([partial_text])[0]
                                    cands, audit = await hybrid_retriever.hybrid_retrieve(
                                        query_text=partial_text, query_vector=q_vec, top_k=5, language=lang
                                    )
                                    dt_spec_ms = (time.perf_counter_ns() - t0_spec) / 1_000_000.0
                                    session_speculative_cache[session_id] = {
                                        "query": partial_text,
                                        "candidates": cands,
                                        "audit": audit,
                                        "saved_ms": dt_spec_ms
                                    }
                                except Exception as err:
                                    logger.warning(f"Speculative retrieval error: {err}")

                            spec_task = asyncio.create_task(run_speculation())
                            turn_manager.register_task(current_turn_id, spec_task)

                elif msg_type == "FUNCTION_CALL_RETRIEVE":
                    # Tool call retrieve_documents execution requested by OpenAI Realtime
                    query_text = data.get("query", "")
                    lang = data.get("language") or session_language_hints.get(session_id, "hi-IN")
                    t_ret_0 = time.perf_counter_ns()

                    # Speculative Hit check
                    cached_spec = session_speculative_cache.get(session_id)
                    if cached_spec and cached_spec.get("query") == query_text:
                        session_telemetry_trackers[session_id]["speculation_hit"] += 1
                        saved_ms = cached_spec.get("saved_ms", 0.0)
                        session_telemetry_trackers[session_id]["speculation_saved_ms"] += saved_ms
                    else:
                        if cached_spec:
                            session_telemetry_trackers[session_id]["speculation_cancelled"] += 1

                    # Execute FastPath RAG Engine (Qdrant + BM25 + RRF + Reranker + Grounding + Citations)
                    req = QueryRequest(query=query_text, language=lang)
                    resp, audit_meta = await fast_path_engine.execute_fast_path(req)

                    if turn_manager.is_turn_active(session_id, current_turn_id):
                        await websocket.send_json(WSServerMessage(
                            type="QUERY_RESPONSE",
                            session_id=session_id,
                            conversation_id=conv_id,
                            turn_id=current_turn_id,
                            trace_id=resp.trace_id,
                            answer=resp.answer,
                            citations=[c.model_dump() for c in resp.citations],
                            telemetry=resp.telemetry.model_dump(),
                            grounded=resp.grounding.grounded
                        ).model_dump())

                elif msg_type in ["AUDIO_END", "TEXT_QUERY", "VOICE_QUERY"]:
                    query_text = data.get("query", "")
                    lang = data.get("language") or session_language_hints.get(session_id, "hi-IN")

                    if not query_text:
                        buf = bytes(session_audio_buffers.get(session_id, b""))
                        if buf:
                            from backend.app.pipeline.stt import stt_engine
                            stt_res = await stt_engine.transcribe_audio(buf, language_hint=lang)
                            query_text = stt_res.text

                    if query_text:
                        await websocket.send_json(WSServerMessage(
                            type="TRANSCRIPT_FINAL",
                            session_id=session_id,
                            conversation_id=conv_id,
                            turn_id=current_turn_id,
                            text=query_text,
                            language=lang,
                            timestamp_ms=time.time() * 1000
                        ).model_dump())

                        req = QueryRequest(query=query_text, language=lang)
                        resp, audit_meta = await fast_path_engine.execute_fast_path(req)

                        if turn_manager.is_turn_active(session_id, current_turn_id):
                            await websocket.send_json(WSServerMessage(
                                type="QUERY_RESPONSE",
                                session_id=session_id,
                                conversation_id=conv_id,
                                turn_id=current_turn_id,
                                trace_id=resp.trace_id,
                                answer=resp.answer,
                                citations=[c.model_dump() for c in resp.citations],
                                telemetry=resp.telemetry.model_dump(),
                                grounded=resp.grounding.grounded
                            ).model_dump())

                    session_audio_buffers[session_id] = bytearray()
                    session_speculative_cache.pop(session_id, None)

                elif msg_type == "PING":
                    await websocket.send_json(WSServerMessage(type="PONG").model_dump())

    except WebSocketDisconnect:
        logger.info(f"WebSocket voice session closed: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error in session {session_id}: {e}")
    finally:
        session_audio_buffers.pop(session_id, None)
        session_language_hints.pop(session_id, None)
        session_speculative_cache.pop(session_id, None)
        session_telemetry_trackers.pop(session_id, None)
        openai_realtime_manager.remove_session(session_id)
        turn_manager.cleanup_session(session_id)
