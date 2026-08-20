"""
SHRUTI Pydantic Data Models & API Schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- STT Schemas ---
class TranscriptionRequest(BaseModel):
    audio_base64: Optional[str] = None
    language_hint: Optional[str] = "hi-IN"

class TranscriptionResponse(BaseModel):
    text: str
    language: str
    confidence: float
    duration_ms: float
    provider: str = "openai"
    request_id: str

# --- TTS Schemas ---
class SynthesisRequest(BaseModel):
    text: str
    language: str = "hi-IN"
    voice: Optional[str] = "meera"

class SynthesisResponse(BaseModel):
    audio_base64: Optional[str] = None
    format: str = "wav"
    duration_ms: float
    provider: str = "openai"

# --- RAG Citation & Context Schemas ---
class CitationItem(BaseModel):
    citation_id: str
    document_id: str
    chunk_id: str
    source: str = "MSMARCO-XI"
    title: str
    language: str
    text: str
    dense_score: float = 0.0
    bm25_score: float = 0.0
    rerank_score: float = 0.0
    final_score: float = 0.0

# --- Grounding & Guardrails Schemas ---
class GroundingReport(BaseModel):
    grounded: bool
    confidence: float
    unsupported_claims: List[str] = []
    citations_valid: bool = True
    reasoning: Optional[str] = None

class GuardrailCheck(BaseModel):
    is_safe: bool = True
    is_answerable: bool = True
    query_class: str = "ANSWERABLE" # ANSWERABLE, OFF_TOPIC, UNSAFE, AMBIGUOUS, GREETING
    rejection_reason: Optional[str] = None

# --- Latency Telemetry Schema ---
class LatencyBreakdown(BaseModel):
    audio_capture_ms: float = 0.0
    stt_ms: float = 0.0
    query_processing_ms: float = 0.0
    embedding_ms: float = 0.0
    dense_retrieval_ms: float = 0.0
    bm25_ms: float = 0.0
    reranking_ms: float = 0.0
    context_assembly_ms: float = 0.0
    generation_ms: float = 0.0
    grounding_ms: float = 0.0
    tts_ms: float = 0.0
    rag_core_ms: float = 0.0
    
    # 4-Metric Waterfall Metrics
    ttst_ms: float = 0.0      # Time To Speech Transcript
    ttr_ms: float = 0.0       # Time To Retrieval
    tta_ms: float = 0.0       # Time To Answer
    ttfa_ms: float = 0.0      # Time To First Answer (QTTA Target <100ms P50, <200ms P95)
    ttfaudio_ms: float = 0.0  # Time To First Audio (ATFA Target <350ms P50)
    ttc_ms: float = 0.0       # Time To Completion
    
    total_voice_ms: float = 0.0
    badge: str = "FAST" # FAST (<50ms), NORMAL (<150ms), SLOW

# --- Engineering Trace Schema ---
class EngineeringTrace(BaseModel):
    trace_id: str
    detected_language: str
    query_classification: str
    chunking_strategy_used: str
    dense_candidates_count: int
    bm25_candidates_count: int
    reranked_scores: List[Dict[str, Any]]
    tier_used: str # Tier 1 Extractive / Tier 2 Generative
    prompt_token_count: int = 0
    retry_count: int = 0

# --- Main Query Response Schema ---
class QueryRequest(BaseModel):
    query: str
    language: Optional[str] = None
    stream_tts: bool = False

class QueryResponse(BaseModel):
    trace_id: str
    original_query: str
    normalized_query: str
    language: str
    classification: str
    answer: str
    tier: str
    citations: List[CitationItem]
    grounding: GroundingReport
    telemetry: LatencyBreakdown
    engineering_trace: Optional[EngineeringTrace] = None
    audio_base64: Optional[str] = None

# --- Real-Time WebSocket Protocol Message Schemas ---
class WSClientMessage(BaseModel):
    type: str # START_STREAM, AUDIO_END, BARGE_IN, CANCEL_TURN, PING, TEXT_QUERY
    language_hint: Optional[str] = "hi-IN"
    query: Optional[str] = None
    language: Optional[str] = None
    turn_id: Optional[str] = None

class WSServerMessage(BaseModel):
    type: str # STREAM_STARTED, TRANSCRIPT_PARTIAL, TRANSCRIPT_STABLE, TRANSCRIPT_FINAL, QUERY_RESPONSE, TTS_START, TTS_FIRST_AUDIO, TTS_END, TURN_CANCELLED, ERROR, PONG
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    turn_id: Optional[str] = None
    trace_id: Optional[str] = None
    text: Optional[str] = None
    language: Optional[str] = None
    answer: Optional[str] = None
    citations: Optional[List[Dict[str, Any]]] = None
    telemetry: Optional[Dict[str, Any]] = None
    grounded: Optional[bool] = None
    error_message: Optional[str] = None
    timestamp_ms: Optional[float] = None
