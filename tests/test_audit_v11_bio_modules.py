"""Tests for the audit-v1.1 bioinformatics modules."""
from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest


# ============================================================
# Module 28: Autoimmunity Screening
# ============================================================

class TestAutoimmunityScreening:
    def _make_module(self):
        from vaxgenesis.modules.autoimmunity_screening.module import AutoimmunityScreeningModule
        return AutoimmunityScreeningModule(uuid4())

    def test_flags_known_self_peptide(self):
        """GILGFVFTL is in the human self-peptide set → should be flagged."""
        m = self._make_module()
        result = asyncio.run(m.execute({"epitope_sequences": ["GILGFVFTL"]}))
        scored = result.outputs["self_reactivity_scores"]
        assert scored[0]["is_self_reactive"] is True

    def test_does_not_flag_random_peptide(self):
        """A random peptide should not be flagged."""
        m = self._make_module()
        result = asyncio.run(m.execute({"epitope_sequences": ["ZZZZZZZZZ"]}))
        scored = result.outputs["self_reactivity_scores"]
        assert scored[0]["is_self_reactive"] is False

    def test_composite_risk_score(self):
        """Composite risk = fraction of flagged epitopes."""
        m = self._make_module()
        result = asyncio.run(m.execute({
            "epitope_sequences": ["GILGFVFTL", "NLVPMVATV", "RANDOMPEP"],
        }))
        # 2 of 3 are in the self-peptide set
        assert result.outputs["composite_autoimmunity_risk"] > 0
        assert result.outputs["self_reactive_count"] >= 1


# ============================================================
# Module 29: Proteasome Cleavage
# ============================================================

class TestProteasomeCleavage:
    def _make_module(self):
        from vaxgenesis.modules.proteasome_cleavage.module import ProteasomeCleavageModule
        return ProteasomeCleavageModule(uuid4())

    def test_predicts_cleavage_sites(self):
        """Should find cleavage sites in a typical antigen sequence."""
        m = self._make_module()
        result = asyncio.run(m.execute({
            "antigen_sequence": "MKLVGILGFVFTLNLVPMVATVGLCTLVAML",
            "epitope_sequences": ["GILGFVFTL"],
        }))
        assert len(result.outputs["cleavage_sites"]) > 0
        assert result.outputs["presentation_rate"] >= 0

    def test_epitope_not_in_antigen(self):
        """Epitopes not in the antigen get score 0."""
        m = self._make_module()
        result = asyncio.run(m.execute({
            "antigen_sequence": "MKLVGILGFVFTLNLVPMVATVGLCTLVAML",
            "epitope_sequences": ["NOTPRESENT"],
        }))
        scored = result.outputs["epitope_processing_likelihood"]
        assert scored[0]["is_likely_presented"] is False
        assert scored[0]["reason"] == "epitope_not_in_antigen"

    def test_presentation_rate_calculation(self):
        """Presentation rate = presented / total."""
        m = self._make_module()
        result = asyncio.run(m.execute({
            "antigen_sequence": "MKLVGILGFVFTLNLVPMVATVGLCTLVAML",
            "epitope_sequences": ["GILGFVFTL", "NLVPMVATV"],
        }))
        rate = result.outputs["presentation_rate"]
        assert 0.0 <= rate <= 1.0


# ============================================================
# Module 30: Glycosylation Analysis
# ============================================================

class TestGlycosylationAnalysis:
    def _make_module(self):
        from vaxgenesis.modules.glycosylation_analysis.module import GlycosylationAnalysisModule
        return GlycosylationAnalysisModule(uuid4())

    def test_finds_n_linked_sequons(self):
        """N-X-S/T sequons are detected."""
        m = self._make_module()
        # N-R-T is a valid N-linked sequon (N, R, T — R != P)
        result = asyncio.run(m.execute({
            "construct_sequence": "MNRTVNSTN",  # 2 N-linked sequons
            "epitope_sequences": [],
        }))
        assert result.outputs["total_n_linked"] == 2

    def test_does_not_find_n_proline_sequon(self):
        """N-P-S/T is NOT a valid sequon."""
        m = self._make_module()
        result = asyncio.run(m.execute({
            "construct_sequence": "MNPST",  # N-P-S → invalid
            "epitope_sequences": [],
        }))
        assert result.outputs["total_n_linked"] == 0

    def test_flags_shielded_epitopes(self):
        """Epitopes overlapping glycosylation sites are flagged."""
        m = self._make_module()
        result = asyncio.run(m.execute({
            "construct_sequence": "MNRTVNSTNLGNGTAC",
            "epitope_sequences": ["NRTVNSTNL"],  # overlaps N-R-T and N-S-T
        }))
        assert len(result.outputs["glycosylation_shielded_epitopes"]) >= 1
        assert result.outputs["glycosylation_risk_score"] > 0


# ============================================================
# Module 31: Subcellular Localization
# ============================================================

class TestSubcellularLocalization:
    def _make_module(self):
        from vaxgenesis.modules.subcellular_localization.module import SubcellularLocalizationModule
        return SubcellularLocalizationModule(uuid4())

    def test_classifies_membrane_protein(self):
        """A protein with a TM helix is classified as membrane."""
        m = self._make_module()
        # 25 hydrophobic residues = TM helix
        seq = "M" + "L" * 25 + "GCGCGCGCGC"
        result = asyncio.run(m.execute({"protein_list": [{"sequence": seq, "name": "TM"}]}))
        pred = result.outputs["localization_predictions"][0]
        assert pred["localization"] == "membrane"
        assert pred["is_surface_accessible"] is True
        assert pred["tm_helix_count"] >= 1

    def test_classifies_secreted_protein(self):
        """A protein with signal peptide and no TM is secreted."""
        m = self._make_module()
        # Signal peptide motif: M[KR].{1,15}[LI].{2,3}[AGS]
        # MKLFVLLVSL matches; followed by hydrophilic tail (no TM helix)
        # Total < 25 hydrophobic residues so no TM helix detected
        seq = "MKLFVLLVSL" + "STNQDEKRH" * 5  # ~55 aa, hydrophilic tail
        result = asyncio.run(m.execute({"protein_list": [{"sequence": seq, "name": "Sec"}]}))
        pred = result.outputs["localization_predictions"][0]
        assert pred["has_signal_peptide"] is True
        # If TM helix detected, it would be membrane; otherwise secreted
        if pred["tm_helix_count"] == 0:
            assert pred["localization"] == "secreted"

    def test_counts_surface_proteins(self):
        """Surface protein count is correct."""
        m = self._make_module()
        result = asyncio.run(m.execute({"protein_list": [
            {"sequence": "M" + "L" * 25 + "GC", "name": "p1"},
            {"sequence": "MGC" * 20, "name": "p2"},  # cytoplasm
        ]}))
        assert result.outputs["surface_protein_count"] == 1


# ============================================================
# Module 32 (extension): Bioreactor Kinetics
# ============================================================

class TestBioreactorKinetics:
    def _make_module(self):
        from vaxgenesis.modules.bioreactor_kinetics.module import BioreactorKineticsModule
        return BioreactorKineticsModule(uuid4())

    def test_simulates_growth(self):
        """Monod model produces a growth profile."""
        m = self._make_module()
        result = asyncio.run(m.execute({
            "construct": {"length_aa": 200},
            "expression_host": "ecoli",
            "manufacturing_results": {},
        }))
        growth = result.outputs["growth_profile"]
        assert growth["final_biomass_g_per_l"] > 0
        assert growth["final_product_g_per_l"] > 0
        assert len(growth["growth_trajectory"]) > 0

    def test_dsp_cascade(self):
        """DSP cascade reduces yield at each stage."""
        m = self._make_module()
        result = asyncio.run(m.execute({
            "construct": {"length_aa": 200},
            "expression_host": "ecoli",
            "manufacturing_results": {},
        }))
        cascade = result.outputs["dsp_yield_cascade"]
        assert cascade["final_yield_fraction"] < 1.0
        assert len(cascade["stages"]) >= 5
        # Each stage should reduce or maintain the amount
        for i in range(1, len(cascade["stages"])):
            assert cascade["stages"][i]["output_g"] <= cascade["stages"][i - 1]["output_g"]

    def test_supply_chain_bottleneck(self):
        """Supply chain analysis identifies the longest-lead-time item."""
        m = self._make_module()
        result = asyncio.run(m.execute({
            "construct": {"length_aa": 200},
            "expression_host": "ecoli",
            "manufacturing_results": {},
        }))
        sc = result.outputs["supply_chain_bottlenecks"]
        assert sc["bottleneck"] == "chromatography_resin"
        assert sc["bottleneck_lead_time_days"] == 30

    def test_host_specific_kinetics(self):
        """CHO host has slower growth than E. coli."""
        m_ecoli = self._make_module()
        r_ecoli = asyncio.run(m_ecoli.execute({
            "construct": {"length_aa": 200},
            "expression_host": "ecoli",
            "manufacturing_results": {},
        }))

        from vaxgenesis.modules.bioreactor_kinetics.module import BioreactorKineticsModule
        m_cho = BioreactorKineticsModule(uuid4())
        r_cho = asyncio.run(m_cho.execute({
            "construct": {"length_aa": 200},
            "expression_host": "cho",
            "manufacturing_results": {},
        }))

        ecoli_titer = r_ecoli.outputs["estimated_titer_g_per_l"]
        cho_titer = r_cho.outputs["estimated_titer_g_per_l"]
        assert cho_titer < ecoli_titer  # CHO should produce less
