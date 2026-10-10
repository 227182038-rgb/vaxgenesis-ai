"""Module 13 - T-cell Epitope Prediction."""
from __future__ import annotations
from typing import Any
from vaxgenesis.modules.base import BaseModule, ModuleResult

class TcellPredictionModule(BaseModule):
    module_id = "tcell_prediction"
    module_name = "T-cell Epitope Prediction."
    description = "Module 13 - T-cell Epitope Prediction."
    category = "reasoning"
    inputs = ['antigen_sequence', 'hla_alleles']
    outputs = ['ctl_epitopes', 'htl_epitopes', 'stability_scores']
    default_model_version = "2.0.0"

async def run(self,inputs):
    ag=inputs.get("antigen_sequence","")
    from vaxgenesis.modules.epitope_prediction.module import EpitopePredictionModule
    em=EpitopePredictionModule(self.candidate_id,self.db_session)
    r=await em.execute({"antigen_sequences":[{"sequence":ag,"name":"input"}]})
    ctl=r.outputs.get("ctl_epitopes",[]);htl=r.outputs.get("htl_epitopes",[])
    for e in ctl+htl:
        e["stability_score"]=0.8 if e["sequence"][-1:] in "LIVFM" else 0.3
        e["presentation_score"]=0.5*e.get("score",0.5)+0.5*e["stability_score"]
    return ModuleResult(outputs={"ctl_epitopes":ctl,"htl_epitopes":htl,"total_tcell_epitopes":len(ctl)+len(htl)},model_version=self.default_model_version)
def score_uncertainty(self,result,inputs): return 0.35
