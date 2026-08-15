"""
SHRUTI Pipeline Orchestrator Harness
Orchestrates the 12-stage online pipeline with trace IDs, retries, and high-precision nanosecond telemetry.
"""
import time
import uuid
import asyncio
from typing import Dict, Any, Optional

from backend.app.schemas import (
    QueryRequest, QueryResponse, LatencyBreakdown, GroundingReport,
    EngineeringTrace, CitationItem
)
from backend.app.pipeline.query_processor import query_processor
from backend.app.pipeline.retrieval import hybrid_retriever
from backend.app.pipeline.reranker import reranker
from backend.app.pipeline.context_assembler import context_assembler
from backend.app.pipeline.answer_engine import answer_engine
from backend.app.pipeline.grounding import grounding_verifier
from backend.app.pipeline.guardrails import guardrail_engine
from backend.app.pipeline.stt import stt_engine
from backend.app.pipeline.tts import tts_engine
from backend.app.pipeline.cache import cache_engine
from scripts.build_embeddings import LightweightMultilingualProvider, SentenceTransformerProvider

_lightweight_embedder = LightweightMultilingualProvider()
_sentence_transformer_embedder = None

def get_embedder(use_heavy: bool = False):
    global _sentence_transformer_embedder
    if use_heavy:
        if _sentence_transformer_embedder is None:
            try:
                _sentence_transformer_embedder = SentenceTransformerProvider()
                _sentence_transformer_embedder._load_model()
            except Exception:
                return _lightweight_embedder
        return _sentence_transformer_embedder
    return _lightweight_embedder

class PipelineOrchestrator:
    async def process_query(
        self, req: QueryRequest, disable_cache: bool = False, use_heavy_embedding: bool = False
    ) -> QueryResponse:
        t_total_0 = time.perf_counter_ns()
        trace_id = f"shruti_tr_{uuid.uuid4().hex[:12]}"
        
        # Check Cache (Skip if disable_cache=True for Cold Benchmarking)
        if not disable_cache:
            cached_resp = cache_engine.get(req.query, req.language or "auto")
            if cached_resp:
                cached_resp.trace_id = trace_id
                return cached_resp

        # Stage 1 & 3 & 4: Query Processing (Normalization, Language ID, Classification)
        t_proc_0 = time.perf_counter_ns()
        proc_res = query_processor.process(req.query)
        target_lang = req.language or proc_res["detected_language"]
        q_class = proc_res["query_type"]
        norm_query = proc_res["normalized_query"]
        retrieval_query = proc_res["retrieval_query"]
        query_proc_ms = (time.perf_counter_ns() - t_proc_0) / 1_000_000.0

        # Stage 1 Guardrail Validation
        guard_res = guardrail_engine.validate_input(norm_query, q_class)
        if not guard_res.is_answerable:
            total_voice_ms = (time.perf_counter_ns() - t_total_0) / 1_000_000.0
            return QueryResponse(
                trace_id=trace_id,
                original_query=req.query,
                normalized_query=norm_query,
                language=target_lang,
                classification=q_class,
                answer=guard_res.rejection_reason or "Question is outside indexed domain.",
                tier="Guardrail Refusal",
                citations=[],
                grounding=GroundingReport(
                    grounded=False, confidence=0.0, unsupported_claims=[], citations_valid=False, reasoning="Rejection by Guardrail."
                ),
                telemetry=LatencyBreakdown(
                    query_processing_ms=round(query_proc_ms, 3),
                    rag_core_ms=round(query_proc_ms, 3),
                    total_voice_ms=round(total_voice_ms, 3),
                    badge="FAST"
                )
            )

        # Stage 5: Embedding & Hybrid Retrieval
        t_emb_0 = time.perf_counter_ns()
        embedder = get_embedder(use_heavy_embedding)
        query_vec = embedder.embed_texts([retrieval_query])[0]
        embedding_ms = (time.perf_counter_ns() - t_emb_0) / 1_000_000.0

        candidates, retrieval_audit = await hybrid_retriever.hybrid_retrieve(
            query_text=retrieval_query,
            query_vector=query_vec,
            top_k=5,
            language=target_lang
        )
        retrieval_ms = retrieval_audit["total_retrieval_ms"]
        dense_ms = retrieval_audit["dense_ms"]
        bm25_ms = retrieval_audit["bm25_ms"]

        # Stage 6: Reranking
        t_rerank_0 = time.perf_counter_ns()
        reranked_candidates, rerank_ms, _ = reranker.rerank(candidates, norm_query, target_lang)


        # Stage 7: Context Assembly & Parent-Child Reconstruction
        t_asm_0 = time.perf_counter_ns()
        citations, context_prompt, assembly_ms = context_assembler.assemble_context(
            reranked_candidates, max_token_budget=600
        )

        # Stage 8: Two-Tier Answer Generation
        context_prompt_sanitized = guardrail_engine.sanitize_retrieved_context(context_prompt)
        answer_text, tier_used, gen_ms = await answer_engine.generate_answer(
            query=norm_query,
            language=target_lang,
            citations=citations,
            context_text=context_prompt_sanitized
        )

        # Stage 9: Grounding Verification
        t_g_0 = time.perf_counter_ns()
        grounding_report, grounding_ms = grounding_verifier.verify(answer_text, citations, norm_query)

        # Stage 10: Fallback if ungrounded
        if not grounding_report.grounded and tier_used == "Tier 2 Generative":
            answer_text, tier_used, gen_ms_fb = await answer_engine.generate_answer(
                query=norm_query, language=target_lang, citations=citations, context_text=""
            )
            gen_ms += gen_ms_fb
            tier_used = "Tier 1 Extractive Fallback"

        # Layer 1 Retrieval Core & Layer 2 Answer Core Latency Calculations
        rag_core_ms = query_proc_ms + embedding_ms + retrieval_ms + rerank_ms + assembly_ms
        answer_core_ms = rag_core_ms + gen_ms + grounding_ms

        # Stage 11: TTS Synthesis (if requested)
        audio_b64 = None
        tts_ms = 0.0
        if req.stream_tts:
            synth_res = await tts_engine.synthesize_speech(text=answer_text, language=target_lang)
            audio_b64 = synth_res.audio_base64
            tts_ms = synth_res.duration_ms

        total_voice_ms = (time.perf_counter_ns() - t_total_0) / 1_000_000.0
        badge = "FAST" if rag_core_ms < 50.0 else ("NORMAL" if rag_core_ms < 150.0 else "SLOW")

        telemetry = LatencyBreakdown(
            audio_capture_ms=0.0,
            stt_ms=0.0,
            query_processing_ms=round(query_proc_ms, 3),
            embedding_ms=round(embedding_ms, 3),
            dense_retrieval_ms=round(dense_ms, 3),
            bm25_ms=round(bm25_ms, 3),
            reranking_ms=round(rerank_ms, 3),
            context_assembly_ms=round(assembly_ms, 3),
            generation_ms=round(gen_ms, 3),
            grounding_ms=round(grounding_ms, 3),
            tts_ms=round(tts_ms, 3),
            rag_core_ms=round(rag_core_ms, 3),
            total_voice_ms=round(total_voice_ms, 3),
            badge=badge
        )

        eng_trace = EngineeringTrace(
            trace_id=trace_id,
            detected_language=target_lang,
            query_classification=q_class,
            chunking_strategy_used=reranked_candidates[0].get("strategy", "multi_strategy") if reranked_candidates else "none",
            dense_candidates_count=len(candidates),
            bm25_candidates_count=len(candidates),
            reranked_scores=[{"chunk_id": c["chunk_id"], "score": c["final_score"]} for c in reranked_candidates],
            tier_used=tier_used,
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
        return resp

orchestrator = PipelineOrchestrator()
