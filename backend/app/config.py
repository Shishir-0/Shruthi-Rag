"""
SHRUTI Backend Configuration
"""
import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings
    class Settings(BaseSettings):
        APP_NAME: str = "SHRUTI — Voice-First Multilingual RAG"
        ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        SHRUTI_TEST_MODE: bool = os.getenv("SHRUTI_TEST_MODE", "false").lower() == "true"
        CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000")
        SARVAM_API_KEY: Optional[str] = os.getenv("SARVAM_API_KEY", "")
        OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
        QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
        QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
        REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
        REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
        MAX_RAG_CORE_MS: float = 50.0
        DENSE_WEIGHT: float = 0.65
        BM25_WEIGHT: float = 0.35
        TOP_K_DENSE: int = 10
        TOP_K_BM25: int = 10
        TOP_K_FINAL: int = 5
        GROUNDING_THRESHOLD: float = 0.70
        SARVAM_STT_WS_URL: str = os.getenv("SARVAM_STT_WS_URL", "wss://api.sarvam.ai/speech-to-text/ws")
        SARVAM_TTS_URL: str = os.getenv("SARVAM_TTS_URL", "https://api.sarvam.ai/text-to-speech")
except ImportError:
    from pydantic import BaseModel
    class Settings(BaseModel):
        APP_NAME: str = "SHRUTI — Voice-First Multilingual RAG"
        ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        SHRUTI_TEST_MODE: bool = os.getenv("SHRUTI_TEST_MODE", "false").lower() == "true"
        CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000")
        SARVAM_API_KEY: Optional[str] = os.getenv("SARVAM_API_KEY", "")
        OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
        QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
        QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
        REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
        REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
        MAX_RAG_CORE_MS: float = 50.0
        DENSE_WEIGHT: float = 0.65
        BM25_WEIGHT: float = 0.35
        TOP_K_DENSE: int = 10
        TOP_K_BM25: int = 10
        TOP_K_FINAL: int = 5
        GROUNDING_THRESHOLD: float = 0.70
        SARVAM_STT_WS_URL: str = os.getenv("SARVAM_STT_WS_URL", "wss://api.sarvam.ai/speech-to-text/ws")
        SARVAM_TTS_URL: str = os.getenv("SARVAM_TTS_URL", "https://api.sarvam.ai/text-to-speech")

settings = Settings()
