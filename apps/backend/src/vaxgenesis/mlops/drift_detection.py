"""Drift detection — monitors prediction distributions for data/serving drift.

Implements two complementary drift metrics:
  - **PSI (Population Stability Index):** bin-based, good for tabular features
  - **KL Divergence:** distribution-based, good for continuous scores

A dedicated Celery beat task runs every 6 hours, fetches the last 1000
predictions for each deployed model, compares against the training-set
baseline, and emits a `DriftDetected` alert if the metric exceeds threshold.

Thresholds (industry-standard):
  - PSI < 0.1: no drift
  - 0.1 <= PSI < 0.25: moderate drift (warning)
  - PSI >= 0.25: significant drift (critical — trigger retraining)
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field


class DriftReport(BaseModel):
    """A drift detection report for a single model."""

    model_name: str
    model_version: str
    metric: Literal["psi", "kl_divergence"]
    value: float
    threshold_warning: float = 0.10
    threshold_critical: float = 0.25
    severity: Literal["none", "warning", "critical"] = "none"
    window_size: int
    baseline_size: int
    recommendation: str = ""

    def compute_severity(self) -> None:
        if self.value >= self.threshold_critical:
            self.severity = "critical"
            self.recommendation = (
                f"Significant drift detected (PSI={self.value:.4f} >= {self.threshold_critical}). "
                "Trigger full model retraining immediately."
            )
        elif self.value >= self.threshold_warning:
            self.severity = "warning"
            self.recommendation = (
                f"Moderate drift detected (PSI={self.value:.4f}). "
                "Schedule incremental retraining within 7 days."
            )
        else:
            self.severity = "none"
            self.recommendation = "No significant drift detected. Continue monitoring."


class DriftDetector:
    """Computes PSI and KL divergence between baseline and current distributions."""

    @staticmethod
    def psi(baseline: Sequence[float], current: Sequence[float], n_bins: int = 10) -> float:
        """Population Stability Index.

        Args:
            baseline: training-set distribution of the score
            current: recent production distribution of the score
            n_bins: number of bins for histogram comparison

        Returns:
            PSI value. <0.1 = stable, 0.1-0.25 = moderate, >0.25 = significant.
        """
        if not baseline or not current:
            return 0.0

        # Use baseline to define bin edges
        lo = min(min(baseline), min(current))
        hi = max(max(baseline), max(current))
        if hi == lo:
            return 0.0  # no variation

        bin_edges = [lo + i * (hi - lo) / n_bins for i in range(n_bins + 1)]

        # Count baseline and current in each bin
        baseline_counts = _histogram(baseline, bin_edges)
        current_counts = _histogram(current, bin_edges)

        # Convert to proportions with smoothing
        baseline_pct = [(c + 0.5) / (len(baseline) + 0.5 * n_bins) for c in baseline_counts]
        current_pct = [(c + 0.5) / (len(current) + 0.5 * n_bins) for c in current_counts]

        # PSI = sum((current - baseline) * ln(current / baseline))
        psi_value = 0.0
        for b, c in zip(baseline_pct, current_pct):
            if b > 0 and c > 0:
                psi_value += (c - b) * math.log(c / b)

        return psi_value

    @staticmethod
    def kl_divergence(baseline: Sequence[float], current: Sequence[float], n_bins: int = 10) -> float:
        """KL divergence D(current || baseline)."""
        if not baseline or not current:
            return 0.0

        lo = min(min(baseline), min(current))
        hi = max(max(baseline), max(current))
        if hi == lo:
            return 0.0

        bin_edges = [lo + i * (hi - lo) / n_bins for i in range(n_bins + 1)]
        baseline_counts = _histogram(baseline, bin_edges)
        current_counts = _histogram(current, bin_edges)

        # Smooth to avoid log(0)
        baseline_pct = [(c + 0.5) / (len(baseline) + 0.5 * n_bins) for c in baseline_counts]
        current_pct = [(c + 0.5) / (len(current) + 0.5 * n_bins) for c in current_counts]

        kl = 0.0
        for p, q in zip(current_pct, baseline_pct):
            if p > 0 and q > 0:
                kl += p * math.log(p / q)
        return kl

    def compute_psi_report(
        self,
        model_name: str,
        model_version: str,
        baseline: Sequence[float],
        current: Sequence[float],
    ) -> DriftReport:
        report = DriftReport(
            model_name=model_name,
            model_version=model_version,
            metric="psi",
            value=self.psi(baseline, current),
            window_size=len(current),
            baseline_size=len(baseline),
        )
        report.compute_severity()
        return report


def _histogram(values: Sequence[float], edges: Sequence[float]) -> list[int]:
    """Count values in bins defined by edges."""
    counts = [0] * (len(edges) - 1)
    for v in values:
        for i in range(len(edges) - 1):
            if edges[i] <= v < edges[i + 1]:
                counts[i] += 1
                break
        else:
            # v >= last edge → put in last bin
            if v >= edges[-1]:
                counts[-1] += 1
    return counts
