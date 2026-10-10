"""Tests for v2.0 XAI and advanced computational biology."""
from __future__ import annotations

import pytest


class TestExplanationGenerator:
    def test_generate_explanation_with_attributions(self):
        from vaxgenesis.xai.explanations import ExplanationGenerator
        gen = ExplanationGenerator()
        explanation = gen.generate(
            prediction_id="pred-123",
            model_name="hla_binding",
            model_version="1.0.0",
            score=0.82,
            ci_low=0.72,
            ci_high=0.92,
            feature_values={
                "peptide_length": 9,
                "hydrophobicity": -0.3,
                "c_terminal_residue": "L",
            },
            feature_attributions={
                "peptide_length": 0.15,
                "hydrophobicity": 0.35,
                "c_terminal_residue": 0.20,
            },
            threshold=0.5,
        )
        assert explanation.prediction_id == "pred-123"
        assert len(explanation.feature_attributions) == 3
        # Top attribution should be hydrophobicity (0.35)
        assert explanation.feature_attributions[0].feature_name == "hydrophobicity"
        assert explanation.confidence_explanation is not None
        assert "0.820" in explanation.confidence_explanation.sentence or "0.82" in explanation.confidence_explanation.sentence
        assert len(explanation.narrative) > 50

    def test_confidence_explanation_certainty_levels(self):
        from vaxgenesis.xai.explanations import ConfidenceExplanation
        # Narrow CI → high certainty
        expl = ConfidenceExplanation.generate(score=0.8, ci_low=0.78, ci_high=0.82)
        assert "high" in expl.sentence

        # Wide CI → low certainty
        expl = ConfidenceExplanation.generate(score=0.5, ci_low=0.2, ci_high=0.8)
        assert "low" in expl.sentence

    def test_counterfactual_generation(self):
        from vaxgenesis.xai.explanations import Counterfactual
        cf = Counterfactual.generate(
            feature_name="hydrophobicity",
            current_value=-0.3,
            threshold=0.5,
            current_score=0.82,
            target_score=0.49,
        )
        assert cf.direction == "decrease"
        assert cf.magnitude_pct > 0
        assert "hydrophobicity" in cf.sentence

    def test_explanation_without_attributions(self):
        from vaxgenesis.xai.explanations import ExplanationGenerator
        gen = ExplanationGenerator()
        explanation = gen.generate(
            prediction_id="pred-456",
            model_name="toxicity_prediction",
            model_version="1.1.0",
            score=0.3,
            ci_low=0.2,
            ci_high=0.4,
            feature_values={"peptide": "GILGFVFTL"},
        )
        assert len(explanation.feature_attributions) == 0
        assert explanation.confidence_explanation is not None


class TestParetoOptimizer:
    def test_find_pareto_front(self):
        from vaxgenesis.modules.advanced.optimization import ParetoOptimizer, ParetoSolution
        solutions = [
            ParetoSolution(candidate_id="c1", objectives={"immunogenicity": 0.8, "safety": 0.9}),
            ParetoSolution(candidate_id="c2", objectives={"immunogenicity": 0.9, "safety": 0.7}),
            ParetoSolution(candidate_id="c3", objectives={"immunogenicity": 0.7, "safety": 0.8}),  # dominated by c1
            ParetoSolution(candidate_id="c4", objectives={"immunogenicity": 0.95, "safety": 0.95}),  # dominates all
        ]
        front = ParetoOptimizer.find_pareto_front(solutions)
        front_ids = {s.candidate_id for s in front}
        # c4 dominates c1, c2, c3 → only c4 is on the front
        assert "c4" in front_ids
        assert "c3" not in front_ids  # dominated by c1 and c4

    def test_pareto_front_empty(self):
        from vaxgenesis.modules.advanced.optimization import ParetoOptimizer
        assert ParetoOptimizer.find_pareto_front([]) == []

    def test_pareto_front_all_non_dominated(self):
        from vaxgenesis.modules.advanced.optimization import ParetoOptimizer, ParetoSolution
        solutions = [
            ParetoSolution(candidate_id="a", objectives={"x": 1.0, "y": 0.0}),
            ParetoSolution(candidate_id="b", objectives={"x": 0.0, "y": 1.0}),
        ]
        front = ParetoOptimizer.find_pareto_front(solutions)
        assert len(front) == 2  # neither dominates the other


class TestEnsembleAggregator:
    def test_uncertainty_weighted_aggregation(self):
        from vaxgenesis.modules.advanced.optimization import (
            EnsembleAggregator, EnsembleMember,
        )
        members = [
            EnsembleMember(name="model_a", version="1.0", prediction=0.8, uncertainty=0.1),
            EnsembleMember(name="model_b", version="1.0", prediction=0.6, uncertainty=0.3),
        ]
        result = EnsembleAggregator.aggregate(members, method="uncertainty_weighted")
        # model_a has lower uncertainty → higher weight → score closer to 0.8
        assert 0.7 < result.aggregated_score < 0.8
        # Disagreement should be low (only 0.2 difference)
        assert result.disagreement < 0.2

    def test_mean_aggregation(self):
        from vaxgenesis.modules.advanced.optimization import (
            EnsembleAggregator, EnsembleMember,
        )
        members = [
            EnsembleMember(name="a", version="1", prediction=0.6, uncertainty=0.1),
            EnsembleMember(name="b", version="1", prediction=0.8, uncertainty=0.1),
        ]
        result = EnsembleAggregator.aggregate(members, method="mean")
        assert result.aggregated_score == pytest.approx(0.7, abs=0.01)

    def test_empty_ensemble(self):
        from vaxgenesis.modules.advanced.optimization import EnsembleAggregator
        result = EnsembleAggregator.aggregate([], method="mean")
        assert result.aggregated_score == 0.0
        assert result.aggregated_uncertainty == 1.0

    def test_disagreement_metric(self):
        from vaxgenesis.modules.advanced.optimization import (
            EnsembleAggregator, EnsembleMember,
        )
        members = [
            EnsembleMember(name="a", version="1", prediction=0.2, uncertainty=0.1),
            EnsembleMember(name="b", version="1", prediction=0.8, uncertainty=0.1),
        ]
        result = EnsembleAggregator.aggregate(members, method="mean")
        assert result.disagreement > 0.2  # high disagreement


class TestCodonHarmonizer:
    def test_harmonize_produces_valid_dna(self):
        from vaxgenesis.modules.advanced.optimization import CodonHarmonizer
        protein = "ALLLR"  # 5 amino acids
        dna = CodonHarmonizer.harmonize(protein, host="ecoli")
        assert len(dna) == len(protein) * 3  # 3 nucleotides per codon
        assert all(c in "ATCG" for c in dna)

    def test_harmonize_empty_protein(self):
        from vaxgenesis.modules.advanced.optimization import CodonHarmonizer
        dna = CodonHarmonizer.harmonize("", host="ecoli")
        assert dna == ""


class TestRegulatoryReport:
    def test_generate_report_ready(self):
        from vaxgenesis.regulatory.reports import RegulatoryReportGenerator
        from uuid import uuid4
        gen = RegulatoryReportGenerator()
        report = gen.generate(
            candidate_id=uuid4(),
            candidate_data={
                "version": 1,
                "risk_score": 0.2,
                "overall_uncertainty": 0.3,
            },
            predictions=[
                {"module": "hla_binding", "model_version": "1.0.0"},
                {"module": "epitope_prediction", "model_version": "2.0.0"},
            ],
            assays=[{"id": "a1", "status": "completed"}],
            audit_trail=[{"entry_id": "e1"}],
        )
        assert report.overall_readiness == "ready"
        assert len(report.blocking_issues) == 0
        assert len(report.sections) >= 5

    def test_generate_report_not_ready(self):
        from vaxgenesis.regulatory.reports import RegulatoryReportGenerator
        from uuid import uuid4
        gen = RegulatoryReportGenerator()
        report = gen.generate(
            candidate_id=uuid4(),
            candidate_data={
                "version": 1,
                "risk_score": 0.6,  # high risk
                "overall_uncertainty": 0.7,  # high uncertainty
            },
            predictions=[],
            assays=[],  # no completed assays
            audit_trail=[],
        )
        assert report.overall_readiness == "not_ready"
        assert len(report.blocking_issues) >= 3

    def test_report_to_markdown(self):
        from vaxgenesis.regulatory.reports import RegulatoryReportGenerator
        from uuid import uuid4
        gen = RegulatoryReportGenerator()
        report = gen.generate(
            candidate_id=uuid4(),
            candidate_data={"version": 1, "risk_score": 0.3, "overall_uncertainty": 0.3},
            predictions=[],
            assays=[{"id": "a1", "status": "completed"}],
            audit_trail=[],
        )
        md = gen.to_markdown(report)
        assert "# Regulatory Readiness Report" in md
        assert "## 1. Software Description" in md
        assert "## 4. 21 CFR Part 11" in md
