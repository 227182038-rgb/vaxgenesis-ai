# VaxGenesis AI — Version 2.0 Roadmap

**Status:** Accepted
**Date:** 2026-03-01
**Author:** VaxGenesis AI Architecture Board
**Supersedes:** v1.x ad-hoc feature additions

## Vision

Transform VaxGenesis AI from a high-quality pipeline platform (v1.x,
~9.5/10 architecture, ~9.0/10 research capability) into a complete
research ecosystem that can compete with leading computational biology
platforms and support real pharmaceutical R&D workflows.

## The 6 Pillars

### Pillar 1 — Advanced MLOps & Experiment Management

**Goal:** Make every prediction reproducible, every model versioned,
every dataset tracked, and every deployment safe.

| Capability | Status (v1.x) | v2.0 Target |
|-----------|---------------|-------------|
| MLflow experiment tracking | Config in docker-compose | Full integration: every module run logs to MLflow |
| Feature Store | Missing | Feast-backed feature store for HLA frequencies, epitope features |
| Model Registry | Stub (ModelVersion table) | Full MLflow Model Registry with stage transitions |
| Model Cards | Missing | Auto-generated per model version |
| Dataset Cards | Missing | Auto-generated per dataset version |
| Drift Detection | Bayesian updater only | Dedicated drift monitor with alerting |
| Data Quality Monitoring | Missing | Great Expectations integration |
| Automatic Rollback | Missing | Champion-challenger with auto-rollback on SLO breach |
| Canary Deployment | Missing | 5% → 25% → 100% traffic splitting |
| Shadow Deployment | Missing | New models run in parallel, no traffic |
| A/B Evaluation | Missing | Statistical comparison of model versions |

**Files:** `apps/backend/src/vaxgenesis/mlops/`

### Pillar 2 — Explainable AI & Scientific Provenance

**Goal:** Every prediction comes with a human-readable explanation
of *why* the model produced it, what features drove the score, and
what the confidence interval means.

| Capability | v2.0 Target |
|-----------|-------------|
| Per-prediction feature attribution | SHAP / LIME for every ML model |
| Confidence explanations | Natural-language: "Score 0.82 ± 0.10 because..." |
| Lineage tracking | Full DAG: dataset → feature → model → prediction → decision |
| Experiment reproducibility | One-click "reproduce this result" with pinned versions |
| Dataset versioning | DVC-style content-addressed dataset versions |
| Automated literature evidence scoring | RAG over PubMed with confidence-weighted citations |

**Files:** `apps/backend/src/vaxgenesis/xai/`

### Pillar 3 — Scientific Visualization & Collaboration

**Goal:** Researchers can explore results interactively, collaborate
with peers, and integrate with their existing lab tools.

| Capability | v2.0 Target |
|-----------|-------------|
| 3D molecular viewer | Three.js + NGL Viewer integration |
| Interactive pathway explorer | React Flow + pathway data |
| Variant browser | Nextstrain-style phylogenetic tree |
| Genome browser | JBrowse2 embedding |
| Explainable epitope viewer | Per-epitope SHAP waterfall |
| Immune response timeline | Simulation time-series charts |
| AI scientific copilot | In-UI chat with the agent orchestrator |
| Organization workspaces | Multi-tenant project isolation |
| Team permissions | Role-based + resource-based ACLs |
| Comments & review workflow | Threaded annotations on candidates |
| Experiment approval | PI sign-off workflow |
| ELN integration | Benchling / LabArchives API |
| Audit timeline | Visual activity feed |
| Activity feed | Real-time WebSocket updates |

**Files:** `apps/frontend/src/components/visualization/`, `collaboration/`

### Pillar 4 — Enterprise Security & Governance

**Goal:** Meet pharmaceutical R&D security requirements for
deploying into GxP-regulated environments.

| Capability | v2.0 Target |
|-----------|-------------|
| SBOM generation | CycloneDX / SPDX on every build |
| Sigstore / Cosign signing | Every container image signed |
| SLSA Level 3 compliance | Provenance attestation for all artifacts |
| OPA / Gatekeeper policies | Admission control for K8s |
| Vault integration | HashiCorp Vault for secrets |
| Secret rotation | Automated via Vault + ExternalSecrets |
| mTLS service mesh | Istio STRICT (already in v1.1) |
| Runtime security | Falco daemonset for syscall monitoring |
| Admission controllers | Kyverno / Gatekeeper for image signing |
| Multi-tenancy | Namespace isolation + network policies |

**Files:** `infra/opa/`, `infra/vault/`, `infra/falco/`, `infra/sbom/`

### Pillar 5 — Regulatory & Reproducibility Tooling

**Goal:** Generate regulatory submission-ready documentation
automatically from the platform's audit trail.

| Capability | v2.0 Target |
|-----------|-------------|
| Regulatory readiness reports | FDA SaMD / ICH M11 / 21 CFR Part 11 compliant |
| Reproducible experiment snapshots | Full environment + data + code pinning |
| Audit timeline | Immutable, hash-chained, SIEM-exported |
| Disaster recovery | Cross-region RDS replica + S3 replication |
| Backup/restore | Automated daily + on-demand |
| High availability validation | Multi-AZ failover tested quarterly |

**Files:** `apps/backend/src/vaxgenesis/regulatory/`

### Pillar 6 — Plugin / SDK Architecture

**Goal:** Third-party labs can add new computational biology modules
without modifying the core platform.

| Capability | v2.0 Target |
|-----------|-------------|
| Plugin marketplace | Registry of community modules |
| Public SDK | `vaxgenesis-sdk` Python package |
| CLI | `vaxgenesis` command-line tool |
| Desktop client | Electron wrapper for offline use |
| Offline mode | Local-first sync with conflict resolution |
| Public API | Stable, versioned, OpenAPI-documented |

**Files:** `sdk/`, `cli/`, `desktop/`, `apps/backend/src/vaxgenesis/plugins/`

## Implementation Priority

| Phase | Pillars | Duration | Deliverable |
|-------|---------|----------|-------------|
| Phase 1 (Q1 2026) | 1, 2 | 3 months | MLOps + XAI foundation |
| Phase 2 (Q2 2026) | 3, 6 | 3 months | Visualization + Plugin SDK |
| Phase 3 (Q3 2026) | 4, 5 | 3 months | Enterprise + Regulatory |
| Phase 4 (Q4 2026) | All | 3 months | Integration + GA |

## Success Metrics

- **MLOps:** 100% of model deployments go through canary; zero untracked
  predictions in production.
- **XAI:** Every prediction has a feature-attribution report accessible
  via API and UI within 1 second.
- **Visualization:** 3D viewer loads any PDB structure in <3 seconds.
- **Security:** All container images signed; SBOM available for every
  release; zero unscanned images admitted to K8s.
- **Regulatory:** Auto-generated ICH M11 submission package passes
  validation on first attempt.
- **Plugin SDK:** Third-party module can be installed, configured, and
  invoked via CLI in <5 minutes.

## Backward Compatibility

v2.0 is fully backward compatible with v1.x:
- All v1 API endpoints continue to work.
- All v1 database schemas are unchanged.
- All v1 modules continue to function.
- New capabilities are opt-in via feature flags.
