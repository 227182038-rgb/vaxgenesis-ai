"""Typed result schemas for agent orchestration (audit 2.2).

Defines:
  - `AgentResult`: structured output of a single agent invocation
  - `StepRecord`: one entry in the execution trace
  - `GraphResult`: full execution trace of a reasoning cycle

These schemas replace the ad-hoc `AgentMessage` dict from v1.0 with
Pydantic-validated types that can be persisted to the database and
inspected via the API.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class StepRecord(BaseModel):
    """A single step in the agent execution graph."""

    step_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: str
    step_type: Literal["think", "act", "observe", "reflect", "decide"]
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    model_version: str | None = None
    token_usage: dict[str, int] = Field(default_factory=dict)
    parent_step_id: str | None = None
    status: Literal["running", "completed", "failed", "skipped"] = "running"
    error: str | None = None


class AgentResult(BaseModel):
    """Structured output of a single agent invocation."""

    agent_name: str
    decision: Literal["proceed", "veto", "escalate", "complete"]
    content: str
    structured_output: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    uncertainty: float = 0.0
    next_agent: str | None = None
    feedback: str | None = None  # for veto/escalate
    artifacts: dict[str, Any] = Field(default_factory=dict)


class GraphResult(BaseModel):
    """Full execution trace of a reasoning cycle.

    Persisted to the database (Candidate.reasoning_trace) and the
    object storage (MinIO/S3) for audit and reproducibility.
    """

    graph_id: str = Field(default_factory=lambda: str(uuid4()))
    candidate_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    iterations: int = 0
    final_status: Literal["completed", "vetoed", "escalated", "failed"] = "completed"
    final_decision: str | None = None
    steps: list[StepRecord] = Field(default_factory=list)
    final_score: float | None = None
    final_uncertainty: float | None = None
    artifacts: dict[str, Any] = Field(default_factory=dict)

    def add_step(self, step: StepRecord) -> None:
        self.steps.append(step)

    def to_audit_dict(self) -> dict[str, Any]:
        """Compact representation for the audit log."""
        return {
            "graph_id": self.graph_id,
            "candidate_id": self.candidate_id,
            "iterations": self.iterations,
            "final_status": self.final_status,
            "final_score": self.final_score,
            "final_uncertainty": self.final_uncertainty,
            "step_count": len(self.steps),
            "duration_seconds": self.duration_seconds,
            "agents_invoked": list({s.agent_name for s in self.steps}),
            "veto_count": sum(1 for s in self.steps if s.outputs.get("decision") == "veto"),
            "escalation_count": sum(1 for s in self.steps if s.outputs.get("decision") == "escalate"),
        }
