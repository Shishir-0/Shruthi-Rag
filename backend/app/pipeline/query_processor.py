"""
SHRUTI Query Processing System
Implements QueryNormalizer, QueryLanguageDetector, QueryClassifier, and QueryRewriter.
"""
import re
from typing import Dict, Any, Tuple

# --- Script ranges for Indic Language Detection ---
INDIC_SCRIPT_RANGES = {
    "hi": (0x0900, 0x097F),  # Devanagari (Hindi, Marathi)
    "gu": (0x0A80, 0x0AFF),  # Gujarati
    "bn": (0x0980, 0x09FF),  # Bengali
    "ta": (0x0B80, 0x0BFF),  # Tamil
    "te": (0x0C00, 0x0C7F),  # Telugu
    "ml": (0x0D00, 0x0D7F),  # Malayalam
    "kn": (0x0C80, 0x0CFF),  # Kannada
    "pa": (0x0A00, 0x0A7F),  # Gurmukhi / Punjabi
}

class QueryNormalizer:
    @staticmethod
    def normalize(query: str) -> str:
        text = query.strip()
        text = re.sub(r'\s+', ' ', text)
        return text

class QueryLanguageDetector:
    @staticmethod
    def detect_language(text: str) -> str:
        counts = {lang: 0 for lang in INDIC_SCRIPT_RANGES}
        english_chars = 0
        total_chars = 0

        for ch in text:
            code = ord(ch)
            if ch.isalpha():
                total_chars += 1
                if 'a' <= ch.lower() <= 'z':
                    english_chars += 1
                else:
                    for lang, (start, end) in INDIC_SCRIPT_RANGES.items():
                        if start <= code <= end:
                            counts[lang] += 1
                            break

        if total_chars == 0:
            return "en"

        max_lang = max(counts, key=counts.get)
        if counts[max_lang] > 0:
            return max_lang
        
        return "en"

class QueryClassifier:
    OFF_TOPIC_KEYWORDS = ["joke", "weather", "recipe", "song", "movie", "chutkula", "kavita", "gaana"]
    UNSAFE_PATTERNS = [
        r"ignore previous instructions", r"system prompt", r"bypass", r"jailbreak",
        r"drop database", r"delete all", r"hack", r"weapon"
    ]
    GREETING_WORDS = ["hello", "hi", "namaste", "kem cho", "vanakkam", "namaskar", "kemon achen"]

    @classmethod
    def classify(cls, query: str) -> Tuple[str, float]:
        q_lower = query.lower()

        # Unsafe check
        for pattern in cls.UNSAFE_PATTERNS:
            if re.search(pattern, q_lower):
                return "UNSAFE", 0.99

        # Greeting check
        if any(g in q_lower for g in cls.GREETING_WORDS) and len(query.split()) <= 3:
            return "GREETING", 0.95

        # Off topic check
        if any(kw in q_lower for kw in cls.OFF_TOPIC_KEYWORDS):
            return "OFF_TOPIC", 0.92

        # Ambiguous check
        if query.strip().lower() in ["explain that", "what", "tell me more", "why"]:
            return "AMBIGUOUS", 0.85

        return "ANSWERABLE", 0.95

class QueryRewriter:
    @staticmethod
    def expand_query(query: str, language: str) -> str:
        # Adds language-specific synonyms / domain context for robust BM25/Dense match
        expanded = query
        if language == "hi" and "आयुष्मान" in query:
            expanded += " ABHA राष्ट्रीय डिजिटल स्वास्थ्य मिशन ABDM"
        elif language == "gu" and "ગિફ્ટ" in query:
            expanded += " GIFT City Gujarat IFSC"
        elif language == "bn" and "সুন্দরবন" in query:
            expanded += " Sundarbans mangrove Royal Bengal Tiger"
        elif language == "ta" and "கோவில்" in query:
            expanded += " Brihadisvara Temple Tanjavur Chola"
        return expanded

class QueryProcessor:
    def process(self, raw_query: str) -> Dict[str, Any]:
        normalized = QueryNormalizer.normalize(raw_query)
        language = QueryLanguageDetector.detect_language(normalized)
        q_class, confidence = QueryClassifier.classify(normalized)
        retrieval_query = QueryRewriter.expand_query(normalized, language)

        return {
            "original_query": raw_query,
            "normalized_query": normalized,
            "detected_language": language,
            "query_type": q_class,
            "classification_confidence": confidence,
            "retrieval_query": retrieval_query
        }

query_processor = QueryProcessor()
