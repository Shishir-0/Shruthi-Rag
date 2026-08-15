"""
SHRUTI Shared HTTP Client Manager
Provides lifecycle-managed, connection-pooled httpx.AsyncClient instance for REST requests.
"""
import httpx
from typing import Optional

_client: Optional[httpx.AsyncClient] = None

def get_http_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=3.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
    return _client

async def close_http_client():
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None
