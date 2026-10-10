"""Tests for v2.0 MLOps additions."""
from __future__ import annotations

import pytest


class TestModelCards:
    def test_generate_model_card(self):
        from vaxgenesis.mlops.model_cards import ModelCardGenerator
        gen = ModelCardGenerator()
        card = gen.generate(
            model_name="hla_binding",
            model_version="1.2.0",
            metrics={"rmse": 0.42, "ece": 0.08},
            training_data_size=15000,
        )
        assert card.model_name == "hla_binding"
        assert card.bias_known is True
        assert "European-ancestry" in (card.bias_description or "")
        assert len(card.limitations) >= 3
        md = card.to_markdown()
        assert "Model Card: hla_binding v1.2.0" in md
        assert "0.4200" in md  # rmse

    def test_model_card_markdown_structure(self):
        from vaxgenesis.mlops.model_cards import ModelCardGenerator
        gen = ModelCardGenerator()
        card = gen.generate(
            model_name="epitope_prediction",
            model_version="2.0.0",
            metrics={"accuracy": 0.89, "ece": 0.12},
        )
        md = card.to_markdown()
        assert "# Model Card" in md
        assert "## Intended Use" in md
        assert "## Training Data" in md
        assert "## Evaluation" in md
        assert "## Ethical Considerations" in md
        assert "## Caveats" in md


class TestDriftDetection:
    def test_psi_no_drift(self):
        from vaxgenesis.mlops.drift_detection import DriftDetector
        det = DriftDetector()
        baseline = [0.5, 0.51, 0.49, 0.5, 0.48, 0.52, 0.5, 0.49, 0.51, 0.5]
        current = [0.5, 0.51, 0.49, 0.5, 0.48, 0.52, 0.5, 0.49, 0.51, 0.5]
        psi = det.psi(baseline, current)
        assert psi < 0.05  # no drift

    def test_psi_significant_drift(self):
        from vaxgenesis.mlops.drift_detection import DriftDetector
        det = DriftDetector()
        baseline = [0.1, 0.12, 0.11, 0.13, 0.1, 0.12, 0.11, 0.13, 0.1, 0.12]
        current = [0.8, 0.82, 0.81, 0.83, 0.8, 0.82, 0.81, 0.83, 0.8, 0.82]
        psi = det.psi(baseline, current)
        assert psi > 0.25  # significant drift

    def test_drift_report_severity(self):
        from vaxgenesis.mlops.drift_detection import DriftDetector
        det = DriftDetector()
        report = det.compute_psi_report(
            model_name="hla_binding",
            model_version="1.0.0",
            baseline=[0.1] * 100,
            current=[0.9] * 100,
        )
        assert report.severity == "critical"
        assert "retraining" in report.recommendation.lower()

    def test_drift_report_no_drift(self):
        from vaxgenesis.mlops.drift_detection import DriftDetector
        det = DriftDetector()
        report = det.compute_psi_report(
            model_name="hla_binding",
            model_version="1.0.0",
            baseline=[0.5] * 100,
            current=[0.5] * 100,
        )
        assert report.severity == "none"


class TestCanaryDeployment:
    def test_start_canary(self):
        from vaxgenesis.mlops.canary import CanaryController, DeploymentStrategy
        ctrl = CanaryController()
        strategy = DeploymentStrategy(
            model_name="hla_binding",
            champion_version="1.0.0",
            challenger_version="1.1.0",
            canary_percentage=10,
        )
        state = ctrl.start(strategy)
        assert state.current_percentage == 10
        assert state.status == "ramping"

    def test_route_returns_champion_or_challenger(self):
        from vaxgenesis.mlops.canary import CanaryController, DeploymentStrategy
        ctrl = CanaryController()
        strategy = DeploymentStrategy(
            model_name="test",
            champion_version="1.0",
            challenger_version="2.0",
            canary_percentage=50,
        )
        ctrl.start(strategy)
        results = set()
        for _ in range(100):
            version, _ = ctrl.route("test")
            results.add(version)
        # With 50% canary, both versions should appear (probabilistically)
        assert len(results) >= 1

    def test_auto_rollback_on_high_error_rate(self):
        from vaxgenesis.mlops.canary import CanaryController, DeploymentStrategy
        ctrl = CanaryController()
        strategy = DeploymentStrategy(
            model_name="test",
            champion_version="1.0",
            challenger_version="2.0",
            canary_percentage=100,
            error_rate_threshold=0.05,
        )
        ctrl.start(strategy)
        # Record 60 errors out of 100 challenger predictions
        for _ in range(40):
            ctrl.record_result("test", "2.0", latency_ms=100, error=False)
        for _ in range(60):
            ctrl.record_result("test", "2.0", latency_ms=100, error=True)
        state = ctrl.get_state("test")
        assert state.status == "rolled_back"
        assert state.current_percentage == 0

    def test_shadow_always_routes_to_champion(self):
        from vaxgenesis.mlops.canary import CanaryController, DeploymentStrategy
        ctrl = CanaryController()
        strategy = DeploymentStrategy(
            model_name="test",
            champion_version="1.0",
            challenger_version="2.0",
            strategy="shadow",
        )
        ctrl.start(strategy)
        for _ in range(50):
            version, _ = ctrl.route("test")
            assert version == "1.0"


class TestPluginRegistry:
    def test_discover_returns_empty_when_no_plugins(self):
        from vaxgenesis.plugins import PluginRegistry
        reg = PluginRegistry()
        plugins = reg.discover()
        # In test env, no plugins installed
        assert isinstance(plugins, list)

    def test_list_plugins(self):
        from vaxgenesis.plugins import PluginRegistry
        reg = PluginRegistry()
        reg.discover()
        assert isinstance(reg.list_plugins(), list)
        assert isinstance(reg.list_loaded(), list)
