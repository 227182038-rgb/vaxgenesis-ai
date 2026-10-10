"""Domain events — things that have happened in the domain.

Events are immutable records of past occurrences. They are published by
aggregate roots when their state changes and consumed by event handlers
(which may trigger side effects like sending notifications, updating
projections, or starting sagas).

This module defines the event classes only. The event bus (publisher)
lives in `vaxgenesis/hexagon/ports/event_bus.py`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from vaxgenesis.hexagon.domain.entities import (
    CandidateStatus, VaccinePlatform,
)
from vaxgenesis.hexagon.domain.value_objects import (
    CandidateId, EscapeScore, ProjectId, VariantId,
)


class DomainEvent(BaseModel):
    """Base class for all domain events."""

    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    aggregate_id: UUID

    @property
    def event_type(self) -> str:
        return self.__class__.__name__


# ============================================================
# Candidate lifecycle events
# ============================================================

class CandidateCreated(DomainEvent):
    """A new vaccine candidate was created."""
    candidate_id: CandidateId
    project_id: ProjectId
    name: str
    platform: VaccinePlatform


class CandidatePredicted(DomainEvent):
    """The prediction pipeline completed for a candidate."""
    candidate_id: CandidateId
    overall_score: float
    uncertainty: float


class CandidateValidated(DomainEvent):
    """A candidate was advanced to VALIDATED status after wet-lab confirmation."""
    candidate_id: CandidateId
    completed_assay_count: int


class CandidateRejected(DomainEvent):
    """A candidate was rejected (e.g., by the Critic agent)."""
    candidate_id: CandidateId
    reason: str


# ============================================================
# Surveillance events
# ============================================================

class VariantIngested(DomainEvent):
    """A new pathogen variant was ingested by the surveillance subsystem."""
    variant_id: VariantId
    pathogen_id: UUID
    name: str
    lineage: str | None
    source: str


class EscapeDetected(DomainEvent):
    """A variant was found to escape a candidate's epitopes."""
    variant_id: VariantId
    candidate_id: CandidateId
    escape_score: EscapeScore


class ReformulationTriggered(DomainEvent):
    """A new candidate version was created in response to escape."""
    parent_candidate_id: CandidateId
    new_candidate_id: CandidateId
    triggered_by_variant_id: VariantId


# ============================================================
# Learning events
# ============================================================

class AssayRequested(DomainEvent):
    """A wet-lab assay was requested for a candidate."""
    candidate_id: CandidateId
    assay_type: str
    target: str


class AssayCompleted(DomainEvent):
    """A wet-lab assay result was submitted."""
    candidate_id: CandidateId
    assay_type: str
    value: float
    unit: str
    is_positive: bool | None


class ModelUpdated(DomainEvent):
    """A prediction model was updated (Bayesian / incremental / full retrain)."""
    module: str
    strategy: str  # "bayesian" | "incremental" | "full_retrain"
    triggered_by_assay_id: UUID | None = None


# ============================================================
# Project events
# ============================================================

class ProjectCreated(DomainEvent):
    """A new project was created."""
    project_id: ProjectId
    name: str
    owner_id: UUID


# ============================================================
# Event handler registry (consumed by use cases)
# ============================================================

# Event handlers are registered at app startup via the DI container.
# This module only defines the event types; handlers are in
# `vaxgenesis/hexagon/use_cases/handlers.py`.

EVENT_TYPES: dict[str, type[DomainEvent]] = {
    "CandidateCreated": CandidateCreated,
    "CandidatePredicted": CandidatePredicted,
    "CandidateValidated": CandidateValidated,
    "CandidateRejected": CandidateRejected,
    "VariantIngested": VariantIngested,
    "EscapeDetected": EscapeDetected,
    "ReformulationTriggered": ReformulationTriggered,
    "AssayRequested": AssayRequested,
    "AssayCompleted": AssayCompleted,
    "ModelUpdated": ModelUpdated,
    "ProjectCreated": ProjectCreated,
}
