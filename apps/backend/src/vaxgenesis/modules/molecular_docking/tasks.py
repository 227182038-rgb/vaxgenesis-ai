"""Celery tasks: molecular_docking."""
import asyncio
from typing import Any
from uuid import UUID
from vaxgenesis.core.celery_app_stub import celery_app
from vaxgenesis.db.session_stub import SessionLocal
from vaxgenesis.modules.molecular_docking.module import MolecularDockingModule

@celery_app.task(name="vaxgenesis.modules.molecular_docking.run")
def run_molecular_docking(candidate_id, inputs):
    db = SessionLocal()
    try:
        module = MolecularDockingModule(UUID(candidate_id), db_session=db)
        result = asyncio.run(module.execute(inputs))
        return {"prediction_id": str(module.prediction.id) if module.prediction else None, "outputs": result.outputs, "uncertainty": result.uncertainty_score}
    finally:
        db.close()
