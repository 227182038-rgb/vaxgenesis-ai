"""Celery tasks: molecular_dynamics."""
import asyncio
from typing import Any
from uuid import UUID
from vaxgenesis.core.celery_app_stub import celery_app
from vaxgenesis.db.session_stub import SessionLocal
from vaxgenesis.modules.molecular_dynamics.module import MolecularDynamicsModule

@celery_app.task(name="vaxgenesis.modules.molecular_dynamics.run")
def run_molecular_dynamics(candidate_id, inputs):
    db = SessionLocal()
    try:
        module = MolecularDynamicsModule(UUID(candidate_id), db_session=db)
        result = asyncio.run(module.execute(inputs))
        return {"prediction_id": str(module.prediction.id) if module.prediction else None, "outputs": result.outputs, "uncertainty": result.uncertainty_score}
    finally:
        db.close()
