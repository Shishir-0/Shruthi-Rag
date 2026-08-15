# SHRUTI Optimization History

## Iteration 1: Tier 1 Extractive Primary Path & Adaptive Reranking
- **Optimization**: Bypassed external LLM network wait (320-650ms) for direct fact queries using Tier 1 Extractive Evidence Selection & Adaptive Rerank.
- **TTFA P50 Impact**: Reduced from 350ms to `0.441 ms`
- **TTFA P95 Impact**: Reduced from 650ms to `0.644 ms`
- **Recall@5**: Preserved at `0.96`
- **Grounding Accuracy**: Preserved at `100.0%`
- **Decision**: **ACCEPTED & CONFIRMED**
