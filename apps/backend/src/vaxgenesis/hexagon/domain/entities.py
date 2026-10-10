"""Domain entities — aggregate roots with identity and state.

Entities have identity (a stable ID) and mutable state. Each entity
encapsulates its own invariants: state transitions are validated by
methods on the entity itself.

This module imports only:
  - Pydantic v2
  - The standard library
  - Other domain modules (value_objects, errors, events)

No SQLAlchemy, no FastAPI, no Redis, no httpx.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from vaxgenesis.hexagon.domain.errors import (
    DuplicateEntityError, EntityNotFoundError, InsufficientEvidenceError,
    InvalidStateTransitionError, InvariantViolationError,
)
from vaxgenesis.hexagon.domain.value_objects import (
    CandidateId, ConfidenceInterval, EscapeScore, HlaAllele,
    Mutation, ProjectId, Sequence, UncertaintyScore, VariantId,
)


# ============================================================
# Enumerations (domain-controlled, not ORM-controlled)
# ============================================================

class CandidateStatus(StrEnum):
    DRAFT = "draft"
    PREDICTED = "predicted"
    VALIDATED = "validated"
    REJECTED = "rejected"
    IN_TRIAL = "in_trial"


class VaccinePlatform(StrEnum):
    MULTI_EPITOPE = "multi_epitope"
    MRNA = "mRNA"
    VIRAL_VECTOR = "viral_vector"
    PROTEIN_SUBUNIT = "protein_subunit"
    VLP = "VLP"
    DNA = "DNA"


class PathogenType(StrEnum):
    VIRUS = "virus"
    BACTERIA = "bacteria"
    PARASITE = "parasite"
    FUNGUS = "fungus"


class EpitopeType(StrEnum):
    CTL = "ctl"
    HTL = "htl"
    LINEAR_BCELL = "linear_bcell"
    CONFORMATIONAL_BCELL = "conformational_bcell"


class AssayStatus(StrEnum):
    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================
# State machine helper
# ============================================================

_VALID_TRANSITIONS: dict[CandidateStatus, set[CandidateStatus]] = {
    CandidateStatus.DRAFT: {CandidateStatus.PREDICTED},
    CandidateStatus.PREDICTED: {
        CandidateStatus.VALIDATED,
        CandidateStatus.REJECTED,
    },
    CandidateStatus.VALIDATED: {CandidateStatus.IN_TRIAL},
    CandidateStatus.REJECTED: set(),
    CandidateStatus.IN_TRIAL: set(),
}


# ============================================================
# Aggregate root: Candidate
# ============================================================

class Epitope(BaseModel):
    """An epitope within a candidate's construct."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    sequence: Sequence
    epitope_type: EpitopeType
    start_position: int = Field(ge=1)
    end_position: int = Field(ge=1)
    score: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("end_position")
    @classmethod
    def _end_after_start(cls, v: int, info) -> int:
        start = info.data.get("start_position")
        if start is not None and v < start:
            raise ValueError(f"end_position ({v}) must be >= start_position ({start})")
        return v


class Construct(BaseModel):
    """The assembled multi-epitope vaccine construct."""

    model_config = ConfigDict(frozen=True)

    sequence: Sequence
    adjuvant: str
    linker: str
    his_tag: bool = True
    epitopes: list[Epitope] = Field(default_factory=list)

    @property
    def length(self) -> int:
        return self.sequence.length

    @property
    def molecular_weight_kda(self) -> float:
        """Approximate molecular weight in kDa."""
        mw_table = {
            "A": 89.1, "R": 174.2, "N": 132.1, "D": 133.1, "C": 121.2,
            "Q": 146.2, "E": 147.1, "G": 75.0, "H": 155.2, "I": 131.2,
            "L": 131.2, "K": 146.2, "M": 149.2, "F": 165.2, "P": 115.1,
            "S": 105.1, "T": 119.1, "W": 204.2, "Y": 181.2, "V": 117.1,
        }
        total = sum(mw_table.get(aa, 110.0) for aa in self.sequence.value)
        # Subtract water for each peptide bond
        return (total - 18.0 * (self.length - 1)) / 1000.0


class Candidate(BaseModel):
    """Aggregate root: a vaccine candidate.

    Invariants enforced:
      - Status transitions follow the state machine.
      - Confidence interval low <= high.
      - Version monotonically increases.
      - A PREDICTED candidate must have a non-null overall_score.
      - A VALIDATED candidate must have at least one completed assay.
    """

    id: CandidateId = Field(default_factory=CandidateId)
    project_id: ProjectId
    version: int = Field(default=1, ge=1)
    name: str = Field(min_length=1, max_length=255)
    platform: VaccinePlatform = VaccinePlatform.MULTI_EPITOPE
    status: CandidateStatus = CandidateStatus.DRAFT
    construct: Construct | None = None
    overall_score: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_interval: ConfidenceInterval | None = None
    uncertainty: UncertaintyScore | None = None
    risk_score: float | None = Field(default=None, ge=0.0, le=1.0)
    population_coverage: float | None = Field(default=None, ge=0.0, le=1.0)
    estimated_cost_per_dose_usd: float | None = Field(default=None, ge=0.0)
    parent_candidate_id: CandidateId | None = None
    triggered_by_variant_id: VariantId | None = None
    completed_assay_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def advance_status(self, new_status: CandidateStatus) -> None:
        """Transition to a new status, enforcing the state machine.

        Raises:
            InvalidStateTransitionError: if the transition is not allowed.
            InvariantViolationError: if a precondition for the new status is unmet.
        """
        allowed = _VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                f"Cannot transition candidate from {self.status} to {new_status}. "
                f"Allowed transitions from {self.status}: {allowed or '(none)'}."
            )

        # Precondition checks
        if new_status == CandidateStatus.PREDICTED:
            if self.overall_score is None:
                raise InvariantViolationError(
                    "Cannot advance to PREDICTED without an overall_score."
                )
        if new_status == CandidateStatus.VALIDATED:
            if self.completed_assay_count == 0:
                raise InsufficientEvidenceError(
                    "Cannot advance to VALIDATED without at least one completed assay."
                )

        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

    def record_assay_completion(self) -> None:
        """Record that a wet-lab assay has completed for this candidate."""
        self.completed_assay_count += 1
        self.updated_at = datetime.now(timezone.utc)

    def bump_version(self) -> None:
        """Increment the version (e.g., for an escape-driven re-formulation)."""
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)

    def attach_construct(self, construct: Construct) -> None:
        """Attach the assembled construct to this candidate."""
        self.construct = construct
        self.updated_at = datetime.now(timezone.utc)

    def set_predictions(
        self,
        overall_score: float,
        confidence_interval: ConfidenceInterval,
        uncertainty: UncertaintyScore,
    ) -> None:
        """Set the aggregate prediction scores."""
        if not (0.0 <= overall_score <= 1.0):
            raise InvariantViolationError(
                f"overall_score must be in [0, 1], got {overall_score}"
            )
        self.overall_score = overall_score
        self.confidence_interval = confidence_interval
        self.uncertainty = uncertainty
        self.updated_at = datetime.now(timezone.utc)


# ============================================================
# Aggregate root: Pathogen
# ============================================================

class Protein(BaseModel):
    """A protein within a pathogen's proteome."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1)
    sequence: Sequence
    is_surface: bool = False
    is_secreted: bool = False
    is_virulence_factor: bool = False
    antigen_score: float | None = Field(default=None, ge=0.0, le=1.0)


class Pathogen(BaseModel):
    """Aggregate root: a pathogen being targeted by a vaccine."""

    id: UUID = Field(default_factory=uuid4)
    project_id: ProjectId
    name: str = Field(min_length=1)
    type: PathogenType
    reference_genome: Sequence
    proteins: list[Protein] = Field(default_factory=list)
    gc_content: float | None = None

    def add_protein(self, protein: Protein) -> None:
        """Add a discovered protein to the proteome."""
        if any(p.name == protein.name for p in self.proteins):
            raise DuplicateEntityError(
                f"Protein named '{protein.name}' already exists in pathogen {self.name}"
            )
        # Use list mutation via model_copy since proteins is on a frozen=False model
        new_proteins = list(self.proteins) + [protein]
        object.__setattr__(self, "proteins", new_proteins)

    @property
    def protective_antigens(self) -> list[Protein]:
        """Proteins flagged as protective antigen candidates."""
        return [p for p in self.proteins if p.antigen_score is not None and p.antigen_score > 0.7]


# ============================================================
# Aggregate root: Variant (surveillance)
# ============================================================

class Variant(BaseModel):
    """Aggregate root: a pathogen variant detected by surveillance."""

    id: VariantId = Field(default_factory=VariantId)
    pathogen_id: UUID
    name: str = Field(min_length=1)
    lineage: str | None = None
    source: str = "manual"
    source_accession: str | None = None
    sequence: Sequence
    mutations: list[Mutation] = Field(default_factory=list)
    collection_date: datetime | None = None
    geography: str | None = None
    escape_score: EscapeScore | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def mutation_count(self) -> int:
        return len(self.mutations)

    def overlaps_epitope(self, epitope_start: int, epitope_end: int) -> bool:
        """Check if any mutation falls within an epitope's position range."""
        return any(
            epitope_start <= m.position <= epitope_end
            for m in self.mutations
        )


# ============================================================
# Aggregate root: WetLabAssay (learning)
# ============================================================

class WetLabAssay(BaseModel):
    """Aggregate root: a wet-lab assay request and its result."""

    id: UUID = Field(default_factory=uuid4)
    candidate_id: CandidateId
    assay_type: str
    target: str
    priority: int = Field(default=5, ge=1, le=10)
    status: AssayStatus = AssayStatus.REQUESTED
    requested_by: str
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    result_value: float | None = None
    result_unit: str | None = None
    result_uncertainty: float | None = None
    is_positive: bool | None = None

    def complete(
        self,
        value: float,
        unit: str,
        uncertainty: float | None = None,
        is_positive: bool | None = None,
    ) -> None:
        """Record the assay result and transition to COMPLETED."""
        if self.status == AssayStatus.COMPLETED:
            raise InvalidStateTransitionError(
                "Assay is already completed; cannot complete again."
            )
        self.result_value = value
        self.result_unit = unit
        self.result_uncertainty = uncertainty
        self.is_positive = is_positive
        self.status = AssayStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)


# ============================================================
# Aggregate root: Project
# ============================================================

class Project(BaseModel):
    """Aggregate root: a vaccine design project."""

    id: ProjectId = Field(default_factory=ProjectId)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    owner_id: UUID
    status: str = "draft"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def rename(self, new_name: str) -> None:
        if not new_name or not new_name.strip():
            raise InvariantViolationError("Project name cannot be empty")
        self.name = new_name.strip()
