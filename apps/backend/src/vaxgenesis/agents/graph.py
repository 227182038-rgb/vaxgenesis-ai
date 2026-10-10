"""Graph-based workflow engine for agent orchestration (audit 2.1).

A minimal DAG executor that formalizes the multi-agent pipeline:

  - Each agent is a `Node` with a typed `Agent.invoke(ctx) -> AgentResult`.
  - Edges define control flow: `proceed`, `veto`, `escalate`.
  - The executor walks the graph, persists every step as a `StepRecord`
    in a `GraphResult`, and emits the trace to the audit log + object
    storage.

This replaces the ad-hoc Python `for` loop in the v1.0 orchestrator
with a structured, auditable workflow.
"""
from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

from vaxgenesis.agents.types import AgentResult, GraphResult, StepRecord


# A node function takes a context dict and returns an AgentResult.
NodeFn = Callable[[dict[str, Any]], Awaitable[AgentResult]]


class Node:
    """A single agent node in the workflow graph."""

    def __init__(
        self,
        name: str,
        invoke: NodeFn,
        *,
        description: str = "",
        max_retries: int = 0,
        timeout_seconds: int = 300,
    ) -> None:
        self.name = name
        self.invoke = invoke
        self.description = description
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        # Edges: decision -> next node name
        self.edges: dict[str, str] = {"proceed": ""}
        # Default next node (when no explicit decision edge matches)
        self.default_next: str | None = None

    def add_edge(self, decision: str, target: str) -> "Node":
        self.edges[decision] = target
        return self

    def set_default_next(self, target: str) -> "Node":
        self.default_next = target
        return self


class WorkflowGraph:
    """A directed graph of agent nodes."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.nodes: dict[str, Node] = {}
        self.entry: str | None = None

    def add_node(self, node: Node) -> Node:
        self.nodes[node.name] = node
        if self.entry is None:
            self.entry = node.name
        return node

    def set_entry(self, name: str) -> None:
        if name not in self.nodes:
            raise ValueError(f"Unknown entry node: {name}")
        self.entry = name

    def next_node(self, current: str, decision: str) -> str | None:
        node = self.nodes[current]
        if decision in node.edges and node.edges[decision]:
            return node.edges[decision]
        return node.default_next


class GraphExecutor:
    """Executes a WorkflowGraph and produces a GraphResult."""

    def __init__(
        self,
        graph: WorkflowGraph,
        candidate_id: str,
        max_iterations: int = 3,
        on_step_complete: Callable[[StepRecord], None] | None = None,
    ) -> None:
        self.graph = graph
        self.candidate_id = candidate_id
        self.max_iterations = max_iterations
        self.on_step_complete = on_step_complete
        self.result = GraphResult(candidate_id=candidate_id)

    async def execute(self, context: dict[str, Any] | None = None) -> GraphResult:
        context = context or {}
        start = time.time()

        if not self.graph.entry:
            self.result.final_status = "failed"
            self.result.completed_at = _now()
            self.result.duration_seconds = time.time() - start
            return self.result

        current = self.graph.entry
        iterations = 0
        last_step_id: str | None = None

        while current and iterations < self.max_iterations:
            node = self.graph.nodes[current]
            step = StepRecord(
                agent_name=node.name,
                step_type="think",
                inputs={"context_keys": list(context.keys())},
                parent_step_id=last_step_id,
            )
            self.result.add_step(step)
            step_start = time.time()

            try:
                agent_result = await asyncio.wait_for(
                    node.invoke(context), timeout=node.timeout_seconds,
                )
                step.completed_at = _now()
                step.duration_seconds = time.time() - step_start
                step.status = "completed"
                step.outputs = {
                    "decision": agent_result.decision,
                    "content": agent_result.content[:500],
                    "structured_output": agent_result.structured_output,
                    "confidence": agent_result.confidence,
                    "uncertainty": agent_result.uncertainty,
                }
                step.model_version = agent_result.artifacts.get("model_version")

                # Merge artifacts into context
                context.update(agent_result.artifacts)
                context["last_decision"] = agent_result.decision
                context["last_feedback"] = agent_result.feedback

                # Notify observer (for audit log + DB persistence)
                if self.on_step_complete:
                    self.on_step_complete(step)

                last_step_id = step.step_id

                # Decide next node
                if agent_result.decision == "complete":
                    self.result.final_status = "completed"
                    self.result.final_decision = agent_result.decision
                    break
                if agent_result.decision == "escalate":
                    self.result.final_status = "escalated"
                    self.result.final_decision = agent_result.decision
                    break
                if agent_result.decision == "veto":
                    # On veto, route via the veto edge if defined
                    nxt = self.graph.next_node(current, "veto")
                    if nxt:
                        # Don't mark as final yet — we're looping back
                        self.result.final_status = "vetoed"
                        current = nxt
                        iterations += 1
                        continue
                    else:
                        self.result.final_status = "vetoed"
                        break
                # default: proceed
                # Reset final_status (a prior veto is now resolved)
                self.result.final_status = "completed"
                nxt = self.graph.next_node(current, agent_result.decision)
                if nxt is None:
                    self.result.final_status = "completed"
                    break
                current = nxt
                iterations += 1

            except asyncio.TimeoutError:
                step.status = "failed"
                step.error = f"Timeout after {node.timeout_seconds}s"
                step.completed_at = _now()
                step.duration_seconds = time.time() - step_start
                self.result.final_status = "failed"
                break
            except Exception as exc:
                step.status = "failed"
                step.error = f"{exc.__class__.__name__}: {exc}"
                step.completed_at = _now()
                step.duration_seconds = time.time() - step_start
                self.result.final_status = "failed"
                break

        self.result.iterations = iterations
        self.result.completed_at = _now()
        self.result.duration_seconds = time.time() - start
        self.result.artifacts = context
        return self.result


def _now() -> datetime:
    from datetime import timezone
    from datetime import datetime as _DT
    return _DT.now(timezone.utc)
