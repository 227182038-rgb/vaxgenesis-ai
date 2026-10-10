"""HTTP client pool for external API calls."""
import httpx
from typing import Any

class ExternalAPIClient:
    def __init__(self, base_url: str, api_key: str | None = None, timeout: float = 30.0):
        headers = {"User-Agent": "VaxGenesis-AI/2.0"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.AsyncClient(base_url=base_url, headers=headers, timeout=timeout)

    async def get(self, path, **kwargs):
        return await self._client.get(path, **kwargs)

    async def post(self, path, **kwargs):
        return await self._client.post(path, **kwargs)

    async def close(self):
        await self._client.aclose()
