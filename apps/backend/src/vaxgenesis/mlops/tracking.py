"""MLflow experiment tracking integration.

Auto-logs every `BaseModule.execute()` call as an MLflow run with:
  - Input parameters (the module's `inputs` dict)
  - Output metrics (uncertainty, execution time, key scores)
  - Artifacts (the full result JSON, stored in MinIO/S3)
  - Model version (champion model URI)
  - Tags (module_id, candidate_id, code_version)

Usage in BaseModule (v2.0 enhancement, non-breaking):

    from vaxgenesis.mlops.tracking import track_module_run

    class MyModule(BaseModule):
        @track_module_run
        async def run(self, inputs):
            ...

The decorator is a no-op if MLflow is unavailable, so v1.x modules
continue to work without modification.
"""
from __future__ import annotations

import functools
import time
from typing import Any, Callable

from vaxgenesis.core.logging import get_logger

logger = get_logger(__name__)

try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logger.info("mlops.mlflow_not_available")


# ============================================================
# Tracking decorator
# ============================================================

def track_module_run(fn: Callable) -> Callable:
    """Decorator that logs the module execution to MLflow.

    Non-breaking: if MLflow is not installed or the tracking URI is
    unreachable, the decorator becomes a no-op and the function runs
    normally.
    """

    @functools.wraps(fn)
    async def wrapper(self, inputs: dict[str, Any], *args, **kwargs):
        if not MLFLOW_AVAILABLE:
            return await fn(self, inputs, *args, **kwargs)

        module_id = getattr(self, "module_id", "unknown")
        candidate_id = str(getattr(self, "candidate_id", "unknown"))
        model_version = getattr(self, "default_model_version", "unknown")

        try:
            with mlflow.start_run(
                run_name=f"{module_id}_{int(time.time())}",
                tags={
                    "module_id": module_id,
                    "candidate_id": candidate_id,
                    "model_version": model_version,
                    "code_version": "2.0.0",
                },
            ) as run:
                # Log inputs as parameters
                _log_dict_as_params(inputs, prefix="input")

                # Execute the module
                result = await fn(self, inputs, *args, **kwargs)

                # Log outputs as metrics (scalars only) and artifacts (full)
                if hasattr(result, "outputs"):
                    _log_dict_as_metrics(result.outputs)
                    mlflow.log_dict(
                        {"outputs": result.outputs, "inputs": inputs},
                        artifact_file="result.json",
                    )
                if hasattr(result, "uncertainty_score") and result.uncertainty_score is not None:
                    mlflow.log_metric("uncertainty", result.uncertainty_score)
                if hasattr(result, "execution_time_seconds"):
                    mlflow.log_metric("execution_time_s", result.execution_time_seconds)

                # Attach the MLflow run ID to the result for provenance
                if hasattr(result, "model_uri"):
                    result.model_uri = f"mlflow://{run.info.run_id}"

                return result

        except Exception as exc:
            logger.warning(
                "mlops.tracking_failed",
                module=module_id,
                error=str(exc),
            )
            # Don't fail the module run if tracking fails
            return await fn(self, inputs, *args, **kwargs)

    return wrapper


# ============================================================
# Helpers
# ============================================================

def _log_dict_as_params(d: dict[str, Any], prefix: str = "") -> None:
    """Recursively log a dict as MLflow params (scalars only)."""
    if not MLFLOW_AVAILABLE:
        return
    for key, value in d.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, (str, int, float, bool)):
            mlflow.log_param(full_key[:250], value)  # MLflow param key limit
        elif isinstance(value, dict):
            _log_dict_as_params(value, prefix=full_key)
        elif isinstance(value, (list, tuple)) and len(value) <= 10:
            mlflow.log_param(full_key[:250], str(value)[:250])


def _log_dict_as_metrics(d: dict[str, Any], prefix: str = "") -> None:
    """Recursively log numeric values from a dict as MLflow metrics."""
    if not MLFLOW_AVAILABLE:
        return
    for key, value in d.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            try:
                mlflow.log_metric(full_key[:250], float(value))
            except (ValueError, OverflowError):
                pass
        elif isinstance(value, dict):
            _log_dict_as_metrics(value, prefix=full_key)


# ============================================================
# Model registry helpers
# ============================================================

class ModelRegistryClient:
    """Wraps MLflow Model Registry with VaxGenesis-specific conventions."""

    def __init__(self, tracking_uri: str | None = None) -> None:
        if not MLFLOW_AVAILABLE:
            raise RuntimeError("MLflow is not installed")
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)

    def register_model(
        self,
        run_id: str,
        name: str,
        tags: dict[str, str] | None = None,
    ) -> str:
        """Register a model version from an MLflow run.

        Returns the model version URI.
        """
        model_uri = f"runs:/{run_id}/model"
        mv = mlflow.register_model(model_uri=model_uri, name=name, tags=tags or {})
        return f"models:/{name}/{mv.version}"

    def transition_stage(
        self,
        name: str,
        version: int,
        stage: str,  # "Staging" | "Production" | "Archived"
    ) -> None:
        """Transition a model version to a new stage."""
        client = mlflow.tracking.MlflowClient()
        client.transition_model_version_stage(
            name=name, version=version, stage=stage,
        )

    def get_production_model(self, name: str) -> str | None:
        """Return the URI of the current Production model, or None."""
        client = mlflow.tracking.MlflowClient()
        versions = client.get_latest_versions(name, stages=["Production"])
        if not versions:
            return None
        return f"models:/{name}/{versions[0].version}"
