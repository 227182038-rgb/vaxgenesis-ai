"""LIMS client for VaxGenesis backend (audit 6.1).

HTTP client that talks to the mock LIMS (or a real LIMS at the same URL).
Used by `vaxgenesis/learning/service.py` to push assay requests and pull
results.
"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx

from vaxgenesis.core.logging import get_logger

logger = get_logger(__name__)


class LIMSClient:
    """Async client for the LIMS REST API."""

    def __init__(self, base_url: str, api_token: str | None = None, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"User-Agent": "VaxGenesis-AI/1.0"}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ============================================================
    # Assay lifecycle
    # ============================================================

    async def submit_assay_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /assays — submit an assay request to the LIMS."""
        client = await self._get_client()
        try:
            response = await client.post("/assays", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("lims.submit_failed", status=exc.response.status_code, body=exc.response.text[:500])
            raise
        except httpx.RequestError as exc:
            logger.error("lims.submit_request_error", error=str(exc))
            raise

    async def get_assay(self, assay_id: str) -> dict[str, Any]:
        """GET /assays/{id} — poll assay status."""
        client = await self._get_client()
        response = await client.get(f"/assays/{assay_id}")
        response.raise_for_status()
        return response.json()

    async def list_assays(
        self, candidate_id: str | None = None, status_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """GET /assays — list assays, optionally filtered."""
        client = await self._get_client()
        params: dict[str, str] = {}
        if candidate_id:
            params["candidate_id"] = candidate_id
        if status_filter:
            params["status_filter"] = status_filter
        response = await client.get("/assays", params=params)
        response.raise_for_status()
        return response.json()

    async def submit_result(
        self, assay_id: str, value: float, unit: str, **kwargs: Any,
    ) -> dict[str, Any]:
        """POST /assays/{id}/result — submit a lab result."""
        client = await self._get_client()
        payload = {"value": value, "unit": unit, **kwargs}
        response = await client.post(f"/assays/{assay_id}/result", json=payload)
        response.raise_for_status()
        return response.json()

    async def wait_for_completion(
        self, assay_id: str, timeout_seconds: int = 600, poll_interval: int = 5,
    ) -> dict[str, Any]:
        """Poll until the assay is completed (or timeout)."""
        elapsed = 0
        while elapsed < timeout_seconds:
            assay = await self.get_assay(assay_id)
            if assay.get("status") == "completed":
                return assay
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        raise TimeoutError(f"Assay {assay_id} not completed within {timeout_seconds}s")

    async def health(self) -> bool:
        """Quick health check."""
        try:
            client = await self._get_client()
            response = await client.get("/health", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False
