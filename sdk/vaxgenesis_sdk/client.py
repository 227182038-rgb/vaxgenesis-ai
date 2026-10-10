"""Main SDK client."""
from __future__ import annotations

from typing import Any

import httpx

from vaxgenesis_sdk.models import (
    Candidate, ModuleInfo, Project, SurveillanceStatus, Token, Variant,
)


class VaxGenesisClient:
    """Typed async client for the VaxGenesis AI REST API.

    Example:
        client = VaxGenesisClient("http://localhost:8000")
        await client.login("admin@vaxgenesis.ai", "admin123")
        projects = await client.projects.list()
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        token: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = token
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._build_headers(),
        )

        # Sub-clients
        self.projects = ProjectsResource(self)
        self.candidates = CandidatesResource(self)
        self.modules = ModulesResource(self)
        self.surveillance = SurveillanceResource(self)
        self.xai = XAIResource(self)

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "User-Agent": "vaxgenesis-sdk/2.0"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def login(self, email: str, password: str) -> Token:
        """Authenticate and store the JWT token."""
        response = await self._client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        response.raise_for_status()
        token_data = response.json()
        self._token = token_data["access_token"]
        self._client.headers["Authorization"] = f"Bearer {self._token}"
        return Token(**token_data)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "VaxGenesisClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def _get(self, path: str, **kwargs: Any) -> dict:
        r = await self._client.get(path, **kwargs)
        r.raise_for_status()
        return r.json()

    async def _post(self, path: str, **kwargs: Any) -> dict:
        r = await self._client.post(path, **kwargs)
        r.raise_for_status()
        return r.json()

    async def health(self) -> dict:
        return await self._get("/api/v1/health")


class _ResourceBase:
    def __init__(self, client: VaxGenesisClient) -> None:
        self._client = client


class ProjectsResource(_ResourceBase):
    async def list(self, page: int = 1, page_size: int = 20) -> dict:
        return await self._client._get(
            "/api/v1/projects", params={"page": page, "page_size": page_size}
        )

    async def get(self, project_id: str) -> Project:
        data = await self._client._get(f"/api/v1/projects/{project_id}")
        return Project(**data)

    async def create(self, name: str, description: str | None = None) -> Project:
        data = await self._client._post(
            "/api/v1/projects",
            json={"name": name, "description": description},
        )
        return Project(**data)


class CandidatesResource(_ResourceBase):
    async def list(self, project_id: str | None = None, page: int = 1, page_size: int = 20) -> dict:
        params = {"page": page, "page_size": page_size}
        if project_id:
            params["project_id"] = project_id
        return await self._client._get("/api/v1/candidates", params=params)

    async def get(self, candidate_id: str) -> Candidate:
        data = await self._client._get(f"/api/v1/candidates/{candidate_id}")
        return Candidate(**data)

    async def create(self, project_id: str, name: str, platform: str = "multi_epitope") -> Candidate:
        data = await self._client._post(
            "/api/v1/candidates",
            json={"project_id": project_id, "name": name, "platform": platform},
        )
        return Candidate(**data)

    async def run_pipeline(
        self,
        candidate_id: str,
        max_iterations: int = 3,
    ) -> dict:
        return await self._client._post(
            "/api/v1/candidates/run-pipeline",
            json={"candidate_id": candidate_id, "max_iterations": max_iterations},
        )

    async def get_passport(self, candidate_id: str) -> dict:
        return await self._client._get(f"/api/v1/reports/{candidate_id}/passport")


class ModulesResource(_ResourceBase):
    async def list(self) -> list[ModuleInfo]:
        data = await self._client._get("/api/v1/modules")
        return [ModuleInfo(**m) for m in data]

    async def get(self, module_id: str) -> ModuleInfo:
        data = await self._client._get(f"/api/v1/modules/{module_id}")
        return ModuleInfo(**data)


class SurveillanceResource(_ResourceBase):
    async def status(self) -> SurveillanceStatus:
        data = await self._client._get("/api/v1/surveillance/status")
        return SurveillanceStatus(**data)

    async def list_variants(self, pathogen_id: str | None = None) -> dict:
        params = {}
        if pathogen_id:
            params["pathogen_id"] = pathogen_id
        return await self._client._get("/api/v1/surveillance/variants", params=params)

    async def ingest(self, pathogen_id: str, name: str, sequence: str, **kwargs: Any) -> Variant:
        data = await self._client._post(
            "/api/v1/surveillance/ingest",
            json={"pathogen_id": pathogen_id, "name": name, "sequence": sequence, **kwargs},
        )
        return Variant(**data)


class XAIResource(_ResourceBase):
    """Explainable AI endpoints (v2.0)."""

    async def get_explanation(self, prediction_id: str) -> dict:
        """Get the XAI explanation for a prediction."""
        return await self._client._get(f"/api/v2/predictions/{prediction_id}/explanation")
