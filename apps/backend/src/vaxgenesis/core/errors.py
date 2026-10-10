"""Errors stub (audit v1.1)."""
from __future__ import annotations
from typing import Any


class VaxGenesisError(Exception):
    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, detail: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


class NotFoundError(VaxGenesisError):
    status_code = 404
    code = "not_found"


class ConflictError(VaxGenesisError):
    status_code = 409
    code = "conflict"


class AuthorizationError(VaxGenesisError):
    status_code = 403
    code = "forbidden"


class PipelineError(VaxGenesisError):
    status_code = 500
    code = "pipeline_error"
