"""Module 2 - Reverse Vaccinology: score surface/secreted/virulence proteins."""
from __future__ import annotations
from typing import Any
from vaxgenesis.modules.base import BaseModule, ModuleResult

class ReverseVaccinologyModule(BaseModule):
    module_id = "reverse_vaccinology"
    module_name = "Reverse Vaccinology"
    description = "Module 2 - Reverse Vaccinology: score surface/secreted/virulence proteins."
    category = "perception"
    inputs = ['protein_list']
    outputs = ['ranked_antigens', 'scores']
    default_model_version = "1.1.0"

HYDRO={"A":1.8,"R":-4.5,"N":-3.5,"D":-3.5,"C":2.5,"Q":-3.5,"E":-3.5,"G":-0.4,"H":-3.2,"I":4.5,"L":3.8,"K":-3.9,"M":1.9,"F":2.8,"P":-1.6,"S":-0.8,"T":-0.7,"W":-0.9,"Y":-1.3,"V":4.2}
W={"accessibility":0.30,"conservation":0.25,"virulence":0.25,"human_similarity_penalty":0.20}
def _score(seq):
    if not seq: return 0
    hydro=sum(HYDRO.get(a,0) for a in seq)/len(seq)
    acc=max(0,min(1,(4-hydro)/8))
    cons=min(1,len(seq)/1000)
    vir=0.1; gp=(seq.count("G")+seq.count("P"))/max(1,len(seq)); human=min(1,gp*4)
    s=(W["accessibility"]*acc+W["conservation"]*cons+W["virulence"]*vir-W["human_similarity_penalty"]*human)*100
    import re
    surface=any(sum(HYDRO.get(a,0) for a in seq[i:i+20])/20>1.5 for i in range(len(seq)-20))
    secreted=bool(re.match(r"M[KR].{1,15}[LI].{2,3}[AGS]",seq[:30]))
    return {"name":"","sequence":seq,"score":round(s,2),"is_surface":surface,"is_secreted":secreted}
async def run(self,inputs):
    proteins=inputs.get("protein_list",[])
    scored=[_score(p["sequence"] if isinstance(p,dict) else p.sequence) for p in proteins]
    for i,s in enumerate(scored): s["name"]=proteins[i].get("name","p"+str(i)) if isinstance(proteins[i],dict) else proteins[i].name
    scored.sort(key=lambda x:x["score"],reverse=True)
    return ModuleResult(outputs={"ranked_antigens":scored[:50],"scores":[{"name":s["name"],"score":s["score"]} for s in scored],"total_proteins_scored":len(scored)},model_version=self.default_model_version)
def score_uncertainty(self,result,inputs):
    s=result.outputs.get("scores",[]); return 1.0 if not s else round(max(0,min(1,1-max(x["score"] for x in s)/100)),3)
