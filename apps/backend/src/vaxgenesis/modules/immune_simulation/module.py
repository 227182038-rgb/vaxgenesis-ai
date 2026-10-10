"""Module 20 - Immune Simulation."""
from __future__ import annotations
from typing import Any
from vaxgenesis.modules.base import BaseModule, ModuleResult

class ImmuneSimulationModule(BaseModule):
    module_id = "immune_simulation"
    module_name = "Immune Simulation."
    description = "Module 20 - Immune Simulation."
    category = "action"
    inputs = ['construct', 'epitopes']
    outputs = ['igm', 'igg', 'iga', 'ifn_gamma', 'il2', 'il10', 'memory_b', 'memory_t']
    default_model_version = "1.1.0"

import numpy as np
from scipy.integrate import solve_ivp
async def run(self,inputs):
    epis=inputs.get("epitopes",[])
    nb=sum(1 for e in epis if e.get("type")=="linear_bcell"); nt=sum(1 for e in epis if e.get("type") in("ctl","htl"))
    ad=max(1,nb+nt); dur=365
    def rhs(t,y):
        ag,igm,igg,iga,ifng,il2,il10,mb,mt=y
        return[-0.1*ag*(igm+igg),0.5*ag*max(nb,1)-0.05*igm,0.3*ag*max(nb,1)*(1+mb)-0.02*igg,0.1*ag*max(nb,1)-0.03*iga,0.4*ag*max(nt,1)-0.1*ifng,0.3*ag*max(nt,1)-0.1*il2,0.2*igg-0.05*il10,0.1*igg-0.001*mb,0.1*ifng-0.001*mt]
    sol=solve_ivp(rhs,(0,dur),[ad,0,0,0,0,0,0,0,0],t_eval=np.linspace(0,dur,100),method="LSODA")
    s=sol.y.T
    return ModuleResult(outputs={"igm_peak":round(float(np.max(s[:,1])),3),"igg_peak":round(float(np.max(s[:,2])),3),"iga_peak":round(float(np.max(s[:,3])),3),"ifn_gamma_peak":round(float(np.max(s[:,4])),3),"il2_peak":round(float(np.max(s[:,5])),3),"il10_peak":round(float(np.max(s[:,6])),3),"memory_b_steady":round(float(s[-1,7]),3),"memory_t_steady":round(float(s[-1,8]),3),"simulation_days":dur},model_version=self.default_model_version)
def score_uncertainty(self,result,inputs): return 0.5
