"""Celery tasks for the surveillance subsystem."""
import asyncio
from datetime import datetime, timezone
from vaxgenesis.core.celery_app_stub import celery_app

@celery_app.task(name="vaxgenesis.surveillance.poll_gisaid")
def poll_gisaid():
    return {"ingested": 0}

@celery_app.task(name="vaxgenesis.surveillance.poll_nextstrain")
def poll_nextstrain():
    return {"ingested": 0}

@celery_app.task(name="vaxgenesis.surveillance.detect_escape_for_variant")
def detect_escape_for_variant(variant_id):
    return {"variant_id": variant_id, "alerts_generated": 0}

@celery_app.task(name="vaxgenesis.surveillance.trigger_reformulation")
def trigger_reformulation(candidate_id, variant_id):
    return {"new_candidate_id": None}
