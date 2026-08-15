"""
SHRUTI Real Voice Telemetry Benchmark Suite
Dual Mode:
  Mode A: Local Test Fixture (--test-mode or SHRUTI_TEST_MODE=true)
  Mode B: Real Provider Benchmark (Requires real SARVAM_API_KEY)
"""
import sys
import json
import time
import os
import asyncio
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding='utf-8')

from backend.app.config import settings
from backend.app.schemas import QueryRequest
from backend.app.pipeline.stt import stt_engine
from backend.app.pipeline.tts import tts_engine
from backend.app.pipeline.fast_path import fast_path_engine

REPORTS_DIR = Path(__file__).parent.parent / "reports"
VOICE_JSON = REPORTS_DIR / "voice-realtime-performance.json"
VOICE_MD = REPORTS_DIR / "voice-realtime-performance.md"

VOICE_TEST_PROMPTS = [
    {"lang_code": "hi", "hint": "hi-IN", "text": "आयुष्मान भारत डिजिटल मिशन क्या है?"},
    {"lang_code": "gu", "hint": "gu-IN", "text": "ગિફ્ટ સિટી ગાંધીનગર ક્યાં આવેલું છે?"},
    {"lang_code": "bn", "hint": "bn-IN", "text": "সুন্দরবন ম্যানগ্রোভ বন কোথায় অবস্থিত?"},
    {"lang_code": "ta", "hint": "ta-IN", "text": "தஞ்சாவூர் பிருகதீஸ்வரர் கோவில் யார் கட்டியது?"},
    {"lang_code": "en", "hint": "en-IN", "text": "What is India's renewable energy target by 2030?"}
]

async def run_voice_realtime_benchmark(num_runs: int = 25):
    is_test_mode = settings.SHRUTI_TEST_MODE or "--test-mode" in sys.argv
    has_api_key = bool(settings.SARVAM_API_KEY and len(settings.SARVAM_API_KEY) > 5)

    print("==================================================")
    print(f"SHRUTI Real-Time Voice Telemetry Benchmark Engine")
    print(f"Mode: {'MODE A — LOCAL TEST FIXTURE' if is_test_mode else 'MODE B — REAL PROVIDER'}")
    print("==================================================")

    if not is_test_mode and not has_api_key:
        print("[!] ERROR: REAL PROVIDER BENCHMARK CANNOT RUN!")
        print("[!] SARVAM_API_KEY is not configured in environment.")
        print("[!] To run local test fixtures for unit testing, set SHRUTI_TEST_MODE=true or pass --test-mode.")
        sys.exit(1)

    dummy_wav_bytes = b"RIFF$ \x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00@\x1f\x00\x00\x80>\x00\x00\x02\x00\x10\x00data\x00 \x00\x00" + b"\x00" * 3200

    stt_times = []
    qtta_times = []
    tts_times = []
    e2e_times = []

    for i in range(num_runs):
        p = VOICE_TEST_PROMPTS[i % len(VOICE_TEST_PROMPTS)]
        t_total_0 = time.perf_counter_ns()

        # 1. STT Call
        t_stt_0 = time.perf_counter_ns()
        try:
            stt_res = await stt_engine.transcribe_audio(dummy_wav_bytes, language_hint=p["hint"])
            stt_ms = (time.perf_counter_ns() - t_stt_0) / 1_000_000.0
            query_text = stt_res.text or p["text"]
        except Exception as e:
            if not is_test_mode:
                print(f"[!] Real STT call failed on run {i}: {e}")
                sys.exit(1)
            query_text = p["text"]
            stt_ms = 0.01

        # 2. FastPath QTTA Call
        req = QueryRequest(query=query_text, language=p["lang_code"])
        resp, audit_meta = await fast_path_engine.execute_fast_path(req, disable_cache=True)
        qtta_ms = audit_meta["ttfa_ms"]

        # 3. TTS Call
        t_tts_0 = time.perf_counter_ns()
        try:
            tts_res = await tts_engine.synthesize_speech(text=resp.answer, language=p["hint"])
            tts_ms = (time.perf_counter_ns() - t_tts_0) / 1_000_000.0
        except Exception as e:
            if not is_test_mode:
                print(f"[!] Real TTS call failed on run {i}: {e}")
                sys.exit(1)
            tts_ms = 0.01

        e2e_ms = (time.perf_counter_ns() - t_total_0) / 1_000_000.0

        stt_times.append(stt_ms)
        qtta_times.append(qtta_ms)
        tts_times.append(tts_ms)
        e2e_times.append(e2e_ms)

    def calc_p(arr):
        a = np.array(arr)
        return {
            "mean": round(float(np.mean(a)), 2),
            "p50": round(float(np.percentile(a, 50)), 2),
            "p95": round(float(np.percentile(a, 95)), 2),
            "p100": round(float(np.max(a)), 2)
        }

    report_data = {
        "benchmark_name": "SHRUTI Voice Telemetry Audit",
        "mode": "LOCAL_TEST_FIXTURE" if is_test_mode else "REAL_PROVIDER",
        "real_provider": not is_test_mode,
        "performance_claim_valid": not is_test_mode,
        "runs_count": num_runs,
        "metric_a_stt": calc_p(stt_times),
        "metric_b_qtta": calc_p(qtta_times),
        "metric_c_atfa_tts": calc_p(tts_times),
        "metric_d_voice_e2e": calc_p(e2e_times)
    }

    with open(VOICE_JSON, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    md_content = f"""# SHRUTI Voice Telemetry Performance Report

> **Mode**: `{'LOCAL_TEST_FIXTURE (Offline Fixture)' if is_test_mode else 'REAL_PROVIDER (Sarvam Saaras v3 & Bulbul v3)'}`  
> **Real Provider Execution**: `{report_data['real_provider']}`  
> **Valid for Production Performance Claims**: `{report_data['performance_claim_valid']}`

---

## 4-Metric Latency Breakdown (ms)

| Metric | Mean | P50 (Median) | P95 | P100 (Max) | Operational Scope |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Metric A: STT Latency** | `{report_data['metric_a_stt']['mean']}` | **`{report_data['metric_a_stt']['p50']} ms`** | `{report_data['metric_a_stt']['p95']}` | `{report_data['metric_a_stt']['p100']}` | Speech capture to transcript |
| **Metric B: QTTA** | `{report_data['metric_b_qtta']['mean']}` | **`{report_data['metric_b_qtta']['p50']} ms`** | `{report_data['metric_b_qtta']['p95']}` | `{report_data['metric_b_qtta']['p100']}` | Query to grounded trusted answer |
| **Metric C: ATFA (TTS)** | `{report_data['metric_c_atfa_tts']['mean']}` | **`{report_data['metric_c_atfa_tts']['p50']} ms`** | `{report_data['metric_c_atfa_tts']['p95']}` | `{report_data['metric_c_atfa_tts']['p100']}` | Answer to first playable audio byte |
| **Metric D: Voice E2E** | `{report_data['metric_d_voice_e2e']['mean']}` | **`{report_data['metric_d_voice_e2e']['p50']} ms`** | `{report_data['metric_d_voice_e2e']['p95']}` | `{report_data['metric_d_voice_e2e']['p100']}` | Full speech-in to audio-out turn |
"""
    with open(VOICE_MD, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"[✔] Voice Telemetry Benchmark Complete across {num_runs} runs.")
    print(f"    - Mode:       {'LOCAL_TEST_FIXTURE' if is_test_mode else 'REAL_PROVIDER'}")
    print(f"    - STT P50:    {report_data['metric_a_stt']['p50']} ms")
    print(f"    - QTTA P50:   {report_data['metric_b_qtta']['p50']} ms")
    print(f"    - TTS P50:    {report_data['metric_c_atfa_tts']['p50']} ms")
    print(f"    - Voice E2E:  {report_data['metric_d_voice_e2e']['p50']} ms")
    print(f"    - Saved to {VOICE_JSON} and {VOICE_MD}")

if __name__ == "__main__":
    asyncio.run(run_voice_realtime_benchmark(25))
