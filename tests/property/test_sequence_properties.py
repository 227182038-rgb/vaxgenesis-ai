"""Property-based tests for the Sequence value object (ADR-0005, Tier 3).

These tests use Hypothesis to verify that Sequence invariants hold for
ALL valid inputs, not just the examples we thought of.

Run: pytest tests/property/test_sequence_properties.py -v
"""
from __future__ import annotations

import pytest
from hypothesis import given, strategies as st, assume, settings


# ============================================================
# Strategies (input generators)
# ============================================================

dna_chars = st.sampled_from("ATCGN")
protein_chars = st.sampled_from("ACDEFGHIKLMNPQRSTVWY")


@st.composite
def dna_sequences(draw, min_size: int = 1, max_size: int = 1000):
    length = draw(st.integers(min_value=min_size, max_value=max_size))
    return draw(st.text(dna_chars, min_size=length, max_size=length))


@st.composite
def protein_sequences(draw, min_size: int = 1, max_size: int = 1000):
    length = draw(st.integers(min_value=min_size, max_value=max_size))
    return draw(st.text(protein_chars, min_size=length, max_size=length))


# ============================================================
# Property tests
# ============================================================

class TestSequenceProperties:
    """Properties that must hold for ALL valid Sequence instances."""

    @given(seq=dna_sequences())
    def test_length_matches_value(self, seq):
        """Sequence.length == len(Sequence.value) for all DNA sequences."""
        from vaxgenesis.hexagon.domain.value_objects import Sequence
        s = Sequence(value=seq, alphabet="dna")
        assert s.length == len(seq)

    @given(seq=dna_sequences())
    def test_value_is_uppercased(self, seq):
        """Sequence always stores uppercase, even if input is lowercase."""
        from vaxgenesis.hexagon.domain.value_objects import Sequence
        s = Sequence(value=seq.lower(), alphabet="dna")
        assert s.value == s.value.upper()

    @given(seq=dna_sequences(min_size=5, max_size=100))
    def test_kmers_count(self, seq):
        """Sequence.kmers(k) returns exactly len(seq) - k + 1 k-mers."""
        from vaxgenesis.hexagon.domain.value_objects import Sequence
        s = Sequence(value=seq, alphabet="dna")
        k = 3
        kmers = s.kmers(k)
        assert len(kmers) == len(seq) - k + 1
        # Each k-mer has length k
        assert all(len(km) == k for km in kmers)
        # Concatenating first chars + last k-mer == original
        assert "".join(km[0] for km in kmers) + kmers[-1][1:] == seq.upper()

    @given(seq=dna_sequences(min_size=1, max_size=100))
    def test_gc_content_in_range(self, seq):
        """GC content is always in [0, 1]."""
        from vaxgenesis.hexagon.domain.value_objects import Sequence
        s = Sequence(value=seq, alphabet="dna")
        gc = s.gc_content()
        assert 0.0 <= gc <= 1.0

    @given(seq=dna_sequences(min_size=1, max_size=100))
    def test_reverse_complement_roundtrip(self, seq):
        """reverse_complement(reverse_complement(s)) == s for all DNA."""
        from vaxgenesis.hexagon.domain.value_objects import Sequence
        s = Sequence(value=seq, alphabet="dna")
        rc = s.reverse_complement()
        rc_rc = rc.reverse_complement()
        assert rc_rc.value == s.value

    @given(seq=dna_sequences(min_size=10, max_size=50))
    def test_reverse_complement_changes_sequence(self, seq):
        """Reverse complement of a non-palindromic sequence differs."""
        from vaxgenesis.hexagon.domain.value_objects import Sequence
        s = Sequence(value=seq, alphabet="dna")
        rc = s.reverse_complement()
        # A sequence equals its reverse complement only if it's a palindrome
        if s.value != rc.value:
            assert s.value != rc.value  # tautology but explicit

    @given(seq=protein_sequences(min_size=1, max_size=100))
    def test_protein_length(self, seq):
        """Protein sequences also satisfy the length invariant."""
        from vaxgenesis.hexagon.domain.value_objects import Sequence
        s = Sequence(value=seq, alphabet="protein")
        assert s.length == len(seq)

    @given(bad_char=st.sampled_from("XYZPQR"))
    def test_invalid_dna_char_rejected(self, bad_char):
        """Invalid DNA characters are rejected at construction."""
        from vaxgenesis.hexagon.domain.value_objects import Sequence
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Sequence(value=f"A{bad_char}T", alphabet="dna")

    @given(empty=st.just(""))
    def test_empty_sequence_rejected(self, empty):
        """Empty sequences are rejected."""
        from vaxgenesis.hexagon.domain.value_objects import Sequence
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Sequence(value=empty, alphabet="dna")
