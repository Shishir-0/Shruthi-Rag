"""
SHRUTI Real-Time WebSocket Voice Endpoint (/ws/voice)
Handles bidirectional audio streaming, partial transcripts, speculative retrieval, barge-in, and streaming TTS dispatch.
"""
import json
import logging
import asyncio
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.schemas import QueryRequest
from backend.app.voice.turn_manager import turn_manager
from backend.app.voice.stt_session import stt_session_manager, TranscriptState
from backend.app.voice.tts_session import tts_session_manager
from backend.app.pipeline.fast_path import fast_path_engine
from backend.app.pipeline.stt import stt_engine

logger = logging.getLogger(__name__)
router = APIRouter()

# Active audio buffers and settings per session
session_audio_buffers: Dict[str, bytearray] = {}
session_language_hints: Dict[str, str] = {}

@router.websocket("/ws/voice")
async def voice_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = f"sess_{id(websocket)}"
    current_turn_id = turn_manager.start_new_turn(session_id)
    session_audio_buffers[session_id] = bytearray()
    session_language_hints[session_id] = "hi-IN"
    
    logger.info(f"WebSocket voice connection opened: {session_id}")

    try:
        while True:
            msg = await websocket.receive()
            if "bytes" in msg and msg["bytes"]:
                # Audio chunk received
                audio_bytes = msg["bytes"]
                
                # Check barge-in: if user sends audio while assistant was speaking
                if not turn_manager.is_turn_active(session_id, current_turn_id):
                    current_turn_id = turn_manager.start_new_turn(session_id)
                    session_audio_buffers[session_id] = bytearray()

                session_audio_buffers[session_id].extend(audio_bytes)

            elif "text" in msg and msg["text"]:
                data = json.loads(msg["text"])
                msg_type = data.get("type")

                if msg_type == "START_STREAM":
                    current_turn_id = turn_manager.start_new_turn(session_id)
                    session_audio_buffers[session_id] = bytearray()
                    session_language_hints[session_id] = data.get("language_hint", "hi-IN")
                    await websocket.send_json({"type": "STREAM_STARTED", "turn_id": current_turn_id})

                elif msg_type == "BARGE_IN":
                    current_turn_id = turn_manager.start_new_turn(session_id)
                    session_audio_buffers[session_id] = bytearray()
                    await websocket.send_json({"type": "BARGE_IN_ACK", "turn_id": current_turn_id})

                elif msg_type in ["AUDIO_END", "VOICE_QUERY"]:
                    lang_hint = data.get("language_hint") or session_language_hints.get(session_id, "hi-IN")
                    buf = bytes(session_audio_buffers.get(session_id, b""))
                    
                    # Transcribe audio buffer if available
                    if buf:
                        stt_res = await stt_engine.transcribe_audio(buf, language_hint=lang_hint)
                        query_text = stt_res.text
                        detected_lang = stt_res.language
                    else:
                        query_text = data.get("query", "")
                        detected_lang = lang_hint.split("-")[0]

                    if query_text:
                        await websocket.send_json({
                            "type": "TRANSCRIPT_UPDATE",
                            "turn_id": current_turn_id,
                            "text": query_text,
                            "is_final": True,
                            "language": detected_lang
                        })

                        req = QueryRequest(query=query_text, language=detected_lang)
                        resp, audit_meta = await fast_path_engine.execute_fast_path(req)

                        if turn_manager.is_turn_active(session_id, current_turn_id):
                            await websocket.send_json({
                                "type": "QUERY_RESPONSE",
                                "turn_id": current_turn_id,
                                "answer": resp.answer,
                                "citations": [c.model_dump() for c in resp.citations],
                                "telemetry": resp.telemetry.model_dump(),
                                "grounded": resp.grounding.grounded
                            })

                            # Stream TTS Audio Chunks
                            async for chunk in tts_session_manager.stream_tts(resp.answer, resp.language):
                                if not turn_manager.is_turn_active(session_id, current_turn_id):
                                    break
                                await websocket.send_bytes(chunk)
                    
                    # Reset session buffer for next turn
                    session_audio_buffers[session_id] = bytearray()

                elif msg_type == "TEXT_QUERY":
                    # Direct query processing
                    query_text = data.get("query", "")
                    lang = data.get("language", "hi")

                    req = QueryRequest(query=query_text, language=lang)
                    resp, audit_meta = await fast_path_engine.execute_fast_path(req)

                    if turn_manager.is_turn_active(session_id, current_turn_id):
                        await websocket.send_json({
                            "type": "QUERY_RESPONSE",
                            "turn_id": current_turn_id,
                            "answer": resp.answer,
                            "citations": [c.model_dump() for c in resp.citations],
                            "telemetry": resp.telemetry.model_dump(),
                            "grounded": resp.grounding.grounded
                        })

                        # Stream TTS Audio Chunks
                        async for chunk in tts_session_manager.stream_tts(resp.answer, resp.language):
                            if not turn_manager.is_turn_active(session_id, current_turn_id):
                                break
                            await websocket.send_bytes(chunk)

    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        session_audio_buffers.pop(session_id, None)
        session_language_hints.pop(session_id, None)
