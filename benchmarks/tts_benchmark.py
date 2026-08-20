"""
SHRUTI TTS Telemetry Benchmark Suite
Benchmarks OpenAI Speech TTS synthesis latency.
"""
import sys
import time
import asyncio
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding='utf-8')

from backend.app.pipeline.tts import tts_engine

TEST_TTS_PHRASES = [
    {"text": "आयुष्मान भारत डिजिटल मिशन का मुख्य उद्देश्य भारत के स्वास्थ्य क्षेत्र को एकीकृत करना है।", "lang": "hi-IN"},
    {"text": "ગુજરાત ઇન્ટરનેશનલ ફાઇનાન્સ ટેક-સિટી ભારતના ગાંધીનગરમાં આવેલું છે.", "lang": "gu-IN"},
    {"text": "সুন্দরবন বঙ্গোপসাগরের অববাহিকায় গঠিত বিশ্বের বৃহত্তম ম্যানগ্রোভ বন।", "lang": "bn-IN"},
    {"text": "தஞ்சாவூர் பிருகதீஸ்வரர் கோவில் சோழர்களால் கட்டப்பட்டது.", "lang": "ta-IN"},
    {"text": "India targets achieving 500 GW of non-fossil renewable energy capacity by 2030.", "lang": "en-IN"}
]

async def benchmark_tts(num_runs: int = 50):
    print("==================================================")
    print("SHRUTI TTS Benchmark (OpenAI Speech)")
    print("==================================================")

    latencies = []
    successes = 0

    for i in range(num_runs):
        phrase = TEST_TTS_PHRASES[i % len(TEST_TTS_PHRASES)]
        t0 = time.perf_counter_ns()
        res = await tts_engine.synthesize_speech(text=phrase["text"], language=phrase["lang"])
        dt_ms = (time.perf_counter_ns() - t0) / 1_000_000.0
        latencies.append(dt_ms)
        if res.audio_base64:
            successes += 1

    a = np.array(latencies)
    print(f"[✔] TTS Benchmark Complete across {num_runs} runs.")
    print(f"    - Mean TTS Latency: {np.mean(a):.2f} ms")
    print(f"    - P50 TTS Latency:  {np.percentile(a, 50):.2f} ms")
    print(f"    - P90 TTS Latency:  {np.percentile(a, 90):.2f} ms")
    print(f"    - P100 TTS Latency: {np.max(a):.2f} ms")
    print(f"    - Success Rate:     {(successes/num_runs)*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(benchmark_tts(50))
