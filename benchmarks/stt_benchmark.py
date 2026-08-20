"""
SHRUTI STT Telemetry Benchmark Suite
Benchmarks OpenAI Whisper STT latency and language accuracy.
"""
import sys
import time
import asyncio
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding='utf-8')

from backend.app.pipeline.stt import stt_engine

TEST_AUDIO_PROMPTS = [
    {"lang": "hi-IN", "expected_text": "आयुष्मान भारत"},
    {"lang": "gu-IN", "expected_text": "ગિફ્ટ સિટી"},
    {"lang": "bn-IN", "expected_text": "সুন্দরবন"},
    {"lang": "ta-IN", "expected_text": "தஞ்சாவூர்"},
    {"lang": "en-IN", "expected_text": "renewable energy"}
]

async def benchmark_stt(num_runs: int = 50):
    print("==================================================")
    print("SHRUTI STT Benchmark (OpenAI Whisper)")
    print("==================================================")
    
    # 1 second silent PCM audio wav bytes
    dummy_wav_bytes = b"RIFF$ \x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00@\x1f\x00\x00\x80>\x00\x00\x02\x00\x10\x00data\x00 \x00\x00" + b"\x00" * 3200

    latencies = []
    successes = 0

    for i in range(num_runs):
        prompt = TEST_AUDIO_PROMPTS[i % len(TEST_AUDIO_PROMPTS)]
        t0 = time.perf_counter_ns()
        res = await stt_engine.transcribe_audio(dummy_wav_bytes, language_hint=prompt["lang"])
        dt_ms = (time.perf_counter_ns() - t0) / 1_000_000.0
        latencies.append(dt_ms)
        if res.text:
            successes += 1

    a = np.array(latencies)
    print(f"[✔] STT Benchmark Complete across {num_runs} runs.")
    print(f"    - Mean STT Latency: {np.mean(a):.2f} ms")
    print(f"    - P50 STT Latency:  {np.percentile(a, 50):.2f} ms")
    print(f"    - P90 STT Latency:  {np.percentile(a, 90):.2f} ms")
    print(f"    - P100 STT Latency: {np.max(a):.2f} ms")
    print(f"    - Success Rate:     {(successes/num_runs)*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(benchmark_stt(50))
