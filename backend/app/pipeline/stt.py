"""
SHRUTI — OpenAI STT Engine
Handles voice transcription using OpenAI Whisper API for Indian languages (Hindi, Gujarati, Bengali, Tamil, English).
"""
import time
import uuid
import logging
from typing import Optional
from fastapi import HTTPException
import httpx

from backend.app.config import settings
from backend.app.schemas import TranscriptionResponse

logger = logging.getLogger(__name__)

OPENAI_TRANSCRIPTION_URL = "https://api.openai.com/v1/audio/transcriptions"

class OpenAISTTEngine:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY

    async def transcribe_audio(
        self, audio_bytes: bytes, language_hint: str = "hi", mime_type: str = "audio/wav"
    ) -> TranscriptionResponse:
        start_time = time.perf_counter()
        req_id = f"stt_{uuid.uuid4().hex[:10]}"
        api_key = self.api_key or settings.OPENAI_API_KEY
        lang_short = language_hint.split("-")[0] if "-" in language_hint else language_hint

        if api_key and len(api_key) > 5 and not settings.SHRUTI_TEST_MODE:
            try:
                headers = {"Authorization": f"Bearer {api_key}"}
                files = {"file": ("speech.wav", audio_bytes, mime_type)}
                data = {"model": "whisper-1", "language": lang_short}

                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(OPENAI_TRANSCRIPTION_URL, headers=headers, files=files, data=data)
                    if resp.status_code == 200:
                        res_data = resp.json()
                        duration_ms = (time.perf_counter() - start_time) * 1000.0
                        return TranscriptionResponse(
                            text=res_data.get("text", ""),
                            language=language_hint,
                            confidence=0.98,
                            duration_ms=round(duration_ms, 2),
                            provider="openai_whisper",
                            request_id=req_id
                        )
                    else:
                        logger.error(f"OpenAI Whisper STT status {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.error(f"OpenAI Whisper STT API call failed: {e}")

        # Guard emulator: Only allow test fallback if SHRUTI_TEST_MODE=True
        if settings.SHRUTI_TEST_MODE:
            duration_ms = (time.perf_counter() - start_time) * 1000.0 + 12.5
            mock_transcripts = {
                "hi-IN": "आयुष्मान भारत डिजिटल मिशन क्या है?",
                "hi": "आयुष्मान भारत डिजिटल मिशन क्या है?",
                "gu-IN": "ગિફ્ટ સિટી ગાંધીનગર ક્યાં આવેલું છે?",
                "gu": "ગિફ્ટ સિટી ગાંધીનગર ક્યાં આવેલું છે?",
                "bn-IN": "সুন্দরবন ম্যানগ্রোভ বন কোথায় অবস্থিত?",
                "bn": "সুন্দরবন ম্যানগ্রোভ বন কোথায় অবস্থিত?",
                "ta-IN": "தஞ்சாவூர் பிருகதீஸ்வரர் கோவில் யார் கட்டியது?",
                "ta": "தஞ்சாவூர் பிருகதீஸ்வரர் கோவில் யார் கட்டியது?",
                "en-IN": "What is the renewable energy target of India by 2030?",
                "en": "What is the renewable energy target of India by 2030?"
            }
            transcript_text = mock_transcripts.get(language_hint, mock_transcripts.get(lang_short, mock_transcripts["hi-IN"]))

            return TranscriptionResponse(
                text=transcript_text,
                language=language_hint,
                confidence=0.97,
                duration_ms=round(duration_ms, 2),
                provider="openai_test_emulator",
                request_id=req_id
            )

        raise HTTPException(
            status_code=502,
            detail="OpenAI Whisper STT service unavailable and OPENAI_API_KEY is not configured."
        )

stt_engine = OpenAISTTEngine()
