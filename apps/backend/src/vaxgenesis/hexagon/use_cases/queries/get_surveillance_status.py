"""GetSurveillanceStatus query — current surveillance subsystem status."""
from __future__ import annotations

from datetime import datetime, timezone

from vaxgenesis.hexagon.ports.repositories import VariantRepository
from vaxgenesis.hexagon.use_cases.dtos import SurveillanceStatusResult


class GetSurveillanceStatusQueryUseCase:
    """Compute the current surveillance subsystem status.

    Depends only on VariantRepository — no direct Redis/Kafka access.
    """

    def __init__(self, variant_repo: VariantRepository) -> None:
        self._variant_repo = variant_repo

    async def execute(self) -> SurveillanceStatusResult:
        seq_24h = await self._variant_repo.count_recent(hours=24)
        seq_7d = await self._variant_repo.count_recent(hours=24 * 7)
        recent = await self._variant_repo.list_recent(limit=1)
        last_ingest = recent[0].created_at if recent else None

        return SurveillanceStatusResult(
            is_running=True,  # In production: check Celery beat heartbeat
            last_ingest_at=last_ingest,
            sequences_seen_24h=seq_24h,
            sequences_seen_7d=seq_7d,
            active_alerts=0,  # In production: query escape_alerts table
            critical_alerts=0,
        )
