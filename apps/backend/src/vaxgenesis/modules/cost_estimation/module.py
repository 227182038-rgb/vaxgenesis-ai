"""Module 24 - Cost Estimation."""
from __future__ import annotations
from typing import Any
from vaxgenesis.modules.base import BaseModule, ModuleResult

class CostEstimationModule(BaseModule):
    module_id = "cost_estimation"
    module_name = "Cost Estimation."
    description = "Module 24 - Cost Estimation."
    category = "action"
    inputs = ['construct', 'manufacturing_results']
    outputs = ['cogs_per_dose', 'capex', 'opex', 'break_even_doses']
    default_model_version = "1.0.0"

async def run(self,inputs):
    m=inputs.get("manufacturing_results",{}); bc=m.get("estimated_cost_per_dose_usd",2.0); sc=m.get("scalability_score",0.5)
    cogs={"1M_doses_year":round(bc*1.5,2),"10M_doses_year":round(bc*1.0,2),"100M_doses_year":round(bc*0.6,2)}
    capex=round(50e6+(1-sc)*100e6); opex=round(cogs["100M_doses_year"]*100e6*1.5); sp=5.0; be=round(capex/max(0.01,sp-cogs["100M_doses_year"]))
    return ModuleResult(outputs={"cogs_per_dose_by_scale":cogs,"capex_usd":capex,"annual_opex_usd":opex,"break_even_doses":be},model_version=self.default_model_version)
def score_uncertainty(self,result,inputs): return 0.35
