"""ListCandidates query — paginated list of candidates for a project."""
from __future__ import annotations

from vaxgenesis.hexagon.domain.value_objects import ProjectId
from vaxgenesis.hexagon.ports.repositories import CandidateRepository
from vaxgenesis.hexagon.use_cases.dtos import (
    CandidateResult, ListCandidatesQuery, PaginatedResult,
)


class ListCandidatesQueryUseCase:
    """List candidates, optionally filtered by project."""

    def __init__(self, repo: CandidateRepository) -> None:
        self._repo = repo

    async def execute(self, query: ListCandidatesQuery) -> PaginatedResult:
        project_id = ProjectId(value=query.project_id) if query.project_id else None
        candidates = await self._repo.get_by_project(
            project_id,  # type: ignore[arg-type]
            limit=query.limit,
            offset=query.offset,
        )
        total = await self._repo.count(project_id)

        items = [
            CandidateResult(
                id=c.id.value,
                project_id=c.project_id.value,
                version=c.version,
                name=c.name,
                platform=c.platform,
                status=c.status,
                overall_score=c.overall_score,
                uncertainty=c.uncertainty.value if c.uncertainty else None,
                confidence_interval_low=c.confidence_interval.low if c.confidence_interval else None,
                confidence_interval_high=c.confidence_interval.high if c.confidence_interval else None,
                risk_score=c.risk_score,
                population_coverage=c.population_coverage,
                estimated_cost_per_dose_usd=c.estimated_cost_per_dose_usd,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in candidates
        ]

        return PaginatedResult(
            items=items,  # type: ignore[arg-type]
            total=total,
            limit=query.limit,
            offset=query.offset,
        )
