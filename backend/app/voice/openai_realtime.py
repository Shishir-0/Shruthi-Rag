"""
SHRUTI OpenAI Realtime API Client Manager
Manages WebSocket sessions to wss://api.openai.com/v1/realtime
Handles bidirectional audio streaming, streaming transcription, function calling tool execution (retrieve_documents), and audio output generation.
"""
import os
import json
import time
import asyncio
import logging
import websockets
from typing import Dict, Any, Optional, Callable, AsyncGenerator

from backend.app.config import settings
from backend.app.schemas import QueryRequest, CitationItem
from backend.app.pipeline.fast_path import fast_path_engine
from backend.app.pipeline.query_stability import stability_detector
from backend.app.voice.turn_manager import turn_manager

logger = logging.getLogger(__name__)

RETRIEVE_DOCUMENTS_TOOL = {
    "type": "function",
    "name": "retrieve_documents",
    "description": "Searches HH Goa MSMARCO-XI Qdrant + BM25 hybrid vector database for grounded context evidence.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Clean search query extracted from user voice input."
            }
        },
        "required": ["query"]
    }
}

class OpenAIRealtimeSession:
    def __init__(self, session_id: str, conversation_id: str):
        self.session_id = session_id
        self.conversation_id = conversation_id
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_active = False
        self.model = settings.OPENAI_REALTIME_MODEL
        self.api_key = settings.OPENAI_API_KEY
        self.ws_url = f"wss://api.openai.com/v1/realtime?model={self.model}"
        self.speculative_cache: Dict[str, Any] = {}
        self._listener_task: Optional[asyncio.Task] = None

    async def connect(self) -> bool:
        """Establishes WebSocket connection to OpenAI Realtime API."""
        if not self.api_key or len(self.api_key) < 5:
            if settings.SHRUTI_TEST_MODE:
                logger.info("OpenAIRealtimeSession initialized in TEST MODE.")
                self.is_active = True
                return True
            logger.error("OPENAI_API_KEY is not set.")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "OpenAI-Beta": "realtime=v1"
            }
            self.ws = await websockets.connect(self.ws_url, extra_headers=headers)
            self.is_active = True
            
            # Configure Session
            await self._send_session_update()
            logger.info(f"OpenAIRealtimeSession connected successfully for session {self.session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to OpenAI Realtime API: {e}")
            self.is_active = False
            return False

    async def _send_session_update(self):
        """Sends session configuration parameters to OpenAI Realtime API."""
        if not self.ws:
            return
        
        payload = {
            "type": "session.update",
            "session": {
                "modalities": ["audio", "text"],
                "instructions": (
                    "You are SHRUTI, a voice-first multilingual assistant for India. "
                    "You MUST call retrieve_documents tool for factual knowledge queries. "
                    "Always reply concisely in the user's language."
                ),
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                "tools": [RETRIEVE_DOCUMENTS_TOOL],
                "tool_choice": "auto"
            }
        }
        await self.ws.send(json.dumps(payload))

    async def send_audio_chunk(self, pcm_base64: str):
        """Sends base64-encoded PCM16 audio input to OpenAI Realtime API."""
        if self.ws and self.is_active:
            try:
                msg = {
                    "type": "input_audio_buffer.append",
                    "audio": pcm_base64
                }
                await self.ws.send(json.dumps(msg))
            except Exception as e:
                logger.error(f"Error sending audio to OpenAI: {e}")

    async def send_barge_in(self):
        """Sends interruption / turn cancel event to OpenAI Realtime API."""
        if self.ws and self.is_active:
            try:
                msg = {"type": "response.cancel"}
                await self.ws.send(json.dumps(msg))
                msg_clear = {"type": "input_audio_buffer.clear"}
                await self.ws.send(json.dumps(msg_clear))
            except Exception as e:
                logger.warning(f"Barge-in signal error: {e}")

    async def close(self):
        """Closes session and cleans up WebSocket resources."""
        self.is_active = False
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None
        logger.info(f"OpenAIRealtimeSession closed for {self.session_id}")

class OpenAIRealtimeManager:
    def __init__(self):
        self.sessions: Dict[str, OpenAIRealtimeSession] = {}

    async def get_or_create_session(self, session_id: str, conv_id: str) -> OpenAIRealtimeSession:
        if session_id not in self.sessions:
            sess = OpenAIRealtimeSession(session_id, conv_id)
            await sess.connect()
            self.sessions[session_id] = sess
        return self.sessions[session_id]

    def remove_session(self, session_id: str):
        if session_id in self.sessions:
            sess = self.sessions.pop(session_id)
            asyncio.create_task(sess.close())

openai_realtime_manager = OpenAIRealtimeManager()
