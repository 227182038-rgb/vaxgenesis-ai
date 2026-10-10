"""CreateCandidate use case — creates a new vaccine candidate.

This is a write use case (command). It:
  1. Validates that the project exists.
  2. Creates a new Candidate aggregate in DRAFT status.
  3. Persists it via the repository.
  4. Publishes a CandidateCreated event.

Depends only on ports — never on concrete adapters.
"""
from __future__ import annotations

from pydantic import BaseModel

from vaxgenesis.hexagon.domain.entities import Candidate, Project
from vaxgenesis.hexagon.domain.errors import EntityNotFoundError
from vaxgenesis.hexagon.domain.events import CandidateCreated
from vaxgenesis.hexagon.domain.value_objects import CandidateId, ProjectId
from vaxgenesis.hexagon.ports.repositories import (
    CandidateRepository, ProjectRepository,
)
from vaxgenesis.hexagon.ports.services import EventBus, UnitOfWork
from vaxgenesis.hexagon.use_cases.dtos import (
    CandidateResult, CreateCandidateCommand,
)


class CreateCandidateUseCase:
    """Create a new vaccine candidate.

    Args:
        uow: UnitOfWork providing transactional access to repositories.
        event_bus: EventBus for publishing CandidateCreated.
    """

    def __init__(self, uow: UnitOfWork, event_bus: EventBus) -> None:
        self._uow = uow
        self._event_bus = event_bus

    async def execute(self, cmd: CreateCandidateCommand) -> CandidateResult:
        """Execute the command. Raises EntityNotFoundError if project doesn't exist."""
        # 1. Validate project exists (within the UoW)
        project = await self._uow.projects.get(ProjectId(value=cmd.project_id))

        # 2. Create the Candidate aggregate
        candidate = Candidate(
            project_id=ProjectId(value=cmd.project_id),
            name=cmd.name,
            platform=cmd.platform,  # type: ignore[arg-type]
        )

        # 3. Persist
        saved = await self._uow.candidates.save(candidate)

        # 4. Publish event
        await self._event_bus.publish(CandidateCreated(
            aggregate_id=saved.id.value,
            candidate_id=saved.id,
            project_id=saved.project_id,
            name=saved.name,
            platform=saved.platform,  # type: ignore[arg-type]
        ))

        # 5. Return result DTO
        return CandidateResult(
            id=saved.id.value,
            project_id=saved.project_id.value,
            version=saved.version,
            name=saved.name,
            platform=saved.platform,
            status=saved.status,
            overall_score=saved.overall_score,
            uncertainty=saved.uncertainty.value if saved.uncertainty else None,
            confidence_interval_low=saved.confidence_interval.low if saved.confidence_interval else None,
            confidence_interval_high=saved.confidence_interval.high if saved.confidence_interval else None,
            risk_score=saved.risk_score,
            population_coverage=saved.population_coverage,
            estimated_cost_per_dose_usd=saved.estimated_cost_per_dose_usd,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
        )
