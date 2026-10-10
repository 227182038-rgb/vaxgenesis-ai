"""Module 6 - Allergenicity Prediction."""
from __future__ import annotations
from typing import Any
from vaxgenesis.modules.base import BaseModule, ModuleResult

class AllergenicityPredictionModule(BaseModule):
    module_id = "allergenicity_prediction"
    module_name = "Allergenicity Prediction."
    description = "Module 6 - Allergenicity Prediction."
    category = "reasoning"
    inputs = ['epitope_sequences']
    outputs = ['allergenicity_class', 'allergen_probability']
    default_model_version = "1.1.0"

import numpy as np,re
MOTIFS=["GEEME","EKNEK","KKEDV","GEEEE","EEEEE","KKKKK","RRRRR","PFPFP","GAGAG"]
async def run(self,inputs):
    epis=inputs.get("epitope_sequences",[]) or inputs.get("epitopes",[])
    scored=[]
    for epi in epis:
        seq=epi["sequence"] if isinstance(epi,dict) else epi
        hits=sum(1 for m in MOTIFS if m in seq); ms=min(1,hits*0.3)
        ekr=(seq.count("E")+seq.count("K")+seq.count("R"))/max(1,len(seq)); cs=min(1,ekr*2)
        lf=max(0,1-len(seq)/50); prob=min(1,ms*0.5+cs*0.3+lf*0.2)
        cls="Strong Allergen" if prob>=0.7 else "Possible Allergen" if prob>=0.4 else "Safe"
        scored.append({"sequence":seq,"allergen_probability":round(prob,3),"allergenicity_class":cls,"is_safe":cls=="Safe"})
    safe=sum(1 for s in scored if s["is_safe"])
    return ModuleResult(outputs={"allergenicity_scores":scored,"safe_count":safe,"allergen_count":len(scored)-safe},model_version=self.default_model_version)
def score_uncertainty(self,result,inputs):
    s=result.outputs.get("allergenicity_scores",[]); return round(sum(1 for x in s if 0.4<x["allergen_probability"]<0.7)/max(1,len(s)),3) if s else 0.5
