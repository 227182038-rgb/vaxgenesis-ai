"""Celery tasks: conservancy_analysis."""
import asyncio
from typing import Any
from uuid import UUID
from vaxgenesis.core.celery_app_stub import celery_app
from vaxgenesis.db.session_stub import SessionLocal
from vaxgenesis.modules.conservancy_analysis.module import ConservancyAnalysisModule

@celery_app.task(name="vaxgenesis.modules.conservancy_analysis.run")
def run_conservancy_analysis(candidate_id, inputs):
    db = SessionLocal()
    try:
        module = ConservancyAnalysisModule(UUID(candidate_id), db_session=db)
        result = asyncio.run(module.execute(inputs))
        return {"prediction_id": str(module.prediction.id) if module.prediction else None, "outputs": result.outputs, "uncertainty": result.uncertainty_score}
    finally:
        db.close()
