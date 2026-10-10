"""Tests for agent orchestration hardening (audit 2.x)."""
from __future__ import annotations

import asyncio

import pytest


# ============================================================
# Agent types (2.2)
# ============================================================

class TestAgentTypes:
    def test_step_record_defaults(self):
        from vaxgenesis.agents.types import StepRecord
        step = StepRecord(agent_name="test", step_type="think")
        assert step.status == "running"
        assert step.inputs == {}
        assert step.outputs == {}

    def test_agent_result_decision_validation(self):
        from vaxgenesis.agents.types import AgentResult
        result = AgentResult(
            agent_name="test",
            decision="proceed",
            content="ok",
            confidence=0.9,
        )
        assert result.decision == "proceed"
        assert result.confidence == 0.9

    def test_graph_result_to_audit_dict(self):
        from vaxgenesis.agents.types import GraphResult, StepRecord
        g = GraphResult(candidate_id="c1")
        g.add_step(StepRecord(agent_name="hypothesis", step_type="think", status="completed", outputs={"decision": "proceed"}))
        g.add_step(StepRecord(agent_name="critic", step_type="think", status="completed", outputs={"decision": "veto"}))
        audit = g.to_audit_dict()
        assert audit["candidate_id"] == "c1"
        assert audit["step_count"] == 2
        assert audit["veto_count"] == 1
        assert "hypothesis" in audit["agents_invoked"]


# ============================================================
# Graph executor (2.1, 2.3)
# ============================================================

class TestGraphExecutor:
    def _make_simple_graph(self):
        from vaxgenesis.agents.graph import Node, WorkflowGraph
        from vaxgenesis.agents.types import AgentResult

        async def hypo(ctx):
            return AgentResult(agent_name="hypothesis", decision="proceed", content="h", artifacts={"h": 1})
        async def valid(ctx):
            return AgentResult(agent_name="validator", decision="proceed", content="v", artifacts={"v": 2})
        async def mem(ctx):
            return AgentResult(agent_name="memory", decision="complete", content="m")

        g = WorkflowGraph("test")
        g.add_node(Node("hypothesis", hypo)).add_edge("proceed", "validator").set_default_next("validator")
        g.add_node(Node("validator", valid)).add_edge("proceed", "memory").set_default_next("memory")
        g.add_node(Node("memory", mem))
        return g

    def test_executes_linear_graph(self):
        from vaxgenesis.agents.graph import GraphExecutor
        g = self._make_simple_graph()
        ex = GraphExecutor(g, candidate_id="c1", max_iterations=5)
        result = asyncio.run(ex.execute({}))
        assert result.final_status == "completed"
        assert len(result.steps) == 3
        assert result.steps[0].agent_name == "hypothesis"
        assert result.steps[2].agent_name == "memory"

    def test_veto_loops_back(self):
        from vaxgenesis.agents.graph import Node, WorkflowGraph, GraphExecutor
        from vaxgenesis.agents.types import AgentResult

        call_count = {"critic": 0}

        async def hypo(ctx):
            return AgentResult(agent_name="hypothesis", decision="proceed", content="h")
        async def valid(ctx):
            return AgentResult(agent_name="validator", decision="proceed", content="v")
        async def crit(ctx):
            call_count["critic"] += 1
            if call_count["critic"] == 1:
                return AgentResult(agent_name="critic", decision="veto", content="too risky", feedback="fix X")
            return AgentResult(agent_name="critic", decision="proceed", content="ok now")
        async def mem(ctx):
            return AgentResult(agent_name="memory", decision="complete", content="m")

        g = WorkflowGraph("test")
        g.add_node(Node("hypothesis", hypo)).set_default_next("validator")
        g.add_node(Node("validator", valid)).set_default_next("critic")
        g.add_node(Node("critic", crit)).add_edge("proceed", "memory").add_edge("veto", "validator")
        g.add_node(Node("memory", mem))

        ex = GraphExecutor(g, candidate_id="c1", max_iterations=5)
        result = asyncio.run(ex.execute({}))
        assert result.final_status == "completed"
        assert call_count["critic"] == 2  # vetoed once, then approved

    def test_timeout_handling(self):
        from vaxgenesis.agents.graph import Node, WorkflowGraph, GraphExecutor
        from vaxgenesis.agents.types import AgentResult

        async def slow(ctx):
            await asyncio.sleep(10)
            return AgentResult(agent_name="slow", decision="proceed", content="never")

        g = WorkflowGraph("test")
        g.add_node(Node("slow", slow, timeout_seconds=1))
        ex = GraphExecutor(g, candidate_id="c1", max_iterations=5)
        result = asyncio.run(ex.execute({}))
        assert result.final_status == "failed"
        assert "Timeout" in (result.steps[0].error or "")

    def test_exception_handling(self):
        from vaxgenesis.agents.graph import Node, WorkflowGraph, GraphExecutor
        from vaxgenesis.agents.types import AgentResult

        async def boom(ctx):
            raise ValueError("test error")

        g = WorkflowGraph("test")
        g.add_node(Node("boom", boom))
        ex = GraphExecutor(g, candidate_id="c1", max_iterations=5)
        result = asyncio.run(ex.execute({}))
        assert result.final_status == "failed"
        assert "ValueError" in (result.steps[0].error or "")


# ============================================================
# Reflection (2.4)
# ============================================================

class TestReflection:
    def test_no_issues_returns_clean_reflection(self):
        from vaxgenesis.agents.reflection import reflect_on_validation
        result = asyncio.run(reflect_on_validation(
            validation_outputs={"hla_binding": {"binder_count": 3}},
            critic_issues=[],
            iteration=0,
        ))
        assert result["issue"] == "none"
        assert "no changes" in result["proposed_fix"]

    def test_critical_issue_proposes_fix(self):
        from vaxgenesis.agents.reflection import reflect_on_validation
        result = asyncio.run(reflect_on_validation(
            validation_outputs={"toxicity_prediction": {"toxic_count": 2}},
            critic_issues=[
                {"module": "toxicity_prediction", "issue": "toxic_epitopes", "severity": "critical", "value": 2},
            ],
            iteration=0,
        ))
        assert result["severity"] == "critical"
        assert "Remove 2 toxic epitope" in result["proposed_fix"]

    def test_warning_issue_proposes_fix(self):
        from vaxgenesis.agents.reflection import reflect_on_validation
        result = asyncio.run(reflect_on_validation(
            validation_outputs={},
            critic_issues=[
                {"module": "allergenicity_prediction", "issue": "allergenic_epitopes", "severity": "warning"},
            ],
            iteration=1,
        ))
        assert result["severity"] == "warning"
        assert "Replace allergenic" in result["proposed_fix"]
        assert result["iteration"] == 1

    def test_reflection_memory_accumulates(self):
        from vaxgenesis.agents.reflection import ReflectionMemory
        mem = ReflectionMemory()
        mem.add(0, "issue A", "warning", "fix A")
        mem.add(1, "issue B", "critical", "fix B")
        prompt = mem.as_prompt_context()
        assert "issue A" in prompt
        assert "issue B" in prompt
        assert "fix A" in prompt
        assert "fix B" in prompt
