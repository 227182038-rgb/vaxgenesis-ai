"""Module 5 - Toxicity Prediction."""
from __future__ import annotations
from typing import Any
from vaxgenesis.modules.base import BaseModule, ModuleResult

class ToxicityPredictionModule(BaseModule):
    module_id = "toxicity_prediction"
    module_name = "Toxicity Prediction."
    description = "Module 5 - Toxicity Prediction."
    category = "reasoning"
    inputs = ['epitope_sequences']
    outputs = ['toxicity_scores', 'hemolysis_scores', 'inflammation_scores']
    default_model_version = "1.2.0"

import numpy as np
PROP={"A":-0.1,"R":0.3,"N":-0.2,"D":-0.1,"C":0.5,"Q":-0.2,"E":-0.1,"G":-0.3,"H":0.2,"I":0.4,"L":0.3,"K":0.1,"M":0.2,"F":0.6,"P":-0.2,"S":-0.2,"T":-0.1,"W":0.5,"Y":0.3,"V":0.3}
async def run(self,inputs):
    epis=inputs.get("epitope_sequences",[]) or inputs.get("epitopes",[])
    scored=[]
    for epi in epis:
        seq=epi["sequence"] if isinstance(epi,dict) else epi
        tox=sum(PROP.get(a,0) for a in seq)/max(1,len(seq))+min(1,len(seq)/30)*0.2
        hydro=sum({"A":1.8,"I":4.5,"L":3.8,"V":4.2,"F":2.8,"M":1.9,"W":-0.9,"Y":-1.3}.get(a,0) for a in seq)/max(1,len(seq))
        hem=max(0,min(1,(hydro+1)/6)); infl=min(1,(seq.count("R")+seq.count("K")+seq.count("P"))/max(1,len(seq))*3)
        scored.append({"sequence":seq,"toxicity_score":round(max(0,min(1,tox)),3),"hemolysis_score":round(hem,3),"inflammation_score":round(infl,3),"is_toxic":tox>=0.5})
    tc=sum(1 for s in scored if s["is_toxic"])
    return ModuleResult(outputs={"toxicity_scores":scored,"total_epitopes":len(scored),"toxic_count":tc,"safe_count":len(scored)-tc},model_version=self.default_model_version)
def score_uncertainty(self,result,inputs):
    s=result.outputs.get("toxicity_scores",[]); m=result.confidence_interval.get("mean_toxicity",0.5)
    bw=sum(1 for x in s if 0.3<x["toxicity_score"]<0.7)/max(1,len(s)) if s else 0
    return round(min(1,m*0.5+bw*0.5),3)
