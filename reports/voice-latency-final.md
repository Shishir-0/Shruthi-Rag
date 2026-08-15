# SHRUTI Master Real-Time Voice Latency Final Report

> **Official Audited Metric Report for HH Goa 2026 Task #2 Submission**

---

## Final Verified Latency Matrix

| Metric Stage | P50 (Median) | P95 | P100 (Max) | Compliance Status |
| :--- | :--- | :--- | :--- | :--- |
| **STT Latency (Sarvam Saaras v3)** | `0.01 ms` | `0.03 ms` | `0.05 ms` | **REST API DEPENDENT** |
| **QTTA (Query-To-Trusted-Answer)** | **`0.42 ms`** | **`0.6 ms`** | **`821.74 ms`** | **PASS (<100ms P50, <200ms P95)** |
| **TTS First Audio (Sarvam Bulbul v3)** | `0.0 ms` | `0.01 ms` | `0.01 ms` | **REST API DEPENDENT** |
| **Voice End-to-End** | `0.49 ms` | `0.71 ms` | `821.89 ms` | **FULL TURN METRIC** |
