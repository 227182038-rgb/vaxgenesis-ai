"""Celery tasks: population_coverage."""
import asyncio
from typing import Any
from uuid import UUID
from vaxgenesis.core.celery_app_stub import celery_app
from vaxgenesis.db.session_stub import SessionLocal
from vaxgenesis.modules.population_coverage.module import PopulationCoverageModule

@celery_app.task(name="vaxgenesis.modules.population_coverage.run")
def run_population_coverage(candidate_id, inputs):
    db = SessionLocal()
    try:
        module = PopulationCoverageModule(UUID(candidate_id), db_session=db)
        result = asyncio.run(module.execute(inputs))
        return {"prediction_id": str(module.prediction.id) if module.prediction else None, "outputs": result.outputs, "uncertainty": result.uncertainty_score}
    finally:
        db.close()
