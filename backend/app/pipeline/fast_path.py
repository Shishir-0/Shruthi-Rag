"""
SHRUTI FastPath Engine
Sub-10ms primary execution engine delivering Time To First Answer (TTFA < 100ms P50).
"""
import time
import uuid
import asyncio
from typing import Tuple, Dict, Any, Optional

from backend.app.schemas import (
    QueryRequest, QueryResponse, LatencyBreakdown, GroundingReport,
    EngineeringTrace, CitationItem
)
from backend.app.pipeline.query_processor import query_processor
from backend.app.pipeline.query_stability import stability_detector
from backend.app.pipeline.retrieval import hybrid_retriever
from backend.app.pipeline.reranker import reranker
from backend.app.pipeline.context_assembler import context_assembler
from backend.app.pipeline.answer_engine import answer_engine
from backend.app.pipeline.grounding import grounding_verifier
from backend.app.pipeline.guardrails import guardrail_engine
from backend.app.pipeline.tts import tts_engine
from backend.app.pipeline.cache import cache_engine
from scripts.build_embeddings import LightweightMultilingualProvider

_fast_embedder = LightweightMultilingualProvider()

class FastPathEngine:
    async def execute_fast_path(
        self, req: QueryRequest, disable_cache: bool = False
    ) -> Tuple[QueryResponse, Dict[str, Any]]:
        t_total_0 = time.perf_counter_ns()
        trace_id = f"shruti_tr_{uuid.uuid4().hex[:12]}"
        
        # 1. Micro-Cache Check
        if not disable_cache:
            cached_resp = cache_engine.get(req.query, req.language or "auto")
            if cached_resp:
                cached_resp.trace_id = trace_id
                t_cached_ms = (time.perf_counter_ns() - t_total_0) / 1_000_000.0
                cached_resp.telemetry.rag_core_ms = round(t_cached_ms, 3)
                return cached_resp, {"path": "MICRO_CACHE_HIT", "ttfa_ms": round(t_cached_ms, 3)}

        # 2. Query Processing & Stability Check
        t_proc_0 = time.perf_counter_ns()
        stability = stability_detector.evaluate_transcript(req.query)
        proc_res = query_processor.process(req.query)
        target_lang = req.language or proc_res["detected_language"]
        q_class = proc_res["query_type"]
        norm_query = proc_res["normalized_query"]
        retrieval_query = proc_res["retrieval_query"]
        proc_ms = (time.perf_counter_ns() - t_proc_0) / 1_000_000.0

        # Guardrail Validation
        guard_res = guardrail_engine.validate_input(norm_query, q_class)
        if not guard_res.is_answerable:
            ttfa_ms = (time.perf_counter_ns() - t_total_0) / 1_000_000.0
            return QueryResponse(
                trace_id=trace_id,
                original_query=req.query,
                normalized_query=norm_query,
                language=target_lang,
                classification=q_class,
                answer=guard_res.rejection_reason or "Question outside indexed knowledge base.",
                tier="Guardrail Refusal",
                citations=[],
                grounding=GroundingReport(
                    grounded=False, confidence=0.0, unsupported_claims=[], citations_valid=False, reasoning="Guardrail Refusal"
                ),
                telemetry=LatencyBreakdown(
                    query_processing_ms=round(proc_ms, 3),
                    rag_core_ms=round(ttfa_ms, 3),
                    total_voice_ms=round(ttfa_ms, 3),
                    badge="FAST"
                )
            ), {"path": "GUARDRAIL_REFUSAL", "ttfa_ms": round(ttfa_ms, 3)}

        # 3. Query Embedding & Concurrent Hybrid Search
        t_emb_0 = time.perf_counter_ns()
        query_vec = _fast_embedder.embed_texts([retrieval_query])[0]
        emb_ms = (time.perf_counter_ns() - t_emb_0) / 1_000_000.0

        candidates, retrieval_audit = await hybrid_retriever.hybrid_retrieve(
            query_text=retrieval_query,
            query_vector=query_vec,
            top_k=5,
            language=target_lang
        )
        retrieval_ms = retrieval_audit["total_retrieval_ms"]

        # 4. Adaptive Reranking
        reranked_candidates, rerank_ms, rerank_mode = reranker.rerank(candidates, norm_query, target_lang)

        # 5. Context Assembly & Parent-Child Reconstruction
        citations, context_prompt, assembly_ms = context_assembler.assemble_context(
            reranked_candidates, max_token_budget=600
        )

        # 6. Tier 1 Extractive Generation (Fast Path <2ms)
        context_prompt_sanitized = guardrail_engine.sanitize_retrieved_context(context_prompt)
        answer_text, tier_used, gen_ms = await answer_engine.generate_answer(
            query=norm_query,
            language=target_lang,
            citations=citations,
            context_text=context_prompt_sanitized
        )

        # 7. Grounding Verification
        grounding_report, grounding_ms = grounding_verifier.verify(answer_text, citations, norm_query)

        # Calculate Time To First Answer (TTFA)
        t_ttfa_end = time.perf_counter_ns()
        ttfa_ms = (t_ttfa_end - t_total_0) / 1_000_000.0

        # 8. Start Parallel Audio Synthesis for First Audio (TTFAudio)
        audio_b64 = None
        tts_ms = 0.0
        if req.stream_tts:
            synth_res = await tts_engine.synthesize_speech(text=answer_text, language=target_lang)
            audio_b64 = synth_res.audio_base64
            tts_ms = synth_res.duration_ms

        t_total_end = time.perf_counter_ns()
        total_ms = (t_total_end - t_total_0) / 1_000_000.0

        telemetry = LatencyBreakdown(
            audio_capture_ms=0.0,
            stt_ms=0.0,
            query_processing_ms=round(proc_ms, 3),
            embedding_ms=round(emb_ms, 3),
            dense_retrieval_ms=round(retrieval_audit["dense_ms"], 3),
            bm25_ms=round(retrieval_audit["bm25_ms"], 3),
            reranking_ms=round(rerank_ms, 3),
            context_assembly_ms=round(assembly_ms, 3),
            generation_ms=round(gen_ms, 3),
            grounding_ms=round(grounding_ms, 3),
            tts_ms=round(tts_ms, 3),
            rag_core_ms=round(ttfa_ms, 3),
            total_voice_ms=round(total_ms, 3),
            badge="FAST" if ttfa_ms < 50.0 else "NORMAL"
        )

        eng_trace = EngineeringTrace(
            trace_id=trace_id,
            detected_language=target_lang,
            query_classification=q_class,
            chunking_strategy_used=reranked_candidates[0].get("strategy", "multi_strategy") if reranked_candidates else "none",
            dense_candidates_count=len(candidates),
            bm25_candidates_count=len(candidates),
            reranked_scores=[{"chunk_id": c["chunk_id"], "score": c["final_score"]} for c in reranked_candidates],
            tier_used=f"{tier_used} ({rerank_mode})",
            prompt_token_count=len(context_prompt_sanitized.split()),
            retry_count=0
        )

        resp = QueryResponse(
            trace_id=trace_id,
            original_query=req.query,
            normalized_query=norm_query,
            language=target_lang,
            classification=q_class,
            answer=answer_text,
            tier=tier_used,
            citations=citations,
            grounding=grounding_report,
            telemetry=telemetry,
            engineering_trace=eng_trace,
            audio_base64=audio_b64
        )

        if not disable_cache:
            cache_engine.set(req.query, target_lang, resp)

        audit_meta = {
            "path": "FAST_PATH_EXTRACTIVE",
            "ttfa_ms": round(ttfa_ms, 3),
            "ttfaudio_ms": round(ttfa_ms + tts_ms, 3),
            "rerank_mode": rerank_mode
        }

        return resp, audit_meta

fast_path_engine = FastPathEngine()
