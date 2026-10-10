"""Mock LIMS server (audit 6.1).

A FastAPI stub that emulates a Laboratory Information Management System
for testing the wet-lab-in-the-loop integration without requiring a
real lab partner.

Endpoints:
  POST /assays                — receive an assay request from VaxGenesis
  GET  /assays/{id}           — get assay status
  POST /assays/{id}/result    — submit a result for an assay
  GET  /assays                — list all assays (for the lab technician UI)

Run:
  uvicorn services.mock_lims.app:app --port 9001

The mock LIMS auto-generates plausible results after a configurable delay.
"""
from __future__ import annotations

import asyncio
import random
import time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="VaxGenesis Mock LIMS",
    description="Test stub for wet-lab-in-the-loop integration",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Models
# ============================================================

class AssayRequest(BaseModel):
    candidate_id: str
    assay_type: str  # elisa, spr, neutralization, etc.
    target: str
    priority: int = 5
    requested_by: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AssayRecord(BaseModel):
    id: str
    candidate_id: str
    assay_type: str
    target: str
    priority: int
    requested_by: str
    status: str = "received"  # received → in_progress → completed
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AssayResultSubmission(BaseModel):
    value: float
    unit: str
    measurement_uncertainty: float | None = None
    is_positive: bool | None = None
    notes: str | None = None


# ============================================================
# In-memory store (in production: replace with a real DB)
# ============================================================

_assays: dict[str, AssayRecord] = {}


# ============================================================
# Endpoints
# ============================================================

@app.post("/assays", response_model=AssayRecord, status_code=201)
async def receive_assay(req: AssayRequest) -> AssayRecord:
    """VaxGenesis calls this to submit an assay request."""
    record = AssayRecord(
        id=str(uuid4()),
        candidate_id=req.candidate_id,
        assay_type=req.assay_type,
        target=req.target,
        priority=req.priority,
        requested_by=req.requested_by,
        metadata=req.metadata,
    )
    _assays[record.id] = record

    # Auto-generate a result after a delay (simulating lab turnaround)
    delay = max(1, 10 - req.priority)  # higher priority = faster
    asyncio.create_task(_auto_complete(record.id, delay_seconds=delay))

    return record


@app.get("/assays/{assay_id}", response_model=AssayRecord)
async def get_assay(assay_id: str) -> AssayRecord:
    if assay_id not in _assays:
        raise HTTPException(404, "Assay not found")
    return _assays[assay_id]


@app.get("/assays", response_model=list[AssayRecord])
async def list_assays(
    candidate_id: str | None = None,
    status_filter: str | None = None,
) -> list[AssayRecord]:
    results = list(_assays.values())
    if candidate_id:
        results = [a for a in results if a.candidate_id == candidate_id]
    if status_filter:
        results = [a for a in results if a.status == status_filter]
    return sorted(results, key=lambda a: a.received_at, reverse=True)


@app.post("/assays/{assay_id}/result", response_model=AssayRecord)
async def submit_result(assay_id: str, result: AssayResultSubmission) -> AssayRecord:
    """Lab technician submits a result for an assay."""
    if assay_id not in _assays:
        raise HTTPException(404, "Assay not found")
    record = _assays[assay_id]
    record.status = "completed"
    record.completed_at = datetime.now(timezone.utc)
    record.result = result.model_dump()
    return record


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "mock-lims"}


# ============================================================
# Auto-completion task (simulates lab work)
# ============================================================

async def _auto_complete(assay_id: str, delay_seconds: int) -> None:
    """Simulate lab work: after delay, generate a plausible result."""
    await asyncio.sleep(delay_seconds)
    if assay_id not in _assays:
        return
    record = _assays[assay_id]
    if record.status != "received":
        return  # already manually completed

    record.status = "in_progress"
    await asyncio.sleep(1)

    # Generate plausible result based on assay type
    result = _generate_plausible_result(record.assay_type)
    record.status = "completed"
    record.completed_at = datetime.now(timezone.utc)
    record.result = result


def _generate_plausible_result(assay_type: str) -> dict[str, Any]:
    """Generate a plausible assay result for the given assay type."""
    rng = random.Random(time.time())
    if assay_type == "elisa":
        return {
            "value": rng.uniform(0.1, 5.0),
            "unit": "OD450",
            "measurement_uncertainty": 0.05,
            "is_positive": rng.random() > 0.3,
        }
    if assay_type == "spr":
        return {
            "value": rng.uniform(1, 500),
            "unit": "nM",
            "measurement_uncertainty": 5.0,
            "is_positive": True,  # SPR always detects binding
        }
    if assay_type == "neutralization":
        titer = rng.choice([40, 80, 160, 320, 640, 1280])
        return {
            "value": titer,
            "unit": "reciprocal_titer",
            "is_positive": titer >= 80,
        }
    if assay_type == "elispot":
        return {
            "value": rng.randint(10, 500),
            "unit": "SFU_per_million",
            "measurement_uncertainty": 5,
            "is_positive": True,
        }
    if assay_type == "in_vivo":
        return {
            "value": rng.uniform(0.5, 5.0),
            "unit": "fold_change",
            "is_positive": True,
        }
    return {
        "value": rng.uniform(0, 1),
        "unit": "arbitrary",
        "is_positive": rng.random() > 0.5,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001)
