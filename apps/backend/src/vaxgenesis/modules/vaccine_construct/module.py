"""Module 19 - Vaccine Construct Generator."""
from __future__ import annotations
from typing import Any
from vaxgenesis.modules.base import BaseModule, ModuleResult

class VaccineConstructModule(BaseModule):
    module_id = "vaccine_construct"
    module_name = "Vaccine Construct Generator."
    description = "Module 19 - Vaccine Construct Generator."
    category = "action"
    inputs = ['epitopes', 'adjuvant', 'linker']
    outputs = ['construct_sequence', 'construct_metadata']
    default_model_version = "1.0.0"

ADJ={"L7L12":"MAKAVLEKNPDVELNKIVELKDKDAIEKVLTTGVDGADIVKVAEGEKVTGDDTVKLAETGA","beta_defensin":"GIPCSTRCYSRQYRIGRCSTRCYSRQYRIGRCS","flagellin":"MAQVINTNSLSLITQRNRRSALHVGDLSQKSAIAENNLRKSAEKLQQ","none":""}
LK={"AAY":"AAY","GPGPG":"GPGPG","EAAAK":"EAAAK","KK":"KK"}
async def run(self,inputs):
    epis=inputs.get("epitopes",[])
    ctl=[e["sequence"] for e in epis if e.get("type")=="ctl"][:10]
    htl=[e["sequence"] for e in epis if e.get("type")=="htl"][:5]
    bcell=[e["sequence"] for e in epis if e.get("type")=="linear_bcell"][:5]
    parts=[];order=[]
    adj=ADJ.get(self.config.get("adjuvant","beta_defensin") if self.config else "beta_defensin","")
    if adj: parts.append(adj); order.append({"component":"adjuvant","length":len(adj)})
    if adj: parts.append(LK["EAAAK"])
    for i,e in enumerate(ctl):
        parts.append(e); order.append({"component":"ctl_epitope","index":i})
        if i<len(ctl)-1: parts.append(LK["AAY"])
    if ctl and htl: parts.append(LK["GPGPG"])
    for i,e in enumerate(htl):
        parts.append(e); order.append({"component":"htl_epitope","index":i})
        if i<len(htl)-1: parts.append(LK["GPGPG"])
    if(ctl or htl)and bcell: parts.append(LK["KK"])
    for i,e in enumerate(bcell):
        parts.append(e); order.append({"component":"bcell_epitope","index":i})
        if i<len(bcell)-1: parts.append(LK["KK"])
    ht="H"*6; parts.append(LK["KK"]); parts.append(ht)
    cs="".join(parts)
    mw=sum({"A":89.1,"R":174.2,"N":132.1,"D":133.1,"C":121.2,"Q":146.2,"E":147.1,"G":75.0,"H":155.2,"I":131.2,"L":131.2,"K":146.2,"M":149.2,"F":165.2,"P":115.1,"S":105.1,"T":119.1,"W":204.2,"Y":181.2,"V":117.1}.get(a,110) for a in cs)-18*(len(cs)-1)
    return ModuleResult(outputs={"construct_sequence":cs,"construct_metadata":{"adjuvant":"beta_defensin","epitope_order":order,"his_tag":True,"molecular_weight_kda":round(mw/1000,2),"length_aa":len(cs),"ctl_count":len(ctl),"htl_count":len(htl),"bcell_count":len(bcell)}},model_version=self.default_model_version)
def score_uncertainty(self,result,inputs):
    l=result.outputs["construct_metadata"]["length_aa"]; return round(min(0.8,l/1000),3)
