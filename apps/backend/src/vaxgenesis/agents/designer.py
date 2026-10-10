"""Designer Agent."""
from vaxgenesis.agents.base import AgentContext, AgentMessage, BaseAgent, record_iteration

class DesignerAgent(BaseAgent):
    name = "designer"
    description = "Builds multi-epitope construct"

    async def think(self, context):
        h = context.artifacts.get("hypothesis", "(no hypothesis)")
        design = await self.call_llm(prompt=f"Design construct from: {h[:500]}", system="You are the Designer Agent.")
        record_iteration("designer", "designed")
        context.artifacts["design"] = design
        return AgentMessage(role="designer", content=design, metadata={"iteration": context.iteration})
