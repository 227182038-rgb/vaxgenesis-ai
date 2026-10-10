"""SubmitAssayResult use case — record a wet-lab result and trigger model update.

This is a write use case that:
  1. Loads the WetLabAssay aggregate.
  2. Calls `assay.complete(...)` to transition state and record the result.
  3. Publishes an AssayCompleted event.
  4. Triggers a Bayesian model update (via event subscriber, not inline).
"""
from __future__ import annotations

from uuid import UUID

from vaxgenesis.hexagon.domain.events import AssayCompleted
from vaxgenesis.hexagon.domain.errors import (
    EntityNotFoundError, InvalidStateTransitionError,
)
from vaxgenesis.hexagon.ports.services import EventBus, UnitOfWork
from vaxgenesis.hexagon.use_cases.dtos import (
    AssayResult, SubmitAssayResultCommand,
)


class SubmitAssayResultUseCase:
    """Record a wet-lab assay result.

    Depends on:
        - UnitOfWork
        - EventBus
    """

    def __init__(self, uow: UnitOfWork, event_bus: EventBus) -> None:
        self._uow = uow
        self._event_bus = event_bus

    async def execute(self, cmd: SubmitAssayResultCommand) -> AssayResult:
        """Execute the command. Raises EntityNotFoundError if assay doesn't exist."""
        # 1. Load the assay
        assay = await self._uow.assays.get(cmd.assay_id)

        # 2. Apply the result (state machine enforces idempotency)
        assay.complete(
            value=cmd.value,
            unit=cmd.unit,
            uncertainty=cmd.measurement_uncertainty,
            is_positive=cmd.is_positive,
        )

        # 3. Persist
        saved = await self._uow.assays.save(assay)

        # 4. Publish event
        await self._event_bus.publish(AssayCompleted(
            aggregate_id=saved.id,
            candidate_id=saved.candidate_id,
            assay_type=saved.assay_type,
            value=saved.result_value,  # type: ignore[arg-type]
            unit=saved.result_unit,  # type: ignore[arg-type]
            is_positive=saved.is_positive,
        ))

        # 5. Return result DTO
        return AssayResult(
            id=saved.id,
            candidate_id=saved.candidate_id.value,
            assay_type=saved.assay_type,
            target=saved.target,
            status=saved.status,
            priority=saved.priority,
            result_value=saved.result_value,
            result_unit=saved.result_unit,
            is_positive=saved.is_positive,
            requested_at=saved.requested_at,
            completed_at=saved.completed_at,
        )
