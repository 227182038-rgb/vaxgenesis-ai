"""Memory Agent."""
from datetime import datetime, timezone
from vaxgenesis.agents.base import AgentContext, AgentMessage, BaseAgent, record_iteration

class MemoryAgent(BaseAgent):
    name = "memory"
    description = "Logs outcomes and updates the knowledge graph"

    async def think(self, context):
        record_iteration("memory", "logged")
        return AgentMessage(role="memory", content=f"Cycle {context.iteration} logged.", metadata={})
