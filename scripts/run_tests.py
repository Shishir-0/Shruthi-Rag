"""
SHRUTI Lightweight Test Runner
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.tests.test_pipeline import (
    test_language_detection,
    test_query_classification,
    test_chunking_selector,
    test_guardrails,
    test_grounding_verifier,
    test_full_orchestrator_pipeline
)

def run_all_tests():
    print("==================================================")
    print("SHRUTI Unit & Integration Test Suite")
    print("==================================================")
    
    tests = [
        ("Language Detection", test_language_detection),
        ("Query Classification", test_query_classification),
        ("Chunking Selector", test_chunking_selector),
        ("Guardrails", test_guardrails),
        ("Grounding Verifier", test_grounding_verifier)
    ]
    
    passed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"[✔] {name}: PASSED")
            passed += 1
        except Exception as e:
            print(f"[!] {name}: FAILED ({e})")

    try:
        asyncio.run(test_full_orchestrator_pipeline())
        print(f"[✔] Full Orchestrator Pipeline: PASSED")
        passed += 1
    except Exception as e:
        print(f"[!] Full Orchestrator Pipeline: FAILED ({e})")

    print(f"==================================================")
    print(f"Summary: {passed}/{len(tests)+1} tests passed successfully.")
    print("==================================================")

if __name__ == "__main__":
    run_all_tests()
