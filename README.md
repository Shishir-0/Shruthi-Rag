# SHRUTI — OpenAI Realtime Voice-First Multilingual RAG System

> Audited Production Submission for **HH Goa 2026 Task #2**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2.35-black.svg)](https://nextjs.org)
[![OpenAI Realtime](https://img.shields.io/badge/Voice-OpenAI%20Realtime-412991.svg)](https://platform.openai.com/docs/guides/realtime)
[![Qdrant](https://img.shields.io/badge/VectorDB-Qdrant-red.svg)](https://qdrant.tech)
[![Audit Status](https://img.shields.io/badge/Migration--Audit-VERIFIED-brightgreen.svg)](reports/final-openai-migration-audit.md)

---

## 1. System Architecture Overview

**SHRUTI** is an explainable, multilingual, voice-first Retrieval-Augmented Generation (RAG) system built for Indian language speakers across Hindi (`hi-IN`), Gujarati (`gu-IN`), Bengali (`bn-IN`), Tamil (`ta-IN`), and English (`en-IN`).

The voice architecture leverages the **OpenAI Realtime API** for native speech-to-speech interactions over WebRTC/WebSockets, integrated directly into the **HH Goa MSMARCO-XI RAG Core (Qdrant + BM25)** via native **Function Calling (`retrieve_documents`)**:

```
Browser Microphone (AudioEngine.ts)
        │
        ▼
WebRTC / WebSocket Audio Stream (16 kHz PCM)
        │
        ▼
OpenAI Realtime API
(STT + Server VAD + Turn Detection)
        │
        ▼
Live Partial Transcript
        │
        ▼
Query Stability Detector
        │
        ▼
Speculative Retrieval (Qdrant + BM25)
        │
        ▼
Function Call (`retrieve_documents`)
        │
        ├──────────────┐
        ▼              ▼
      BM25         Dense Search (Qdrant)
        │              │
        └──────┬───────┘
               ▼
        Reciprocal Rank Fusion (RRF)
               ▼
        Adaptive Reranking
               ▼
        Context Assembly
               ▼
     Grounding Verification
               ▼
       Trusted Tier-1 Evidence
               │
               ▼
OpenAI Realtime Audio Response (PCM16 24kHz)
               ▼
Browser Streaming Playback & Interruption Handling
```

---

## 2. Key Technical Innovations

1. **Ephemeral Session Security (`GET /api/v1/realtime/session`)**: Mints temporary session tokens via OpenAI API (`POST https://api.openai.com/v1/realtime/sessions`) so the production `OPENAI_API_KEY` is **never exposed** to browser clients.
2. **Function Calling RAG (`retrieve_documents`)**: Registers tool calls with OpenAI Realtime so factual queries invoke FastAPI's `FastPathEngine` to search Qdrant + BM25, format citations, and verify grounding before spoken responses are generated.
3. **Speculative Retrieval**: `QueryStabilityDetector` evaluates streaming partial transcripts to pre-fetch vector & keyword candidates in parallel.
4. **Barge-In Interruption**: Supports local audio queue cancellation and server turn truncation in **<100ms** when user speech is detected during playback.
5. **Grounded Citation Verification**: Validates claims against retrieved passages from MSMARCO-XI, refusing ungrounded hallucinatory responses.

---

## 3. HH Goa 2026 Task #2 Compliance Matrix

| Requirement | SHRUTI Status | Implementation Details |
| :--- | :--- | :--- |
| **OpenAI Realtime API** | **PASS** | Native Speech-to-Speech via `openai_realtime.py` & `ws_voice.py` |
| **Ephemeral Session Security** | **PASS** | Token minting endpoint `GET /api/v1/realtime/session` |
| **Function Calling RAG** | **PASS** | `retrieve_documents` tool registered with OpenAI Realtime |
| **Vector DB Retrieval** | **PASS** | Qdrant Vector Collection `shruti_msmarco` + BM25 Okapi RRF |
| **Barge-In Interruption** | **PASS** | Instant turn cancellation & playback interrupt <100ms |
| **Speculative Retrieval** | **PASS** | Stability detection & concurrent retrieval pre-fetch (`query_stability.py`) |
| **Guardrails & Grounding** | **PASS** | `GuardrailEngine` & `GroundingVerifier` factual claim validator |
| **Multilingual Support** | **PASS** | Hindi, Gujarati, Bengali, Tamil, English, and code-mixed speech |

---

## 4. API Endpoints & Health Verification

- `GET /health/live`: Process liveness check (`ALIVE`).
- `GET /health/ready`: Qdrant connectivity and index loading check.
- `GET /health/providers`: Honest verification of OpenAI API reachability (`https://api.openai.com/v1/models`) and Qdrant readiness.
- `GET /api/v1/realtime/session`: Ephemeral session token generation for browser WebRTC/WebSocket.
- `WS /ws/voice`: Bidirectional real-time voice streaming endpoint.

---

## 5. Quick Start & Execution

### Environment Setup
Copy `.env.example` to `.env`:
```bash
OPENAI_API_KEY=your_real_openai_api_key
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-10-01
QDRANT_URL=http://localhost:6333
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
SHRUTI_TEST_MODE=false
```

### Backend API Server
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Next.js Web App
```bash
cd frontend
npm install
npm run build
npm run dev
```

### Benchmarks & Validation
```bash
python scripts/run_tests.py
python scripts/benchmark_voice_realtime.py
python scripts/run_full_benchmark.py
```

### Docker Compose
```bash
docker-compose up --build
```
