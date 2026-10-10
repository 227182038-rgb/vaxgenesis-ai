"""Service ports — interfaces for domain services (external capabilities).

A domain service is an operation that doesn't naturally belong to a
single aggregate but is still part of the domain. Examples:
  - SequenceAnalyzer (runs genome analysis)
  - StructurePredictor (calls AlphaFold)
  - HlaBindingPredictor (calls NetMHCpan)
  - EventBus (publishes domain events)
  - UnitOfWork (transaction boundary)

These ports are implemented by adapters in `adapters/`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from vaxgenesis.hexagon.domain.entities import (
    Candidate, Construct, Epitope, Pathogen, Variant,
)
from vaxgenesis.hexagon.domain.events import DomainEvent
from vaxgenesis.hexagon.domain.value_objects import (
    ConfidenceInterval, HlaAllele, Sequence, UncertaintyScore,
)


# ============================================================
# Pipeline service ports (one per module category)
# ============================================================

class SequenceAnalyzer(ABC):
    """Analyzes a pathogen genome (ORF prediction, GC content)."""

    @abstractmethod
    async def analyze(self, genome: Sequence) -> dict[str, Any]:
        """Returns dict with keys: orfs, cds, protein_list, gc_content, codon_usage."""
        ...


class AntigenDiscoveryService(ABC):
    """Ranks proteins by protective-antigen likelihood (ESM3 + PLGDL)."""

    @abstractmethod
    async def discover(self, proteins: list[Any]) -> list[dict[str, Any]]:
        """Returns list of {name, score, uncertainty, embedding_hash}."""
        ...


class EpitopePredictionService(ABC):
    """Predicts CTL, HTL, B-cell epitopes from antigen sequences."""

    @abstractmethod
    async def predict(self, antigen_sequences: list[Sequence]) -> list[Epitope]:
        ...


class HlaBindingPredictor(ABC):
    """Predicts peptide-HLA binding affinity."""

    @abstractmethod
    async def predict_binding(
        self, epitopes: list[Sequence], alleles: list[HlaAllele],
    ) -> list[dict[str, Any]]:
        """Returns list of {epitope, allele, ic50_nm, is_binder}."""
        ...


class StructurePredictor(ABC):
    """Predicts 3D protein structure (AlphaFold3)."""

    @abstractmethod
    async def predict(self, sequence: Sequence) -> dict[str, Any]:
        """Returns dict with keys: pdb_uri, plddt, pae, quality_score."""
        ...


class ToxicityPredictor(ABC):
    """Predicts toxic / hemolytic / inflammatory peptides."""

    @abstractmethod
    async def predict(self, epitopes: list[Sequence]) -> list[dict[str, Any]]:
        ...


class AutoimmunityScreener(ABC):
    """Screens epitopes against the human proteome (molecular mimicry)."""

    @abstractmethod
    async def screen(self, epitopes: list[Sequence]) -> dict[str, Any]:
        """Returns {self_reactive_count, composite_risk, hits}."""
        ...


class ImmuneSimulator(ABC):
    """Simulates the immune response to a construct."""

    @abstractmethod
    async def simulate(self, construct: Construct, epitopes: list[Epitope]) -> dict[str, Any]:
        """Returns {igm, igg, iga, ifn_gamma, il2, il10, memory_b, memory_t}."""
        ...


# ============================================================
# Surveillance service ports
# ============================================================

class VariantIngestionService(ABC):
    """Ingests new pathogen variants from external sources."""

    @abstractmethod
    async def ingest(self, sequence: Sequence, source: str, **kwargs: Any) -> Variant:
        ...


class EscapeDetectionService(ABC):
    """Detects whether a variant escapes a candidate's epitopes."""

    @abstractmethod
    async def detect_escape(
        self, variant: Variant, candidate: Candidate,
    ) -> dict[str, Any]:
        """Returns {escape_score, escaped_epitopes, tier}."""
        ...


# ============================================================
# Learning service ports
# ============================================================

class LimsClient(ABC):
    """Client for the Laboratory Information Management System."""

    @abstractmethod
    async def submit_assay_request(
        self, candidate_id: Any, assay_type: str, target: str, priority: int,
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def poll_assay(self, assay_id: str) -> dict[str, Any]:
        ...


class BayesianModelUpdater(ABC):
    """Updates prediction models from wet-lab results."""

    @abstractmethod
    async def update(self, assay_id: Any, result: dict[str, Any]) -> str:
        """Returns the update strategy used."""
        ...


# ============================================================
# Cross-cutting ports
# ============================================================

class EventBus(ABC):
    """Publishes domain events to subscribers."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        ...

    @abstractmethod
    def subscribe(self, event_type: type[DomainEvent], handler: Any) -> None:
        """Register a handler for an event type."""
        ...


class UnitOfWork(ABC):
    """Transaction boundary.

    Ensures that a use case's changes are atomic: either all repositories
    commit or none do.
    """

    candidates: "CandidateRepository"
    pathogens: "PathogenRepository"
    variants: "VariantRepository"
    assays: "WetLabAssayRepository"
    projects: "ProjectRepository"

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        ...

    @abstractmethod
    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        """Commit on success, rollback on exception."""
        ...

    @abstractmethod
    async def commit(self) -> None:
        ...

    @abstractmethod
    async def rollback(self) -> None:
        ...


# Forward-references for type hints
from vaxgenesis.hexagon.ports.repositories import (  # noqa: E402
    CandidateRepository, PathogenRepository, ProjectRepository,
    VariantRepository, WetLabAssayRepository,
)
