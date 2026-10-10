"""Typed models for the VaxGenesis SDK."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user_id: str


class Project(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    owner_id: UUID
    status: str = "draft"
    created_at: datetime
    updated_at: datetime


class Candidate(BaseModel):
    id: UUID
    project_id: UUID
    version: int = 1
    name: str
    platform: str = "multi_epitope"
    status: str = "draft"
    overall_score: float | None = None
    overall_uncertainty: float | None = None
    risk_score: float | None = None
    population_coverage: float | None = None
    estimated_cost_per_dose_usd: float | None = None
    created_at: datetime
    updated_at: datetime


class ModuleInfo(BaseModel):
    id: str
    name: str
    description: str
    category: str
    inputs: list[str]
    outputs: list[str]
    is_implemented: bool
    average_latency_seconds: float | None = None


class Variant(BaseModel):
    id: UUID
    pathogen_id: UUID
    name: str
    lineage: str | None = None
    source: str = "manual"
    mutation_count: int = 0
    escape_score: float | None = None
    escape_tier: str | None = None
    created_at: datetime


class SurveillanceStatus(BaseModel):
    is_running: bool
    last_ingest_at: datetime | None = None
    sequences_seen_24h: int = 0
    sequences_seen_7d: int = 0
    active_alerts: int = 0
    critical_alerts: int = 0


class Explanation(BaseModel):
    """XAI explanation for a prediction (v2.0)."""
    prediction_id: str
    model_name: str
    model_version: str
    narrative: str
    feature_attributions: list[dict[str, Any]] = Field(default_factory=list)
    confidence_explanation: dict[str, Any] | None = None
    counterfactuals: list[dict[str, Any]] = Field(default_factory=list)


class PaginatedResponse(BaseModel, generic=True[Any]):
    """Generic paginated response."""
    items: list[Any]
    total: int
    page: int
    page_size: int
    pages: int
