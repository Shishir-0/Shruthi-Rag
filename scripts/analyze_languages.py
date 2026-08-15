"""
SHRUTI — Dataset Analysis & Language Distribution Script
Computes comprehensive dataset statistics and outputs dataset-analysis.json & dataset-analysis.md.
"""
import os
import sys
import json
import numpy as np
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')


DATA_DIR = Path(__file__).parent.parent / "data"
REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = DATA_DIR / "msmarco_xi_sampled.jsonl"
JSON_REPORT = REPORTS_DIR / "dataset-analysis.json"
MD_REPORT = REPORTS_DIR / "dataset-analysis.md"

def analyze_dataset():
    print("==================================================")
    print("SHRUTI Data Analyzer & Statistical Profiler")
    print("==================================================")
    
    if not INPUT_FILE.exists():
        print(f"[-] Input file {INPUT_FILE} not found. Run download_dataset.py first.")
        return

    records = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    total_records = len(records)
    empty_records = 0
    malformed_records = 0
    texts_seen = set()
    duplicate_records = 0

    language_counts = {}
    char_lengths = []
    token_lengths = []
    lang_char_lengths = {}
    lang_token_lengths = {}
    metadata_count = 0

    for rec in records:
        text = rec.get("text", "")
        if not text:
            empty_records += 1
            continue
        
        if text in texts_seen:
            duplicate_records += 1
        else:
            texts_seen.add(text)

        lang = rec.get("language", "unknown").lower()
        language_counts[lang] = language_counts.get(lang, 0) + 1

        c_len = len(text)
        t_len = len(text.split())
        char_lengths.append(c_len)
        token_lengths.append(t_len)

        if lang not in lang_char_lengths:
            lang_char_lengths[lang] = []
            lang_token_lengths[lang] = []
        lang_char_lengths[lang].append(c_len)
        lang_token_lengths[lang].append(t_len)

        if rec.get("metadata") or rec.get("source"):
            metadata_count += 1

    duplicate_pct = (duplicate_records / total_records * 100) if total_records else 0.0
    metadata_availability_pct = (metadata_count / total_records * 100) if total_records else 0.0

    # Percentiles
    p50_tokens = float(np.percentile(token_lengths, 50)) if token_lengths else 0.0
    p75_tokens = float(np.percentile(token_lengths, 75)) if token_lengths else 0.0
    p90_tokens = float(np.percentile(token_lengths, 90)) if token_lengths else 0.0
    p99_tokens = float(np.percentile(token_lengths, 99)) if token_lengths else 0.0

    p50_chars = float(np.percentile(char_lengths, 50)) if char_lengths else 0.0
    p75_chars = float(np.percentile(char_lengths, 75)) if char_lengths else 0.0
    p90_chars = float(np.percentile(char_lengths, 90)) if char_lengths else 0.0
    p99_chars = float(np.percentile(char_lengths, 99)) if char_lengths else 0.0

    lang_stats = {}
    for lang in language_counts:
        t_arr = lang_token_lengths[lang]
        c_arr = lang_char_lengths[lang]
        lang_stats[lang] = {
            "count": language_counts[lang],
            "percentage": round(language_counts[lang] / total_records * 100, 2),
            "avg_tokens": round(float(np.mean(t_arr)), 2),
            "avg_chars": round(float(np.mean(c_arr)), 2),
            "p50_tokens": round(float(np.percentile(t_arr, 50)), 2),
            "p90_tokens": round(float(np.percentile(t_arr, 90)), 2),
        }

    report_data = {
        "dataset_name": "ai4bharat/MSMARCO-XI (SHRUTI Profiled)",
        "total_records": total_records,
        "empty_records": empty_records,
        "malformed_records": malformed_records,
        "duplicate_records": duplicate_records,
        "duplicate_percentage": round(duplicate_pct, 2),
        "metadata_availability_percentage": round(metadata_availability_pct, 2),
        "overall_token_stats": {
            "mean": round(float(np.mean(token_lengths)), 2) if token_lengths else 0,
            "min": int(np.min(token_lengths)) if token_lengths else 0,
            "max": int(np.max(token_lengths)) if token_lengths else 0,
            "p50": p50_tokens,
            "p75": p75_tokens,
            "p90": p90_tokens,
            "p99": p99_tokens,
        },
        "overall_char_stats": {
            "mean": round(float(np.mean(char_lengths)), 2) if char_lengths else 0,
            "p50": p50_chars,
            "p90": p90_chars,
        },
        "language_distribution": lang_stats
    }

    # Save JSON Report
    with open(JSON_REPORT, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)


    # Save Markdown Report
    md_content = f"""# SHRUTI Dataset Analysis Report

## Overview
- **Dataset**: `ai4bharat/MSMARCO-XI`
- **Total Ingested Records**: `{total_records}`
- **Duplicate Records**: `{duplicate_records}` ({duplicate_pct:.2f}%)
- **Empty / Malformed Records**: `{empty_records}` / `{malformed_records}`
- **Metadata Availability**: `{metadata_availability_pct:.2f}%`

## Passage Length Statistics (Tokens)
| Metric | Token Count | Character Count |
| :--- | :--- | :--- |
| **Mean** | `{report_data['overall_token_stats']['mean']}` | `{report_data['overall_char_stats']['mean']}` |
| **P50 (Median)** | `{p50_tokens}` | `{p50_chars}` |
| **P75** | `{p75_tokens}` | `{p75_chars}` |
| **P90** | `{p90_tokens}` | `{p90_chars}` |
| **P99** | `{p99_tokens}` | `{p99_chars}` |

## Language Distribution & Statistics
| Language | Code | Passage Count | Percentage | Avg Tokens | P50 Tokens | P90 Tokens |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    lang_names = {
        "hi": "Hindi", "gu": "Gujarati", "bn": "Bengali", "ta": "Tamil",
        "en": "English", "te": "Telugu", "mr": "Marathi", "pa": "Punjabi", "ml": "Malayalam"
    }

    for lang, st in lang_stats.items():
        lname = lang_names.get(lang, lang.upper())
        md_content += f"| **{lname}** | `{lang}` | `{st['count']}` | `{st['percentage']}%` | `{st['avg_tokens']}` | `{st['p50_tokens']}` | `{st['p90_tokens']}` |\n"

    md_content += "\n---\n*Report generated automatically by `scripts/analyze_languages.py`*\n"

    with open(MD_REPORT, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"[✔] Analysis complete. Reports generated:")
    print(f"    - JSON: {JSON_REPORT}")
    print(f"    - Markdown: {MD_REPORT}")

if __name__ == "__main__":
    analyze_dataset()
