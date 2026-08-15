"""
SHRUTI Context Assembler & Parent-Child Context Reconstructor
Assembles deduplicated, budget-capped, citation-tagged evidence for generation.
"""
import time
import json
from typing import List, Dict, Any, Tuple
from pathlib import Path
from backend.app.schemas import CitationItem

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
CHUNKS_INDEX_FILE = DATA_DIR / "chunks_index.json"

class ContextAssembler:
    def __init__(self):
        self.chunks_lookup = {}

    def _load_lookup(self):
        if not self.chunks_lookup and CHUNKS_INDEX_FILE.exists():
            with open(CHUNKS_INDEX_FILE, "r", encoding="utf-8") as f:
                self.chunks_lookup = json.load(f)

    def assemble_context(
        self, reranked_chunks: List[Dict[str, Any]], max_token_budget: int = 600
    ) -> Tuple[List[CitationItem], str, float]:
        start = time.perf_counter()
        self._load_lookup()

        citations = []
        assembled_texts = []
        used_tokens = 0
        seen_texts = set()

        for idx, chk in enumerate(reranked_chunks, start=1):
            text = chk.get("text", "").strip()
            if not text or text in seen_texts:
                continue
            seen_texts.add(text)

            # Reconstruct parent context if parent_id exists and is parent-child chunk
            parent_id = chk.get("parent_id")
            if parent_id and parent_id in self.chunks_lookup and chk.get("chunk_type") == "child":
                parent_chk = self.chunks_lookup[parent_id]
                parent_text = parent_chk.get("text", "").strip()
                if parent_text:
                    text = parent_text

            tok_count = len(text.split())
            if used_tokens + tok_count > max_token_budget and citations:
                break

            citation_id = f"[{idx}]"
            cit = CitationItem(
                citation_id=citation_id,
                document_id=chk.get("document_id", f"doc_{idx}"),
                chunk_id=chk.get("chunk_id", f"chk_{idx}"),
                source=chk.get("source", "MSMARCO-XI"),
                title=chk.get("title", "MS MARCO Passage"),
                language=chk.get("language", "en"),
                text=text,
                dense_score=chk.get("dense_score", 0.0),
                bm25_score=chk.get("bm25_score", 0.0),
                rerank_score=chk.get("rerank_score", 0.0),
                final_score=chk.get("final_score", 0.0)
            )
            citations.append(cit)
            assembled_texts.append(f"{citation_id} Source: {cit.title}\n{cit.text}")
            used_tokens += tok_count

        assembled_prompt_context = "\n\n".join(assembled_texts)
        assembly_ms = (time.perf_counter() - start) * 1000.0

        return citations, assembled_prompt_context, round(assembly_ms, 2)

context_assembler = ContextAssembler()
