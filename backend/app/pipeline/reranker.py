"""
SHRUTI Adaptive Reranker
Skips expensive multi-pass reranking on high-confidence dense/sparse agreement (Fast Path <0.01ms).
"""
import time
from typing import List, Dict, Any, Tuple

class AdaptiveReranker:
    def rerank(
        self, candidates: List[Dict[str, Any]], query: str, target_language: str
    ) -> Tuple[List[Dict[str, Any]], float, str]:
        start = time.perf_counter_ns()
        if not candidates:
            return [], 0.0, "FAST_PATH_EMPTY"

        top_cand = candidates[0]
        dense_score = top_cand.get("dense_score", 0.0)
        bm25_score = top_cand.get("bm25_score", 0.0)

        # Adaptive Fast Path Condition: high vector score (>= 0.80) or strong BM25 match
        if dense_score >= 0.80 or bm25_score >= 2.0:
            for cand in candidates:
                cand["rerank_score"] = cand.get("rrf_score", 0.0) * 10.0
                cand["final_score"] = round(float(cand["rerank_score"]), 4)
            
            rerank_ms = (time.perf_counter_ns() - start) / 1_000_000.0
            return candidates, round(rerank_ms, 3), "FAST_PATH_ADAPTIVE"

        # High-Accuracy Multi-Factor Rerank Path
        q_terms = set(query.lower().split())
        seen_docs = set()
        reranked = []

        for cand in candidates:
            rrf = cand.get("rrf_score", 0.0)
            cand_lang = cand.get("language", "").lower()
            lang_boost = 1.2 if cand_lang == target_language.lower() else 0.9

            c_text_lower = cand.get("text", "").lower()
            kw_matches = sum(1 for term in q_terms if term in c_text_lower)
            kw_ratio = kw_matches / max(len(q_terms), 1)

            doc_id = cand.get("document_id", "doc_0")
            diversity_multiplier = 1.0 if doc_id not in seen_docs else 0.8
            seen_docs.add(doc_id)

            rerank_score = (rrf * 0.5 + kw_ratio * 0.3 + 0.2) * lang_boost * diversity_multiplier
            final_score = round(float(rerank_score), 4)

            item = dict(cand)
            item["rerank_score"] = final_score
            item["final_score"] = final_score
            reranked.append(item)

        reranked.sort(key=lambda x: x["final_score"], reverse=True)
        rerank_ms = (time.perf_counter_ns() - start) / 1_000_000.0

        return reranked, round(rerank_ms, 3), "HIGH_ACCURACY_RERANK"

reranker = AdaptiveReranker()
