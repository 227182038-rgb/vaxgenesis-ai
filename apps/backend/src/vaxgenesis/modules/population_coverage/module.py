"""Module 10 - Population Coverage."""
from __future__ import annotations
from typing import Any
from vaxgenesis.modules.base import BaseModule, ModuleResult

class PopulationCoverageModule(BaseModule):
    module_id = "population_coverage"
    module_name = "Population Coverage."
    description = "Module 10 - Population Coverage."
    category = "reasoning"
    inputs = ['hla_bindings', 'target_populations']
    outputs = ['coverage_by_population', 'global_coverage']
    default_model_version = "1.1.0"

import numpy as np
FREQ={"USA":{"HLA-A*01:01":0.14,"HLA-A*02:01":0.26,"HLA-A*03:01":0.14,"HLA-B*07:02":0.12,"HLA-B*08:01":0.10,"HLA-DRB1*01:01":0.08,"HLA-DRB1*03:01":0.10,"HLA-DRB1*04:01":0.10,"HLA-DRB1*07:01":0.10,"HLA-DRB1*11:01":0.08,"HLA-DRB1*15:01":0.10},
"India":{"HLA-A*01:01":0.10,"HLA-A*02:01":0.18,"HLA-A*24:02":0.16,"HLA-B*07:02":0.06,"HLA-B*35:01":0.10,"HLA-DRB1*01:01":0.06,"HLA-DRB1*03:01":0.10,"HLA-DRB1*07:01":0.08,"HLA-DRB1*11:01":0.10,"HLA-DRB1*15:01":0.12},
"Europe":{"HLA-A*01:01":0.16,"HLA-A*02:01":0.27,"HLA-A*03:01":0.16,"HLA-B*07:02":0.14,"HLA-B*08:01":0.12,"HLA-DRB1*01:01":0.10,"HLA-DRB1*03:01":0.12,"HLA-DRB1*04:01":0.10,"HLA-DRB1*07:01":0.12,"HLA-DRB1*15:01":0.12},
"Africa":{"HLA-A*02:01":0.14,"HLA-A*23:01":0.10,"HLA-A*30:01":0.10,"HLA-B*35:01":0.12,"HLA-B*53:01":0.08,"HLA-DRB1*03:01":0.12,"HLA-DRB1*11:01":0.12,"HLA-DRB1*13:01":0.10,"HLA-DRB1*15:01":0.10},
"Japan":{"HLA-A*02:01":0.25,"HLA-A*24:02":0.35,"HLA-A*26:01":0.10,"HLA-B*35:01":0.10,"HLA-B*44:02":0.08,"HLA-B*46:01":0.08,"HLA-B*51:01":0.08,"HLA-DRB1*04:05":0.16,"HLA-DRB1*08:03":0.10,"HLA-DRB1*09:01":0.12,"HLA-DRB1*15:01":0.10},
"Australia":{"HLA-A*01:01":0.16,"HLA-A*02:01":0.26,"HLA-A*03:01":0.14,"HLA-B*07:02":0.12,"HLA-B*08:01":0.10,"HLA-DRB1*01:01":0.10,"HLA-DRB1*03:01":0.12,"HLA-DRB1*04:01":0.10,"HLA-DRB1*07:01":0.10,"HLA-DRB1*15:01":0.12}}
async def run(self,inputs):
    hla=inputs.get("hla_bindings",[]); pops=inputs.get("target_populations",list(FREQ.keys()))
    covered={b["hla_allele"] for b in hla if b.get("is_binder")}
    cov={}
    for pop in pops:
        ft=FREQ.get(pop,{})
        if not ft: cov[pop]=0; continue
        cum=1.0
        for al,fr in ft.items():
            if al in covered: cum*=(1-fr)
        cov[pop]=round(1-cum,4)
    gc=float(np.mean(list(cov.values()))) if cov else 0
    return ModuleResult(outputs={"coverage_by_population":cov,"global_coverage":round(gc,4),"covered_alleles":list(covered)},model_version=self.default_model_version)
def score_uncertainty(self,result,inputs):
    n=len(result.outputs.get("covered_alleles",[])); return 0.9 if n==0 else round(min(1,1/n),3)
