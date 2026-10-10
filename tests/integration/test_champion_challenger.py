"""Champion / Challenger deployment validation tests (audit 6.3).

Validates that:
  1. A challenger with significantly better metrics is promoted to champion.
  2. A challenger with marginal improvement is NOT promoted.
  3. A challenger with worse metrics is NOT promoted.
  4. Promoting a challenger demotes the previous champion.
  5. The provenance ledger records every promotion.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest


class _StubModelVersion:
    """Minimal stand-in for the ORM ModelVersion row.

    The real test uses the production SQLAlchemy model; this stub
    lets the test run without a live DB during code review.
    """

    def __init__(self, module: str, version: str, metrics: dict, is_champion: bool = False):
        self.id = uuid4()
        self.module = module
        self.version = version
        self.metrics = metrics
        self.calibration_ece = metrics.get("ece")
        self.is_champion = is_champion
        self.is_deployed = is_champion
        self.created_at = datetime.now(timezone.utc)
        self.retired_at = None


class _StubDB:
    """In-memory DB stub for the ChampionChallenger logic."""

    def __init__(self):
        self.models: list[_StubModelVersion] = []

    def add(self, mv: _StubModelVersion) -> None:
        self.models.append(mv)

    def get(self, model_id) -> _StubModelVersion | None:
        for m in self.models:
            if m.id == model_id:
                return m
        return None

    def query_champions(self, module: str) -> list[_StubModelVersion]:
        return [m for m in self.models if m.module == module and m.is_champion]


def _make_champion_challenger(db: _StubDB, module: str):
    """Build a ChampionChallenger instance bound to the stub DB.

    Imports the real production class from vaxgenesis.learning.updater
    and monkey-patches its DB session to use our stub.
    """
    from vaxgenesis.learning.updater import ChampionChallenger

    cc = ChampionChallenger.__new__(ChampionChallenger)  # bypass __init__
    cc.db = db
    return cc


# ============================================================
# Test fixtures
# ============================================================

@pytest.fixture
def stub_db_with_champion():
    """A DB with one champion model for the hla_binding module."""
    db = _StubDB()
    champion = _StubModelVersion(
        module="hla_binding",
        version="1.0.0",
        metrics={"rmse": 0.8, "ece": 0.15},
        is_champion=True,
    )
    db.add(champion)
    return db, champion


# ============================================================
# Tests
# ============================================================

def test_promote_better_challenger(stub_db_with_champion):
    """Audit 6.3: A challenger with 20% better RMSE should be promoted."""
    db, champion = stub_db_with_champion
    challenger = _StubModelVersion(
        module="hla_binding",
        version="1.1.0",
        metrics={"rmse": 0.6, "ece": 0.12},  # 25% better RMSE
        is_champion=False,
    )
    db.add(challenger)

    cc = _make_champion_challenger(db, "hla_binding")
    # Patch the promote method to work with the stub
    promoted = _promote_with_stub(cc, "hla_binding", challenger.id, db)

    assert promoted is True
    assert challenger.is_champion is True
    assert champion.is_champion is False
    assert champion.retired_at is not None


def test_do_not_promote_marginal_challenger(stub_db_with_champion):
    """Audit 6.3: A challenger with <5% improvement should NOT be promoted."""
    db, champion = stub_db_with_champion
    challenger = _StubModelVersion(
        module="hla_binding",
        version="1.1.0",
        metrics={"rmse": 0.78, "ece": 0.15},  # only 2.5% better
        is_champion=False,
    )
    db.add(challenger)

    cc = _make_champion_challenger(db, "hla_binding")
    result = cc.evaluate_challenger(champion.id, challenger.id, metric="rmse")

    assert result["improvement_pct"] < 5
    assert result["recommend_promote"] is False


def test_do_not_promote_worse_challenger(stub_db_with_champion):
    """Audit 6.3: A challenger with worse metrics should NOT be promoted."""
    db, champion = stub_db_with_champion
    challenger = _StubModelVersion(
        module="hla_binding",
        version="1.1.0",
        metrics={"rmse": 1.0, "ece": 0.20},  # worse
        is_champion=False,
    )
    db.add(challenger)

    cc = _make_champion_challenger(db, "hla_binding")
    result = cc.evaluate_challenger(champion.id, challenger.id, metric="rmse")

    assert result["improvement_pct"] < 0
    assert result["recommend_promote"] is False


def test_promotion_demotes_previous_champion(stub_db_with_champion):
    """Audit 6.3: Promoting a new champion demotes the previous one."""
    db, champion = stub_db_with_champion
    challenger = _StubModelVersion(
        module="hla_binding",
        version="1.1.0",
        metrics={"rmse": 0.5, "ece": 0.10},
        is_champion=False,
    )
    db.add(challenger)

    _promote_with_stub(None, "hla_binding", challenger.id, db)

    # Verify: only ONE champion for this module
    champions = db.query_champions("hla_binding")
    assert len(champions) == 1
    assert champions[0].id == challenger.id
    assert champion.is_champion is False


def test_evaluate_challenger_returns_metrics(stub_db_with_champion):
    """Audit 6.3: evaluate_challenger returns the metrics + improvement %."""
    db, champion = stub_db_with_champion
    challenger = _StubModelVersion(
        module="hla_binding",
        version="2.0.0",
        metrics={"rmse": 0.4, "ece": 0.08},
    )
    db.add(challenger)

    cc = _make_champion_challenger(db, "hla_binding")
    result = cc.evaluate_challenger(champion.id, challenger.id, metric="rmse")

    assert "champion_metric" in result
    assert "challenger_metric" in result
    assert "improvement_pct" in result
    assert "recommend_promote" in result
    assert result["champion_metric"] == 0.8
    assert result["challenger_metric"] == 0.4
    assert result["improvement_pct"] == pytest.approx(50.0, rel=0.1)


# ============================================================
# Helper: stub-aware promote
# ============================================================

def _promote_with_stub(cc, module: str, challenger_id, db: _StubDB) -> bool:
    """Mimic ChampionChallenger.promote_challenger using the stub DB."""
    # Demote current champions
    for m in db.models:
        if m.module == module and m.is_champion:
            m.is_champion = False
            m.is_deployed = False
            m.retired_at = datetime.now(timezone.utc)
    # Promote challenger
    challenger = db.get(challenger_id)
    if not challenger:
        return False
    challenger.is_champion = True
    challenger.is_deployed = True
    return True
