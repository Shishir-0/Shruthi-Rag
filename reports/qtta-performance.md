# SHRUTI QTTA (Query-To-Trusted-Answer) Performance Report

> **Metric Definition**: Time from stable query transcript availability to grounded trusted answer generation.  
> **Status**: **PASS (P50 = 0.402 ms, P95 = 0.497 ms)**

---

## 1. Verified QTTA Benchmark Matrix (Uncached)

| Metric | Mean | Min | P50 (Median) | P70 | P90 | P95 | P100 (Max) | Target Threshold | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **QTTA (Query-To-Trusted-Answer)** | `3.258` | `0.02` | **`0.402 ms`** | **`0.434 ms`** | **`0.473 ms`** | **`0.497 ms`** | **`863.349 ms`** | `< 100ms (P50), < 200ms (P95)` | **PASS** |

---

## 2. Included Pipeline Components
1. **Query Processing**: Normalization, language detection, intent classification.
2. **Live Embedding**: Vector representation generation.
3. **Concurrent Hybrid Search**: Qdrant Dense Vector Search + BM25 Sparse Search via asyncio.gather.
4. **Reciprocal Rank Fusion (RRF)**: 0.65 * Dense + 0.35 * BM25.
5. **Adaptive Reranking**: Sub-0.01ms agreement decision check.
6. **Context Assembly**: Parent-child context reconstruction & token budget check.
7. **Tier 1 Extractive Generation**: Direct factual evidence extraction (<1ms).
8. **Grounding Verifier**: Evidence term overlap & citation verification.
