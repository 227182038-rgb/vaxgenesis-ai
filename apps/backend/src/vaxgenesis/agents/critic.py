"""Critic Agent."""
from vaxgenesis.agents.base import AgentContext, AgentMessage, BaseAgent, record_iteration

class CriticAgent(BaseAgent):
    name = "critic"
    description = "Adversarially challenges predictions"

    async def think(self, context):
        v = context.artifacts.get("validation", {})
        issues = []
        for mod, res in v.items():
            if isinstance(res, dict):
                u = res.get("uncertainty_score") or res.get("mean_uncertainty")
                if u and u > 0.7: issues.append({"module": mod, "issue": "high_uncertainty", "severity": "warning"})
        r = v.get("ai_risk_assessment", {})
        if r.get("risk_score", 0) > 0.7: issues.append({"module": "ai_risk_assessment", "issue": "high_risk", "severity": "critical"})
        t = v.get("toxicity_prediction", {})
        if t.get("toxic_count", 0) > 0: issues.append({"module": "toxicity_prediction", "issue": "toxic_epitopes", "severity": "critical"})
        veto = any(i["severity"] == "critical" for i in issues)
        critique = await self.call_llm(prompt=f"Validation: {str(v)[:500]}. Issues: {issues}", system="You are the Critic Agent.")
        record_iteration("critic", "vetoed" if veto else "approved")
        context.artifacts["critique"] = {"issues": issues, "veto": veto, "critique_text": critique}
        return AgentMessage(role="critic", content=critique, metadata={"issues_count": len(issues), "veto": veto})
