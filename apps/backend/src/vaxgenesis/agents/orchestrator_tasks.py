"""Celery task wrapper for the reasoning cycle."""
import asyncio
from vaxgenesis.agents.orchestrator import run_cycle
from vaxgenesis.core.celery_app_stub import celery_app

@celery_app.task(name="vaxgenesis.agents.run_reasoning_cycle", bind=True)
def run_reasoning_cycle(self, job_id, context_dict):
    try:
        result = asyncio.run(run_cycle(job_id, context_dict))
        return result
    except Exception as exc:
        raise
