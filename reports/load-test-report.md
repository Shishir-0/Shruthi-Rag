# SHRUTI Concurrent Multi-User Load Test Report

> **Concurrency Levels Tested**: 1, 5, and 10 Concurrent Users  
> **Status**: **PASSED (ZERO ERRORS ACROSS ALL CONCURRENCY LEVELS)**

---

## Concurrency Performance Matrix

| Concurrency Level | Total Requests | Error Count | P50 Latency (ms) | P95 Latency (ms) | Max Latency (ms) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1 User** | `5` | `0` | **`0.46 ms`** | **`639.88 ms`** | `799.69 ms` | **PASS** |
| **5 Concurrent Users** | `25` | `0` | **`2.13 ms`** | **`2.26 ms`** | `2.28 ms` | **PASS** |
| **10 Concurrent Users** | `50` | `0` | **`4.25 ms`** | **`4.77 ms`** | `4.8 ms` | **PASS** |
