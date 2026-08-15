"""
SHRUTI — Multi-Strategy Hierarchical Chunking Pipeline
Implements Strategy A-F chunkers and a strategy selector for multilingual text.
"""
import re
import sys
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')


# --- Base Chunker Interface ---
class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

# --- Strategy A: Semantic Chunker ---
class SemanticChunker(BaseChunker):
    """Splits text on semantic boundaries using language-aware sentence & paragraph delimiters."""
    def chunk(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = record.get("text", "")
        # Devanagari/Bengali full stop '।', Tamil/English '.', newline '\n'
        delimiters = r'(?<=[।\.\!\?])\s+|\n\n+'
        raw_sentences = [s.strip() for s in re.split(delimiters, text) if s.strip()]
        
        chunks = []
        curr_sentences = []
        curr_tokens = 0

        for sent in raw_sentences:
            s_tokens = len(sent.split())
            if curr_tokens + s_tokens > 200 and curr_sentences:
                chunk_text = " ".join(curr_sentences)
                chunks.append(self._create_chunk(record, chunk_text, "semantic"))
                curr_sentences = []
                curr_tokens = 0
            curr_sentences.append(sent)
            curr_tokens += s_tokens

        if curr_sentences:
            chunk_text = " ".join(curr_sentences)
            chunks.append(self._create_chunk(record, chunk_text, "semantic"))

        return chunks

    def _create_chunk(self, record: Dict[str, Any], text: str, strategy: str) -> Dict[str, Any]:
        return {
            "chunk_id": f"{record['passage_id']}_sem_{len(text[:20])}",
            "parent_id": record["passage_id"],
            "document_id": record.get("document_id", "doc_0"),
            "title": record.get("title", ""),
            "section": record.get("section", ""),
            "language": record.get("language", "en"),
            "text": text,
            "token_count": len(text.split()),
            "character_count": len(text),
            "strategy": strategy,
            "chunk_type": "child",
            "metadata": record.get("metadata", {})
        }

# --- Strategy B: Recursive Chunker ---
class RecursiveChunker(BaseChunker):
    """Hierarchical splitting with fallback separators."""
    def __init__(self, max_tokens: int = 150):
        self.max_tokens = max_tokens

    def chunk(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = record.get("text", "")
        separators = ["\n\n", "\n", "। ", ". ", " ", ""]
        
        def _recursive_split(t: str, seps: List[str]) -> List[str]:
            tokens = len(t.split())
            if tokens <= self.max_tokens or not seps:
                return [t]
            sep = seps[0]
            parts = t.split(sep) if sep else list(t)
            result = []
            current = []
            curr_tok = 0
            for part in parts:
                p_tok = len(part.split())
                if curr_tok + p_tok > self.max_tokens and current:
                    result.append(sep.join(current))
                    current = []
                    curr_tok = 0
                current.append(part)
                curr_tok += p_tok
            if current:
                result.append(sep.join(current))
            
            # Further split overlong chunks with remaining separators
            final_chunks = []
            for sub in result:
                if len(sub.split()) > self.max_tokens and len(seps) > 1:
                    final_chunks.extend(_recursive_split(sub, seps[1:]))
                else:
                    final_chunks.append(sub)
            return final_chunks

        splits = _recursive_split(text, separators)
        chunks = []
        for idx, s in enumerate(splits):
            s_clean = s.strip()
            if not s_clean:
                continue
            chunks.append({
                "chunk_id": f"{record['passage_id']}_rec_{idx}",
                "parent_id": record["passage_id"],
                "document_id": record.get("document_id", "doc_0"),
                "title": record.get("title", ""),
                "section": record.get("section", ""),
                "language": record.get("language", "en"),
                "text": s_clean,
                "token_count": len(s_clean.split()),
                "character_count": len(s_clean),
                "strategy": "recursive",
                "chunk_type": "child",
                "metadata": record.get("metadata", {})
            })
        return chunks

# --- Strategy C: Sliding Window Chunker ---
class SlidingWindowChunker(BaseChunker):
    """Sliding window with controlled overlap."""
    def __init__(self, window_size: int = 150, overlap: int = 30):
        self.window_size = window_size
        self.overlap = overlap

    def chunk(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = record.get("text", "")
        words = text.split()
        if len(words) <= self.window_size:
            return [{
                "chunk_id": f"{record['passage_id']}_slide_0",
                "parent_id": record["passage_id"],
                "document_id": record.get("document_id", "doc_0"),
                "title": record.get("title", ""),
                "section": record.get("section", ""),
                "language": record.get("language", "en"),
                "text": text,
                "token_count": len(words),
                "character_count": len(text),
                "strategy": "sliding_window",
                "chunk_type": "child",
                "metadata": record.get("metadata", {})
            }]

        chunks = []
        step = self.window_size - self.overlap
        for i in range(0, len(words), step):
            window_words = words[i:i + self.window_size]
            if len(window_words) < 15 and chunks:
                break
            w_text = " ".join(window_words)
            chunks.append({
                "chunk_id": f"{record['passage_id']}_slide_{i}",
                "parent_id": record["passage_id"],
                "document_id": record.get("document_id", "doc_0"),
                "title": record.get("title", ""),
                "section": record.get("section", ""),
                "language": record.get("language", "en"),
                "text": w_text,
                "token_count": len(window_words),
                "character_count": len(w_text),
                "strategy": "sliding_window",
                "chunk_type": "child",
                "metadata": record.get("metadata", {})
            })
        return chunks

# --- Strategy E: Parent-Child Chunker ---
class ParentChildChunker(BaseChunker):
    """Generates 1 parent chunk (full context) and multiple small child chunks for vector precision."""
    def chunk(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = record.get("text", "")
        parent_id = f"parent_{record['passage_id']}"
        
        # Parent Chunk
        parent_chunk = {
            "chunk_id": parent_id,
            "parent_id": parent_id,
            "document_id": record.get("document_id", "doc_0"),
            "title": record.get("title", ""),
            "section": record.get("section", ""),
            "language": record.get("language", "en"),
            "text": text,
            "token_count": len(text.split()),
            "character_count": len(text),
            "strategy": "parent_child",
            "chunk_type": "parent",
            "metadata": record.get("metadata", {})
        }

        # Child Chunks (using semantic boundaries)
        sem_chunker = SemanticChunker()
        children = sem_chunker.chunk(record)
        for idx, child in enumerate(children):
            child["chunk_id"] = f"child_{record['passage_id']}_{idx}"
            child["parent_id"] = parent_id
            child["chunk_type"] = "child"
            child["strategy"] = "parent_child"

        return [parent_chunk] + children

# --- Strategy Selector ---
class ChunkStrategySelector:
    def __init__(self):
        self.semantic = SemanticChunker()
        self.recursive = RecursiveChunker()
        self.sliding = SlidingWindowChunker()
        self.parent_child = ParentChildChunker()

    def select_and_chunk(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        token_count = len(record.get("text", "").split())
        lang = record.get("language", "en").lower()

        # Selection logic based on length, language, and structural complexity
        if token_count > 250:
            return self.parent_child.chunk(record)
        elif lang in ["hi", "gu", "bn", "ta", "te", "mr", "pa", "kn", "ml"]:
            return self.semantic.chunk(record)
        elif token_count > 120:
            return self.sliding.chunk(record)
        else:
            return self.recursive.chunk(record)

def build_chunked_dataset():
    data_dir = Path(__file__).parent.parent / "data"
    input_file = data_dir / "msmarco_xi_sampled.jsonl"
    output_file = data_dir / "msmarco_xi_chunked.jsonl"

    if not input_file.exists():
        print(f"[-] Input dataset {input_file} not found.")
        return

    records = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    selector = ChunkStrategySelector()
    all_chunks = []

    print(f"==================================================")
    print(f"SHRUTI Multi-Strategy Chunking Pipeline")
    print(f"==================================================")
    print(f"[*] Processing {len(records)} raw documents...")

    for rec in records:
        chunks = selector.select_and_chunk(rec)
        all_chunks.extend(chunks)

    with open(output_file, "w", encoding="utf-8") as f:
        for chk in all_chunks:
            f.write(json.dumps(chk, ensure_ascii=False) + "\n")

    print(f"[✔] Chunking complete. Generated {len(all_chunks)} chunks from {len(records)} documents.")
    print(f"[✔] Chunked dataset saved to: {output_file}")

if __name__ == "__main__":
    build_chunked_dataset()
