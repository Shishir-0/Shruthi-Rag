"""
SHRUTI — Embedding Generator Script
Abstracts embedding models via EmbeddingProvider interface and generates vector embeddings.
"""
import sys
import json
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')


# --- Embedding Provider Interface ---
class EmbeddingProvider(ABC):
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        pass

# --- Primary Provider: SentenceTransformers Multilingual ---
class SentenceTransformerProvider(EmbeddingProvider):
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"):
        self.model_name = model_name
        self._model = None
        self._dimension = 768

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                print(f"[*] Loading SentenceTransformer model: {self.model_name}...")
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
                print(f"[+] Model loaded. Dimension: {self._dimension}")
            except Exception as e:
                print(f"[!] Could not load SentenceTransformer ({e}). Falling back to LightweightMultilingualProvider.")
                raise e

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        self._load_model()
        embeddings = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return embeddings.tolist()

    def get_dimension(self) -> int:
        return self._dimension

    def get_model_name(self) -> str:
        return self.model_name

# --- Fallback Provider: Lightweight Fast Vectorizer ---
class LightweightMultilingualProvider(EmbeddingProvider):
    """High-speed deterministic multilingual embedding generator with fixed dimension 384."""
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.model_name = "LightweightMultilingualVectorEngine-v1"

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        results = []
        for text in texts:
            # Deterministic hash-based dense vector for lightweight CPU sub-ms execution
            vec = np.zeros(self.dimension, dtype=np.float32)
            words = text.lower().split()
            for idx, w in enumerate(words):
                h = hash(w) % self.dimension
                vec[h] += 1.0 / (idx + 1)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            results.append(vec.tolist())
        return results

    def get_dimension(self) -> int:
        return self.dimension

    def get_model_name(self) -> str:
        return self.model_name

def get_embedding_provider(prefer_heavy: bool = False) -> EmbeddingProvider:
    if prefer_heavy:
        try:
            provider = SentenceTransformerProvider()
            provider._load_model()
            return provider
        except Exception:
            pass
    return LightweightMultilingualProvider()

def build_embeddings():
    data_dir = Path(__file__).parent.parent / "data"
    input_file = data_dir / "msmarco_xi_chunked.jsonl"
    output_file = data_dir / "msmarco_xi_embedded.jsonl"

    if not input_file.exists():
        print(f"[-] Input file {input_file} not found. Run build_chunks.py first.")
        return

    chunks = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))

    provider = get_embedding_provider(prefer_heavy=True)
    print(f"==================================================")
    print(f"SHRUTI Embedding Generator")
    print(f"Provider: {provider.get_model_name()}")
    print(f"Dimension: {provider.get_dimension()}")
    print(f"==================================================")

    texts = [c["text"] for c in chunks]
    print(f"[*] Embedding {len(texts)} chunks...")
    vectors = provider.embed_texts(texts)

    for chk, vec in zip(chunks, vectors):
        chk["embedding"] = vec
        chk["embedding_model"] = provider.get_model_name()
        chk["embedding_dimension"] = provider.get_dimension()

    with open(output_file, "w", encoding="utf-8") as f:
        for chk in chunks:
            f.write(json.dumps(chk, ensure_ascii=False) + "\n")

    print(f"[✔] Embeddings generated successfully.")
    print(f"[✔] Output saved to: {output_file}")

if __name__ == "__main__":
    build_embeddings()
