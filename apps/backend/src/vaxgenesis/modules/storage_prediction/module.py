"""Module 23 - Storage Prediction."""
from __future__ import annotations
from typing import Any
from vaxgenesis.modules.base import BaseModule, ModuleResult

class StoragePredictionModule(BaseModule):
    module_id = "storage_prediction"
    module_name = "Storage Prediction."
    description = "Module 23 - Storage Prediction."
    category = "action"
    inputs = ['construct', 'stability_results']
    outputs = ['shelf_life_by_condition', 'recommended_condition']
    default_model_version = "1.0.0"

async def run(self,inputs):
    st=inputs.get("stability_results",{}); tm=st.get("predicted_tm_celsius",60)
    sl={"2-8C":round(max(30,(tm-25)*30)),"-20C":round(max(180,(tm-25)*100)),"-80C":round(max(365,(tm-25)*365)),"lyophilized":round(max(730,(tm-25)*730))}
    rec="lyophilized" if sl["lyophilized"]>=730 else "-80C"
    return ModuleResult(outputs={"shelf_life_days_by_condition":sl,"recommended_condition":rec},model_version=self.default_model_version)
def score_uncertainty(self,result,inputs): return 0.5
