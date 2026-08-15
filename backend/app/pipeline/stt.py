"""
SHRUTI — Sarvam Saaras v3 REST STT Engine
Handles voice transcription for Indian languages (Hindi, Gujarati, Bengali, Tamil, English).
"""
import time
import uuid
import base64
from typing import Optional, Dict, Any
from fastapi import HTTPException
from backend.app.config import settings
from backend.app.schemas import TranscriptionResponse
from backend.app.pipeline.http_client import get_http_client

SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"

class SarvamSTTEngine:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SARVAM_API_KEY

    async def transcribe_audio(
        self, audio_bytes: bytes, language_hint: str = "hi-IN", mime_type: str = "audio/wav"
    ) -> TranscriptionResponse:
        start_time = time.perf_counter()
        req_id = f"stt_{uuid.uuid4().hex[:10]}"
        api_key = self.api_key or settings.SARVAM_API_KEY

        if api_key and len(api_key) > 5:
            try:
                headers = {"api-subscription-key": api_key}
                files = {"file": ("speech.wav", audio_bytes, mime_type)}
                data = {"model": "saaras:v3", "language_code": language_hint}

                client = get_http_client()
                resp = await client.post(SARVAM_STT_URL, headers=headers, files=files, data=data)
                if resp.status_code == 200:
                    res_data = resp.json()
                    duration_ms = (time.perf_counter() - start_time) * 1000.0
                    return TranscriptionResponse(
                        text=res_data.get("transcript", ""),
                        language=res_data.get("language_code", language_hint),
                        confidence=res_data.get("confidence", 0.96),
                        duration_ms=round(duration_ms, 2),
                        provider="sarvam",
                        request_id=req_id
                    )
                else:
                    print(f"[!] Sarvam STT returned status {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"[!] Sarvam STT API call failed: {e}")

        # Guard emulator: Only allow test fallback if SHRUTI_TEST_MODE=True
        if settings.SHRUTI_TEST_MODE:
            duration_ms = (time.perf_counter() - start_time) * 1000.0 + 12.5
            mock_transcripts = {
                "hi-IN": "आयुष्मान भारत डिजिटल मिशन क्या है?",
                "gu-IN": "ગિફ્ટ સિટી ગાંધીનગર ક્યાં આવેલું છે?",
                "bn-IN": "সুন্দরবন ম্যানগ্রোভ বন কোথায় অবস্থিত?",
                "ta-IN": "தஞ்சாவூர் பிருகதீஸ்வரர் கோவில் யார் கட்டியது?",
                "en-IN": "What is the renewable energy target of India by 2030?"
            }
            transcript_text = mock_transcripts.get(language_hint, mock_transcripts["hi-IN"])

            return TranscriptionResponse(
                text=transcript_text,
                language=language_hint,
                confidence=0.97,
                duration_ms=round(duration_ms, 2),
                provider="sarvam_test_emulator",
                request_id=req_id
            )

        raise HTTPException(
            status_code=502,
            detail="Sarvam STT service unavailable and SARVAM_API_KEY is not configured."
        )

stt_engine = SarvamSTTEngine()
