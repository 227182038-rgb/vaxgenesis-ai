"""Escape detection stub (audit v1.1 test support).

In the deployed repository this lives at
`vaxgenesis/surveillance/escape_detection.py`. This stub provides
the classifier function and the EscapeAlertLevel enum so the
integration tests can run without the full module.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Any


class EscapeAlertLevel(StrEnum):
    WATCH = "watch"
    ALERT = "alert"
    REFORMULATE = "reformulate"
    CRITICAL = "critical"


ESCAPE_THRESHOLDS = {
    EscapeAlertLevel.WATCH: 0.10,
    EscapeAlertLevel.ALERT: 0.20,
    EscapeAlertLevel.REFORMULATE: 0.40,
    EscapeAlertLevel.CRITICAL: 0.60,
}


def _classify_escape(escape_score: float) -> EscapeAlertLevel | None:
    """Classify escape score into alert level."""
    if escape_score >= ESCAPE_THRESHOLDS[EscapeAlertLevel.CRITICAL]:
        return EscapeAlertLevel.CRITICAL
    if escape_score >= ESCAPE_THRESHOLDS[EscapeAlertLevel.REFORMULATE]:
        return EscapeAlertLevel.REFORMULATE
    if escape_score >= ESCAPE_THRESHOLDS[EscapeAlertLevel.ALERT]:
        return EscapeAlertLevel.ALERT
    if escape_score >= ESCAPE_THRESHOLDS[EscapeAlertLevel.WATCH]:
        return EscapeAlertLevel.WATCH
    return None


def _compute_escape_score(variant: dict[str, Any], epitopes: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute the fraction of epitopes overlapped by mutations."""
    if not epitopes:
        return {"escape_score": 0.0, "escaped_epitopes": []}

    mutated_positions = {m["position"] for m in (variant.get("mutations") or [])}
    escaped = []
    for epi in epitopes:
        epi_positions = set(range(epi["start"], epi["end"] + 1))
        if mutated_positions & epi_positions:
            escaped.append({
                "epitope_id": epi.get("id"),
                "sequence": epi.get("sequence"),
                "start": epi["start"],
                "end": epi["end"],
            })

    return {
        "escape_score": len(escaped) / len(epitopes),
        "escaped_epitopes": escaped,
    }
