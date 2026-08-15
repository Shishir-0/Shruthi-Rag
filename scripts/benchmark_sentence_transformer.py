"""
SHRUTI SentenceTransformer Live Embedding Benchmark
Measures live PyTorch CPU embedding inference latency using sentence-transformers/paraphrase-multilingual-mpnet-base-v2.
"""
import sys
import time
import asyncio
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding='utf-8')

from backend.app.schemas import QueryRequest
from backend.app.pipeline.orchestrator import orchestrator

async def run_heavy_embedding_benchmark():
    print("==================================================")
    print("SHRUTI SentenceTransformer Live Embedding Benchmark")
    print("Model: sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
    print("==================================================")
    
    test_queries = [
        "आयुष्मान भारत डिजिटल मिशन क्या है?",
        "ગિફ્ટ સિટી ગાંધીનગર ક્યાં આવેલું છે?",
        "সুন্দরবন ম্যানগ্রোভ বন কোথায় অবস্থিত?",
        "தஞ்சாவூர் பிருகதீஸ்வரர் கோவில் யார் கட்டியது?",
        "What is India's renewable energy target by 2030?"
    ]

    latencies = []
    for i in range(20):
        q = test_queries[i % len(test_queries)]
        req = QueryRequest(query=q)
        t0 = time.perf_counter_ns()
        resp = await orchestrator.process_query(req, disable_cache=True, use_heavy_embedding=True)
        dt_ms = (time.perf_counter_ns() - t0) / 1_000_000.0
        latencies.append(dt_ms)

    a = np.array(latencies)
    print(f"[✔] Live SentenceTransformer Embedding Benchmark Complete (20 runs):")
    print(f"    - Mean Live Retrieval Core (Heavy Embedding): {np.mean(a):.2f} ms")
    print(f"    - P50 Live Retrieval Core (Heavy Embedding):  {np.percentile(a, 50):.2f} ms")
    print(f"    - P100 Live Retrieval Core (Heavy Embedding): {np.max(a):.2f} ms")
    print(f"    - Target (< 50ms): {'MET' if np.percentile(a, 50) < 50.0 else 'EXCEEDED'}")

if __name__ == "__main__":
    asyncio.run(run_heavy_embedding_benchmark())
