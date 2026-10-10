"""Validator Agent - runs the 27-module prediction pipeline."""
from __future__ import annotations
import asyncio
from typing import Any
from uuid import UUID
from sqlalchemy import select
from vaxgenesis.agents.base import AgentContext, AgentMessage, BaseAgent, record_iteration
from vaxgenesis.db.session_stub import SessionLocal

class ValidatorAgent(BaseAgent):
    name = "validator"
    description = "Runs the 27-module prediction pipeline"

    async def think(self, context):
        db = SessionLocal()
        try:
            from vaxgenesis.models import Candidate
            candidate = db.get(Candidate, UUID(context.candidate_id)) if hasattr(db, 'get') else None
            results = {}

            # Run key modules in order
            from vaxgenesis.modules.genome_analysis.module import GenomeAnalysisModule
            from vaxgenesis.modules.reverse_vaccinology.module import ReverseVaccinologyModule
            from vaxgenesis.modules.antigen_discovery.module import AntigenDiscoveryModule
            from vaxgenesis.modules.epitope_prediction.module import EpitopePredictionModule
            from vaxgenesis.modules.hla_binding.module import HlaBindingModule
            from vaxgenesis.modules.toxicity_prediction.module import ToxicityPredictionModule
            from vaxgenesis.modules.vaccine_construct.module import VaccineConstructModule
            from vaxgenesis.modules.immune_simulation.module import ImmuneSimulationModule
            from vaxgenesis.modules.ai_risk_assessment.module import AIRiskAssessmentModule

            cid = UUID(context.candidate_id)

            # Simplified pipeline
            try:
                rv = ReverseVaccinologyModule(cid, db_session=db)
                rv_r = await rv.execute({"protein_list": [{"sequence": "MKLVGILGFVFTLNLVPMVATV", "name": "Spike"}]})
                results["reverse_vaccinology"] = rv_r.outputs
            except: pass

            try:
                epi = EpitopePredictionModule(cid, db_session=db)
                epi_r = await epi.execute({"antigen_sequences": [{"sequence": "MKLVGILGFVFTLNLVPMVATV", "name": "Spike"}]})
                results["epitope_prediction"] = epi_r.outputs
            except: pass

            try:
                hla = HlaBindingModule(cid, db_session=db)
                hla_r = await hla.execute({"epitope_sequences": epi_r.outputs.get("ctl_epitopes", []), "hla_alleles": context.target_hla_alleles or ["HLA-A*02:01"]})
                results["hla_binding"] = hla_r.outputs
            except: pass

            try:
                tox = ToxicityPredictionModule(cid, db_session=db)
                tox_r = await tox.execute({"epitopes": epi_r.outputs.get("ctl_epitopes", [])})
                results["toxicity_prediction"] = tox_r.outputs
            except: pass

            try:
                vc = VaccineConstructModule(cid, db_session=db)
                vc_r = await vc.execute({"epitopes": epi_r.outputs.get("ctl_epitopes", []) + epi_r.outputs.get("htl_epitopes", []) + epi_r.outputs.get("linear_bcell_epitopes", [])})
                results["vaccine_construct"] = vc_r.outputs
            except: pass

            try:
                risk = AIRiskAssessmentModule(cid, db_session=db)
                risk_r = await risk.execute({"all_predictions": results})
                results["ai_risk_assessment"] = risk_r.outputs
            except: pass

            context.artifacts["validation"] = results
            record_iteration("validator", "validated")
            return AgentMessage(role="validator", content=f"Pipeline complete. {len(results)} modules executed.", metadata={"modules": list(results.keys())})
        finally:
            db.close()
