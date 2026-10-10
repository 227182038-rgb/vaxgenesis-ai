"""MLOps package — experiment tracking, feature store, model registry,
model cards, drift detection, canary/shadow deployment.

This module integrates the v1.x platform with a full MLOps stack:

  - MLflow Tracking: auto-logs every module execution as an MLflow run
  - MLflow Model Registry: stage transitions (Staging → Production → Archived)
  - Feast Feature Store: versioned HLA frequencies, epitope features
  - Model Cards: auto-generated from run metadata + metrics + dataset cards
  - Dataset Cards: auto-generated from dataset metadata + statistics
  - Drift Detection: KL-divergence + PSI monitors on prediction distributions
  - Data Quality: Great Expectations validation on every dataset load
  - Canary/Shadow Deployment: traffic splitting + parallel inference
  - A/B Evaluation: statistical comparison of model versions

See ADR-0006 for the architectural rationale.
"""
