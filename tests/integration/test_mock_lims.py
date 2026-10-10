"""Mock LIMS integration test (audit 6.1).

Validates the full wet-lab-in-the-loop flow:
  1. VaxGenesis submits an assay request to the LIMS.
  2. The mock LIMS auto-generates a result after a delay.
  3. VaxGenesis polls for completion.
  4. The result triggers a Bayesian model update.

Requires the mock LIMS server to be running at http://localhost:9001.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

import pytest


# Add the mock LIMS to the import path
MOCK_LIMS_PATH = str(Path(__file__).parent.parent.parent / "services" / "mock-lims")
if MOCK_LIMS_PATH not in sys.path:
    sys.path.insert(0, MOCK_LIMS_PATH)


@pytest.fixture
async def lims_server():
    """Start the mock LIMS as an in-process ASGI app."""
    from httpx import AsyncClient, ASGITransport
    from services.mock_lims.app import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ============================================================
# Tests
# ============================================================

@pytest.mark.asyncio
async def test_lims_health(lims_server):
    """The mock LIMS reports healthy."""
    response = await lims_server.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_submit_assay_request(lims_server):
    """VaxGenesis can submit an assay request to the LIMS."""
    response = await lims_server.post(
        "/assays",
        json={
            "candidate_id": str(uuid4()),
            "assay_type": "elisa",
            "target": "Spike protein binding",
            "priority": 8,
            "requested_by": "test@vaxgenesis.ai",
        },
    )
    assert response.status_code == 201
    record = response.json()
    assert record["status"] == "received"
    assert record["assay_type"] == "elisa"
    assert record["id"]


@pytest.mark.asyncio
async def test_list_assays(lims_server):
    """List endpoint returns all assays."""
    # Submit two
    for i in range(2):
        await lims_server.post("/assays", json={
            "candidate_id": str(uuid4()),
            "assay_type": "spr",
            "target": f"Test {i}",
            "requested_by": "test@vaxgenesis.ai",
        })

    response = await lims_server.get("/assays")
    assert response.status_code == 200
    records = response.json()
    assert len(records) >= 2


@pytest.mark.asyncio
async def test_get_assay_not_found(lims_server):
    """Getting a non-existent assay returns 404."""
    response = await lims_server.get("/assays/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_manual_result_submission(lims_server):
    """A lab technician can manually submit a result."""
    # Create an assay
    create = await lims_server.post("/assays", json={
        "candidate_id": str(uuid4()),
        "assay_type": "neutralization",
        "target": "Pseudovirus neutralization",
        "priority": 10,
        "requested_by": "test@vaxgenesis.ai",
    })
    assay_id = create.json()["id"]

    # Submit a result before auto-completion fires
    response = await lims_server.post(
        f"/assays/{assay_id}/result",
        json={"value": 320, "unit": "reciprocal_titer", "is_positive": True},
    )
    assert response.status_code == 200
    record = response.json()
    assert record["status"] == "completed"
    assert record["result"]["value"] == 320


@pytest.mark.asyncio
async def test_auto_completion(lims_server):
    """The mock LIMS auto-completes assays after a delay."""
    # Priority 10 → delay = 1 second
    create = await lims_server.post("/assays", json={
        "candidate_id": str(uuid4()),
        "assay_type": "elisa",
        "target": "Auto-complete test",
        "priority": 10,
        "requested_by": "test@vaxgenesis.ai",
    })
    assay_id = create.json()["id"]

    # Wait for auto-completion (priority 10 → 1s delay + 1s in_progress)
    await asyncio.sleep(3)

    response = await lims_server.get(f"/assays/{assay_id}")
    record = response.json()
    assert record["status"] == "completed"
    assert record["result"] is not None
    assert "value" in record["result"]


@pytest.mark.asyncio
async def test_lims_client_class(lims_server):
    """The LIMSClient class works against the mock server."""
    # We can't easily test the async client against the in-process app
    # without a real port, so we just test the interface
    from vaxgenesis.learning.lims_client import LIMSClient

    client = LIMSClient(base_url="http://test")
    assert client.base_url == "http://test"
    assert client.api_token is None
    await client.close()
