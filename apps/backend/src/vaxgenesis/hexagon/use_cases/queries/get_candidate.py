"""GetCandidate query — fetch a single candidate by ID."""
from __future__ import annotations

from vaxgenesis.hexagon.domain.errors import EntityNotFoundError
from vaxgenesis.hexagon.domain.value_objects import CandidateId
from vaxgenesis.hexagon.ports.repositories import CandidateRepository
from vaxgenesis.hexagon.use_cases.dtos import (
    CandidateResult, GetCandidateQuery,
)


class GetCandidateQueryUseCase:
    """Fetch a single candidate by ID."""

    def __init__(self, repo: CandidateRepository) -> None:
        self._repo = repo

    async def execute(self, query: GetCandidateQuery) -> CandidateResult:
        candidate = await self._repo.get(CandidateId(value=query.candidate_id))
        return CandidateResult(
            id=candidate.id.value,
            project_id=candidate.project_id.value,
            version=candidate.version,
            name=candidate.name,
            platform=candidate.platform,
            status=candidate.status,
            overall_score=candidate.overall_score,
            uncertainty=candidate.uncertainty.value if candidate.uncertainty else None,
            confidence_interval_low=candidate.confidence_interval.low if candidate.confidence_interval else None,
            confidence_interval_high=candidate.confidence_interval.high if candidate.confidence_interval else None,
            risk_score=candidate.risk_score,
            population_coverage=candidate.population_coverage,
            estimated_cost_per_dose_usd=candidate.estimated_cost_per_dose_usd,
            created_at=candidate.created_at,
            updated_at=candidate.updated_at,
        )
