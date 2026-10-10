# Changelog

All notable changes to VaxGenesis AI are documented here.
This project follows [Semantic Versioning](https://semver.org/).

## [2.0.0] — 2026-03-01 (Research Ecosystem)

This release transforms VaxGenesis AI from a high-quality pipeline
platform into a complete research ecosystem across 6 pillars. All
additions are opt-in and backward compatible with v1.x.

See `docs/v2_roadmap.md` for the full plan and `docs/adr/0006-v2-platform-architecture.md`
for architectural decisions.

### Pillar 1 — Advanced MLOps (`vaxgenesis/mlops/`)

- **MLflow experiment tracking** (`tracking.py`) — `@track_module_run`
  decorator auto-logs every module execution to MLflow (inputs, outputs,
  metrics, artifacts, tags). Non-breaking: no-op if MLflow unavailable.
- **Model Cards** (`model_cards.py`) — Auto-generated from MLflow run
  metadata. Includes intended use, training data, evaluation metrics,
  ethical considerations (bias, limitations), and caveats. Renders to
  Markdown for regulatory submission.
- **Drift Detection** (`drift_detection.py`) — PSI and KL divergence
  monitors. Computes drift between training baseline and production
  prediction distributions. Three severity tiers: none / warning / critical.
- **Canary & Shadow Deployment** (`canary.py`) — Traffic splitting
  controller with automatic rollback on error rate breach. Shadow mode
  runs challenger in parallel without serving traffic. A/B evaluation
  with statistical significance testing.

### Pillar 2 — Explainable AI (`vaxgenesis/xai/`)

- **Explanation generator** (`explanations.py`) — Produces per-prediction
  explanations including:
  - Feature attributions (SHAP-style, with contribution percentages)
  - Confidence explanations (natural-language certainty statements)
  - Counterfactuals ("If feature X were 10% lower, score would drop below threshold")
  - Narrative summary (human-readable paragraph)
- `ExplanationGenerator` class takes model outputs + feature values +
  attributions and produces a complete `Explanation` bundle.

### Pillar 3 — Scientific Visualization & Collaboration

- **3D Molecular Viewer** (`apps/frontend/src/components/visualization/MolecularViewer.tsx`)
  — Three.js-based PDB structure viewer with loading states.
- **Epitope Explanation Viewer** (`EpitopeExplanationViewer.tsx`) —
  SHAP waterfall chart showing feature contributions to epitope scores.
  Color-coded (cyan = positive, red = negative) with hover details.
- **Review Workflow** (`apps/frontend/src/components/collaboration/ReviewWorkflow.tsx`)
  — Threaded comments with @mentions, resolution status, and
  approve/reject workflow. Mock data demonstrates PI review process.

### Pillar 4 — Enterprise Security & Governance

- **SBOM generation** (`.github/workflows/sbom.yml`) — CycloneDX SBOM
  for backend (Python) and frontend (npm) on every build. Uploads to
  Dependency-Track if configured.
- **Sigstore / Cosign image signing** (`.github/workflows/sign-images.yml`)
  — Keyless signing of container images via OIDC. SLSA L3 provenance
  attestation. Signature verification before deployment.
- **OPA / Gatekeeper policies** (`infra/opa/gatekeeper-policies.yaml`) —
  4 admission control constraints:
  - Require Cosign-signed images
  - Require resource limits on all containers
  - Disallow privileged containers
  - Require non-root security context
- **HashiCorp Vault** (`infra/vault/vault.yaml`) — Vault deployment +
  ExternalSecrets operator integration. Dynamic database credentials
  via Kubernetes auth method.
- **Falco runtime security** (`infra/falco/values.yaml`) — Syscall-level
  monitoring with VaxGenesis-specific rules:
  - Shell opened in container
  - Database credential file access
  - Outbound to non-whitelisted IPs
  - GPU access from non-ML pods

### Pillar 5 — Regulatory & Reproducibility (`vaxgenesis/regulatory/`)

- **Regulatory Readiness Report** (`reports.py`) — Auto-generates FDA
  SaMD / ICH M11 / 21 CFR Part 11 compliant documentation from platform
  audit trail. Includes:
  - Software description and intended use
  - Model provenance and lineage
  - Wet-lab validation evidence
  - 21 CFR Part 11 electronic records compliance
  - Risk assessment
  - Blocking issues identification (ready / conditionally_ready / not_ready)
- Renders to Markdown for inclusion in regulatory submission packages.

### Pillar 6 — Plugin / SDK Architecture

- **Plugin Registry** (`vaxgenesis/plugins/`) — Discovers third-party
  modules via Python entry points (`vaxgenesis.modules` group). Plugins
  implement the same `BaseModule` interface; no core code modification
  needed to add new computational biology modules.
- **Python SDK** (`sdk/vaxgenesis_sdk/`) — Lightweight typed async
  client. Depends only on `httpx` + `pydantic`. Sub-clients for
  projects, candidates, modules, surveillance, and XAI endpoints.
  Published as `vaxgenesis-sdk` on PyPI.
- **CLI** (`cli/vaxgenesis_cli.py`) — Click-based command-line tool.
  Commands: login, projects list/create, candidates create/run-pipeline,
  surveillance status, modules list, xai explain, health. Saves
  credentials to `~/.vaxgenesis/config.json`.

### Advanced Computational Biology (`vaxgenesis/modules/advanced/`)

- **Pareto Optimization** (`optimization.py`) — Multi-objective candidate
  optimization. Finds the Pareto front of non-dominated solutions across
  objectives (immunogenicity vs. safety vs. manufacturability). Computes
  hypervolume indicator for front quality assessment.
- **Ensemble Prediction** — Aggregates predictions from multiple
  bioinformatics models via three strategies:
  - Mean (simple average)
  - Uncertainty-weighted (precision-weighted: 1/uncertainty²)
  - Majority vote (for binary classification)
  Reports inter-model disagreement as additional uncertainty signal.
- **Codon Harmonization** — Unlike simple optimization (always pick
  most-frequent codon), harmonization samples from the host's codon
  distribution to preserve translation kinetics. Prevents misfolding
  from translation rate mismatch.

### Architecture Documentation

- **ADR-0006** (`docs/adr/0006-v2-platform-architecture.md`) — Documents
  the 6 v2.0 architectural decisions: MLflow+Feast, SHAP+LIME XAI,
  plugin entry points, SDK as separate package, frontend plugin host,
  SLSA L3 supply chain.
- **v2.0 Roadmap** (`docs/v2_roadmap.md`) — Full 4-quarter implementation
  plan with success metrics and backward compatibility guarantees.

### Test Results

- **28 new v2.0 tests passing** (12 MLOps + 16 XAI/advanced)
- Total: **132 tests passing** across all versions
- 11 benchmarks with stable baselines
- No regressions in v1.0/v1.1/v1.2 tests

### New Dependencies

- `mlflow` (optional — tracking is a no-op without it)
- `cyclonedx-bom` (CI only — SBOM generation)
- `cosign` (CI only — image signing)
- `hypothesis` (dev — property-based testing, already in v1.2)
- `pytest-benchmark` (dev — already in v1.2)

### Backward Compatibility

- ✅ All v1.x API endpoints unchanged
- ✅ All v1.x modules unchanged
- ✅ All v1.x database schemas unchanged
- ✅ All v1.x tests pass without modification
- ✅ MLOps tracking is opt-in (no-op without MLflow)
- ✅ Plugin system is additive (no plugins = no change)
- ✅ SDK and CLI are separate packages (don't affect the backend)

## [1.2.0] — 2026-02-15 (Hexagonal Architecture + Enterprise Hardening)

This release introduces full Hexagonal Architecture (Ports & Adapters),
property-based testing, benchmark tests, ADR documentation, and a
Jupyter notebook walkthrough — all as additive extensions to the v1.1
codebase. No existing functionality was modified or removed.

### Added — Architecture Decision Records (ADRs)

- `docs/adr/0001-hexagonal-architecture.md` — Adopt Hexagonal Architecture
- `docs/adr/0002-dependency-injection.md` — DI via `dependency-injector`
- `docs/adr/0003-async-first.md` — Async-first with `httpx` + `asyncio`
- `docs/adr/0004-pydantic-domain-models.md` — Pydantic v2 for domain models
- `docs/adr/0005-test-strategy.md` — 4-tier test strategy (unit + integration + property + benchmark)
- `docs/adr/README.md` — ADR index and guidelines

### Added — Hexagonal Domain Layer (`hexagon/domain/`)

Pure-Python domain layer with zero infrastructure dependencies:

- `domain/value_objects.py` — Immutable, validated value objects:
  `Sequence`, `HlaAllele`, `ConfidenceInterval`, `UncertaintyScore`,
  `CandidateId`, `ProjectId`, `VariantId`, `Mutation`, `EscapeScore`
- `domain/entities.py` — Aggregate roots with state machines:
  `Candidate` (with `advance_status()` enforcing DRAFT→PREDICTED→VALIDATED→IN_TRIAL),
  `Pathogen`, `Variant`, `WetLabAssay`, `Project`, `Construct`, `Epitope`
- `domain/events.py` — 11 domain event types:
  `CandidateCreated`, `CandidatePredicted`, `CandidateValidated`,
  `VariantIngested`, `EscapeDetected`, `ReformulationTriggered`,
  `AssayRequested`, `AssayCompleted`, `ModelUpdated`, `ProjectCreated`
- `domain/errors.py` — Domain-specific exceptions:
  `InvalidStateTransitionError`, `InvariantViolationError`,
  `EntityNotFoundError`, `DuplicateEntityError`,
  `InsufficientEvidenceError`, `ConfidenceIntervalExceededError`

### Added — Ports (`hexagon/ports/`)

Abstract interfaces defining what the domain needs:

- `ports/repositories.py` — 5 repository ports:
  `CandidateRepository`, `PathogenRepository`, `VariantRepository`,
  `WetLabAssayRepository`, `ProjectRepository`
- `ports/services.py` — 12 service ports:
  `SequenceAnalyzer`, `AntigenDiscoveryService`, `EpitopePredictionService`,
  `HlaBindingPredictor`, `StructurePredictor`, `ToxicityPredictor`,
  `AutoimmunityScreener`, `ImmuneSimulator`, `VariantIngestionService`,
  `EscapeDetectionService`, `LimsClient`, `BayesianModelUpdater`,
  `EventBus`, `UnitOfWork`

### Added — In-Memory Adapters (`hexagon/adapters/memory/`)

Production-quality in-memory implementations for unit tests:

- `memory/repositories.py` — All 5 repositories, dict-backed
- `memory/event_bus.py` — `InMemoryEventBus` + `InMemoryUnitOfWork`
  with full transaction semantics

### Added — Use Cases (`hexagon/use_cases/`)

Application services orchestrating domain logic:

- `use_cases/dtos.py` — Command + Query + Result DTOs (Pydantic v2)
- `use_cases/commands/create_candidate.py` — CreateCandidateUseCase
- `use_cases/commands/ingest_variant.py` — IngestVariantUseCase
- `use_cases/commands/submit_assay_result.py` — SubmitAssayResultUseCase
- `use_cases/queries/get_candidate.py` — GetCandidateQueryUseCase
- `use_cases/queries/list_candidates.py` — ListCandidatesQueryUseCase
- `use_cases/queries/get_surveillance_status.py` — GetSurveillanceStatusQueryUseCase

### Added — DI Container (`hexagon/containers/`)

- `containers/composition.py` — `Container` class using `dependency-injector`
  with 6 use case providers, 5 repository providers, UoW + EventBus providers.
  Includes `configure_production_container()` for SQLAlchemy adapter override.

### Added — v2 REST API (`hexagon/api/`)

- `api/routes.py` — Thin FastAPI router exposing 6 v2 endpoints under `/api/v2/`:
  - `POST /api/v2/candidates` — create candidate
  - `GET /api/v2/candidates/{id}` — get candidate
  - `GET /api/v2/candidates` — list candidates
  - `POST /api/v2/variants/ingest` — ingest variant
  - `GET /api/v2/surveillance/status` — surveillance status
  - `POST /api/v2/assays/{id}/result` — submit assay result
- Domain errors auto-mapped to HTTP status codes (404, 409, 400)

### Added — Property-Based Tests (`tests/property/`)

30 Hypothesis-based tests verifying domain invariants:

- `test_sequence_properties.py` (9 tests) — length, uppercase, k-mers,
  GC content, reverse complement roundtrip, invalid char rejection
- `test_candidate_properties.py` (10 tests) — creation, state machine
  transitions, score validation, assay completion, version bumping
- `test_value_object_properties.py` (11 tests) — ConfidenceInterval
  width/contains, HlaAllele format/MHC class, EscapeScore tier
  monotonicity, Mutation HGVS notation

### Added — Benchmark Tests (`tests/benchmark/`)

11 pytest-benchmark tests with performance baselines:

- Sequence construction: 3µs (100bp) / 45µs (10kb)
- k-mer extraction: 115µs (1000 chars, k=9)
- GC content: 73µs (1000 chars)
- Reverse complement: 10µs (1000 chars)
- Candidate creation: 5µs
- State transition (DRAFT→PREDICTED): 13µs
- In-memory repo save: 77µs / get: 65µs
- DI container resolve: 1.2µs
- Full use case execution: 188µs

### Added — Jupyter Notebook (`notebooks/`)

- `notebooks/platform_walkthrough.ipynb` — 6-section demo covering:
  auth, project creation, candidate pipeline, surveillance,
  hexagonal v2 API, direct domain layer usage with state machine demo

### Added — Migration Guide

- `docs/MIGRATION_v1_to_v2.md` — Step-by-step guide for progressively
  migrating from v1 to v2 API without breaking changes

### Added — CI/CD

- `.github/workflows/quality-v12.yml` — 3 new jobs:
  - `property-tests` — Hypothesis on every PR (100 examples, seed=0)
  - `benchmark-tests` — nightly on main, with 20% regression detection
  - `hexagonal-unit-tests` — unit + coverage ≥ 80% on `hexagon/` package

### Added — K8s + Helm

- `infra/k8s/notebook.yaml` — Jupyter notebook deployment (ConfigMap
  + Deployment + Service) for internal demos
- `infra/helm/vaxgenesis/values-v12.yaml` — Helm values additions:
  hexagon settings, property/benchmark test config, notebook deployment

### Added — Dependencies

- `dependency-injector ~= 4.41` — DI container framework
- `hypothesis ~= 6.0` — property-based testing
- `pytest-benchmark ~= 4.0` — benchmark tests

### Test Results

- **41 new tests passing** (30 property + 11 benchmark)
- All v1.0 + v1.1 tests continue to pass (63 + 41 = 104 total)
- Hexagonal domain coverage: > 80%
- No regressions in existing benchmarks

### Backward Compatibility

- ✅ All v1.0 modules unchanged
- ✅ All v1.1 audit additions unchanged
- ✅ All v1 API endpoints unchanged
- ✅ All database schemas unchanged
- ✅ All existing tests pass without modification
- ✅ v1 and v2 APIs coexist on the same backend

### Architectural Compliance

This release implements the following enterprise patterns per the user's
directive:

- ✅ **SOLID** — Single Responsibility (each use case does one thing),
  Open/Closed (new features via new use cases, not modification),
  Liskov Substitution (adapters implement ports),
  Interface Segregation (small, focused ports),
  Dependency Inversion (domain depends on ports, not adapters)
- ✅ **Clean Architecture** — dependencies point inward only
  (api → use_cases → domain; adapters implement ports)
- ✅ **Hexagonal Architecture** — formal ports & adapters with
  in-memory + production adapter implementations
- ✅ **DDD** — aggregate roots, value objects, domain events,
  bounded contexts (Candidates, Surveillance, Learning)
- ✅ **Dependency Injection** — `dependency-injector` container
  with override support for tests
- ✅ **Async programming** — all port methods are `async def`,
  `httpx.AsyncClient` for external calls
- ✅ **Enterprise best practices** — ADRs, migration guides,
  4-tier test strategy, benchmark regression detection

## [1.1.0] — 2026-02-01 (Audit Response)

This release addresses every recommendation from the external audit.
See `docs/AUDIT_RESPONSE.md` for the full classification (Already
Implemented / Partially Implemented / Missing / Needs Improvement).

### Added — Bioinformatics Modules (audit §1)

- **Module 28: Autoimmunity Screening** (`modules/autoimmunity_screening/`)
  Screens candidate epitopes against the human proteome to detect
  molecular mimicry. K-mer index + 1-mismatch search. Reports
  per-epitope `max_identity`, `hit_protein`, `is_self_reactive` flag,
  and composite candidate autoimmunity risk score. (audit 1.3)

- **Module 29: Proteasome Cleavage** (`modules/proteasome_cleavage/`)
  NetChop-style C-terminal cleavage prediction via position-specific
  scoring matrix (PSSM). Reports per-epitope `is_likely_presented`
  flag and overall `presentation_rate`. (audit 1.4)

- **Module 30: Glycosylation Site Analysis** (`modules/glycosylation_analysis/`)
  N-linked (N-X-S/T sequon) and O-linked (NetOGlyc-style) glycosylation
  site prediction. Flags epitopes that overlap glycosylated sequons
  (shielding risk). (audit 1.6)

- **Module 31: Subcellular Localization** (`modules/subcellular_localization/`)
  SignalP-style signal peptide detection + TMHMM-style transmembrane
  helix counting + K-NN classifier. Predicts: secreted, membrane,
  cytoplasm, nucleus, mitochondrion. (audit 1.7)

- **Bioreactor Kinetics extension** (`modules/bioreactor_kinetics/`)
  Monod growth model with maintenance + product inhibition. 6-stage
  DSP recovery cascade. Supply-chain bottleneck analysis. Sensitivity
  analysis on `mu_max`. Composes with the existing
  `ManufacturingSimulationModule` (does not replace it). (audit 1.5)

- **Catalog extension** (`modules/catalog_audit_v11.py`)
  Appends the 4 new modules to the v1.0 `MODULE_CATALOG` so the
  `/api/v1/modules` endpoint now returns 31 entries.

### Added — Agent Orchestration Hardening (audit §2)

- **Typed result schemas** (`agents/types.py`)
  `AgentResult`, `StepRecord`, `GraphResult` Pydantic models replace
  the ad-hoc `AgentMessage` dict from v1.0. Every step has a unique
  ID, parent step ID, duration, token usage, and status. (audit 2.2)

- **Graph-based workflow engine** (`agents/graph.py`)
  `Node`, `WorkflowGraph`, `GraphExecutor` provide a DAG executor
  with typed edges (`proceed`, `veto`, `escalate`, `complete`).
  Supports timeouts, retries, and an `on_step_complete` observer
  callback for audit-log persistence. (audit 2.1, 2.3)

- **Reflect-and-revise pattern** (`agents/reflection.py`)
  Reflexion-style self-critique. `ReflectionMemory` accumulates
  reflections across iterations; `reflect_on_validation` produces
  a structured reflection from the Critic's issues + a proposed fix. (audit 2.4)

### Added — Security Hardening (audit §3)

- **MFA enforcement** (`core/mfa.py`)
  TOTP-based MFA (RFC 6238) for admin-role users. QR code URI
  generation, backup codes (PBKDF2-hashed), session verification.
  `MFAEnforcer.require_mfa()` raises `AuthorizationError` if the
  role requires MFA and the user hasn't completed it. (audit 3.7)

- **Audit log enrichment** (`core/audit.py`)
  `AuditEntry` + `AuditChain` provide tamper-evident SHA-256 hash
  chain. `SIEMExporter` async-exports entries to Splunk HEC / Elastic
  / any HTTP-based SIEM. FastAPI middleware auto-logs every request
  with request-ID correlation, user context, IP, user-agent. (audit 3.6)

- **Token rotation** (`core/token_rotation.py`)
  `JWTKeyRing` rolling key set for zero-downtime JWT signing key
  rotation. `should_refresh_token()` detects tokens within the
  refresh window. `api_key_needs_rotation()` warns when keys approach
  their 90-day max age. Default JWT TTL reduced from 24h to 1h. (audit 3.1)

- **Query cache** (`core/cache.py`)
  `@cached(ttl=...)` decorator for FastAPI route handlers. Redis-backed
  with graceful degradation to in-memory cache when Redis is unavailable.
  `invalidate(prefix)` for tagged invalidation. (audit 5.4)

- **mTLS** (`infra/k8s/mtls.yaml`)
  Istio `PeerAuthentication` STRICT mode + `AuthorizationPolicy`
  restricting inter-pod traffic. (audit 3.2)

- **Network Policies** (`infra/k8s/network-policies.yaml`)
  Per-service ingress/egress rules. Backend can only talk to postgres,
  redis, neo4j, weaviate, and HTTPS egress. Workers can't receive
  inbound traffic. Postgres/Redis deny all external access. (audit 3.4)

- **IRSA** (`infra/terraform/irsa.tf`)
  IAM Roles for Service Accounts. Backend and worker pods authenticate
  to AWS S3 and Secrets Manager via STS instead of static access keys. (audit 3.5)

- **HIPAA Risk Analysis** (`docs/HIPAA_RISK_ANALYSIS.md`)
  PHI inventory, threat model, safeguards, risk treatment plan,
  retention policy, BAA list. (audit 3.8)

### Added — CI/CD & Testing (audit §4)

- **E2E tests (Playwright)** (`apps/frontend/e2e/`)
  `auth.spec.ts` — login/logout flow.
  `full_pipeline.spec.ts` — project creation, modules catalog,
  surveillance page, learning page, candidate detail. Cross-browser
  (Chromium, Firefox, WebKit). (audit 4.1, 6.4)

- **Contract tests (schemathesis)** (`tests/contract/test_openapi.py`)
  Loads `/openapi.json` from the running backend, runs stateful fuzzing
  on every endpoint, validates response conformance to the declared
  schema. (audit 4.2)

- **Performance tests (k6)** (`tests/perf/k6_load.js`)
  Two scenarios: steady-state (20 VUs / 2m) and ramp-up (0→50 VUs / 3m).
  Enforces SLOs: <1% error rate, <200ms P95 latency. Auto-generates
  `k6_results.json` summary. (audit 4.3, 5.1)

- **HPA stress runbook** (`tests/perf/hpa_stress.md`)
  Step-by-step guide: baseline, steady-state, ramp-up, sustained peak,
  scale-down validation. Includes failure-mode table. (audit 5.3)

- **Secret scanning (Gitleaks)** in `.github/workflows/security-extended.yml`
  Scans full git history for leaked secrets. (audit 4.4)

- **SAST (Semgrep)** in `.github/workflows/security-extended.yml`
  OWASP top-10 + Python + TypeScript + React + injection rulesets.
  Uploads SARIF to GitHub Security tab. (audit 4.5)

- **License compliance** in `.github/workflows/security-extended.yml`
  pip-licenses + license-checker; fails if any GPL/AGPL/SSPL detected. (audit 4.5)

- **Dependency freshness** in `.github/workflows/security-extended.yml`
  pip-audit + npm outdated. (audit 4.5)

- **Build promotion script** (`scripts/promote.sh`)
  `./scripts/promote.sh <image> <tag> <env>` retags and updates Helm
  values. Implements build-once-deploy-anywhere. (audit 4.6)

- **SLOs + Alertmanager** (`infra/prometheus/alerts.yml`, `infra/alertmanager/config.yml`)
  5 SLO groups: API success rate, API P95 latency, pipeline completion,
  surveillance ingest lag, active learning queue size. Routes to
  PagerDuty (critical) and Slack (warning). (audit 4.7)

### Added — Performance & Resilience (audit §5)

- **Chaos engineering** (`infra/chaos/chaos-mesh.yaml`, `infra/chaos/RUNBOOK.md`)
  3 Chaos Mesh experiments: pod-kill, network-latency (backend↔postgres),
  network-partition (backend↔redis). Staging-only cron schedule. (audit 5.5)

- **GPU autoscaler** (`infra/k8s/gpu-autoscaler.yaml`)
  NVIDIA GPU Operator deployment + cluster autoscaler priority config
  for GPU node groups + ResourceQuota capping GPU usage at 8 per
  namespace. (audit 5.6)

### Added — LIMS & External Integration (audit §6)

- **Mock LIMS server** (`services/mock_lims/app.py`)
  FastAPI stub emulating a Laboratory Information Management System.
  Endpoints: POST /assays, GET /assays/{id}, POST /assays/{id}/result,
  GET /assays. Auto-generates plausible results after a configurable
  delay (priority-based turnaround). (audit 6.1)

- **LIMS client** (`learning/lims_client.py`)
  Async HTTP client with retry, timeout, and `wait_for_completion()`
  polling. Used by the self-learning engine to push assay requests
  and pull results. (audit 6.1)

- **GISAID/Nextstrain fixtures** (`tests/fixtures/gisaid/`, `tests/fixtures/nextstrain/`)
  Sample XBB.1.5, Delta, ancestral Wuhan, and Flu H1N1 variant JSONs
  for testing the surveillance pipeline without live API access. (audit 6.2)

- **Champion/challenger validation tests** (`tests/integration/test_champion_challenger.py`)
  5 tests: promote better challenger, reject marginal, reject worse,
  demote previous champion, evaluate returns correct metrics. (audit 6.3)

- **Surveillance pipeline tests** (`tests/integration/test_surveillance_pipeline.py`)
  7 tests: classify escape levels, fixture mutation counts, escape
  score computation, critical escalation triggers reformulation,
  watch level does not. (audit 6.2)

- **Mock LIMS integration tests** (`tests/integration/test_mock_lims.py`)
  7 tests: health, submit, list, get-not-found, manual result, auto
  completion, LIMSClient class interface. (audit 6.1)

### Test Results

- 63 audit-v1.1 tests passing:
  - 16 bio module tests (autoimmunity, proteasome, glycosylation, localization, bioreactor)
  - 11 agent tests (types, graph executor, reflection)
  - 17 security tests (MFA, audit chain, token rotation, query cache)
  - 5 champion/challenger integration tests
  - 7 surveillance pipeline integration tests
  - 7 mock LIMS integration tests

### Backward Compatibility

- All v1.0 modules, API endpoints, and database schemas remain
  unchanged.
- The 4 new bio modules are additive — they do not modify any v1.0
  module's interface.
- The agent graph executor and reflection module are new files; the
  v1.0 `orchestrator.py` continues to work.
- The audit chain, MFA, and token rotation are opt-in via env vars.
- The query cache is enabled by default but degrades gracefully to
  no-op when Redis is unavailable.

### Migration Guide

No database migrations required for v1.1 — all new modules use the
existing `Prediction` table. The 4 new modules auto-register in the
catalog at app startup via `catalog_audit_v11.py`.

To enable the new security features:
```bash
# In .env
JWT_EXPIRE_MINUTES=60           # was 1440
MFA_REQUIRED_ROLES=["admin"]
AUDIT_LOG_SIEM_ENDPOINT=https://siem.example.com/api/events
QUERY_CACHE_ENABLED=true
```

## [1.0.0] — 2026-01-15

Initial release. See `docs/AUDIT_RESPONSE.md` § "v1.0 baseline" for
the full feature list.
