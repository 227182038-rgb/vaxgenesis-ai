"""Celery tasks: vaccine_construct."""
import asyncio
from typing import Any
from uuid import UUID
from vaxgenesis.core.celery_app_stub import celery_app
from vaxgenesis.db.session_stub import SessionLocal
from vaxgenesis.modules.vaccine_construct.module import VaccineConstructModule

@celery_app.task(name="vaxgenesis.modules.vaccine_construct.run")
def run_vaccine_construct(candidate_id, inputs):
    db = SessionLocal()
    try:
        module = VaccineConstructModule(UUID(candidate_id), db_session=db)
        result = asyncio.run(module.execute(inputs))
        return {"prediction_id": str(module.prediction.id) if module.prediction else None, "outputs": result.outputs, "uncertainty": result.uncertainty_score}
    finally:
        db.close()
