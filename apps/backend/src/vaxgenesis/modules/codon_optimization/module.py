"""Module 18 - Codon Optimization."""
from __future__ import annotations
from typing import Any
from vaxgenesis.modules.base import BaseModule, ModuleResult

class CodonOptimizationModule(BaseModule):
    module_id = "codon_optimization"
    module_name = "Codon Optimization."
    description = "Module 18 - Codon Optimization."
    category = "action"
    inputs = ['construct_sequence', 'expression_host']
    outputs = ['optimized_dna', 'cai', 'gc_content']
    default_model_version = "1.0.0"

import math
TABLES={"human":{"A":{"GCT":0.27,"GCC":0.40,"GCA":0.21,"GCG":0.12},"R":{"CGT":0.09,"CGC":0.19,"CGA":0.10,"CGG":0.22,"AGA":0.21,"AGG":0.20},"N":{"AAT":0.47,"AAC":0.53},"D":{"GAT":0.46,"GAC":0.54},"C":{"TGT":0.46,"TGC":0.54},"Q":{"CAA":0.25,"CAG":0.75},"E":{"GAA":0.42,"GAG":0.58},"G":{"GGT":0.16,"GGC":0.34,"GGA":0.25,"GGG":0.25},"H":{"CAT":0.42,"CAC":0.58},"I":{"ATT":0.36,"ATC":0.47,"ATA":0.17},"L":{"TTA":0.07,"TTG":0.13,"CTT":0.13,"CTC":0.20,"CTA":0.07,"CTG":0.40},"K":{"AAA":0.43,"AAG":0.57},"M":{"ATG":1.00},"F":{"TTT":0.46,"TTC":0.54},"P":{"CCT":0.29,"CCC":0.32,"CCA":0.28,"CCG":0.11},"S":{"TCT":0.18,"TCC":0.22,"TCA":0.15,"TCG":0.06,"AGT":0.15,"AGC":0.24},"T":{"ACT":0.25,"ACC":0.36,"ACA":0.28,"ACG":0.11},"W":{"TGG":1.00},"Y":{"TAT":0.47,"TAC":0.53},"V":{"GTT":0.18,"GTC":0.24,"GTA":0.12,"GTG":0.46},"*":{"TAA":0.30,"TAG":0.20,"TGA":0.50}},
"ecoli":{"A":{"GCT":0.16,"GCC":0.27,"GCA":0.21,"GCG":0.36},"R":{"CGT":0.38,"CGC":0.36,"CGA":0.07,"CGG":0.10,"AGA":0.05,"AGG":0.04},"N":{"AAT":0.49,"AAC":0.51},"D":{"GAT":0.63,"GAC":0.37},"C":{"TGT":0.46,"TGC":0.54},"Q":{"CAA":0.34,"CAG":0.66},"E":{"GAA":0.68,"GAG":0.32},"G":{"GGT":0.35,"GGC":0.37,"GGA":0.13,"GGG":0.15},"H":{"CAT":0.57,"CAC":0.43},"I":{"ATT":0.49,"ATC":0.42,"ATA":0.09},"L":{"TTA":0.14,"TTG":0.13,"CTT":0.12,"CTC":0.10,"CTA":0.04,"CTG":0.47},"K":{"AAA":0.74,"AAG":0.26},"M":{"ATG":1.00},"F":{"TTT":0.58,"TTC":0.42},"P":{"CCT":0.18,"CCC":0.13,"CCA":0.20,"CCG":0.49},"S":{"TCT":0.17,"TCC":0.15,"TCA":0.14,"TCG":0.14,"AGT":0.16,"AGC":0.24},"T":{"ACT":0.19,"ACC":0.40,"ACA":0.17,"ACG":0.24},"W":{"TGG":1.00},"Y":{"TAT":0.59,"TAC":0.41},"V":{"GTT":0.28,"GTC":0.20,"GTA":0.17,"GTG":0.35},"*":{"TAA":0.61,"TAG":0.09,"TGA":0.30}}}
async def run(self,inputs):
    prot=inputs.get("construct_sequence",""); host=inputs.get("expression_host","human")
    if host not in TABLES: host="human"
    t=TABLES[host]; dna=[]
    for aa in prot:
        if aa in t: dna.append(max(t[aa].items(),key=lambda x:x[1])[0])
    ds="".join(dna); cai=math.exp(sum(math.log(max(t[aa].values())) for aa in prot if aa in t)/max(1,len([a for a in prot if a in t])))
    gc=sum(1 for c in ds if c in "GC")/max(1,len(ds))
    return ModuleResult(outputs={"optimized_dna":ds,"expression_host":host,"cai":round(cai,4),"gc_content":round(gc,4),"length_bp":len(ds)},model_version=self.default_model_version)
def score_uncertainty(self,result,inputs):
    c=result.outputs.get("cai",0.5); return round(max(0,1-c),3)
