"""
SHRUTI True Cold-Start Benchmark Script
Measures process startup, model loading, index loading, database connection, and first query execution.
"""
import sys
import time
import json
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding='utf-8')

REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
COLD_START_REPORT = REPORTS_DIR / "cold-start-report.json"

async def run_cold_start_benchmark():
    print("==================================================")
    print("SHRUTI True Cold-Start Benchmark Engine")
    print("==================================================")

    # 1. Process & Import Startup
    t0 = time.perf_counter_ns()
    from backend.app.schemas import QueryRequest
    from backend.app.pipeline.orchestrator import orchestrator
    from backend.app.pipeline.retrieval import hybrid_retriever
    import_ms = (time.perf_counter_ns() - t0) / 1_000_000.0

    # 2. Model & DB Index Loading
    t_idx0 = time.perf_counter_ns()
    hybrid_retriever.initialize()
    index_load_ms = (time.perf_counter_ns() - t_idx0) / 1_000_000.0

    # 3. First Query Execution (Cold Request)
    t_fq0 = time.perf_counter_ns()
    req = QueryRequest(query="आयुष्मान भारत डिजिटल मिशन क्या है?", language="hi")
    resp = await orchestrator.process_query(req, disable_cache=True)
    first_query_ms = (time.perf_counter_ns() - t_fq0) / 1_000_000.0

    total_cold_start_ms = import_ms + index_load_ms + first_query_ms

    report = {
        "benchmark": "SHRUTI True Cold-Start",
        "import_and_module_load_ms": round(import_ms, 2),
        "index_and_db_connection_ms": round(index_load_ms, 2),
        "first_un_cached_query_ms": round(first_query_ms, 2),
        "total_cold_start_ms": round(total_cold_start_ms, 2),
        "subsequent_warm_query_rag_core_ms": resp.telemetry.rag_core_ms
    }

    with open(COLD_START_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[✔] Cold-Start Benchmark Complete:")
    print(f"    - Import & Module Load:   {import_ms:.2f} ms")
    print(f"    - Index & DB Load:        {index_load_ms:.2f} ms")
    print(f"    - First Query Execution:  {first_query_ms:.2f} ms")
    print(f"    - Total Cold-Start:       {total_cold_start_ms:.2f} ms")
    print(f"    - Warm Sub-Query RAG Core: {resp.telemetry.rag_core_ms:.3f} ms")
    print(f"    - Saved to {COLD_START_REPORT}")

if __name__ == "__main__":
    asyncio.run(run_cold_start_benchmark())
