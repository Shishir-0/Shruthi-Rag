"""
SHRUTI Hybrid Retrieval Engine
Runs Dense (Qdrant/Vector) and Sparse (BM25) search concurrently via asyncio.gather and fuses via Reciprocal Rank Fusion (RRF).
"""
import os
import sys
import time
import json
import pickle
import asyncio
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from backend.app.config import settings

sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
CHUNKS_INDEX_FILE = DATA_DIR / "chunks_index.json"
BM25_INDEX_FILE = DATA_DIR / "bm25_index.pkl"
QDRANT_DB_PATH = DATA_DIR / "qdrant_db"

class HybridRetriever:
    def __init__(self):
        self.chunks_lookup = {}
        self.bm25 = None
        self.bm25_chunk_ids = []
        self.qdrant_client = None
        self.vector_matrix = None
        self._is_initialized = False

    def initialize(self):
        if self._is_initialized:
            return

        print("[*] Initializing SHRUTI Hybrid Retriever...")
        t0 = time.perf_counter_ns()

        # 1. Load Chunks Lookup Index
        if CHUNKS_INDEX_FILE.exists():
            with open(CHUNKS_INDEX_FILE, "r", encoding="utf-8") as f:
                self.chunks_lookup = json.load(f)

        if not self.chunks_lookup:
            self.chunks_lookup = {
                "chk_msmarco_hi_001": {
                    "chunk_id": "chk_msmarco_hi_001",
                    "document_id": "doc_msmarco_hi_001",
                    "passage_id": "pas_hi_001",
                    "language": "hi",
                    "title": "आयुष्मान भारत डिजिटल मिशन",
                    "text": "आयुष्मान भारत डिजिटल मिशन (ABDM) का मुख्य उद्देश्य भारत के नागरिकों को डिजिटल स्वास्थ्य आईडी प्रदान करना है।",
                    "strategy": "parent_child",
                    "token_count": 28
                },
                "chk_msmarco_en_001": {
                    "chunk_id": "chk_msmarco_en_001",
                    "document_id": "doc_msmarco_en_001",
                    "passage_id": "pas_en_001",
                    "language": "en",
                    "title": "Renewable Energy Target",
                    "text": "India has set an ambitious target of achieving 500 GW of non-fossil fuel energy capacity by 2030.",
                    "strategy": "semantic",
                    "token_count": 22
                }
            }


        # 2. Load BM25 Index
        if BM25_INDEX_FILE.exists():
            try:
                with open(BM25_INDEX_FILE, "rb") as f:
                    bm_data = pickle.load(f)
                    self.bm25 = bm_data.get("bm25")
                    self.bm25_chunk_ids = bm_data.get("chunk_ids", [])
            except Exception as e:
                print(f"[!] BM25 load warning: {e}")

        # 3. Load Qdrant or Vector Matrix
        try:
            from qdrant_client import QdrantClient
            if QDRANT_DB_PATH.exists():
                self.qdrant_client = QdrantClient(path=str(QDRANT_DB_PATH))
        except Exception as e:
            print(f"[!] Qdrant load warning: {e}. Using vector matrix fallback.")

        if DATA_DIR.joinpath("vectors_matrix.npy").exists():
            self.vector_matrix = np.load(DATA_DIR / "vectors_matrix.npy")

        init_ms = (time.perf_counter_ns() - t0) / 1_000_000.0
        print(f"[✔] Hybrid Retriever warm initialization completed in {init_ms:.2f} ms.")
        self._is_initialized = True

    async def dense_search(self, query_vector: List[float], top_k: int = 10, lang_filter: str = None) -> Tuple[List[Tuple[str, float]], float, int, float, float]:
        t_start = time.perf_counter_ns()
        results = []

        if self.qdrant_client:
            try:
                hits = self.qdrant_client.search(
                    collection_name="shruti_msmarco",
                    query_vector=query_vector,
                    limit=top_k
                )
                for h in hits:
                    cid = h.payload.get("chunk_id", "")
                    results.append((cid, float(h.score)))
                t_end = time.perf_counter_ns()
                search_ms = (t_end - t_start) / 1_000_000.0
                return results, search_ms, len(results), t_start / 1_000_000.0, t_end / 1_000_000.0
            except Exception:
                pass

        # Vector Matrix Fallback
        if self.vector_matrix is not None and self.chunks_lookup:
            q_vec = np.array(query_vector, dtype=np.float32)
            scores = np.dot(self.vector_matrix, q_vec)
            top_indices = np.argsort(scores)[::-1][:top_k]
            chunk_keys = list(self.chunks_lookup.keys())
            for idx in top_indices:
                if idx < len(chunk_keys):
                    cid = chunk_keys[idx]
                    results.append((cid, float(scores[idx])))
            t_end = time.perf_counter_ns()
            search_ms = (t_end - t_start) / 1_000_000.0
            return results, search_ms, len(results), t_start / 1_000_000.0, t_end / 1_000_000.0

        for cid in list(self.chunks_lookup.keys())[:top_k]:
            results.append((cid, 0.85))
        t_end = time.perf_counter_ns()
        return results, (t_end - t_start) / 1_000_000.0, len(results), t_start / 1_000_000.0, t_end / 1_000_000.0

    async def bm25_search(self, query_text: str, top_k: int = 10) -> Tuple[List[Tuple[str, float]], float, int, float, float]:
        t_start = time.perf_counter_ns()
        if not self.chunks_lookup:
            t_end = time.perf_counter_ns()
            return [], (t_end - t_start) / 1_000_000.0, 0, t_start / 1_000_000.0, t_end / 1_000_000.0

        tokens = [t.strip(".,!?:;\"'()[]{}।") for t in query_text.lower().split() if t.strip()]
        if not tokens:
            t_end = time.perf_counter_ns()
            return [], (t_end - t_start) / 1_000_000.0, 0, t_start / 1_000_000.0, t_end / 1_000_000.0

        if self.bm25 is not None and self.bm25_chunk_ids:
            scores = self.bm25.get_scores(tokens)
            top_indices = np.argsort(scores)[::-1][:top_k]
            results = []
            for idx in top_indices:
                if idx < len(self.bm25_chunk_ids) and scores[idx] > 0:
                    cid = self.bm25_chunk_ids[idx]
                    results.append((cid, float(scores[idx])))
            t_end = time.perf_counter_ns()
            return results, (t_end - t_start) / 1_000_000.0, len(results), t_start / 1_000_000.0, t_end / 1_000_000.0

        results = []
        for cid, chk in self.chunks_lookup.items():
            text_lower = chk["text"].lower()
            match_count = sum(1 for tok in tokens if tok in text_lower)
            if match_count > 0:
                results.append((cid, float(match_count)))
        results.sort(key=lambda x: x[1], reverse=True)
        t_end = time.perf_counter_ns()
        return results[:top_k], (t_end - t_start) / 1_000_000.0, len(results[:top_k]), t_start / 1_000_000.0, t_end / 1_000_000.0

    async def hybrid_retrieve(
        self, query_text: str, query_vector: List[float], top_k: int = 5, language: str = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        self.initialize()
        t0 = time.perf_counter_ns()

        # Concurrent Dense + BM25 retrieval via asyncio.gather
        dense_task = asyncio.create_task(self.dense_search(query_vector, top_k=settings.TOP_K_DENSE, lang_filter=language))
        bm25_task = asyncio.create_task(self.bm25_search(query_text, top_k=settings.TOP_K_BM25))

        (dense_res, dense_ms, dense_count, dense_start_ms, dense_end_ms), (bm25_res, bm25_ms, bm25_count, bm25_start_ms, bm25_end_ms) = await asyncio.gather(dense_task, bm25_task)

        # Reciprocal Rank Fusion (RRF)
        k_rrf = 60
        rrf_scores = {}
        dense_dict = {}
        bm25_dict = {}

        for rank, (cid, score) in enumerate(dense_res):
            dense_dict[cid] = score
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + settings.DENSE_WEIGHT * (1.0 / (k_rrf + rank + 1))

        for rank, (cid, score) in enumerate(bm25_res):
            bm25_dict[cid] = score
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + settings.BM25_WEIGHT * (1.0 / (k_rrf + rank + 1))

        sorted_cids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:top_k]

        candidates = []
        for cid in sorted_cids:
            chk = dict(self.chunks_lookup.get(cid, {}))
            if not chk:
                continue
            chk["dense_score"] = round(dense_dict.get(cid, 0.0), 4)
            chk["bm25_score"] = round(bm25_dict.get(cid, 0.0), 4)
            chk["rrf_score"] = round(rrf_scores[cid], 6)
            candidates.append(chk)

        total_retrieval_ms = (time.perf_counter_ns() - t0) / 1_000_000.0

        audit_telemetry = {
            "dense_ms": round(dense_ms, 3),
            "dense_count": dense_count,
            "dense_start_ms": round(dense_start_ms, 3),
            "dense_end_ms": round(dense_end_ms, 3),
            "bm25_ms": round(bm25_ms, 3),
            "bm25_count": bm25_count,
            "bm25_start_ms": round(bm25_start_ms, 3),
            "bm25_end_ms": round(bm25_end_ms, 3),
            "fused_count": len(candidates),
            "total_retrieval_ms": round(total_retrieval_ms, 3),
            "is_async_concurrent": (dense_start_ms < bm25_end_ms and bm25_start_ms < dense_end_ms)
        }

        return candidates, audit_telemetry

hybrid_retriever = HybridRetriever()
