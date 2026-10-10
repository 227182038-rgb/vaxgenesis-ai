"""Celery tasks: codon_optimization."""
import asyncio
from typing import Any
from uuid import UUID
from vaxgenesis.core.celery_app_stub import celery_app
from vaxgenesis.db.session_stub import SessionLocal
from vaxgenesis.modules.codon_optimization.module import CodonOptimizationModule

@celery_app.task(name="vaxgenesis.modules.codon_optimization.run")
def run_codon_optimization(candidate_id, inputs):
    db = SessionLocal()
    try:
        module = CodonOptimizationModule(UUID(candidate_id), db_session=db)
        result = asyncio.run(module.execute(inputs))
        return {"prediction_id": str(module.prediction.id) if module.prediction else None, "outputs": result.outputs, "uncertainty": result.uncertainty_score}
    finally:
        db.close()
