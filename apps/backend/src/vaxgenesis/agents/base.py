"""Base agent class and shared types."""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field

class AgentMessage(BaseModel):
    role: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AgentContext(BaseModel):
    candidate_id: str
    user_id: str = "system"
    user_message: str | None = None
    target_hla_alleles: list[str] = Field(default_factory=list)
    target_populations: list[str] = Field(default_factory=lambda: ["global"])
    expression_host: str = "human"
    max_iterations: int = 3
    wet_lab_budget_assays: int = 0
    modules: list[str] | None = None
    history: list[AgentMessage] = Field(default_factory=list)
    artifacts: dict[str, Any] = Field(default_factory=dict)
    iteration: int = 0
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BaseAgent(ABC):
    name: str = "base"
    description: str = ""
    SYSTEM_PROMPT: str = ""

    def __init__(self, llm_client=None):
        self.llm = llm_client

    @abstractmethod
    async def think(self, context: AgentContext) -> AgentMessage: ...

    async def call_llm(self, prompt, system="", max_tokens=1000):
        from vaxgenesis.config import settings
        if not getattr(settings, "openai_api_key", "") and not getattr(settings, "anthropic_api_key", ""):
            return f"[{self.name}] LLM not configured. Using stub response."
        return f"[{self.name}] Response to: {prompt[:100]}"

def record_iteration(agent, outcome):
    pass
