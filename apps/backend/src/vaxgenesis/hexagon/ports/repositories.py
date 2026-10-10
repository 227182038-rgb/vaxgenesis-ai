"""Repository ports — interfaces for persisting and retrieving aggregates.

A repository is a collection-like interface over an aggregate root.
It hides the persistence technology (SQLAlchemy, MongoDB, in-memory)
from the domain layer.

Pattern: each aggregate root gets its own repository port.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from vaxgenesis.hexagon.domain.entities import (
    Candidate, Pathogen, Project, Variant, WetLabAssay,
)
from vaxgenesis.hexagon.domain.value_objects import CandidateId, ProjectId, VariantId


class CandidateRepository(ABC):
    """Repository for the Candidate aggregate root."""

    @abstractmethod
    async def get(self, id: CandidateId) -> Candidate:
        """Fetch a candidate by ID. Raises EntityNotFoundError if missing."""
        ...

    @abstractmethod
    async def get_by_project(
        self, project_id: ProjectId, *, limit: int = 50, offset: int = 0,
    ) -> Sequence[Candidate]:
        """List candidates for a project, paginated."""
        ...

    @abstractmethod
    async def save(self, candidate: Candidate) -> Candidate:
        """Persist a candidate (insert or update)."""
        ...

    @abstractmethod
    async def delete(self, id: CandidateId) -> None:
        """Delete a candidate by ID."""
        ...

    @abstractmethod
    async def count(self, project_id: ProjectId | None = None) -> int:
        """Count candidates, optionally filtered by project."""
        ...


class PathogenRepository(ABC):
    """Repository for the Pathogen aggregate root."""

    @abstractmethod
    async def get(self, id: UUID) -> Pathogen:
        ...

    @abstractmethod
    async def get_by_project(self, project_id: ProjectId) -> Pathogen | None:
        """Fetch the pathogen associated with a project (one-to-one)."""
        ...

    @abstractmethod
    async def save(self, pathogen: Pathogen) -> Pathogen:
        ...


class VariantRepository(ABC):
    """Repository for the Variant aggregate root (surveillance)."""

    @abstractmethod
    async def get(self, id: VariantId) -> Variant:
        ...

    @abstractmethod
    async def save(self, variant: Variant) -> Variant:
        ...

    @abstractmethod
    async def list_recent(
        self, pathogen_id: UUID | None = None, *, limit: int = 50,
    ) -> Sequence[Variant]:
        """List recently-ingested variants, newest first."""
        ...

    @abstractmethod
    async def count_recent(self, hours: int = 24) -> int:
        """Count variants ingested in the last N hours."""
        ...


class WetLabAssayRepository(ABC):
    """Repository for the WetLabAssay aggregate root (learning)."""

    @abstractmethod
    async def get(self, id: UUID) -> WetLabAssay:
        ...

    @abstractmethod
    async def save(self, assay: WetLabAssay) -> WetLabAssay:
        ...

    @abstractmethod
    async def list_for_candidate(
        self, candidate_id: CandidateId,
    ) -> Sequence[WetLabAssay]:
        ...

    @abstractmethod
    async def list_pending(self, *, limit: int = 50) -> Sequence[WetLabAssay]:
        """List assays that are requested but not yet completed."""
        ...


class ProjectRepository(ABC):
    """Repository for the Project aggregate root."""

    @abstractmethod
    async def get(self, id: ProjectId) -> Project:
        ...

    @abstractmethod
    async def list_for_owner(
        self, owner_id: UUID, *, limit: int = 50, offset: int = 0,
    ) -> Sequence[Project]:
        ...

    @abstractmethod
    async def save(self, project: Project) -> Project:
        ...

    @abstractmethod
    async def delete(self, id: ProjectId) -> None:
        ...
