"""Celery app - delegates to stub for dev, real Celery in production."""
from vaxgenesis.core.celery_app_stub import celery_app

# In production, this would be:
# from celery import Celery
# celery_app = Celery("vaxgenesis", broker=..., backend=...)
