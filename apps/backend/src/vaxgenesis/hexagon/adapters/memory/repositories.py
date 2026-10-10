"""In-memory repository adapters — for unit tests and property-based tests.

These adapters implement the repository ports using plain Python dicts.
They are fast, deterministic, and require no infrastructure.
"""
from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from vaxgenesis.hexagon.domain.entities import (
    Candidate, Pathogen, Project, Variant, WetLabAssay,
)
from vaxgenesis.hexagon.domain.errors import EntityNotFoundError
from vaxgenesis.hexagon.domain.value_objects import CandidateId, ProjectId, VariantId
from vaxgenesis.hexagon.ports.repositories import (
    CandidateRepository, PathogenRepository, ProjectRepository,
    VariantRepository, WetLabAssayRepository,
)


class InMemoryCandidateRepository(CandidateRepository):
    """In-memory CandidateRepository for tests."""

    def __init__(self) -> None:
        self._store: dict[UUID, Candidate] = {}

    async def get(self, id: CandidateId) -> Candidate:
        if id.value not in self._store:
            raise EntityNotFoundError(f"Candidate {id} not found")
        return self._store[id.value]

    async def get_by_project(
        self, project_id: ProjectId, *, limit: int = 50, offset: int = 0,
    ) -> Sequence[Candidate]:
        items = [c for c in self._store.values() if c.project_id == project_id]
        return items[offset : offset + limit]

    async def save(self, candidate: Candidate) -> Candidate:
        self._store[candidate.id.value] = candidate
        return candidate

    async def delete(self, id: CandidateId) -> None:
        self._store.pop(id.value, None)

    async def count(self, project_id: ProjectId | None = None) -> int:
        if project_id is None:
            return len(self._store)
        return sum(1 for c in self._store.values() if c.project_id == project_id)


class InMemoryPathogenRepository(PathogenRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Pathogen] = {}
        self._by_project: dict[UUID, UUID] = {}

    async def get(self, id: UUID) -> Pathogen:
        if id not in self._store:
            raise EntityNotFoundError(f"Pathogen {id} not found")
        return self._store[id]

    async def get_by_project(self, project_id: ProjectId) -> Pathogen | None:
        pid = self._by_project.get(project_id.value)
        if pid is None:
            return None
        return self._store.get(pid)

    async def save(self, pathogen: Pathogen) -> Pathogen:
        self._store[pathogen.id] = pathogen
        self._by_project[pathogen.project_id.value] = pathogen.id
        return pathogen


class InMemoryVariantRepository(VariantRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Variant] = {}
        self._order: list[UUID] = []  # insertion order

    async def get(self, id: VariantId) -> Variant:
        if id.value not in self._store:
            raise EntityNotFoundError(f"Variant {id} not found")
        return self._store[id.value]

    async def save(self, variant: Variant) -> Variant:
        if variant.id.value not in self._store:
            self._order.append(variant.id.value)
        self._store[variant.id.value] = variant
        return variant

    async def list_recent(
        self, pathogen_id: UUID | None = None, *, limit: int = 50,
    ) -> Sequence[Variant]:
        items = list(self._store.values())
        if pathogen_id:
            items = [v for v in items if v.pathogen_id == pathogen_id]
        # Newest first
        items.reverse()
        return items[:limit]

    async def count_recent(self, hours: int = 24) -> int:
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return sum(1 for v in self._store.values() if v.created_at >= cutoff)


class InMemoryWetLabAssayRepository(WetLabAssayRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, WetLabAssay] = {}

    async def get(self, id: UUID) -> WetLabAssay:
        if id not in self._store:
            raise EntityNotFoundError(f"Assay {id} not found")
        return self._store[id]

    async def save(self, assay: WetLabAssay) -> WetLabAssay:
        self._store[assay.id] = assay
        return assay

    async def list_for_candidate(self, candidate_id: CandidateId) -> Sequence[WetLabAssay]:
        return [a for a in self._store.values() if a.candidate_id == candidate_id]

    async def list_pending(self, *, limit: int = 50) -> Sequence[WetLabAssay]:
        from vaxgenesis.hexagon.domain.entities import AssayStatus
        pending = [a for a in self._store.values() if a.status == AssayStatus.REQUESTED]
        return pending[:limit]


class InMemoryProjectRepository(ProjectRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Project] = {}

    async def get(self, id: ProjectId) -> Project:
        if id.value not in self._store:
            raise EntityNotFoundError(f"Project {id} not found")
        return self._store[id.value]

    async def list_for_owner(
        self, owner_id: UUID, *, limit: int = 50, offset: int = 0,
    ) -> Sequence[Project]:
        items = [p for p in self._store.values() if p.owner_id == owner_id]
        return items[offset : offset + limit]

    async def save(self, project: Project) -> Project:
        self._store[project.id.value] = project
        return project

    async def delete(self, id: ProjectId) -> None:
        self._store.pop(id.value, None)
