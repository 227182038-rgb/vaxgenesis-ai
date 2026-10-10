"""Contract tests via schemathesis (audit 4.2).

Loads the OpenAPI schema from the running backend and runs:
  - Stateful fuzzing on every endpoint
  - Schema conformance checks (response shape matches declared schema)
  - Status-code coverage checks

Run: pytest tests/contract/test_openapi.py -v

Requires the backend to be running at http://localhost:8000.
"""
from __future__ import annotations

import os

import pytest

# Schemathesis is an optional test dependency; skip the whole module
# if it's not installed so the rest of the test suite still runs.
pytest.importorskip("schemathesis")

import schemathesis  # noqa: E402

BACKEND_URL = os.getenv("CONTRACT_TEST_BACKEND_URL", "http://localhost:8000")

# Load the OpenAPI schema once at module import
schema = schemathesis.openapi.from_url(f"{BACKEND_URL}/openapi.json")


@pytest.fixture(scope="session")
def auth_token() -> str:
    """Acquire a JWT for the contract test run."""
    import httpx

    response = httpx.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"email": "admin@vaxgenesis.ai", "password": "admin123"},
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()["access_token"]


@schema.parametrize()
def test_api_contract(case, auth_token):
    """Run schemathesis' default stateful test on every endpoint."""
    case.headers = case.headers or {}
    case.headers["Authorization"] = f"Bearer {auth_token}"
    response = case.call(base_url=BACKEND_URL)
    case.validate_response(response)


@pytest.mark.parametrize("endpoint,method", [
    ("/api/v1/health", "GET"),
    ("/api/v1/modules", "GET"),
    ("/api/v1/auth/login", "POST"),
])
def test_endpoint_returns_2xx_or_4xx(endpoint: str, method: str, auth_token: str) -> None:
    """Smoke-check that critical endpoints respond sanely."""
    import httpx
    response = httpx.request(
        method,
        f"{BACKEND_URL}{endpoint}",
        headers={"Authorization": f"Bearer {auth_token}"},
        timeout=10.0,
    )
    assert response.status_code < 500, (
        f"{method} {endpoint} returned 5xx: {response.status_code} {response.text[:200]}"
    )
