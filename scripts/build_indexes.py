"""
SHRUTI — Index Builder Script
Indexes vectors into Qdrant database and builds BM25 sparse keyword index.
"""
import os
import sys
import json
import pickle
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

sys.stdout.reconfigure(encoding='utf-8')



DATA_DIR = Path(__file__).parent.parent / "data"
QDRANT_DB_PATH = DATA_DIR / "qdrant_db"
BM25_INDEX_FILE = DATA_DIR / "bm25_index.pkl"
CHUNKS_INDEX_FILE = DATA_DIR / "chunks_index.json"
COLLECTION_NAME = "shruti_msmarco"

def build_indexes():
    input_file = DATA_DIR / "msmarco_xi_embedded.jsonl"
    if not input_file.exists():
        print(f"[-] Input file {input_file} not found. Run build_embeddings.py first.")
        return

    chunks = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))

    print("==================================================")
    print("SHRUTI Index Builder: Qdrant + BM25")
    print("==================================================")
    print(f"[*] Loaded {len(chunks)} embedded chunks for indexing.")

    # 1. Save local chunk index for direct zero-latency lookup
    chunks_lookup = {c["chunk_id"]: c for c in chunks}
    with open(CHUNKS_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks_lookup, f, indent=2, ensure_ascii=False)
    print(f"[+] Direct Chunk Index saved to {CHUNKS_INDEX_FILE}")


    # 2. Build BM25 Index
    print("[*] Building BM25 sparse keyword index...")
    tokenized_corpus = []
    for c in chunks:
        # Multilingual tokenization on whitespace & punctuation
        text = c["text"].lower()
        tokens = [t.strip(".,!?:;\"'()[]{}।") for t in text.split() if t.strip()]
        tokenized_corpus.append(tokens)

    try:
        from rank_bm25 import BM25Okapi
        bm25 = BM25Okapi(tokenized_corpus)
        with open(BM25_INDEX_FILE, "wb") as f:
            pickle.dump({"bm25": bm25, "chunk_ids": [c["chunk_id"] for c in chunks]}, f)
        print(f"[+] BM25 Index saved to {BM25_INDEX_FILE}")
    except Exception as e:
        print(f"[!] rank_bm25 error: {e}. Building fallback BM25 index...")
        bm25_data = {
            "chunk_ids": [c["chunk_id"] for c in chunks],
            "tokenized_corpus": tokenized_corpus
        }
        with open(BM25_INDEX_FILE, "wb") as f:
            pickle.dump(bm25_data, f)
        print(f"[+] Fallback BM25 tokenized corpus saved to {BM25_INDEX_FILE}")

    # 3. Build Qdrant Vector Collection
    print("[*] Indexing into Qdrant Vector Database...")
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import VectorParams, Distance, PointStruct

        client = QdrantClient(path=str(QDRANT_DB_PATH))
        dim = chunks[0]["embedding_dimension"] if chunks else 384
        
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
        )

        points = []
        for idx, c in enumerate(chunks):
            payload = {
                "chunk_id": c["chunk_id"],
                "parent_id": c["parent_id"],
                "document_id": c.get("document_id", ""),
                "title": c.get("title", ""),
                "section": c.get("section", ""),
                "language": c.get("language", "en"),
                "text": c["text"],
                "token_count": c.get("token_count", 0),
                "character_count": c.get("character_count", 0),
                "strategy": c.get("strategy", ""),
                "chunk_type": c.get("chunk_type", "child"),
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            points.append(PointStruct(id=idx, vector=c["embedding"], payload=payload))

        client.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"[+] Qdrant vector index created at {QDRANT_DB_PATH} with {len(points)} vectors.")
    except Exception as e:
        print(f"[!] Qdrant client error: {e}. Storing local vector index matrix.")
        vectors_matrix = np.array([c["embedding"] for c in chunks], dtype=np.float32)
        np.save(DATA_DIR / "vectors_matrix.npy", vectors_matrix)
        print(f"[+] Local vector numpy matrix saved for fallback vector search.")

    print(f"[✔] All indexes built successfully!")

if __name__ == "__main__":
    build_indexes()
