"""Celery tasks: epitope_prediction."""
import asyncio
from typing import Any
from uuid import UUID
from vaxgenesis.core.celery_app_stub import celery_app
from vaxgenesis.db.session_stub import SessionLocal
from vaxgenesis.modules.epitope_prediction.module import EpitopePredictionModule

@celery_app.task(name="vaxgenesis.modules.epitope_prediction.run")
def run_epitope_prediction(candidate_id, inputs):
    db = SessionLocal()
    try:
        module = EpitopePredictionModule(UUID(candidate_id), db_session=db)
        result = asyncio.run(module.execute(inputs))
        return {"prediction_id": str(module.prediction.id) if module.prediction else None, "outputs": result.outputs, "uncertainty": result.uncertainty_score}
    finally:
        db.close()
