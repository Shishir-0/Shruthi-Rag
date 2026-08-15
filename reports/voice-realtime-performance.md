# SHRUTI Voice Telemetry Performance Report

> **Mode**: `LOCAL_TEST_FIXTURE (Offline Fixture)`  
> **Real Provider Execution**: `False`  
> **Valid for Production Performance Claims**: `False`

---

## 4-Metric Latency Breakdown (ms)

| Metric | Mean | P50 (Median) | P95 | P100 (Max) | Operational Scope |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Metric A: STT Latency** | `0.01` | **`0.01 ms`** | `0.01` | `0.01` | Speech capture to transcript |
| **Metric B: QTTA** | `36.01` | **`0.4 ms`** | `0.62` | `890.22` | Query to grounded trusted answer |
| **Metric C: ATFA (TTS)** | `0.01` | **`0.01 ms`** | `0.01` | `0.01` | Answer to first playable audio byte |
| **Metric D: Voice E2E** | `36.09` | **`0.46 ms`** | `0.73` | `890.42` | Full speech-in to audio-out turn |
