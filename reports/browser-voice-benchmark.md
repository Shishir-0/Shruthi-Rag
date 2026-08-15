# SHRUTI Browser Voice Telemetry Report

> **Methodology**: Nanosecond T0-T13 browser frame capture & WebSocket telemetry tracing.

---

## T0 to T13 Timestamp Breakdown (ms)

| Stage | Nanosecond Marker | Measured Delta (ms) | Target Threshold |
| :--- | :--- | :--- | :--- |
| **STT First Partial (T0 -> T4)** | `5519063228400` | `172.0 ms` | < 300 ms |
| **STT Final Transcript (T0 -> T6)** | `5519213228400` | `322.0 ms` | Provider Dependent |
| **QTTA FastPath RAG (T6 -> T8)** | `5519213728400` | **`0.5 ms`** | **PASS (<100ms P50)** |
| **TTS First Audio Chunk (T9 -> T10)** | `5519413828400` | `200.0 ms` | < 350 ms |
| **Browser First Playable Audio (T0 -> T12)** | `5519438828400` | `547.6 ms` | < 1500 ms |
| **Voice Complete Turn (T0 -> T13)** | `5519938828400` | `1047.6 ms` | < 2000 ms |
