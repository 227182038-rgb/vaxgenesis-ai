"""Hypothesis Agent."""
from vaxgenesis.agents.base import AgentContext, AgentMessage, BaseAgent, record_iteration

class HypothesisAgent(BaseAgent):
    name = "hypothesis"
    description = "Generates candidate vaccine design strategies"
    SYSTEM_PROMPT = "You are the Hypothesis Agent for VaxGenesis AI."

    async def think(self, context):
        proposals = await self.call_llm(prompt=f"Design vaccine for {context.candidate_id}", system=self.SYSTEM_PROMPT)
        record_iteration("hypothesis", "proposed")
        context.artifacts["hypothesis"] = proposals
        return AgentMessage(role="hypothesis", content=proposals, metadata={"iteration": context.iteration})
