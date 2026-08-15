"""
SHRUTI Multi-Level Caching Engine (L1 Memory + L2 Storage)
Caches query embeddings, normalized queries, and deterministic answers.
"""
import time
import hashlib
from typing import Dict, Any, Optional

class CacheEngine:
    def __init__(self, max_l1_items: int = 500):
        self.l1_cache: Dict[str, Any] = {}
        self.max_l1_items = max_l1_items

    def _hash_key(self, query: str, language: str) -> str:
        raw = f"{query.strip().lower()}_{language}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, query: str, language: str) -> Optional[Any]:
        key = self._hash_key(query, language)
        if key in self.l1_cache:
            entry = self.l1_cache[key]
            # 5 minute TTL
            if time.time() - entry["timestamp"] < 300:
                return entry["data"]
            else:
                del self.l1_cache[key]
        return None

    def set(self, query: str, language: str, data: Any):
        key = self._hash_key(query, language)
        if len(self.l1_cache) >= self.max_l1_items:
            # Evict oldest entry
            oldest_key = min(self.l1_cache.keys(), key=lambda k: self.l1_cache[k]["timestamp"])
            del self.l1_cache[oldest_key]
        self.l1_cache[key] = {"data": data, "timestamp": time.time()}

cache_engine = CacheEngine()
