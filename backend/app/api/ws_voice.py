"""
SHRUTI Real-Time WebSocket Voice Endpoint (/ws/voice)
Handles bidirectional audio streaming, partial/stable/final transcripts, speculative retrieval, barge-in, turn cancellation, and streaming TTS dispatch.
"""
import json
import time
import uuid
import logging
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.schemas import QueryRequest, WSClientMessage, WSServerMessage
from backend.app.voice.turn_manager import turn_manager
from backend.app.voice.stt_session import stt_session_manager, TranscriptState
from backend.app.voice.tts_session import tts_session_manager
from backend.app.pipeline.fast_path import fast_path_engine
from backend.app.pipeline.query_stability import stability_detector
from backend.app.pipeline.stt import stt_engine
from backend.app.pipeline.retrieval import hybrid_retriever
from scripts.build_embeddings import LightweightMultilingualProvider

logger = logging.getLogger(__name__)
router = APIRouter()

_fast_embedder = LightweightMultilingualProvider()

# Session state trackers
session_audio_buffers: Dict[str, bytearray] = {}
session_language_hints: Dict[str, str] = {}
session_speculative_cache: Dict[str, Dict[str, Any]] = {}

@router.websocket("/ws/voice")
async def voice_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id, conv_id = turn_manager.get_or_create_session()
    current_turn_id = turn_manager.start_new_turn(session_id)
    session_audio_buffers[session_id] = bytearray()
    session_language_hints[session_id] = "hi-IN"
    
    logger.info(f"WebSocket voice session connected: {session_id}")

    try:
        while True:
            msg = await websocket.receive()

            # --- Binary Audio Chunk Processing ---
            if "bytes" in msg and msg["bytes"]:
                audio_bytes = msg["bytes"]
                
                # Instant Barge-In Detection: User sends audio frames while previous turn is active
                if not turn_manager.is_turn_active(session_id, current_turn_id):
                    current_turn_id = turn_manager.start_new_turn(session_id)
                    session_audio_buffers[session_id] = bytearray()

                session_audio_buffers[session_id].extend(audio_bytes)

                # Real-time incremental STT stream attempt
                async def handle_transcript_state(state: TranscriptState):
                    if state.text and turn_manager.is_turn_active(session_id, current_turn_id):
                        await websocket.send_json(WSServerMessage(
                            type="TRANSCRIPT_PARTIAL",
                            session_id=session_id,
                            conversation_id=conv_id,
                            turn_id=current_turn_id,
                            text=state.text,
                            language=state.language,
                            timestamp_ms=time.time() * 1000
                        ).model_dump())

                        # Speculative Retrieval: Start background retrieval on stable partial transcripts
                        stability = stability_detector.evaluate_transcript(state.text)
                        if stability.is_stable:
                            async def run_speculation():
                                try:
                                    t0_spec = time.perf_counter_ns()
                                    q_vec = _fast_embedder.embed_texts([state.text])[0]
                                    cands, audit = await hybrid_retriever.hybrid_retrieve(
                                        query_text=state.text, query_vector=q_vec, top_k=5, language=state.language
                                    )
                                    dt_spec_ms = (time.perf_counter_ns() - t0_spec) / 1_000_000.0
                                    session_speculative_cache[session_id] = {
                                        "query": state.text,
                                        "candidates": cands,
                                        "audit": audit,
                                        "saved_ms": dt_spec_ms
                                    }
                                except Exception as err:
                                    logger.warning(f"Speculative retrieval warning: {err}")

                            spec_task = asyncio.create_task(run_speculation())
                            turn_manager.register_task(current_turn_id, spec_task)

                await stt_session_manager.stream_audio_chunk(audio_bytes, handle_transcript_state)

            # --- Text Control Frame Processing ---
            elif "text" in msg and msg["text"]:
                data = json.loads(msg["text"])
                msg_type = data.get("type")

                if msg_type == "START_STREAM":
                    current_turn_id = turn_manager.start_new_turn(session_id)
                    session_audio_buffers[session_id] = bytearray()
                    session_language_hints[session_id] = data.get("language_hint", "hi-IN")
                    await websocket.send_json(WSServerMessage(
                        type="STREAM_STARTED",
                        session_id=session_id,
                        conversation_id=conv_id,
                        turn_id=current_turn_id
                    ).model_dump())

                elif msg_type == "BARGE_IN":
                    turn_manager.cancel_turn(current_turn_id, reason="User Barge-In")
                    current_turn_id = turn_manager.start_new_turn(session_id)
                    session_audio_buffers[session_id] = bytearray()
                    session_speculative_cache.pop(session_id, None)
                    await websocket.send_json(WSServerMessage(
                        type="TURN_CANCELLED",
                        session_id=session_id,
                        conversation_id=conv_id,
                        turn_id=current_turn_id,
                        error_message="Barge-in: Turn cancelled immediately."
                    ).model_dump())

                elif msg_type == "CANCEL_TURN":
                    turn_id_to_cancel = data.get("turn_id") or current_turn_id
                    turn_manager.cancel_turn(turn_id_to_cancel, reason="Explicit client cancel")
                    await websocket.send_json(WSServerMessage(
                        type="TURN_CANCELLED",
                        session_id=session_id,
                        conversation_id=conv_id,
                        turn_id=turn_id_to_cancel
                    ).model_dump())

                elif msg_type == "PING":
                    await websocket.send_json(WSServerMessage(type="PONG").model_dump())

                elif msg_type in ["AUDIO_END", "VOICE_QUERY"]:
                    lang_hint = data.get("language_hint") or session_language_hints.get(session_id, "hi-IN")
                    buf = bytes(session_audio_buffers.get(session_id, b""))
                    
                    # Transcribe accumulated audio buffer
                    if buf:
                        stt_state = await stt_session_manager.finalize_stream(buf, language_hint=lang_hint)
                        query_text = stt_state.text
                        detected_lang = stt_state.language
                    else:
                        query_text = data.get("query", "")
                        detected_lang = lang_hint.split("-")[0]

                    if query_text:
                        await websocket.send_json(WSServerMessage(
                            type="TRANSCRIPT_FINAL",
                            session_id=session_id,
                            conversation_id=conv_id,
                            turn_id=current_turn_id,
                            text=query_text,
                            language=detected_lang,
                            timestamp_ms=time.time() * 1000
                        ).model_dump())

                        req = QueryRequest(query=query_text, language=detected_lang)
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

                            # Stream TTS Audio Chunks
                            await websocket.send_json(WSServerMessage(
                                type="TTS_START",
                                session_id=session_id,
                                conversation_id=conv_id,
                                turn_id=current_turn_id
                            ).model_dump())

                            first_chunk_sent = False
                            async for chunk in tts_session_manager.stream_tts(resp.answer, resp.language):
                                if not turn_manager.is_turn_active(session_id, current_turn_id):
                                    break
                                if not first_chunk_sent:
                                    await websocket.send_json(WSServerMessage(
                                        type="TTS_FIRST_AUDIO",
                                        turn_id=current_turn_id
                                    ).model_dump())
                                    first_chunk_sent = True
                                await websocket.send_bytes(chunk)

                            if turn_manager.is_turn_active(session_id, current_turn_id):
                                await websocket.send_json(WSServerMessage(
                                    type="TTS_END",
                                    turn_id=current_turn_id
                                ).model_dump())
                    
                    # Reset audio buffer
                    session_audio_buffers[session_id] = bytearray()
                    session_speculative_cache.pop(session_id, None)

                elif msg_type == "TEXT_QUERY":
                    query_text = data.get("query", "")
                    lang = data.get("language", "hi")

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

                        await websocket.send_json(WSServerMessage(
                            type="TTS_START",
                            turn_id=current_turn_id
                        ).model_dump())

                        first_chunk_sent = False
                        async for chunk in tts_session_manager.stream_tts(resp.answer, resp.language):
                            if not turn_manager.is_turn_active(session_id, current_turn_id):
                                break
                            if not first_chunk_sent:
                                await websocket.send_json(WSServerMessage(
                                    type="TTS_FIRST_AUDIO",
                                    turn_id=current_turn_id
                                ).model_dump())
                                first_chunk_sent = True
                            await websocket.send_bytes(chunk)

                        if turn_manager.is_turn_active(session_id, current_turn_id):
                            await websocket.send_json(WSServerMessage(
                                type="TTS_END",
                                turn_id=current_turn_id
                            ).model_dump())

    except WebSocketDisconnect:
        logger.info(f"WebSocket voice session closed: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error in session {session_id}: {e}")
        try:
            await websocket.send_json(WSServerMessage(
                type="ERROR",
                session_id=session_id,
                turn_id=current_turn_id,
                error_message=f"Voice processing error: {str(e)}"
            ).model_dump())
        except Exception:
            pass
    finally:
        session_audio_buffers.pop(session_id, None)
        session_language_hints.pop(session_id, None)
        session_speculative_cache.pop(session_id, None)
        turn_manager.cleanup_session(session_id)
