# SHRUTI Final Bug Audit & Resolution Matrix

> **Verification Matrix of Resolved Codebase Bugs**

| Bug ID | Description | Component / File | Fix Applied | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **BUG 1** | STTSessionManager was a placeholder | `backend/app/voice/stt_session.py` | Implemented real Sarvam Saaras v3 WebSocket streaming client with reconnect, audio chunk transmission, and transcript callbacks. Test fallbacks guarded strictly behind `SHRUTI_TEST_MODE=true`. | **RESOLVED & VERIFIED** |
| **BUG 2** | TTSSessionManager generated fake WAV bytes | `backend/app/voice/tts_session.py` | Implemented real Sarvam Bulbul v3 streaming TTS with 4KB audio chunk streaming. Test fallbacks guarded strictly behind `SHRUTI_TEST_MODE=true`. | **RESOLVED & VERIFIED** |
| **BUG 3** | WebSocket voice endpoint ran batch STT | `backend/app/api/ws_voice.py` | Replaced batch accumulation with full real-time protocol handling `START_STREAM`, binary `AUDIO_CHUNK`, `TRANSCRIPT_PARTIAL`, `TRANSCRIPT_FINAL`, `QUERY_RESPONSE`, and `TTS_START`/`TTS_FIRST_AUDIO`/`TTS_END`. | **RESOLVED & VERIFIED** |
| **BUG 4** | REST STT silent emulator fallback | `backend/app/pipeline/stt.py` | Removed automatic emulator fallback in production mode. Service returns structured HTTP 502 error if credentials are missing unless `SHRUTI_TEST_MODE=true`. | **RESOLVED & VERIFIED** |
| **BUG 5** | REST TTS silent WAV emulator fallback | `backend/app/pipeline/tts.py` | Removed automatic fake WAV generation in production mode. Returns structured `audio_base64=None` with provider `"unavailable"` if API key is unconfigured. | **RESOLVED & VERIFIED** |
| **BUG 6** | Frontend voice recorder used batch MediaRecorder blob | `frontend/src/components/VoiceRecorder.tsx` | Replaced batch MediaRecorder with `AudioEngine` downsampling 16kHz PCM audio frames and streaming via `VoiceWebSocketClient`. | **RESOLVED & VERIFIED** |
| **BUG 7** | Frontend page used batch `sendVoiceQuery(blob)` | `frontend/src/app/page.tsx` | Integrated `VoiceWebSocketClient` real-time state machine (`IDLE`, `CONNECTING`, `LISTENING`, `TRANSCRIBING`, `THINKING`, `ANSWER_READY`, `SPEAKING`, `BARGE_IN`, `ERROR`). | **RESOLVED & VERIFIED** |
| **BUG 8** | CORS wildcard `allow_origins=["*"]` with credentials | `backend/app/main.py` | Replaced wildcard with environment-controlled `CORS_ORIGINS` whitelist. | **RESOLVED & VERIFIED** |
| **BUG 9** | Dishonest health endpoints | `backend/app/main.py` | Implemented `/health/live`, `/health/ready` (checking Qdrant & indexes), and `/health/providers`. | **RESOLVED & VERIFIED** |
| **BUG 10** | Unmanaged `httpx.AsyncClient` allocation per request | `backend/app/pipeline/http_client.py` | Implemented shared, connection-pooled HTTP client with lifecycle management and connection limits. | **RESOLVED & VERIFIED** |
