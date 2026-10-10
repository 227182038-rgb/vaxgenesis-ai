"""Celery tasks for the learning subsystem."""
from vaxgenesis.core.celery_app_stub import celery_app

@celery_app.task(name="vaxgenesis.learning.run_active_learning_batch")
def run_active_learning_batch():
    return {"enqueued": 0, "assays_generated": 0}

@celery_app.task(name="vaxgenesis.learning.check_model_drift")
def check_model_drift():
    return {}

@celery_app.task(name="vaxgenesis.learning.ingest_recent_pubmed")
def ingest_recent_pubmed():
    return {"status": "ingest_completed"}
