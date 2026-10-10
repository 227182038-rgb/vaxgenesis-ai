"""Celery tasks: tcell_prediction."""
import asyncio
from typing import Any
from uuid import UUID
from vaxgenesis.core.celery_app_stub import celery_app
from vaxgenesis.db.session_stub import SessionLocal
from vaxgenesis.modules.tcell_prediction.module import TcellPredictionModule

@celery_app.task(name="vaxgenesis.modules.tcell_prediction.run")
def run_tcell_prediction(candidate_id, inputs):
    db = SessionLocal()
    try:
        module = TcellPredictionModule(UUID(candidate_id), db_session=db)
        result = asyncio.run(module.execute(inputs))
        return {"prediction_id": str(module.prediction.id) if module.prediction else None, "outputs": result.outputs, "uncertainty": result.uncertainty_score}
    finally:
        db.close()
