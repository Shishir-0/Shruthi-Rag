"""
SHRUTI Ephemeral Realtime Session Endpoint
Generates temporary, ephemeral session credentials via POST https://api.openai.com/v1/realtime/sessions
Ensures OPENAI_API_KEY is never exposed to the frontend browser.
"""
import uuid
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import httpx

from backend.app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Realtime Session Security"])

RETRIEVE_DOCUMENTS_TOOL = {
    "type": "function",
    "name": "retrieve_documents",
    "description": "Searches HH Goa MSMARCO-XI Qdrant + BM25 hybrid vector database for grounded context evidence.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Clean search query extracted from user voice input."
            }
        },
        "required": ["query"]
    }
}

@router.get("/realtime/session")
@router.post("/realtime/session")
async def create_realtime_session() -> Dict[str, Any]:
    """
    Creates an ephemeral session for OpenAI Realtime API.
    Returns client_secret token so the browser can connect directly to OpenAI WebRTC/WebSocket securely.
    """
    api_key = settings.OPENAI_API_KEY
    model = settings.OPENAI_REALTIME_MODEL

    if api_key and len(api_key) > 5 and not settings.SHRUTI_TEST_MODE:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/realtime/sessions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "modalities": ["audio", "text"],
                        "voice": "alloy",
                        "instructions": (
                            "You are SHRUTI, a voice-first multilingual assistant for India. "
                            "You MUST use the retrieve_documents tool whenever answering factual questions or seeking knowledge. "
                            "Never answer from unverified memory when retrieval is required. "
                            "Respond in the language spoken by the user."
                        ),
                        "input_audio_format": "pcm16",
                        "output_audio_format": "pcm16",
                        "turn_detection": {
                            "type": "server_vad",
                            "threshold": 0.5,
                            "prefix_padding_ms": 300,
                            "silence_duration_ms": 500
                        },
                        "tools": [RETRIEVE_DOCUMENTS_TOOL],
                        "tool_choice": "auto"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Successfully generated ephemeral OpenAI Realtime session: {data.get('id')}")
                    return {
                        "session_id": data.get("id"),
                        "client_secret": data.get("client_secret", {}).get("value"),
                        "expires_at": data.get("client_secret", {}).get("expires_at"),
                        "model": model,
                        "status": "ACTIVE"
                    }
                else:
                    logger.error(f"OpenAI session endpoint error {response.status_code}: {response.text}")
        except Exception as err:
            logger.error(f"Failed to connect to OpenAI Realtime session API: {err}")

    # Fallback for TEST MODE or missing key (allows fixture testing)
    if settings.SHRUTI_TEST_MODE:
        mock_id = f"sess_mock_{uuid.uuid4().hex[:12]}"
        return {
            "session_id": mock_id,
            "client_secret": f"ek_test_{uuid.uuid4().hex}",
            "expires_at": 9999999999,
            "model": model,
            "status": "TEST_MODE_EMULATED"
        }

    raise HTTPException(
        status_code=502,
        detail="OpenAI API key is missing or invalid, and SHRUTI_TEST_MODE is disabled."
    )
