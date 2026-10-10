"""Agent orchestrator - coordinates the 5-agent reasoning cycle."""
from __future__ import annotations
import asyncio, json, time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4
from vaxgenesis.agents.base import AgentContext, AgentMessage
from vaxgenesis.agents.hypothesis import HypothesisAgent
from vaxgenesis.agents.designer import DesignerAgent
from vaxgenesis.agents.validator import ValidatorAgent
from vaxgenesis.agents.critic import CriticAgent
from vaxgenesis.agents.memory import MemoryAgent

_JOBS = {}

async def orchestrate_pipeline_run(candidate_id, modules=None, target_hla_alleles=None, target_populations=None, expression_host="human", max_iterations=3, wet_lab_budget_assays=0, user_id=None, user_message=None):
    job_id = str(uuid4())
    context = AgentContext(candidate_id=str(candidate_id), user_id=str(user_id) if user_id else "system", user_message=user_message, target_hla_alleles=target_hla_alleles or [], target_populations=target_populations or ["global"], expression_host=expression_host, max_iterations=max_iterations)
    _JOBS[job_id] = {"status": "queued", "candidate_id": str(candidate_id)}
    return job_id

async def run_cycle(job_id, context_dict):
    context = AgentContext(**context_dict)
    _JOBS[job_id]["status"] = "running"
    h = HypothesisAgent(); d = DesignerAgent(); v = ValidatorAgent(); c = CriticAgent(); m = MemoryAgent()
    for iteration in range(context.max_iterations):
        context.iteration = iteration
        context.history.append(await h.think(context))
        context.history.append(await d.think(context))
        context.history.append(await v.think(context))
        context.history.append(await c.think(context))
        context.history.append(await m.think(context))
        if not context.artifacts.get("critique", {}).get("veto"): break
    _JOBS[job_id]["status"] = "completed"
    return {"status": "completed", "iterations": context.iteration + 1}

async def get_pipeline_status(job_id):
    return _JOBS.get(job_id)

async def cancel_pipeline_run(job_id):
    if job_id in _JOBS: _JOBS[job_id]["status"] = "cancelled"; return True
    return False
