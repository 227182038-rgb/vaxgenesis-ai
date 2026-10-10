"""DTOs (Data Transfer Objects) for use case inputs and outputs.

DTOs are Pydantic models that define the contract between the API
layer and the use case layer. They are NOT domain entities — they
are flattened, serializable representations.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# Command DTOs (inputs to write use cases)
# ============================================================

class CreateCandidateCommand(BaseModel):
    project_id: UUID
    name: str = Field(min_length=1, max_length=255)
    platform: Literal[
        "multi_epitope", "mRNA", "viral_vector", "protein_subunit", "VLP", "DNA",
    ] = "multi_epitope"


class CreateProjectCommand(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    owner_id: UUID


class UploadPathogenCommand(BaseModel):
    project_id: UUID
    name: str = Field(min_length=1)
    pathogen_type: Literal["virus", "bacteria", "parasite", "fungus"]
    reference_genome: str = Field(min_length=1)
    reference_genome_alphabet: Literal["dna", "rna"] = "dna"


class SubmitAssayResultCommand(BaseModel):
    assay_id: UUID
    value: float
    unit: str = Field(min_length=1)
    measurement_uncertainty: float | None = None
    is_positive: bool | None = None
    notes: str | None = None


class IngestVariantCommand(BaseModel):
    pathogen_id: UUID
    name: str = Field(min_length=1)
    sequence: str = Field(min_length=1)
    sequence_alphabet: Literal["dna", "rna"] = "dna"
    lineage: str | None = None
    source: str = "manual"
    source_accession: str | None = None
    collection_date: datetime | None = None
    geography: str | None = None


# ============================================================
# Query DTOs (inputs to read use cases)
# ============================================================

class GetCandidateQuery(BaseModel):
    candidate_id: UUID


class ListCandidatesQuery(BaseModel):
    project_id: UUID | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class GetSurveillanceStatusQuery(BaseModel):
    pass


class ListVariantsQuery(BaseModel):
    pathogen_id: UUID | None = None
    limit: int = Field(default=50, ge=1, le=200)


# ============================================================
# Result DTOs (outputs)
# ============================================================

class CandidateResult(BaseModel):
    id: UUID
    project_id: UUID
    version: int
    name: str
    platform: str
    status: str
    overall_score: float | None
    uncertainty: float | None
    confidence_interval_low: float | None
    confidence_interval_high: float | None
    risk_score: float | None
    population_coverage: float | None
    estimated_cost_per_dose_usd: float | None
    created_at: datetime
    updated_at: datetime


class ProjectResult(BaseModel):
    id: UUID
    name: str
    description: str | None
    owner_id: UUID
    status: str
    created_at: datetime


class VariantResult(BaseModel):
    id: UUID
    pathogen_id: UUID
    name: str
    lineage: str | None
    source: str
    source_accession: str | None
    mutation_count: int
    escape_score: float | None
    escape_tier: str | None
    collection_date: datetime | None
    created_at: datetime


class SurveillanceStatusResult(BaseModel):
    is_running: bool
    last_ingest_at: datetime | None
    sequences_seen_24h: int
    sequences_seen_7d: int
    active_alerts: int
    critical_alerts: int


class AssayResult(BaseModel):
    id: UUID
    candidate_id: UUID
    assay_type: str
    target: str
    status: str
    priority: int
    result_value: float | None
    result_unit: str | None
    is_positive: bool | None
    requested_at: datetime
    completed_at: datetime | None


class PaginatedResult(BaseModel):
    """Generic paginated result wrapper."""
    items: list[Any]
    total: int
    limit: int
    offset: int
