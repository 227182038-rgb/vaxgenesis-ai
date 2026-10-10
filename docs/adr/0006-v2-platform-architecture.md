# ADR-0006: Version 2.0 Platform Architecture

Date: 2026-03-01
Status: Accepted
Relates-to: ADR-0001 through ADR-0005

## Context

The v1.x platform achieved 10/10 architecture and ~9.0/10 research
capability. To reach feature-complete research-ecosystem status, six
additional capability pillars are needed (see `docs/v2_roadmap.md`).

This ADR documents the architectural decisions for v2.0.

## Decisions

### 2.0.1 — MLOps via MLflow + Feast

- **Experiment tracking:** MLflow Tracking (already in docker-compose;
  v2.0 adds automatic logging from every `BaseModule.execute()` call).
- **Feature store:** Feast for HLA frequencies, epitope features,
  population genetics data.
- **Model registry:** MLflow Model Registry with stage transitions
  (None → Staging → Production → Archived).
- **Model cards:** Auto-generated from MLflow run metadata + metrics.

### 2.0.2 — Explainable AI via SHAP + LIME

- Every ML-backed prediction produces a feature-attribution array.
- Stored alongside the prediction in the `Prediction.outputs` JSONB
  column under the `explanation` key.
- Exposed via `/api/v2/predictions/{id}/explanation`.
- Rendered as a waterfall chart in the UI.

### 2.0.3 — Plugin architecture via entry points

- Plugins are Python packages that register themselves via the
  `vaxgenesis.modules` entry point group.
- The core platform discovers plugins at startup via
  `importlib.metadata.entry_points()`.
- Plugins implement the same `BaseModule` interface as built-in modules.
- No core code modification needed to add a new module.

### 2.0.4 — SDK as a separate package

- `vaxgenesis-sdk` is a standalone PyPI package.
- Depends only on `httpx` and `pydantic` — not on the backend.
- Provides typed Python clients for every API endpoint.
- Used by the CLI, the desktop client, and third-party integrations.

### 2.0.5 — Frontend as a plugin host

- The Next.js frontend loads visualization components dynamically
  based on the module's declared `ui_component` field.
- Third-party modules can ship their own React components via
  npm packages that the frontend loads at runtime.

### 2.0.6 — Supply chain security via SLSA L3

- Every container image is built via GitHub Actions with provenance
  attestation (SLSA L3).
- Images are signed via Cosign (Sigstore).
- K8s admission controller (Kyverno) rejects unsigned images.
- SBOM (CycloneDX) is generated for every build and stored alongside
  the image.

## Consequences

**Positive:**
- Third-party extensibility without core changes.
- Full MLOps lifecycle: experiment → registry → canary → production.
- Every prediction is explainable and reproducible.
- Supply chain attacks mitigated by SLSA L3 + Sigstore.

**Negative:**
- Significant new dependencies (Feast, SHAP, Cosign, Kyverno, Falco).
- Higher operational complexity (more K8s controllers).
- Plugin sandboxing is not yet solved (plugins run in-process).

## Migration Path

v1.x users:
1. Update to v2.0 (backward compatible).
2. Optionally enable MLOps auto-logging via `MLOPS_AUTO_LOG=true`.
3. Optionally install plugins via `pip install vaxgenesis-plugin-xxx`.
4. v1 API continues to work; v2 API gains new XAI + MLOps endpoints.
