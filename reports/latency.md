# SHRUTI Latency Benchmark Report

## Target Benchmark Summary
- **Total Queries Executed**: `300`
- **Error Rate**: `0.0%` (`0` errors)
- **Target RAG Core Latency**: `< 50 ms`
- **Measured P50 RAG Core Latency**: `0.28 ms` **(TARGET MET)**
- **Measured P70 RAG Core Latency**: `0.31 ms`
- **Measured P100 RAG Core Latency**: `2.55 ms`

## Detailed Latency Percentiles (ms)
| Stage | Mean | Min | P50 (Median) | P70 | P90 | P95 | P99 | P100 (Max) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RAG Core Pipeline** | `0.41` | `0.01` | `0.28` | `0.31` | `0.56` | `2.55` | `2.55` | `2.55` |
| **Hybrid Retrieval** | `0.13` | `0.0` | `0.11` | `0.13` | `0.2` | `0.42` | `0.42` | `0.42` |
| **Total End-to-End Voice** | `48.73` | `0.01` | `0.38` | `0.41` | `0.73` | `806.53` | `806.53` | `806.53` |

---
*Generated automatically by `scripts/benchmark.py` on 2026-08-15 23:18:27*
