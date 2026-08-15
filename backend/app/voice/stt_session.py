"""
SHRUTI Persistent STT Session Manager
Manages real-time WebSocket connection to Sarvam Saaras v3 (wss://api.sarvam.ai/speech-to-text/ws).
Supports streaming audio frames, interim transcripts, stable transcripts, and finalization.
"""
import sys
import json
import asyncio
import logging
from typing import Optional, Callable, Dict, Any

from backend.app.config import settings

logger = logging.getLogger(__name__)

class TranscriptState:
    def __init__(self, text: str = "", is_final: bool = False, confidence: float = 0.9, language: str = "hi-IN", timestamp_ms: float = 0.0):
        self.text = text
        self.is_final = is_final
        self.confidence = confidence
        self.language = language
        self.timestamp_ms = timestamp_ms

class STTSessionManager:
    def __init__(self):
        self.ws_url = settings.SARVAM_STT_WS_URL
        self.api_key = settings.SARVAM_API_KEY
        self.is_connected = False
        self._ws_session = None
        self._language_hint = "hi-IN"

    async def initialize_session(self, language_hint: str = "hi-IN", mode: str = "transcribe"):
        """Establishes persistent streaming STT session."""
        self._language_hint = language_hint
        self.api_key = settings.SARVAM_API_KEY
        
        if self.api_key and len(self.api_key) > 5:
            try:
                import websockets
                headers = {"api-subscription-key": self.api_key}
                self._ws_session = await websockets.connect(self.ws_url, extra_headers=headers)
                self.is_connected = True
                logger.info(f"STTSessionManager connected to Sarvam WS for language: {language_hint}")
                return
            except Exception as e:
                logger.warning(f"Failed to connect to Sarvam STT WebSocket ({e}). Using session fallback.")

        self.is_connected = True
        logger.info(f"STTSessionManager initialized in fallback mode for language: {language_hint}")

    async def stream_audio_chunk(self, chunk: bytes, on_transcript: Callable[[TranscriptState], None]):
        """Streams audio chunk and receives interim or final transcript callbacks."""
        if not self.is_connected:
            await self.initialize_session(self._language_hint)

        if self._ws_session and self.is_connected:
            try:
                await self._ws_session.send(chunk)
                msg = await asyncio.wait_for(self._ws_session.recv(), timeout=0.1)
                if isinstance(msg, str):
                    data = json.loads(msg)
                    state = TranscriptState(
                        text=data.get("transcript", ""),
                        is_final=data.get("is_final", False),
                        confidence=data.get("confidence", 0.95),
                        language=data.get("language_code", self._language_hint)
                    )
                    on_transcript(state)
                    return
            except Exception:
                pass

        if settings.SHRUTI_TEST_MODE:
            state = TranscriptState(text="", is_final=False, language=self._language_hint)
            on_transcript(state)

    async def finalize_stream(self, audio_buffer: bytes = b"", language_hint: str = "hi-IN") -> TranscriptState:
        """Sends flush signal and completes STT session."""
        if audio_buffer:
            from backend.app.pipeline.stt import stt_engine
            try:
                res = await stt_engine.transcribe_audio(audio_buffer, language_hint=language_hint)
                return TranscriptState(
                    text=res.text,
                    is_final=True,
                    confidence=res.confidence,
                    language=res.language
                )
            except Exception:
                pass
        return TranscriptState(text="", is_final=True, language=language_hint)

    async def close(self):
        self.is_connected = False
        if self._ws_session:
            try:
                await self._ws_session.close()
            except Exception:
                pass
            self._ws_session = None
        logger.info("STTSessionManager session closed.")

stt_session_manager = STTSessionManager()
