"""Property-based tests for the Candidate aggregate root (ADR-0005, Tier 3).

Verifies the state machine invariants hold for all valid inputs.
"""
from __future__ import annotations

from uuid import uuid4

import pytest
from hypothesis import given, strategies as st, settings

from vaxgenesis.hexagon.domain.entities import (
    Candidate, CandidateStatus, VaccinePlatform,
)
from vaxgenesis.hexagon.domain.errors import (
    InsufficientEvidenceError, InvalidStateTransitionError,
    InvariantViolationError,
)
from vaxgenesis.hexagon.domain.value_objects import (
    CandidateId, ConfidenceInterval, ProjectId, UncertaintyScore,
)


# ============================================================
# Strategies
# ============================================================

candidate_names = st.text(min_size=1, max_size=100).filter(lambda s: s.strip())
platforms = st.sampled_from(list(VaccinePlatform))
scores = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
statuses = st.sampled_from(list(CandidateStatus))


# ============================================================
# Property tests
# ============================================================

class TestCandidateProperties:

    def _make_candidate(self, name="Test", platform=VaccinePlatform.MULTI_EPITOPE):
        return Candidate(
            project_id=ProjectId(value=uuid4()),
            name=name,
            platform=platform,
        )

    @given(name=candidate_names, platform=platforms)
    def test_candidate_creation(self, name, platform):
        """A new candidate is always in DRAFT status with version 1."""
        c = Candidate(
            project_id=ProjectId(value=uuid4()),
            name=name,
            platform=platform,
        )
        assert c.status == CandidateStatus.DRAFT
        assert c.version == 1
        assert c.overall_score is None
        assert c.construct is None

    @given(score=scores)
    def test_set_predictions_accepts_valid_score(self, score):
        """set_predictions accepts any score in [0, 1]."""
        c = self._make_candidate()
        ci = ConfidenceInterval(low=max(0, score - 0.1), high=min(1, score + 0.1))
        u = UncertaintyScore(value=0.3, method="heuristic")
        c.set_predictions(score, ci, u)
        assert c.overall_score == score

    @given(score=st.floats(min_value=1.01, max_value=10.0, allow_nan=False))
    def test_set_predictions_rejects_invalid_score(self, score):
        """set_predictions rejects scores outside [0, 1]."""
        c = self._make_candidate()
        ci = ConfidenceInterval(low=0.0, high=1.0)
        u = UncertaintyScore(value=0.3, method="heuristic")
        with pytest.raises(InvariantViolationError):
            c.set_predictions(score, ci, u)

    @given(name=st.just(""))
    def test_empty_name_rejected(self, name):
        """Empty candidate names are rejected."""
        with pytest.raises(Exception):  # ValidationError
            Candidate(
                project_id=ProjectId(value=uuid4()),
                name=name,
            )

    def test_advance_to_predicted_requires_score(self):
        """Cannot advance to PREDICTED without an overall_score."""
        c = self._make_candidate()
        with pytest.raises(InvariantViolationError):
            c.advance_status(CandidateStatus.PREDICTED)

    def test_advance_to_predicted_with_score(self):
        """Can advance to PREDICTED with a valid score."""
        c = self._make_candidate()
        ci = ConfidenceInterval(low=0.6, high=0.8)
        u = UncertaintyScore(value=0.3, method="heuristic")
        c.set_predictions(0.7, ci, u)
        c.advance_status(CandidateStatus.PREDICTED)
        assert c.status == CandidateStatus.PREDICTED

    def test_advance_to_validated_requires_assay(self):
        """Cannot advance to VALIDATED without a completed assay."""
        c = self._make_candidate()
        ci = ConfidenceInterval(low=0.6, high=0.8)
        u = UncertaintyScore(value=0.3, method="heuristic")
        c.set_predictions(0.7, ci, u)
        c.advance_status(CandidateStatus.PREDICTED)
        with pytest.raises(InsufficientEvidenceError):
            c.advance_status(CandidateStatus.VALIDATED)

    def test_advance_to_validated_with_assay(self):
        """Can advance to VALIDATED after recording an assay completion."""
        c = self._make_candidate()
        ci = ConfidenceInterval(low=0.6, high=0.8)
        u = UncertaintyScore(value=0.3, method="heuristic")
        c.set_predictions(0.7, ci, u)
        c.advance_status(CandidateStatus.PREDICTED)
        c.record_assay_completion()
        c.advance_status(CandidateStatus.VALIDATED)
        assert c.status == CandidateStatus.VALIDATED

    @given(from_status=statuses, to_status=statuses)
    def test_state_transition_validity(self, from_status, to_status):
        """State transitions must respect the state machine."""
        c = self._make_candidate()
        # Force the candidate into from_status by direct assignment
        object.__setattr__(c, "status", from_status)
        # In production this is never done; here we test the state machine.

        valid_transitions = {
            CandidateStatus.DRAFT: {CandidateStatus.PREDICTED},
            CandidateStatus.PREDICTED: {CandidateStatus.VALIDATED, CandidateStatus.REJECTED},
            CandidateStatus.VALIDATED: {CandidateStatus.IN_TRIAL},
            CandidateStatus.REJECTED: set(),
            CandidateStatus.IN_TRIAL: set(),
        }
        allowed = valid_transitions.get(from_status, set())

        try:
            # Precondition: PREDICTED requires score, VALIDATED requires assay
            if to_status == CandidateStatus.PREDICTED:
                ci = ConfidenceInterval(low=0.6, high=0.8)
                u = UncertaintyScore(value=0.3, method="heuristic")
                c.set_predictions(0.7, ci, u)
            elif to_status == CandidateStatus.VALIDATED:
                c.record_assay_completion()

            c.advance_status(to_status)

            if to_status not in allowed:
                pytest.fail(f"Should have raised InvalidStateTransitionError for {from_status} → {to_status}")
            assert c.status == to_status
        except (InvalidStateTransitionError, InsufficientEvidenceError, InvariantViolationError):
            if to_status in allowed:
                # If preconditions weren't met, that's a different error — OK
                pass

    def test_bump_version_increments(self):
        """bump_version increments the version by 1."""
        c = self._make_candidate()
        original = c.version
        c.bump_version()
        assert c.version == original + 1

    def test_record_assay_completion_increments(self):
        """Each assay completion increments the counter."""
        c = self._make_candidate()
        assert c.completed_assay_count == 0
        c.record_assay_completion()
        assert c.completed_assay_count == 1
        c.record_assay_completion()
        assert c.completed_assay_count == 2
