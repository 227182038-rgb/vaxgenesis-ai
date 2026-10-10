"""Module 8 - Conservancy Analysis."""
from __future__ import annotations
from typing import Any
from vaxgenesis.modules.base import BaseModule, ModuleResult

class ConservancyAnalysisModule(BaseModule):
    module_id = "conservancy_analysis"
    module_name = "Conservancy Analysis."
    description = "Module 8 - Conservancy Analysis."
    category = "reasoning"
    inputs = ['epitope_sequences', 'reference_genome']
    outputs = ['conservation_scores']
    default_model_version = "1.0.0"

import numpy as np
async def run(self,inputs):
    epis=inputs.get("epitope_sequences",[]) or inputs.get("epitopes",[]); hom=inputs.get("homologous_sequences",[])
    scored=[]
    for epi in epis:
        seq=epi["sequence"] if isinstance(epi,dict) else epi
        cons=sum(1 for s in hom if seq in s)/len(hom) if hom else 0.5
        scored.append({"sequence":seq,"conservation_score":round(cons,3),"is_conserved":cons>=0.8})
    mc=float(np.mean([s["conservation_score"] for s in scored])) if scored else 0.0
    return ModuleResult(outputs={"conservation_scores":scored,"mean_conservation":round(mc,3),"total_sequences_compared":len(hom)+1},model_version=self.default_model_version)
def score_uncertainty(self,result,inputs):
    t=result.outputs.get("total_sequences_compared",1); return round(min(1,1/t),3)
