"""Celery app stub for audit-v1.1 modules.

In the deployed repository this lives at
`vaxgenesis/core/celery_app.py` and returns the production Celery
instance. This stub provides a no-op `celery_app` so that audit-v1.1
task modules import cleanly during testing without requiring a live
Redis broker.
"""
from __future__ import annotations


class _TaskStub:
    """Drop-in for @celery_app.task that returns the wrapped function unchanged."""

    def __init__(self, name: str | None = None) -> None:
        self.name = name

    def __call__(self, fn):
        # Attach .delay() so callers can pretend to enqueue
        def _delay(*args, **kwargs):
            # In tests, just call the function synchronously
            return fn(*args, **kwargs)

        fn.delay = _delay  # type: ignore[attr-defined]
        return fn


class _CeleryAppStub:
    """Minimal Celery-like object for testing."""

    def task(self, name: str | None = None, **_kwargs):
        return _TaskStub(name=name)

    def conf(self):  # pragma: no cover
        return type("Conf", (), {"task_routes": {}, "beat_schedule": {}})()


celery_app = _CeleryAppStub()
