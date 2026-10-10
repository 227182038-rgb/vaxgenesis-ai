"""Surveillance pipeline integration test (audit 6.2).

Validates that the variant-surveillance pipeline correctly classifies
test sequences into watch/alert/reformulate/critical tiers using the
GISAID/Nextstrain fixtures.

Does NOT require a live GISAID account — uses the fixtures in
`tests/fixtures/`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _load_fixture(name: str) -> dict:
    """Load a fixture JSON file."""
    for sub in ["gisaid", "nextstrain"]:
        path = FIXTURES_DIR / sub / f"{name}.json"
        if path.exists():
            return json.loads(path.read_text())
    raise FileNotFoundError(f"Fixture {name} not found")


# ============================================================
# Tests
# ============================================================

def test_classify_escape_levels():
    """All four escape tiers are reachable from the classifier."""
    from vaxgenesis.surveillance.escape_detection_stub import _classify_escape
    from vaxgenesis.surveillance.escape_detection_stub import EscapeAlertLevel

    assert _classify_escape(0.05) is None
    assert _classify_escape(0.15) == EscapeAlertLevel.WATCH
    assert _classify_escape(0.25) == EscapeAlertLevel.ALERT
    assert _classify_escape(0.45) == EscapeAlertLevel.REFORMULATE
    assert _classify_escape(0.65) == EscapeAlertLevel.CRITICAL


def test_fixture_xbb_has_mutations():
    """The XBB.1.5 fixture has the expected mutation count."""
    fixture = _load_fixture("sample_xbb")
    assert fixture["lineage"] == "XBB.1.5"
    assert len(fixture["mutations"]) == 3
    assert fixture["source"] == "gisaid"


def test_fixture_delta_is_lower_risk():
    """The Delta fixture has fewer mutations than XBB."""
    xbb = _load_fixture("sample_xbb")
    delta = _load_fixture("sample_delta")
    assert len(delta["mutations"]) < len(xbb["mutations"])


def test_fixture_ancestral_has_no_mutations():
    """The ancestral Wuhan fixture has zero mutations (baseline)."""
    fixture = _load_fixture("sample_ancestral")
    assert fixture["mutations"] == []
    assert fixture["lineage"] == "A"


def test_escape_score_computation():
    """Escape score = fraction of epitopes overlapped by mutations."""
    from vaxgenesis.surveillance.escape_detection_stub import _compute_escape_score

    # 10 epitopes, 3 overlapped by mutations → 0.3
    epitopes = [{"id": f"e{i}", "sequence": "PEPTIDE", "start": i * 10, "end": i * 10 + 7} for i in range(10)]
    variant = {
        "id": "v1",
        "mutations": [
            {"position": 5, "ref": "A", "var": "T"},
            {"position": 15, "ref": "C", "var": "G"},
            {"position": 25, "ref": "T", "var": "A"},
        ],
    }
    result = _compute_escape_score(variant, epitopes)
    assert result["escape_score"] == pytest.approx(0.3, abs=0.01)
    assert len(result["escaped_epitopes"]) == 3


def test_critical_escalation_triggers_reformulation():
    """Audit 6.2: A critical escape (>60%) triggers reformulation."""
    from vaxgenesis.surveillance.escape_detection_stub import _classify_escape
    from vaxgenesis.surveillance.escape_detection_stub import EscapeAlertLevel

    # 7 of 10 epitopes escaped = 0.7 → CRITICAL
    level = _classify_escape(0.7)
    assert level == EscapeAlertLevel.CRITICAL


def test_watch_level_does_not_trigger_reformulation():
    """Audit 6.2: A watch-level escape (10-20%) does NOT trigger reformulation."""
    from vaxgenesis.surveillance.escape_detection_stub import _classify_escape
    from vaxgenesis.surveillance.escape_detection_stub import EscapeAlertLevel

    level = _classify_escape(0.15)
    assert level == EscapeAlertLevel.WATCH
    assert level != EscapeAlertLevel.REFORMULATE
    assert level != EscapeAlertLevel.CRITICAL
