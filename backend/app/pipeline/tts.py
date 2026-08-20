"""
SHRUTI — OpenAI TTS Engine
Handles speech synthesis using OpenAI Audio Speech API (tts-1 / tts-1-hd).
"""
import time
import uuid
import base64
import logging
from typing import Optional
import httpx

from backend.app.config import settings
from backend.app.schemas import SynthesisResponse

logger = logging.getLogger(__name__)

OPENAI_TTS_URL = "https://api.openai.com/v1/audio/speech"

class OpenAITTSEngine:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY

    async def synthesize_speech(
        self, text: str, language: str = "hi-IN", voice: Optional[str] = "alloy"
    ) -> SynthesisResponse:
        start_time = time.perf_counter()
        api_key = self.api_key or settings.OPENAI_API_KEY
        speaker_voice = voice or "alloy"

        if api_key and len(api_key) > 5 and not settings.SHRUTI_TEST_MODE:
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "tts-1",
                    "input": text,
                    "voice": speaker_voice,
                    "response_format": "mp3"
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(OPENAI_TTS_URL, headers=headers, json=payload)
                    if resp.status_code == 200:
                        audio_b64 = base64.b64encode(resp.content).decode("utf-8")
                        duration_ms = (time.perf_counter() - start_time) * 1000.0
                        return SynthesisResponse(
                            audio_base64=audio_b64,
                            format="mp3",
                            duration_ms=round(duration_ms, 2),
                            provider="openai_tts"
                        )
                    else:
                        logger.error(f"OpenAI TTS returned status {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.error(f"OpenAI TTS API call failed: {e}")

        # Guard emulator: Only allow test fallback if SHRUTI_TEST_MODE=True
        if settings.SHRUTI_TEST_MODE:
            duration_ms = (time.perf_counter() - start_time) * 1000.0 + 8.2
            mock_mp3_b64 = "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA//5AwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            return SynthesisResponse(
                audio_base64=mock_mp3_b64,
                format="mp3",
                duration_ms=round(duration_ms, 2),
                provider="openai_test_emulator"
            )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return SynthesisResponse(
            audio_base64=None,
            format="none",
            duration_ms=round(duration_ms, 2),
            provider="unavailable"
        )

tts_engine = OpenAITTSEngine()
