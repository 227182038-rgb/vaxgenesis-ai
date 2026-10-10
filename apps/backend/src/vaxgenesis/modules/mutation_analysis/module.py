"""Module 9 - Mutation Analysis."""
from __future__ import annotations
from typing import Any
from vaxgenesis.modules.base import BaseModule, ModuleResult

class MutationAnalysisModule(BaseModule):
    module_id = "mutation_analysis"
    module_name = "Mutation Analysis."
    description = "Module 9 - Mutation Analysis."
    category = "reasoning"
    inputs = ['epitopes', 'variant_sequences']
    outputs = ['mutation_map', 'escape_risk_scores']
    default_model_version = "1.0.0"

import numpy as np
async def run(self,inputs):
    epis=inputs.get("epitopes",[]); variants=inputs.get("variant_sequences",[])
    scores=[];mut_map=[]
    for epi in epis:
        seq=epi["sequence"] if isinstance(epi,dict) else epi
        risk=sum(1 for v in variants if seq not in v.get("sequence",""))/len(variants) if variants else 0
        scores.append({"sequence":seq,"escape_risk":round(risk,3),"is_escaped":risk>=0.5})
        for v in variants:
            if seq not in v.get("sequence",""): mut_map.append({"epitope":seq,"variant":v.get("name","unk")})
    mr=float(np.mean([s["escape_risk"] for s in scores])) if scores else 0
    return ModuleResult(outputs={"escape_risk_scores":scores,"mutation_map":mut_map,"mean_escape_risk":round(mr,3),"variant_count":len(variants)},model_version=self.default_model_version)
def score_uncertainty(self,result,inputs):
    v=result.outputs.get("variant_count",0); return 0.8 if v==0 else round(min(1,1/v),3)
