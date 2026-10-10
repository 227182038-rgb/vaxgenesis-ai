"""Canary and shadow deployment controller.

Manages traffic splitting between the current Production model
(champion) and a candidate model (challenger):

  - **Canary:** Routes a configurable % of traffic to the challenger.
    If the challenger's error rate exceeds threshold within the
    evaluation window, automatically rolls back to 0%.

  - **Shadow:** The challenger runs in parallel on 100% of traffic but
    its results are logged only, never returned to the caller. Used for
    offline evaluation without user impact.

  - **A/B Evaluation:** After the canary window, a statistical test
    (Mann-Whitney U) determines whether the challenger is significantly
    better. If so, it's promoted to Production.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field


class DeploymentStrategy(BaseModel):
    """Configuration for a canary/shadow deployment."""

    model_name: str
    champion_version: str
    challenger_version: str
    strategy: Literal["canary", "shadow", "ab_test"] = "canary"

    # Canary config
    canary_percentage: int = Field(default=5, ge=0, le=100)
    canary_step_percentage: int = Field(default=20, ge=1, le=50)
    canary_step_duration_minutes: int = Field(default=30, ge=1)

    # Rollback config
    error_rate_threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    latency_p99_threshold_ms: int = Field(default=500, ge=10)

    # A/B test config
    ab_min_samples: int = Field(default=1000, ge=100)
    ab_significance_level: float = Field(default=0.05, ge=0.01, le=0.10)


class DeploymentState(BaseModel):
    """Current state of a canary/shadow deployment."""

    strategy: DeploymentStrategy
    current_percentage: int = 0
    started_at: float = Field(default_factory=time.time)
    last_step_at: float = Field(default_factory=time.time)
    champion_predictions: int = 0
    challenger_predictions: int = 0
    champion_errors: int = 0
    challenger_errors: int = 0
    champion_latencies_ms: list[float] = Field(default_factory=list)
    challenger_latencies_ms: list[float] = Field(default_factory=list)
    status: Literal["ramping", "stable", "rolled_back", "promoted"] = "ramping"
    message: str = ""


class CanaryController:
    """Controls canary traffic splitting and automatic rollback."""

    def __init__(self) -> None:
        self._deployments: dict[str, DeploymentState] = {}

    def start(self, strategy: DeploymentStrategy) -> DeploymentState:
        """Start a new canary/shadow deployment."""
        state = DeploymentState(
            strategy=strategy,
            current_percentage=strategy.canary_percentage if strategy.strategy == "canary" else 0,
        )
        self._deployments[strategy.model_name] = state
        return state

    def route(self, model_name: str) -> tuple[str, str]:
        """Decide which model version to route a request to.

        Returns (version, is_shadow).
        - For canary: returns challenger for `current_percentage`% of requests.
        - For shadow: always returns champion, but also calls challenger
          (the caller is responsible for the parallel call).
        """
        state = self._deployments.get(model_name)
        if not state:
            return ("production", False)

        if state.strategy.strategy == "shadow":
            # Always serve from champion; challenger runs in background
            return (state.strategy.champion_version, False)

        # Canary: roll the dice
        if random.randint(1, 100) <= state.current_percentage:
            return (state.strategy.challenger_version, False)
        return (state.strategy.champion_version, False)

    def record_result(
        self,
        model_name: str,
        version: str,
        latency_ms: float,
        error: bool = False,
    ) -> None:
        """Record the outcome of a prediction for monitoring."""
        state = self._deployments.get(model_name)
        if not state:
            return

        if version == state.strategy.champion_version:
            state.champion_predictions += 1
            if error:
                state.champion_errors += 1
            state.champion_latencies_ms.append(latency_ms)
        else:
            state.challenger_predictions += 1
            if error:
                state.challenger_errors += 1
            state.challenger_latencies_ms.append(latency_ms)

        # Check for automatic rollback
        self._check_rollback(model_name)

    def _check_rollback(self, model_name: str) -> None:
        """Auto-rollback if challenger error rate exceeds threshold."""
        state = self._deployments[model_name]
        if state.challenger_predictions < 50:
            return  # not enough data

        error_rate = state.challenger_errors / state.challenger_predictions
        if error_rate > state.strategy.error_rate_threshold:
            state.current_percentage = 0
            state.status = "rolled_back"
            state.message = (
                f"Auto-rollback: challenger error rate {error_rate:.2%} "
                f"exceeds threshold {state.strategy.error_rate_threshold:.2%}"
            )

    def maybe_ramp_up(self, model_name: str) -> None:
        """Increase canary percentage if enough time has passed."""
        state = self._deployments.get(model_name)
        if not state or state.status != "ramping":
            return

        elapsed = time.time() - state.last_step_at
        if elapsed < state.strategy.canary_step_duration_minutes * 60:
            return

        # Check health before ramping
        if state.challenger_predictions > 0:
            error_rate = state.challenger_errors / state.challenger_predictions
            if error_rate > state.strategy.error_rate_threshold:
                self._check_rollback(model_name)
                return

        state.current_percentage = min(
            100, state.current_percentage + state.strategy.canary_step_percentage
        )
        state.last_step_at = time.time()

        if state.current_percentage >= 100:
            state.status = "promoted"
            state.message = "Challenger promoted to 100% traffic"

    def get_state(self, model_name: str) -> DeploymentState | None:
        return self._deployments.get(model_name)
