"""Celery tasks: mutation_analysis."""
import asyncio
from typing import Any
from uuid import UUID
from vaxgenesis.core.celery_app_stub import celery_app
from vaxgenesis.db.session_stub import SessionLocal
from vaxgenesis.modules.mutation_analysis.module import MutationAnalysisModule

@celery_app.task(name="vaxgenesis.modules.mutation_analysis.run")
def run_mutation_analysis(candidate_id, inputs):
    db = SessionLocal()
    try:
        module = MutationAnalysisModule(UUID(candidate_id), db_session=db)
        result = asyncio.run(module.execute(inputs))
        return {"prediction_id": str(module.prediction.id) if module.prediction else None, "outputs": result.outputs, "uncertainty": result.uncertainty_score}
    finally:
        db.close()
