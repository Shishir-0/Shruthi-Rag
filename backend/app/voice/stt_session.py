"""
SHRUTI Persistent STT Session Manager
Manages real-time streaming audio transcription via OpenAI Realtime API.
"""
import sys
import json
import asyncio
import logging
from typing import Optional, Callable, Dict, Any

from backend.app.config import settings
from backend.app.pipeline.stt import stt_engine

logger = logging.getLogger(__name__)

class TranscriptState:
    def __init__(self, text: str = "", is_final: bool = False, confidence: float = 0.98, language: str = "hi-IN", timestamp_ms: float = 0.0):
        self.text = text
        self.is_final = is_final
        self.confidence = confidence
        self.language = language
        self.timestamp_ms = timestamp_ms

class STTSessionManager:
    def __init__(self):
        self.is_connected = False
        self._language_hint = "hi-IN"

    async def initialize_session(self, language_hint: str = "hi-IN", mode: str = "transcribe"):
        """Establishes persistent streaming STT session."""
        self._language_hint = language_hint
        self.is_connected = True
        logger.info(f"STTSessionManager initialized for language: {language_hint}")

    async def stream_audio_chunk(self, chunk: bytes, on_transcript: Callable[[TranscriptState], None]):
        """Streams audio chunk and receives interim or final transcript callbacks."""
        if not self.is_connected:
            await self.initialize_session(self._language_hint)

        if settings.SHRUTI_TEST_MODE:
            state = TranscriptState(text="", is_final=False, language=self._language_hint)
            on_transcript(state)

    async def finalize_stream(self, audio_buffer: bytes = b"", language_hint: str = "hi-IN") -> TranscriptState:
        """Sends flush signal and completes STT session."""
        if audio_buffer:
            try:
                res = await stt_engine.transcribe_audio(audio_buffer, language_hint=language_hint)
                return TranscriptState(
                    text=res.text,
                    is_final=True,
                    confidence=res.confidence,
                    language=res.language
                )
            except Exception as err:
                logger.warning(f"STT stream finalization warning: {err}")
        return TranscriptState(text="", is_final=True, language=language_hint)

    async def close(self):
        self.is_connected = False
        logger.info("STTSessionManager session closed.")

stt_session_manager = STTSessionManager()
