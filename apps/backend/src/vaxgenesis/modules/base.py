"""Stub for the v1.0 BaseModule / ModuleResult.

In the deployed repository these live at vaxgenesis/modules/base.py.
This stub mirrors the interface so that audit-v1.1 modules import
cleanly during testing and review without requiring the full v1.0
codebase to be present.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, ClassVar
from uuid import UUID

from pydantic import BaseModel


class ModuleResult(BaseModel):
    """Structured result of a module execution."""

    outputs: dict[str, Any] = {}
    confidence_interval: dict[str, Any] = {}
    uncertainty_score: float | None = None
    model_version: str = "unknown"
    model_uri: str | None = None
    execution_time_seconds: float = 0.0


class BaseModule(ABC):
    """Abstract base for all pipeline modules.

    Audit v1.1: subclasses continue to implement run() + score_uncertainty().
    """

    module_id: ClassVar[str] = ""
    module_name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    category: ClassVar[str] = "reasoning"
    inputs: ClassVar[list[str]] = []
    outputs: ClassVar[list[str]] = []
    default_model_version: ClassVar[str] = "1.0.0"

    def __init__(
        self,
        candidate_id: UUID,
        db_session: Any | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.candidate_id = candidate_id
        self.db_session = db_session
        self.config = config or {}
        self._prediction: Any | None = None

    @abstractmethod
    async def run(self, inputs: dict[str, Any]) -> ModuleResult:
        ...

    @abstractmethod
    def score_uncertainty(self, result: ModuleResult, inputs: dict[str, Any]) -> float:
        ...

    async def execute(self, inputs: dict[str, Any]) -> ModuleResult:
        """Execute the module lifecycle (v1.0 contract)."""
        start = time.time()
        result = await self.run(inputs)
        result.uncertainty_score = self.score_uncertainty(result, inputs)
        result.execution_time_seconds = time.time() - start
        if not result.model_version:
            result.model_version = self.default_model_version
        return result

    @property
    def prediction(self) -> Any | None:
        return self._prediction
