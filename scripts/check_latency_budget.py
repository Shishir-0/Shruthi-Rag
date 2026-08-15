"""
SHRUTI Latency & Quality Budget Checker
Fails with non-zero exit code if latency exceeds targets or if retrieval/grounding quality regresses.
"""
import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

REPORTS_DIR = Path(__file__).parent.parent / "reports"
SUB200_JSON = REPORTS_DIR / "sub200-performance.json"
EVAL_JSON = REPORTS_DIR / "evaluation.json"
REGRESSION_JSON = REPORTS_DIR / "latency-regression.json"

MAX_RETRIEVAL_P50 = 10.0
MAX_TTFA_P95 = 200.0
MIN_RECALL_AT_5 = 0.90
MIN_GROUNDING_RATE = 90.0

def check_budgets():
    print("==================================================")
    print("SHRUTI Performance & Quality Budget Checker")
    print("==================================================")
    
    if not SUB200_JSON.exists():
        print(f"[-] Missing {SUB200_JSON}. Run benchmark_sub200.py first.")
        sys.exit(1)

    with open(SUB200_JSON, "r", encoding="utf-8") as f:
        sub200 = json.load(f)

    with open(EVAL_JSON, "r", encoding="utf-8") as f:
        eval_data = json.load(f)

    ttfa_p95 = sub200.get("ttfa_time_to_first_answer_ms", {}).get("p95", 999.0)
    ttr_p50 = sub200.get("ttr_time_to_retrieval_ms", {}).get("p50", 999.0)
    recall = eval_data.get("recall_at_k", 0.0)
    grounding = eval_data.get("grounding_rate_pct", 0.0)

    regressions = []

    if ttr_p50 > MAX_RETRIEVAL_P50:
        regressions.append(f"Retrieval P50 ({ttr_p50} ms) exceeds budget ({MAX_RETRIEVAL_P50} ms)")

    if ttfa_p95 > MAX_TTFA_P95:
        regressions.append(f"TTFA P95 ({ttfa_p95} ms) exceeds budget ({MAX_TTFA_P95} ms)")

    if recall < MIN_RECALL_AT_5:
        regressions.append(f"Recall@5 ({recall}) below minimum quality threshold ({MIN_RECALL_AT_5})")

    if grounding < MIN_GROUNDING_RATE:
        regressions.append(f"Grounding Rate ({grounding}%) below minimum quality threshold ({MIN_GROUNDING_RATE}%)")

    status = "PASSED" if not regressions else "FAILED"

    reg_report = {
        "status": status,
        "regressions": regressions,
        "measured_retrieval_p50_ms": ttr_p50,
        "measured_ttfa_p95_ms": ttfa_p95,
        "measured_recall_at_5": recall,
        "measured_grounding_rate_pct": grounding
    }

    with open(REGRESSION_JSON, "w", encoding="utf-8") as f:
        json.dump(reg_report, f, indent=2, ensure_ascii=False)

    if regressions:
        print(f"[!] REGRESSION DETECTED ({len(regressions)} violations):")
        for reg in regressions:
            print(f"    - {reg}")
        sys.exit(1)

    print(f"[✔] ALL PERFORMANCE & QUALITY BUDGETS PASSED:")
    print(f"    - Retrieval P50:  {ttr_p50} ms (< {MAX_RETRIEVAL_P50} ms)")
    print(f"    - TTFA P95:       {ttfa_p95} ms (< {MAX_TTFA_P95} ms)")
    print(f"    - Recall@5:       {recall} (>= {MIN_RECALL_AT_5})")
    print(f"    - Grounding Rate: {grounding}% (>= {MIN_GROUNDING_RATE}%)")

if __name__ == "__main__":
    check_budgets()
