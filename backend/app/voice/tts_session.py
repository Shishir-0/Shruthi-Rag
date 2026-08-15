"""
SHRUTI Persistent TTS Session Manager
Manages real-time streaming TTS audio generation for Sarvam Bulbul v3.
"""
import sys
import json
import base64
import asyncio
import logging
from typing import AsyncGenerator, Optional

from backend.app.config import settings
from backend.app.pipeline.http_client import get_http_client

logger = logging.getLogger(__name__)

VOICE_MAPPING = {
    "hi-IN": "meera",
    "hi": "meera",
    "gu-IN": "niranjan",
    "gu": "niranjan",
    "bn-IN": "shubhro",
    "bn": "shubhro",
    "ta-IN": "kavitha",
    "ta": "kavitha",
    "en-IN": "arvind",
    "en": "arvind"
}

class TTSSessionManager:
    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.model = "bulbul:v3"

    async def stream_tts(
        self, text: str, language: str = "hi-IN", speaker: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """Streams audio chunks for immediate browser playback."""
        if not text:
            return

        api_key = self.api_key or settings.SARVAM_API_KEY
        spk = speaker or VOICE_MAPPING.get(language, "meera")
        lang_code = language if "-" in language else f"{language}-IN"

        if api_key and len(api_key) > 5:
            try:
                headers = {"api-subscription-key": api_key, "Content-Type": "application/json"}
                payload = {
                    "inputs": [text],
                    "target_language_code": lang_code,
                    "speaker": spk,
                    "model": self.model
                }
                client = get_http_client()
                resp = await client.post(settings.SARVAM_TTS_URL, headers=headers, json=payload)
                if resp.status_code == 200:
                    audios = resp.json().get("audios", [])
                    if audios:
                        raw_bytes = base64.b64decode(audios[0])
                        # Stream in 4KB chunks for rapid browser playback
                        chunk_size = 4096
                        for i in range(0, len(raw_bytes), chunk_size):
                            yield raw_bytes[i:i + chunk_size]
                            await asyncio.sleep(0.005)
                        return
            except Exception as e:
                logger.error(f"Sarvam TTS streaming error: {e}")

        # Guard emulator: Only stream dummy audio in test mode
        if settings.SHRUTI_TEST_MODE:
            dummy_chunk = b"RIFF$ \x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00@\x1f\x00\x00\x80>\x00\x00\x02\x00\x10\x00data\x00 \x00\x00" + b"\x00" * 1024
            for _ in range(3):
                yield dummy_chunk
                await asyncio.sleep(0.01)

tts_session_manager = TTSSessionManager()
