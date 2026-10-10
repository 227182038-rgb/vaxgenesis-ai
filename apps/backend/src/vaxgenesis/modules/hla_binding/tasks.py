"""Celery tasks: hla_binding."""
import asyncio
from typing import Any
from uuid import UUID
from vaxgenesis.core.celery_app_stub import celery_app
from vaxgenesis.db.session_stub import SessionLocal
from vaxgenesis.modules.hla_binding.module import HlaBindingModule

@celery_app.task(name="vaxgenesis.modules.hla_binding.run")
def run_hla_binding(candidate_id, inputs):
    db = SessionLocal()
    try:
        module = HlaBindingModule(UUID(candidate_id), db_session=db)
        result = asyncio.run(module.execute(inputs))
        return {"prediction_id": str(module.prediction.id) if module.prediction else None, "outputs": result.outputs, "uncertainty": result.uncertainty_score}
    finally:
        db.close()
