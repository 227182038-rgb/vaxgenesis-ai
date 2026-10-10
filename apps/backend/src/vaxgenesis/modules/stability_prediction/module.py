"""Module 22 - Stability Prediction."""
from __future__ import annotations
from typing import Any
from vaxgenesis.modules.base import BaseModule, ModuleResult

class StabilityPredictionModule(BaseModule):
    module_id = "stability_prediction"
    module_name = "Stability Prediction."
    description = "Module 22 - Stability Prediction."
    category = "action"
    inputs = ['construct', 'md_results']
    outputs = ['thermostability', 'long_term_stability', 'aggregation_risk']
    default_model_version = "1.0.0"

async def run(self,inputs):
    c=inputs.get("construct",{}); md=inputs.get("md_results",{})
    seq=c.get("sequence","") if isinstance(c,dict) else ""
    rmsd=md.get("rmsd_mean",2.0); st=max(0,1-rmsd/5)
    hy=sum(1 for a in seq if a in "LIVFMW")/max(1,len(seq)); ar=min(1,hy*3)
    lt=st*(1-ar*0.5); tm=50+st*30
    return ModuleResult(outputs={"thermostability_score":round(st,3),"predicted_tm_celsius":round(tm,1),"long_term_stability_score":round(lt,3),"aggregation_risk":round(ar,3)},model_version=self.default_model_version)
def score_uncertainty(self,result,inputs): return 0.45
