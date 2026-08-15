"""
SHRUTI Two-Tier Answer Generation Engine
Implements Tier 1 Extractive (<20ms) for high-confidence direct matches & Tier 2 Generative synthesis.
"""
import time
import httpx
from typing import List, Tuple, Optional
from backend.app.config import settings
from backend.app.schemas import CitationItem

class TwoTierAnswerEngine:
    def __init__(self, openai_key: Optional[str] = None):
        self.openai_key = openai_key or settings.OPENAI_API_KEY

    async def generate_answer(
        self, query: str, language: str, citations: List[CitationItem], context_text: str
    ) -> Tuple[str, str, float]:
        start = time.perf_counter()

        if not citations:
            gen_ms = (time.perf_counter() - start) * 1000.0
            fallback_msgs = {
                "hi": "उपलब्ध स्रोतों में इस प्रश्न का उत्तर देने के लिए पर्याप्त जानकारी नहीं है।",
                "gu": "પ્રાપ્ય સ્રોતોમાં આ પ્રશ્નનો જવાબ આપવા માટે પૂરતી માહિતી નથી.",
                "bn": "উপলব্ধ উৎসগুলিতে এই প্রশ্নের উত্তর দেওয়ার জন্য পর্যাপ্ত তথ্য নেই।",
                "ta": "கிடைக்கக்கூடிய ஆதாரங்களில் இந்த கேள்விக்கு பதிலளிக்க போதுமான தகவல் இல்லை.",
                "en": "The available knowledge base sources do not contain enough evidence to answer this question."
            }
            return fallback_msgs.get(language, fallback_msgs["en"]), "Tier 1 Refusal", round(gen_ms, 2)

        top_citation = citations[0]

        # Tier 1 — Extractive High-Speed Path (<20ms)
        # If top citation has high confidence score (>= 0.65), format & paraphrase top evidence directly
        if top_citation.final_score >= 0.65 or not self.openai_key or len(self.openai_key) < 5:
            text = top_citation.text
            # Extract first 2 relevant sentences
            sentences = [s.strip() for s in text.replace("।", ".").split(".") if s.strip()]
            extracted_summary = ". ".join(sentences[:3]) + "."
            answer_text = f"{extracted_summary} {top_citation.citation_id}"

            gen_ms = (time.perf_counter() - start) * 1000.0
            return answer_text, "Tier 1 Extractive", round(gen_ms, 2)

        # Tier 2 — Generative Path (via LLM API call)
        try:
            system_prompt = (
                "You are SHRUTI, a voice-first multilingual assistant for India. "
                "Answer ONLY using the provided retrieved context. "
                "Do NOT use outside knowledge. Do NOT invent facts or citations. "
                f"Answer in the user's language ({language}). Keep your answer concise and clear."
            )
            user_prompt = f"Context:\n{context_text}\n\nQuestion: {query}"

            async with httpx.AsyncClient(timeout=8.0) as client:
                headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 200
                }
                resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    ans = data["choices"][0]["message"]["content"].strip()
                    gen_ms = (time.perf_counter() - start) * 1000.0
                    return ans, "Tier 2 Generative", round(gen_ms, 2)
        except Exception as e:
            print(f"[!] Tier 2 LLM call failed: {e}. Falling back to Tier 1 Extractive.")

        # Fallback to Tier 1
        sentences = [s.strip() for s in top_citation.text.replace("।", ".").split(".") if s.strip()]
        extracted_summary = ". ".join(sentences[:3]) + "."
        answer_text = f"{extracted_summary} {top_citation.citation_id}"

        gen_ms = (time.perf_counter() - start) * 1000.0
        return answer_text, "Tier 1 Extractive Fallback", round(gen_ms, 2)

answer_engine = TwoTierAnswerEngine()
