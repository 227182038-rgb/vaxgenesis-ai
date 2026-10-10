"""Module 4 - Epitope Prediction: CTL, HTL, linear B-cell."""
from __future__ import annotations
from typing import Any
from vaxgenesis.modules.base import BaseModule, ModuleResult

class EpitopePredictionModule(BaseModule):
    module_id = "epitope_prediction"
    module_name = "Epitope Prediction"
    description = "Module 4 - Epitope Prediction: CTL, HTL, linear B-cell."
    category = "reasoning"
    inputs = ['antigen_sequences']
    outputs = ['ctl_epitopes', 'htl_epitopes', 'linear_bcell_epitopes']
    default_model_version = "3.0.0"

import numpy as np
HYDRO={"A":-0.5,"R":3.0,"N":0.2,"D":3.0,"C":-1.0,"Q":0.2,"E":3.0,"G":0.0,"H":-0.5,"I":-1.8,"L":-1.8,"K":3.0,"M":-1.3,"F":-2.5,"P":0.0,"S":0.3,"T":-0.4,"W":-3.8,"Y":-2.3,"V":-1.5}
def _ctl(pep):
    if len(pep)<8: return 0
    p2=pep[1] if len(pep)>1 else "X"; pc=pep[-1]; s=0
    if p2 in "LMIVF": s+=0.4
    if pc in "LMIVF": s+=0.4
    if p2=="P": s-=0.2
    h=sum(HYDRO.get(a,0) for a in pep)/len(pep); return min(1,s+max(0,min(1,(h+2)/5))*0.3)
def _htl(pep):
    if len(pep)<12: return 0
    f=0.4; h=sum(HYDRO.get(a,0) for a in pep)/len(pep); return min(1,f*1.5+(h+2)/5)
def _bcell(pep):
    if len(pep)<6: return 0
    sa=0.43; h=sum(HYDRO.get(a,0) for a in pep)/len(pep); return min(1,0.4*sa+0.3*(h+2)/5+0.3*0.45)
async def run(self,inputs):
    antigens=inputs.get("antigen_sequences",[])
    ctl=[];htl=[];bcell=[]
    for ag in antigens:
        seq=ag["sequence"] if isinstance(ag,dict) else ag
        name=ag.get("name","unk") if isinstance(ag,dict) else "unk"
        for L in [8,9,10,11]:
            for i in range(len(seq)-L+1):
                p=seq[i:i+L]; s=_ctl(p)
                if s>=0.5: ctl.append({"sequence":p,"start":i+1,"end":i+L,"type":"ctl","score":round(s,3),"protein_name":name})
        for L in range(12,21):
            for i in range(len(seq)-L+1):
                p=seq[i:i+L]; s=_htl(p)
                if s>=0.5: htl.append({"sequence":p,"start":i+1,"end":i+L,"type":"htl","score":round(s,3),"protein_name":name})
        for L in range(8,21):
            for i in range(len(seq)-L+1):
                p=seq[i:i+L]; s=_bcell(p)
                if s>=0.5: bcell.append({"sequence":p,"start":i+1,"end":i+L,"type":"linear_bcell","score":round(s,3),"protein_name":name})
    return ModuleResult(outputs={"ctl_epitopes":ctl,"htl_epitopes":htl,"linear_bcell_epitopes":bcell,"total_epitopes":len(ctl)+len(htl)+len(bcell)},model_version=self.default_model_version)
def score_uncertainty(self,result,inputs):
    scores=[e["score"] for e in result.outputs["ctl_epitopes"]+result.outputs["htl_epitopes"]+result.outputs["linear_bcell_epitopes"]]
    return round(min(1,float(np.std(scores))*2),3) if scores else 1.0
