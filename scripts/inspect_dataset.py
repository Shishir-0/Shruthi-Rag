"""
SHRUTI — Dataset Inspector Script
Inspects ai4bharat/MSMARCO-XI dataset schema, configs, and sample records.
"""
import sys
import json
import requests

DATASET_NAME = "ai4bharat/MSMARCO-XI"

def inspect_dataset():
    print(f"==================================================")
    print(f"SHRUTI Dataset Inspector: {DATASET_NAME}")
    print(f"==================================================")
    
    # 1. Fetch splits
    splits_url = f"https://datasets-server.huggingface.co/splits?dataset={DATASET_NAME}"
    try:
        r = requests.get(splits_url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            splits = data.get("splits", [])
            print(f"[+] Available Dataset Splits: {len(splits)}")
            for s in splits:
                print(f"    - Config: {s.get('config')}, Split: {s.get('split')}")
        else:
            print(f"[-] Failed to fetch splits HTTP {r.status_code}")
    except Exception as e:
        print(f"[-] Error fetching splits: {e}")

    # 2. Fetch parquet files metadata
    parquet_url = f"https://datasets-server.huggingface.co/parquet?dataset={DATASET_NAME}"
    try:
        r = requests.get(parquet_url, timeout=15)
        if r.status_code == 200:
            files = r.json().get("parquet_files", [])
            print(f"\n[+] Parquet Files Count: {len(files)}")
            total_size_bytes = sum(f.get("size", 0) for f in files)
            print(f"[+] Total Remote Dataset Size: {total_size_bytes / (1024**3):.2f} GB")
            for f in files[:5]:
                print(f"    - File: {f.get('filename')}, Size: {f.get('size', 0)/(1024**2):.1f} MB")
        else:
            print(f"[-] Failed to fetch parquet list: HTTP {r.status_code}")
    except Exception as e:
        print(f"[-] Error fetching parquet files: {e}")

if __name__ == "__main__":
    inspect_dataset()
