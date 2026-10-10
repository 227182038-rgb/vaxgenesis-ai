"""Value objects — immutable, validated domain primitives.

Value objects have no identity; they are defined entirely by their
attributes. Two value objects with the same attributes are
interchangeable.

All value objects are Pydantic v2 BaseModel subclasses with
`frozen=True` to enforce immutability.
"""
from __future__ import annotations

import re
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================
# Sequence value objects
# ============================================================

class Sequence(BaseModel):
    """An amino acid or nucleotide sequence.

    The `alphabet` field constrains which characters are allowed in
    `value`. Validation happens at construction time, so an invalid
    Sequence can never exist.
    """

    model_config = ConfigDict(frozen=True)

    alphabet: Literal["dna", "rna", "protein"]
    value: str = Field(min_length=1, max_length=1_000_000)

    @field_validator("value")
    @classmethod
    def _validate_alphabet_content(cls, v: str, info) -> str:
        alphabet = info.data.get("alphabet")
        if alphabet is None:
            return v.upper()
        allowed = {
            "dna": set("ATCGN"),
            "rna": set("AUCGN"),
            "protein": set("ACDEFGHIKLMNPQRSTVWYBXZJUO"),
        }
        alpha = allowed[alphabet]
        upper = v.upper()
        invalid = set(upper) - alpha
        if invalid:
            raise ValueError(
                f"Invalid characters {sorted(invalid)} for {alphabet} alphabet"
            )
        return upper

    @property
    def length(self) -> int:
        return len(self.value)

    def kmers(self, k: int) -> list[str]:
        """Return all overlapping k-mers of length k."""
        if k < 1 or k > self.length:
            return []
        return [self.value[i : i + k] for i in range(self.length - k + 1)]

    def gc_content(self) -> float:
        """Fraction of G/C bases (only meaningful for DNA/RNA)."""
        if self.alphabet == "protein":
            raise ValueError("gc_content not defined for protein sequences")
        gc = sum(1 for c in self.value if c in "GC")
        at = sum(1 for c in self.value if c in "ATU")
        return gc / max(1, gc + at)

    def reverse_complement(self) -> "Sequence":
        """Reverse complement (DNA only)."""
        if self.alphabet != "dna":
            raise ValueError("reverse_complement only defined for DNA")
        complement = str.maketrans("ATCGN", "TAGCN")
        return Sequence(value=self.value.translate(complement)[::-1], alphabet="dna")


class HlaAllele(BaseModel):
    """An HLA allele identifier, e.g. HLA-A*02:01."""

    model_config = ConfigDict(frozen=True)

    value: str

    @field_validator("value")
    @classmethod
    def _validate_format(cls, v: str) -> str:
        v = v.upper().strip()
        # Accepts HLA-A*02:01, HLA-DRB1*01:01, HLA-DPA1*01:03, etc.
        # Locus: 1-4 letters optionally followed by a digit (e.g. A, B, C, DRB1, DPA1)
        if not re.match(r"^HLA-[A-Z]{1,4}\d?\*\d{2,3}:\d{2,3}$", v):
            raise ValueError(
                f"Invalid HLA allele format: {v}. Expected HLA-A*02:01 or HLA-DRB1*01:01 style."
            )
        return v

    @property
    def mhc_class(self) -> Literal[1, 2]:
        """MHC class I (A, B, C) or II (DR, DP, DQ, DM, DO)."""
        locus_part = self.value.split("-")[1]
        if len(locus_part) >= 2 and locus_part[0] == "D" and locus_part[1] in "RPQMO":
            return 2
        return 1

    @property
    def locus(self) -> str:
        """Return the locus (e.g., 'A', 'B', 'DRB1', 'DPA1')."""
        return self.value.split("-")[1].split("*")[0]


# ============================================================
# Measurement value objects
# ============================================================

class ConfidenceInterval(BaseModel):
    """A calibrated confidence interval for a prediction."""

    model_config = ConfigDict(frozen=True)

    low: float
    high: float
    confidence_level: float = Field(default=0.95, ge=0.0, le=1.0)

    @field_validator("high")
    @classmethod
    def _high_ge_low(cls, v: float, info) -> float:
        low = info.data.get("low")
        if low is not None and v < low:
            raise ValueError(f"high ({v}) must be >= low ({low})")
        return v

    @property
    def width(self) -> float:
        return self.high - self.low

    @property
    def midpoint(self) -> float:
        return (self.low + self.high) / 2

    def contains(self, value: float) -> bool:
        return self.low <= value <= self.high


class UncertaintyScore(BaseModel):
    """A scalar uncertainty in [0, 1] with provenance."""

    model_config = ConfigDict(frozen=True)

    value: float = Field(ge=0.0, le=1.0)
    method: Literal["bayesian", "mc_dropout", "ensemble", "heuristic"]
    n_samples: int | None = Field(default=None, ge=1)

    @property
    def is_high(self) -> bool:
        """True if uncertainty exceeds the wet-lab validation threshold."""
        return self.value > 0.5


# ============================================================
# Identifier value objects
# ============================================================

class CandidateId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: UUID = Field(default_factory=uuid4)

    def __str__(self) -> str:
        return str(self.value)


class ProjectId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: UUID = Field(default_factory=uuid4)

    def __str__(self) -> str:
        return str(self.value)


class VariantId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: UUID = Field(default_factory=uuid4)

    def __str__(self) -> str:
        return str(self.value)


# ============================================================
# Composite value objects
# ============================================================

class Mutation(BaseModel):
    """A single point mutation relative to a reference."""

    model_config = ConfigDict(frozen=True)

    position: int = Field(ge=1)  # 1-based
    reference: str = Field(min_length=1, max_length=1)
    alternate: str = Field(min_length=1, max_length=1)
    kind: Literal["substitution", "insertion", "deletion"] = "substitution"

    @property
    def hgvs_like(self) -> str:
        """HGVS-style notation, e.g. 'A123T'."""
        return f"{self.reference}{self.position}{self.alternate}"


class EscapeScore(BaseModel):
    """Fraction of a candidate's epitopes escaped by a variant."""

    model_config = ConfigDict(frozen=True)

    value: float = Field(ge=0.0, le=1.0)
    escaped_epitope_count: int = Field(ge=0)
    total_epitope_count: int = Field(ge=1)

    @field_validator("value")
    @classmethod
    def _matches_counts(cls, v: float, info) -> float:
        escaped = info.data.get("escaped_epitope_count")
        total = info.data.get("total_epitope_count")
        if escaped is not None and total and total > 0:
            expected = escaped / total
            if abs(v - expected) > 0.01:
                raise ValueError(
                    f"value {v} doesn't match {escaped}/{total} = {expected}"
                )
        return v

    @property
    def tier(self) -> Literal["none", "watch", "alert", "reformulate", "critical"]:
        """Classify into alert tier per the v1.1 surveillance thresholds."""
        if self.value >= 0.60:
            return "critical"
        if self.value >= 0.40:
            return "reformulate"
        if self.value >= 0.20:
            return "alert"
        if self.value >= 0.10:
            return "watch"
        return "none"
