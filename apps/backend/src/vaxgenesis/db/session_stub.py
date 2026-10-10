"""DB session stub for audit-v1.1 modules.

In the deployed repository this lives at `vaxgenesis/db/session.py`
and returns the production SQLAlchemy session factory.
"""
from __future__ import annotations


class _SessionStub:
    """Context-manager-like session stub."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def close(self) -> None:
        pass

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass


def SessionLocal() -> _SessionStub:  # noqa: N802 - mirrors v1.0 casing
    return _SessionStub()
