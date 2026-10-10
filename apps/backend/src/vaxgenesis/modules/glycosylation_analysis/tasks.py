"""Celery tasks: glycosylation analysis."""
from __future__ import annotations
import asyncio
from typing import Any
from uuid import UUID

from vaxgenesis.core.celery_app_stub import celery_app
from vaxgenesis.db.session_stub import SessionLocal
from vaxgenesis.modules.glycosylation_analysis.module import GlycosylationAnalysisModule


@celery_app.task(name="vaxgenesis.modules.glycosylation_analysis.run")
def run_glycosylation_analysis(candidate_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
    db = SessionLocal()
    try:
        module = GlycosylationAnalysisModule(UUID(candidate_id), db_session=db)
        result = asyncio.run(module.execute(inputs))
        return {
            "prediction_id": str(module.prediction.id) if module.prediction else None,
            "outputs": result.outputs,
            "uncertainty": result.uncertainty_score,
        }
    finally:
        db.close()
