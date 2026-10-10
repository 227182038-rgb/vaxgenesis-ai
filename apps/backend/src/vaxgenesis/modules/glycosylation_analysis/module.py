"""Module 30 — Glycosylation Site Analysis.

Predicts N-linked and O-linked glycosylation sites on the construct.

N-linked: canonical sequon N-X-S/T where X is not P.
O-linked: predicted via a NetOGlyc-style position-specific model
          (simplified: S/T in surface-exposed, proline-rich contexts).

Why it matters for vaccine design:
  - Glycosylation can shield epitopes from antibody recognition.
  - N-linked glycans can be exploited (e.g. HIV gp120 high-mannose
    patch as a target for broadly neutralizing antibodies).
  - Unexpected glycosylation changes the construct's apparent molecular
    weight and can complicate purification.

Audit item 1.6 (construct refinement).
"""
from __future__ import annotations

import re
from typing import Any

from vaxgenesis.modules.base import BaseModule, ModuleResult

# N-linked sequon: N-X-S/T, X != P
N_LINKED_MOTIF = re.compile(r"N[^P][ST]")

# O-linked: simplified NetOGlyc-style score (Ser/Thr in P-rich context)
O_LINKED_PROLINE_CONTEXT = re.compile(r"[ST]P|P[ST]")


class GlycosylationAnalysisModule(BaseModule):
    module_id = "glycosylation_analysis"
    module_name = "Glycosylation Site Analysis"
    description = (
        "Predict N-linked and O-linked glycosylation sites on the construct; "
        "flag epitopes that overlap glycosylated sequons."
    )
    category = "action"
    inputs = ["construct_sequence", "epitope_sequences"]
    outputs = [
        "n_linked_sites",
        "o_linked_sites",
        "glycosylation_shielded_epitopes",
        "glycosylation_risk_score",
    ]
    default_model_version = "1.0.0"

    async def run(self, inputs: dict[str, Any]) -> ModuleResult:
        sequence = inputs.get("construct_sequence", "")
        epitopes = inputs.get("epitope_sequences", []) or inputs.get("epitopes", [])

        n_sites = self._find_n_linked(sequence)
        o_sites = self._find_o_linked(sequence)

        # Check epitope overlap with glycosylation sites
        shielded: list[dict[str, Any]] = []
        for epi in epitopes:
            seq = epi["sequence"] if isinstance(epi, dict) else epi
            pos = sequence.find(seq)
            if pos < 0:
                continue
            epi_start = pos + 1
            epi_end = pos + len(seq)
            overlapping_n = [s for s in n_sites if epi_start <= s["position"] <= epi_end]
            overlapping_o = [s for s in o_sites if epi_start <= s["position"] <= epi_end]
            if overlapping_n or overlapping_o:
                shielded.append({
                    "sequence": seq,
                    "start": epi_start,
                    "end": epi_end,
                    "overlapping_n_sites": len(overlapping_n),
                    "overlapping_o_sites": len(overlapping_o),
                })

        # Risk: fraction of epitopes that are shielded
        risk = len(shielded) / max(1, len(epitopes)) if epitopes else 0.0

        return ModuleResult(
            outputs={
                "n_linked_sites": n_sites,
                "o_linked_sites": o_sites,
                "glycosylation_shielded_epitopes": shielded,
                "glycosylation_risk_score": round(risk, 3),
                "total_n_linked": len(n_sites),
                "total_o_linked": len(o_sites),
                "construct_length": len(sequence),
            },
            confidence_interval={
                "risk_low": round(max(0.0, risk - 0.1), 3),
                "risk_high": round(min(1.0, risk + 0.1), 3),
            },
            model_version=self.default_model_version,
        )

    def score_uncertainty(self, result: ModuleResult, inputs: dict[str, Any]) -> float:
        # N-linked prediction is near-certain (sequon-based); O-linked is noisy
        return 0.25

    # ============================================================
    # Site prediction
    # ============================================================

    @staticmethod
    def _find_n_linked(sequence: str) -> list[dict[str, Any]]:
        """Find all N-X-S/T sequons. Position is the N residue (1-based)."""
        sites: list[dict[str, Any]] = []
        for match in N_LINKED_MOTIF.finditer(sequence):
            sites.append({
                "position": match.start() + 1,
                "residue": "N",
                "type": "n_linked",
                "sequon": match.group(),
                "confidence": 0.95,  # canonical sequon is highly reliable
            })
        return sites

    @staticmethod
    def _find_o_linked(sequence: str) -> list[dict[str, Any]]:
        """Predict O-linked sites via proline-context heuristic.

        In production: replace with NetOGlyc-4.0 model output.
        """
        sites: list[dict[str, Any]] = []
        for match in O_LINKED_PROLINE_CONTEXT.finditer(sequence):
            # The glycosylated residue is the S/T in the match
            st_pos = match.start() if match.group()[0] in "ST" else match.start() + 1
            sites.append({
                "position": st_pos + 1,
                "residue": sequence[st_pos],
                "type": "o_linked",
                "context": match.group(),
                "confidence": 0.55,  # heuristic — lower confidence
            })
        return sites
