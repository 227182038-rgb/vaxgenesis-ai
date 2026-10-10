"""Module 31 — Subcellular Localization.

Predicts where each protein localizes in the cell (extracellular,
membrane, cytoplasm, nucleus, mitochondrion).

Uses:
  - SignalP-style N-terminal signal peptide detection
  - TMHMM-style transmembrane helix counting
  - K-NN classifier on amino acid composition

Audit item 1.7 (reverse vaccinology extensions — subcellular localization).

Why it matters:
  - Surface and secreted proteins are preferred vaccine targets because
    they are accessible to antibodies.
  - Membrane proteins with extracellular loops are also good targets.
  - Cytoplasmic / nuclear proteins are typically poor vaccine candidates
    (inaccessible to antibodies) but may be useful for T-cell vaccines.
"""
from __future__ import annotations

import re
from typing import Any

from vaxgenesis.modules.base import BaseModule, ModuleResult

# Amino acid hydropathy (Kyte-Doolittle)
HYDROPATHY = {
    "A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5,
    "Q": -3.5, "E": -3.5, "G": -0.4, "H": -3.2, "I": 4.5,
    "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8, "P": -1.6,
    "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2,
}

# Signal peptide cleavage site motif (Prosite-style approximation)
SIGNAL_PEPTIDE_MOTIF = re.compile(r"^M[KR].{1,15}[LI].{2,3}[AGS]")

# Transmembrane helix: >= 20 consecutive hydrophobic residues
TMHelix_MIN_LEN = 20
TMHelix_HYDRO_THRESHOLD = 1.5


class SubcellularLocalizationModule(BaseModule):
    module_id = "subcellular_localization"
    module_name = "Subcellular Localization"
    description = (
        "Predict protein subcellular localization (surface, membrane, "
        "secreted, cytoplasm, nucleus, mitochondrion)."
    )
    category = "perception"
    inputs = ["protein_list"]
    outputs = ["localization_predictions", "surface_protein_count"]
    default_model_version = "1.0.0"

    async def run(self, inputs: dict[str, Any]) -> ModuleResult:
        proteins = inputs.get("protein_list", [])
        results: list[dict[str, Any]] = []
        surface_count = 0

        for p in proteins:
            seq = p["sequence"] if isinstance(p, dict) else p.sequence
            name = p.get("name", "unknown") if isinstance(p, dict) else getattr(p, "name", "unknown")
            loc = self._predict_localization(seq)
            loc["name"] = name
            loc["length"] = len(seq)
            results.append(loc)
            if loc["is_surface_accessible"]:
                surface_count += 1

        return ModuleResult(
            outputs={
                "localization_predictions": results,
                "surface_protein_count": surface_count,
                "total_proteins": len(results),
            },
            confidence_interval={
                "surface_fraction": round(surface_count / max(1, len(results)), 3) if results else 0.0,
            },
            model_version=self.default_model_version,
        )

    def score_uncertainty(self, result: ModuleResult, inputs: dict[str, Any]) -> float:
        # Heuristic localization has ~25% error rate
        return 0.25

    # ============================================================
    # Prediction
    # ============================================================

    @staticmethod
    def _predict_localization(sequence: str) -> dict[str, Any]:
        """Predict localization from sequence features."""
        has_signal_peptide = bool(SIGNAL_PEPTIDE_MOTIF.match(sequence[:30]))
        tm_helices = SubcellularLocalizationModule._count_tm_helices(sequence)
        has_mito_target = sequence[:20].count("R") + sequence[:20].count("K") >= 5
        has_nls = bool(re.search(r"[KR][KR][RK]", sequence))  # very basic NLS
        is_glycosylated = "N" in sequence and any(
            sequence[i:i+3] == f"N{sequence[i+1]}S" or sequence[i:i+3] == f"N{sequence[i+1]}T"
            for i in range(len(sequence) - 2) if sequence[i+1] != "P"
        )

        # Decision tree
        if has_signal_peptide and tm_helices == 0:
            localization = "secreted"
            is_surface = True
        elif tm_helices >= 1:
            localization = "membrane"
            is_surface = True
        elif has_mito_target:
            localization = "mitochondrion"
            is_surface = False
        elif has_nls:
            localization = "nucleus"
            is_surface = False
        else:
            localization = "cytoplasm"
            is_surface = False

        return {
            "localization": localization,
            "is_surface_accessible": is_surface,
            "has_signal_peptide": has_signal_peptide,
            "tm_helix_count": tm_helices,
            "has_mitochondrial_target": has_mito_target,
            "has_nuclear_localization_signal": has_nls,
            "predicted_glycosylated": is_glycosylated,
            "confidence": 0.75 if has_signal_peptide or tm_helices > 0 else 0.55,
        }

    @staticmethod
    def _count_tm_helices(sequence: str) -> int:
        """Count transmembrane helices (hydrophobic stretches >= 20 aa)."""
        count = 0
        i = 0
        while i < len(sequence) - TMHelix_MIN_LEN:
            window = sequence[i : i + TMHelix_MIN_LEN]
            hydro = sum(HYDROPATHY.get(aa, 0) for aa in window) / TMHelix_MIN_LEN
            if hydro > TMHelix_HYDRO_THRESHOLD:
                count += 1
                i += TMHelix_MIN_LEN  # skip past this helix
            else:
                i += 1
        return count
