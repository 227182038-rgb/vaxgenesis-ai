"""Celery tasks: autoimmunity screening."""
from __future__ import annotations
import asyncio
from typing import Any
from uuid import UUID

from vaxgenesis.core.celery_app_stub import celery_app
from vaxgenesis.db.session_stub import SessionLocal
from vaxgenesis.modules.autoimmunity_screening.module import AutoimmunityScreeningModule


@celery_app.task(name="vaxgenesis.modules.autoimmunity_screening.run")
def run_autoimmunity_screening(candidate_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
    db = SessionLocal()
    try:
        module = AutoimmunityScreeningModule(UUID(candidate_id), db_session=db)
        result = asyncio.run(module.execute(inputs))
        return {
            "prediction_id": str(module.prediction.id) if module.prediction else None,
            "outputs": result.outputs,
            "uncertainty": result.uncertainty_score,
        }
    finally:
        db.close()
