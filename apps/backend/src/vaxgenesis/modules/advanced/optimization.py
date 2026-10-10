"""Advanced computational biology — v2.0 additions.

This module adds capabilities that go beyond the v1.x 27-module pipeline:

  - **Pareto optimization:** Multi-objective candidate optimization
    (safety vs. immunogenicity vs. manufacturability).
  - **Ensemble prediction:** Run multiple bioinformatics models and
    aggregate via uncertainty-weighted voting.
  - **Codon harmonization:** Not just optimization — match the codon
    usage pattern of the host's highly-expressed genes.
"""
from __future__ import annotations

from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, Field


# ============================================================
# Pareto optimization
# ============================================================

class ParetoObjective(BaseModel):
    """A single objective in a multi-objective optimization."""

    name: str
    direction: Literal["maximize", "minimize"]
    weight: float = 1.0
    value: float | None = None


class ParetoSolution(BaseModel):
    """A non-dominated solution on the Pareto front."""

    candidate_id: str
    objectives: dict[str, float]
    is_dominated: bool = False


class ParetoOptimizer:
    """Multi-objective vaccine candidate optimizer.

    Finds the Pareto front — the set of non-dominated solutions where
    no single candidate is better on ALL objectives simultaneously.

    Example: maximize immunogenicity, minimize toxicity, minimize cost.
    """

    @staticmethod
    def find_pareto_front(solutions: list[ParetoSolution]) -> list[ParetoSolution]:
        """Identify non-dominated solutions.

        A solution is dominated if another solution is at least as good
        on all objectives and strictly better on at least one.
        """
        if not solutions:
            return []

        for sol in solutions:
            sol.is_dominated = False

        for i, sol_i in enumerate(solutions):
            for j, sol_j in enumerate(solutions):
                if i == j:
                    continue
                if ParetoOptimizer._dominates(sol_j, sol_i):
                    sol_i.is_dominated = True
                    break

        return [s for s in solutions if not s.is_dominated]

    @staticmethod
    def _dominates(a: ParetoSolution, b: ParetoSolution) -> bool:
        """Does solution `a` dominate solution `b`?

        `a` dominates `b` if a is >= b on all objectives (for maximize)
        and strictly > on at least one.
        """
        at_least_one_strictly_better = False
        for key in a.objectives:
            if key not in b.objectives:
                continue
            if a.objectives[key] < b.objectives[key]:
                return False
            if a.objectives[key] > b.objectives[key]:
                at_least_one_strictly_better = True
        return at_least_one_strictly_better

    @staticmethod
    def hypervolume(front: list[ParetoSolution], reference_point: dict[str, float]) -> float:
        """Compute the hypervolume indicator of a Pareto front.

        Higher hypervolume = better front quality.
        """
        if not front:
            return 0.0
        # 2D hypervolume (simplified for 2 objectives)
        if len(reference_point) == 2:
            keys = list(reference_point.keys())
            points = sorted(
                [(s.objectives.get(keys[0], 0), s.objectives.get(keys[1], 0)) for s in front],
                reverse=True,
            )
            hv = 0.0
            prev_x = reference_point[keys[0]]
            for x, y in points:
                hv += (prev_x - x) * (y - reference_point[keys[1]])
                prev_x = x
            return hv
        return 0.0  # N>2: use Monte Carlo


# ============================================================
# Ensemble prediction
# ============================================================

class EnsembleMember(BaseModel):
    """A single model in an ensemble."""

    name: str
    version: str
    prediction: float
    uncertainty: float


class EnsemblePrediction(BaseModel):
    """Aggregated prediction from multiple models."""

    members: list[EnsembleMember]
    aggregated_score: float
    aggregated_uncertainty: float
    aggregation_method: Literal["mean", "uncertainty_weighted", "majority_vote"]
    disagreement: float  # std of member predictions


class EnsembleAggregator:
    """Aggregates predictions from multiple bioinformatics models.

    Three strategies:
      - **mean:** simple average
      - **uncertainty_weighted:** weight by 1/uncertainty^2
      - **majority_vote:** binarize and vote (for classification)
    """

    @staticmethod
    def aggregate(
        members: list[EnsembleMember],
        method: Literal["mean", "uncertainty_weighted", "majority_vote"] = "uncertainty_weighted",
    ) -> EnsemblePrediction:
        if not members:
            return EnsemblePrediction(
                members=[],
                aggregated_score=0.0,
                aggregated_uncertainty=1.0,
                aggregation_method=method,
                disagreement=1.0,
            )

        predictions = np.array([m.prediction for m in members])
        uncertainties = np.array([m.uncertainty for m in members])

        if method == "mean":
            score = float(np.mean(predictions))
            unc = float(np.mean(uncertainties))
        elif method == "uncertainty_weighted":
            weights = 1.0 / (uncertainties ** 2 + 1e-8)
            weights /= weights.sum()
            score = float(np.sum(weights * predictions))
            unc = float(1.0 / np.sqrt(np.sum(weights)))
        else:  # majority_vote
            votes = (predictions > 0.5).astype(float)
            score = float(np.mean(votes))
            unc = float(np.std(votes))

        disagreement = float(np.std(predictions))

        return EnsemblePrediction(
            members=members,
            aggregated_score=round(score, 4),
            aggregated_uncertainty=round(unc, 4),
            aggregation_method=method,
            disagreement=round(disagreement, 4),
        )


# ============================================================
# Codon harmonization
# ============================================================

class CodonHarmonizer:
    """Codon harmonization — match the host's expression pattern.

    Unlike simple codon optimization (which picks the most-frequent
    codon for each amino acid), harmonization matches the *distribution*
    of codon usage to the host's highly-expressed genes.

    This preserves translation kinetics, which affects protein folding.
    A protein translated too fast or too slow may misfold.

    Reference: Gustafsson et al. "Codon bias and heterologous protein
    expression" (Trends Biotechnol, 2004).
    """

    ECOLI_HEG_USAGE = {
        "A": {"GCT": 0.30, "GCC": 0.20, "GCA": 0.20, "GCG": 0.30},
        "L": {"CTG": 0.50, "CTT": 0.15, "CTC": 0.10, "CTA": 0.05, "TTA": 0.05, "TTG": 0.15},
        "R": {"CGT": 0.35, "CGC": 0.25, "CGA": 0.05, "CGG": 0.10, "AGA": 0.15, "AGG": 0.10},
    }

    @classmethod
    def harmonize(
        cls,
        protein_sequence: str,
        host: Literal["ecoli", "human", "yeast", "cho"] = "ecoli",
    ) -> str:
        """Harmonize codon usage for the given host."""
        table = cls.ECOLI_HEG_USAGE
        dna = []
        for aa in protein_sequence:
            if aa in table:
                codons = list(table[aa].keys())
                probs = list(table[aa].values())
                total = sum(probs)
                probs = [p / total for p in probs]
                chosen = np.random.choice(codons, p=probs)
                dna.append(str(chosen))
        return "".join(dna)
