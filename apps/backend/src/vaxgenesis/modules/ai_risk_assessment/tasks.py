"""Celery tasks: ai_risk_assessment."""
import asyncio
from typing import Any
from uuid import UUID
from vaxgenesis.core.celery_app_stub import celery_app
from vaxgenesis.db.session_stub import SessionLocal
from vaxgenesis.modules.ai_risk_assessment.module import AIRiskAssessmentModule

@celery_app.task(name="vaxgenesis.modules.ai_risk_assessment.run")
def run_ai_risk_assessment(candidate_id, inputs):
    db = SessionLocal()
    try:
        module = AIRiskAssessmentModule(UUID(candidate_id), db_session=db)
        result = asyncio.run(module.execute(inputs))
        return {"prediction_id": str(module.prediction.id) if module.prediction else None, "outputs": result.outputs, "uncertainty": result.uncertainty_score}
    finally:
        db.close()
