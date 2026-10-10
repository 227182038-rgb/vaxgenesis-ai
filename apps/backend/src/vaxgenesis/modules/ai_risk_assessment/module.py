"""Module 25 - AI Risk Assessment."""
from __future__ import annotations
from typing import Any
from vaxgenesis.modules.base import BaseModule, ModuleResult

class AIRiskAssessmentModule(BaseModule):
    module_id = "ai_risk_assessment"
    module_name = "AI Risk Assessment."
    description = "Module 25 - AI Risk Assessment."
    category = "action"
    inputs = ['all_predictions']
    outputs = ['risk_score', 'risk_factors', 'mitigation_recommendations']
    default_model_version = "1.0.0"

async def run(self,inputs):
    ap=inputs.get("all_predictions",{})
    tox=ap.get("toxicity_prediction",{}).get("toxic_count",0); all=ap.get("allergenicity_prediction",{}).get("allergen_count",0)
    esc=ap.get("mutation_analysis",{}).get("mean_escape_risk",0); mu=ap.get("mean_uncertainty",0.5)
    rf=[]
    if tox>0: rf.append({"factor":"toxicity","severity":min(1,tox/10)})
    if all>0: rf.append({"factor":"allergenicity","severity":min(1,all/10)})
    if esc>0.3: rf.append({"factor":"escape_risk","severity":esc})
    if mu>0.5: rf.append({"factor":"prediction_uncertainty","severity":mu})
    cs=sum(f["severity"] for f in rf)/max(1,len(rf)) if rf else 0
    recs=[]
    if tox>0: recs.append("Remove toxic epitopes")
    if all>0: recs.append("Replace allergenic epitopes")
    if esc>0.3: recs.append("Prioritize conserved epitopes")
    if mu>0.6: recs.append("Request additional wet-lab validation")
    cat="critical" if cs>0.7 else "high" if cs>0.4 else "moderate" if cs>0.2 else "low"
    return ModuleResult(outputs={"risk_score":round(cs,3),"risk_category":cat,"risk_factors":rf,"mitigation_recommendations":recs},model_version=self.default_model_version)
def score_uncertainty(self,result,inputs): return result.outputs.get("risk_score",0.5)
