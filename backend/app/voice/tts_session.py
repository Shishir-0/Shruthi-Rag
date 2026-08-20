"""
SHRUTI Persistent TTS Session Manager
Manages real-time streaming TTS audio generation using OpenAI Speech API.
"""
import sys
import json
import base64
import asyncio
import logging
from typing import AsyncGenerator, Optional

from backend.app.config import settings
from backend.app.pipeline.tts import tts_engine

logger = logging.getLogger(__name__)

class TTSSessionManager:
    def __init__(self):
        self.model = "tts-1"

    async def stream_tts(
        self, text: str, language: str = "hi-IN", speaker: Optional[str] = "alloy"
    ) -> AsyncGenerator[bytes, None]:
        """Streams audio chunks for immediate browser playback."""
        if not text:
            return

        res = await tts_engine.synthesize_speech(text, language=language, voice=speaker)
        if res.audio_base64:
            raw_bytes = base64.b64decode(res.audio_base64)
            chunk_size = 4096
            for i in range(0, len(raw_bytes), chunk_size):
                yield raw_bytes[i:i + chunk_size]
                await asyncio.sleep(0.005)
            return

        if settings.SHRUTI_TEST_MODE:
            dummy_chunk = b"ID3\x04\x00\x00\x00\x00\x00#TSSE\x00\x00\x00\x0f\x00\x00Lavf58.76.100" + b"\x00" * 1024
            for _ in range(3):
                yield dummy_chunk
                await asyncio.sleep(0.01)

tts_session_manager = TTSSessionManager()
