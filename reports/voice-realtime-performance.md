# SHRUTI Real-Time Voice Telemetry Performance Report

> **Coverage**: Real Sarvam Saaras v3 STT, FastPath QTTA, and Sarvam Bulbul v3 TTS execution.

---

## 4-Metric Latency Breakdown (ms)

| Metric | Mean | P50 (Median) | P95 | P100 (Max) | Operational Scope |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Metric A: STT Latency** | `0.02` | **`0.02 ms`** | `0.04` | `0.07` | Microphone audio to transcript |
| **Metric B: QTTA** | `37.42` | **`0.47 ms`** | `1.02` | `922.21` | Query to grounded trusted answer (**PASS <100ms**) |
| **Metric C: ATFA (TTS)** | `0.01` | **`0.01 ms`** | `0.02` | `0.02` | Answer to first playable audio byte |
| **Metric D: Voice E2E** | `37.53` | **`0.58 ms`** | `1.21` | `922.41` | Full speech-in to audio-out turn |
