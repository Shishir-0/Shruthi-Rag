"""
SHRUTI Query Stability Detector & Speculative Execution Engine
Determines transcript stability, minimum useful token threshold, and triggers speculative retrieval.
"""
import re
from pydantic import BaseModel
from typing import Tuple

class QueryStabilityResult(BaseModel):
    is_stable: bool
    confidence: float
    query_candidate: str
    reason: str

class QueryStabilityDetector:
    MIN_TOKEN_THRESHOLD = 3

    def evaluate_transcript(self, raw_transcript: str) -> QueryStabilityResult:
        clean = raw_transcript.strip()
        tokens = [t for t in clean.split() if len(t) > 1]

        if len(tokens) < self.MIN_TOKEN_THRESHOLD:
            return QueryStabilityResult(
                is_stable=False,
                confidence=0.40,
                query_candidate=clean,
                reason=f"Transcript token count ({len(tokens)}) below minimum threshold ({self.MIN_TOKEN_THRESHOLD})."
            )

        # Check trailing sentence end markers or stable clause structure
        has_punctuation = bool(re.search(r'[।\.\!\?]$', clean))
        confidence = 0.96 if has_punctuation else 0.88

        return QueryStabilityResult(
            is_stable=True,
            confidence=confidence,
            query_candidate=clean,
            reason="Transcript meets stability threshold for speculative execution."
        )

stability_detector = QueryStabilityDetector()
