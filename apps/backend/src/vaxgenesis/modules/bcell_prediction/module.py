"""Module 12 - B-cell Epitope Prediction."""
from __future__ import annotations
from typing import Any
from vaxgenesis.modules.base import BaseModule, ModuleResult

class BcellPredictionModule(BaseModule):
    module_id = "bcell_prediction"
    module_name = "B-cell Epitope Prediction."
    description = "Module 12 - B-cell Epitope Prediction."
    category = "reasoning"
    inputs = ['antigen_sequence', 'structure']
    outputs = ['linear_bcell_epitopes', 'conformational_epitopes']
    default_model_version = "3.0.0"

async def run(self,inputs):
    ag=inputs.get("antigen_sequence","")
    from vaxgenesis.modules.epitope_prediction.module import EpitopePredictionModule
    em=EpitopePredictionModule(self.candidate_id,self.db_session)
    r=await em.execute({"antigen_sequences":[{"sequence":ag,"name":"input"}]})
    linear=r.outputs.get("linear_bcell_epitopes",[])
    return ModuleResult(outputs={"linear_bcell_epitopes":linear,"conformational_epitopes":[],"total_bcell_epitopes":len(linear)},model_version=self.default_model_version)
def score_uncertainty(self,result,inputs): return 0.4 if not inputs.get("structure") else 0.7
