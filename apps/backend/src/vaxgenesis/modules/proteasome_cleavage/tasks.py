"""Celery tasks: proteasome cleavage."""
from __future__ import annotations
import asyncio
from typing import Any
from uuid import UUID

from vaxgenesis.core.celery_app_stub import celery_app
from vaxgenesis.db.session_stub import SessionLocal
from vaxgenesis.modules.proteasome_cleavage.module import ProteasomeCleavageModule


@celery_app.task(name="vaxgenesis.modules.proteasome_cleavage.run")
def run_proteasome_cleavage(candidate_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
    db = SessionLocal()
    try:
        module = ProteasomeCleavageModule(UUID(candidate_id), db_session=db)
        result = asyncio.run(module.execute(inputs))
        return {
            "prediction_id": str(module.prediction.id) if module.prediction else None,
            "outputs": result.outputs,
            "uncertainty": result.uncertainty_score,
        }
    finally:
        db.close()
