"""Celery tasks: antigen_discovery."""
import asyncio
from typing import Any
from uuid import UUID
from vaxgenesis.core.celery_app_stub import celery_app
from vaxgenesis.db.session_stub import SessionLocal
from vaxgenesis.modules.antigen_discovery.module import AntigenDiscoveryModule

@celery_app.task(name="vaxgenesis.modules.antigen_discovery.run")
def run_antigen_discovery(candidate_id, inputs):
    db = SessionLocal()
    try:
        module = AntigenDiscoveryModule(UUID(candidate_id), db_session=db)
        result = asyncio.run(module.execute(inputs))
        return {"prediction_id": str(module.prediction.id) if module.prediction else None, "outputs": result.outputs, "uncertainty": result.uncertainty_score}
    finally:
        db.close()
