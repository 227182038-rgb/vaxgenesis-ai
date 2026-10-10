"""Property-based tests for value objects (ConfidenceInterval, EscapeScore, HlaAllele)."""
from __future__ import annotations

import pytest
from hypothesis import given, strategies as st, assume

from vaxgenesis.hexagon.domain.value_objects import (
    ConfidenceInterval, EscapeScore, HlaAllele, Mutation,
)


class TestConfidenceIntervalProperties:
    @given(
        low=st.floats(min_value=0.0, max_value=0.5, allow_nan=False),
        width=st.floats(min_value=0.0, max_value=0.5, allow_nan=False),
    )
    def test_width_equals_difference(self, low, width):
        high = low + width
        ci = ConfidenceInterval(low=low, high=high)
        assert ci.width == pytest.approx(width)

    @given(
        low=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        high=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    def test_high_must_be_ge_low(self, low, high):
        if high < low:
            with pytest.raises(Exception):
                ConfidenceInterval(low=low, high=high)
        else:
            ci = ConfidenceInterval(low=low, high=high)
            assert ci.low == low
            assert ci.high == high

    @given(
        low=st.floats(min_value=0.0, max_value=0.9, allow_nan=False),
        width=st.floats(min_value=0.01, max_value=0.1, allow_nan=False),
        val=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    def test_contains_predicate(self, low, width, val):
        high = low + width
        ci = ConfidenceInterval(low=low, high=high)
        expected = low <= val <= high
        assert ci.contains(val) == expected


class TestHlaAlleleProperties:
    @given(
        locus=st.sampled_from(["A", "B", "C", "DRA", "DRB1", "DPA1", "DPB1", "DQA1", "DQB1"]),
        num=st.integers(min_value=1, max_value=99),
    )
    def test_valid_alleles_parse(self, locus, num):
        allele_str = f"HLA-{locus}*{num:02d}:01"
        a = HlaAllele(value=allele_str)
        assert a.value == allele_str

    @given(bad=st.sampled_from([
        "HLA-A02:01",    # missing asterisk
        "HLA-A*2:1",      # too few digits
        "garbage",        # not HLA at all
        "HLA-*01:01",     # missing locus
        "HLA-A*01",       # missing colon+group
        "A*02:01",        # missing HLA- prefix
    ]))
    def test_invalid_alleles_rejected(self, bad):
        with pytest.raises(Exception):
            HlaAllele(value=bad)

    @given(locus=st.sampled_from(["A", "B", "C"]))
    def test_mhc_class_i(self, locus):
        a = HlaAllele(value=f"HLA-{locus}*01:01")
        assert a.mhc_class == 1

    @given(locus=st.sampled_from(["DRB1", "DPA1", "DPB1", "DQA1", "DQB1"]))
    def test_mhc_class_ii(self, locus):
        a = HlaAllele(value=f"HLA-{locus}*01:01")
        assert a.mhc_class == 2


class TestEscapeScoreProperties:
    @given(
        total=st.integers(min_value=1, max_value=100),
        escaped_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    def test_value_matches_counts(self, total, escaped_ratio):
        escaped = int(escaped_ratio * total)
        expected = escaped / total
        es = EscapeScore(
            value=expected,
            escaped_epitope_count=escaped,
            total_epitope_count=total,
        )
        assert es.value == pytest.approx(expected, abs=0.01)

    @given(
        total=st.integers(min_value=1, max_value=100),
        escaped_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    def test_tier_monotonic(self, total, escaped_ratio):
        escaped = int(escaped_ratio * total)
        ratio = escaped / total
        es = EscapeScore(
            value=ratio,
            escaped_epitope_count=escaped,
            total_epitope_count=total,
        )
        # Verify tier boundaries
        if ratio >= 0.6:
            assert es.tier == "critical"
        elif ratio >= 0.4:
            assert es.tier == "reformulate"
        elif ratio >= 0.2:
            assert es.tier == "alert"
        elif ratio >= 0.1:
            assert es.tier == "watch"
        else:
            assert es.tier == "none"


class TestMutationProperties:
    @given(
        pos=st.integers(min_value=1, max_value=10000),
        ref=st.sampled_from("ACDEFGHIKLMNPQRSTVWY"),
        alt=st.sampled_from("ACDEFGHIKLMNPQRSTVWY"),
    )
    def test_hgvs_notation(self, pos, ref, alt):
        assume(ref != alt)  # mutation must change something
        m = Mutation(position=pos, reference=ref, alternate=alt)
        assert m.hgvs_like == f"{ref}{pos}{alt}"
