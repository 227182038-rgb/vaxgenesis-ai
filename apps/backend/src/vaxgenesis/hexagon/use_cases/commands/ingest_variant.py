"""IngestVariant use case — ingest a new pathogen variant into surveillance.

This is a write use case that:
  1. Validates the pathogen exists.
  2. Creates a Variant aggregate.
  3. Persists it via the variant repository.
  4. Publishes a VariantIngested event.
  5. (Async follow-up) Triggers escape detection — handled by an event subscriber.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from vaxgenesis.hexagon.domain.entities import Variant
from vaxgenesis.hexagon.domain.errors import EntityNotFoundError
from vaxgenesis.hexagon.domain.events import VariantIngested
from vaxgenesis.hexagon.domain.value_objects import Sequence, VariantId
from vaxgenesis.hexagon.ports.repositories import (
    PathogenRepository, VariantRepository,
)
from vaxgenesis.hexagon.ports.services import EventBus, UnitOfWork
from vaxgenesis.hexagon.use_cases.dtos import (
    IngestVariantCommand, VariantResult,
)


class IngestVariantUseCase:
    """Ingest a new pathogen variant.

    Depends on:
        - UnitOfWork (for transactional access)
        - EventBus (for publishing VariantIngested)
    """

    def __init__(self, uow: UnitOfWork, event_bus: EventBus) -> None:
        self._uow = uow
        self._event_bus = event_bus

    async def execute(self, cmd: IngestVariantCommand) -> VariantResult:
        """Execute the command. Raises EntityNotFoundError if pathogen doesn't exist."""
        # 1. Validate pathogen exists
        pathogen = await self._uow.pathogens.get(cmd.pathogen_id)

        # 2. Build the Variant aggregate
        sequence = Sequence(value=cmd.sequence, alphabet=cmd.sequence_alphabet)
        variant = Variant(
            pathogen_id=cmd.pathogen_id,
            name=cmd.name,
            lineage=cmd.lineage,
            source=cmd.source,
            source_accession=cmd.source_accession,
            sequence=sequence,
            collection_date=cmd.collection_date,
            geography=cmd.geography,
        )

        # 3. Persist
        saved = await self._uow.variants.save(variant)

        # 4. Publish event
        await self._event_bus.publish(VariantIngested(
            aggregate_id=saved.id.value,
            variant_id=saved.id,
            pathogen_id=saved.pathogen_id,
            name=saved.name,
            lineage=saved.lineage,
            source=saved.source,
        ))

        # 5. Return result DTO
        escape_tier = saved.escape_score.tier if saved.escape_score else None
        return VariantResult(
            id=saved.id.value,
            pathogen_id=saved.pathogen_id,
            name=saved.name,
            lineage=saved.lineage,
            source=saved.source,
            source_accession=saved.source_accession,
            mutation_count=saved.mutation_count(),
            escape_score=saved.escape_score.value if saved.escape_score else None,
            escape_tier=escape_tier,
            collection_date=saved.collection_date,
            created_at=saved.created_at,
        )
