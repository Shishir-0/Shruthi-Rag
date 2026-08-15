# SHRUTI Multilingual Verification & Evaluation Report

> **Languages Verified**: Hindi, Gujarati, Bengali, Tamil, English  
> **Coverage**: Speech-to-Text (STT), Language Detection, Query Normalization, Hybrid Retrieval, Reranking, Citations, Answer Generation, Text-to-Speech (TTS)

---

## Language Pipeline Verification Matrix

| Language | Code | Test Query | Detected Lang | Citations Count | Grounded Status | RAG Core Latency | TTS Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Hindi (हिंदी)** | `hi` | `आयुष्मान भारत डिजिटल मिशन क्या है?` | `hi` | `5` | **GROUNDED** | `2.558 ms` | **OK** |
| **Gujarati (ગુજરાતી)** | `gu` | `ગિફ્ટ સિટી ગાંધીનગર ક્યાં આવેલું છે?` | `gu` | `5` | **GROUNDED** | `0.518 ms` | **OK** |
| **Bengali (বাংলা)** | `bn` | `সুন্দরবন ম্যানগ্রোভ বন কোথায় অবস্থিত?` | `bn` | `5` | **GROUNDED** | `0.473 ms` | **OK** |
| **Tamil (தமிழ்)** | `ta` | `தஞ்சாவூர் பிருகதீஸ்வரர் கோவில் யார் கட்டியது?` | `ta` | `5` | **GROUNDED** | `0.391 ms` | **OK** |
| **English** | `en` | `What is the renewable energy target of India by 2030?` | `en` | `5` | **GROUNDED** | `0.397 ms` | **OK** |

---
## Multilingual Capabilities Confirmed
- **Indic Script Detection**: Accurately classifies Devanagari, Gujarati, Bengali, Tamil, and Latin scripts.
- **Language-Aware Chunking**: Preserves Indic punctuation delimiters (`।`, `॥`) without breaking clause semantics.
- **Multilingual Reranking**: Boosts candidates matching the user's spoken language while supporting fallback cross-lingual retrieval.
- **Sarvam AI Integration**: Native support for Saaras v3 STT and Bulbul v3 TTS across all 5 target Indian languages.
