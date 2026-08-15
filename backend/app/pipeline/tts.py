"""
SHRUTI — Sarvam Bulbul v3 TTS Engine
Handles multilingual speech synthesis for Indian languages.
"""
import time
import uuid
import base64
from typing import Optional
from backend.app.config import settings
from backend.app.schemas import SynthesisResponse
from backend.app.pipeline.http_client import get_http_client

SARVAM_TTS_URL = settings.SARVAM_TTS_URL

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

class SarvamTTSEngine:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SARVAM_API_KEY

    async def synthesize_speech(
        self, text: str, language: str = "hi-IN", voice: Optional[str] = None
    ) -> SynthesisResponse:
        start_time = time.perf_counter()
        language = language or "hi-IN"
        speaker = voice or VOICE_MAPPING.get(language, "meera")
        api_key = self.api_key or settings.SARVAM_API_KEY
        
        # Standardize language code for Sarvam
        lang_code = language if "-" in language else f"{language}-IN"

        if api_key and len(api_key) > 5:
            try:
                headers = {"api-subscription-key": api_key, "Content-Type": "application/json"}
                payload = {
                    "inputs": [text],
                    "target_language_code": lang_code,
                    "speaker": speaker,
                    "model": "bulbul:v3"
                }
                client = get_http_client()
                resp = await client.post(SARVAM_TTS_URL, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    audios = data.get("audios", [])
                    if audios:
                        duration_ms = (time.perf_counter() - start_time) * 1000.0
                        return SynthesisResponse(
                            audio_base64=audios[0],
                            format="wav",
                            duration_ms=round(duration_ms, 2),
                            provider="sarvam"
                        )
                else:
                    print(f"[!] Sarvam TTS returned status {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"[!] Sarvam TTS API call failed: {e}")

        # Guard emulator: Only allow test fallback if SHRUTI_TEST_MODE=True
        if settings.SHRUTI_TEST_MODE:
            duration_ms = (time.perf_counter() - start_time) * 1000.0 + 8.2
            mock_wav_b64 = "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="
            return SynthesisResponse(
                audio_base64=mock_wav_b64,
                format="wav",
                duration_ms=round(duration_ms, 2),
                provider="sarvam_test_emulator"
            )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return SynthesisResponse(
            audio_base64=None,
            format="none",
            duration_ms=round(duration_ms, 2),
            provider="unavailable"
        )

tts_engine = SarvamTTSEngine()
