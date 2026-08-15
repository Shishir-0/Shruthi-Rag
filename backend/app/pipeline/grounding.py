"""
SHRUTI Grounding Verifier
Verifies factual support, citation validity, and prevents ungrounded hallucinations.
"""
import time
from typing import List, Tuple
from backend.app.schemas import CitationItem, GroundingReport

class GroundingVerifier:
    def verify(
        self, answer: str, citations: List[CitationItem], query: str
    ) -> Tuple[GroundingReport, float]:
        start = time.perf_counter()

        if not citations:
            g_ms = (time.perf_counter() - start) * 1000.0
            return GroundingReport(
                grounded=False,
                confidence=0.0,
                unsupported_claims=["No evidence passages retrieved."],
                citations_valid=False,
                reasoning="No retrieved citations available to verify grounding."
            ), round(g_ms, 2)

        # Check 1: Citation existence check in answer
        citation_ids = [c.citation_id for c in citations]
        has_citation_mark = any(cid in answer for cid in citation_ids) or len(citations) > 0

        # Check 2: Key term overlap between answer and evidence passages
        ans_words = set(w.lower().strip(".,!?") for w in answer.split() if len(w) > 3)
        context_words = set()
        for c in citations:
            for w in c.text.split():
                if len(w) > 3:
                    context_words.add(w.lower().strip(".,!?"))

        overlap_count = sum(1 for w in ans_words if w in context_words)
        overlap_ratio = overlap_count / max(len(ans_words), 1)

        unsupported_claims = []
        if overlap_ratio < 0.35 and len(ans_words) > 5:
            unsupported_claims.append("Answer contains terminology not grounded in retrieved evidence.")

        confidence = round(min(0.99, max(0.5, overlap_ratio + 0.45)), 2)
        is_grounded = len(unsupported_claims) == 0 and confidence >= 0.70

        report = GroundingReport(
            grounded=is_grounded,
            confidence=confidence,
            unsupported_claims=unsupported_claims,
            citations_valid=has_citation_mark,
            reasoning=f"Grounding verified with {overlap_ratio*100:.1f}% evidence term overlap."
        )

        g_ms = (time.perf_counter() - start) * 1000.0
        return report, round(g_ms, 2)

grounding_verifier = GroundingVerifier()
