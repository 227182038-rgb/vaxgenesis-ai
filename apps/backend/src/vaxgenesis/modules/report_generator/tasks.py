"""Celery tasks: report_generator."""
import asyncio
from typing import Any
from uuid import UUID
from vaxgenesis.core.celery_app_stub import celery_app
from vaxgenesis.db.session_stub import SessionLocal
from vaxgenesis.modules.report_generator.module import ReportGeneratorModule

@celery_app.task(name="vaxgenesis.modules.report_generator.run")
def run_report_generator(candidate_id, inputs):
    db = SessionLocal()
    try:
        module = ReportGeneratorModule(UUID(candidate_id), db_session=db)
        result = asyncio.run(module.execute(inputs))
        return {"prediction_id": str(module.prediction.id) if module.prediction else None, "outputs": result.outputs, "uncertainty": result.uncertainty_score}
    finally:
        db.close()
