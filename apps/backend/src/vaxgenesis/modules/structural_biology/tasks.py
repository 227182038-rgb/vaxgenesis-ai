"""Celery tasks: structural_biology."""
import asyncio
from typing import Any
from uuid import UUID
from vaxgenesis.core.celery_app_stub import celery_app
from vaxgenesis.db.session_stub import SessionLocal
from vaxgenesis.modules.structural_biology.module import StructuralBiologyModule

@celery_app.task(name="vaxgenesis.modules.structural_biology.run")
def run_structural_biology(candidate_id, inputs):
    db = SessionLocal()
    try:
        module = StructuralBiologyModule(UUID(candidate_id), db_session=db)
        result = asyncio.run(module.execute(inputs))
        return {"prediction_id": str(module.prediction.id) if module.prediction else None, "outputs": result.outputs, "uncertainty": result.uncertainty_score}
    finally:
        db.close()
