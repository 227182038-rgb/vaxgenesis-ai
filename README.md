# VaxGenesis AI

> A self-learning, real-time, problem-solving vaccine digital twin platform.

[![CI Backend](https://img.shields.io/badge/CI-backend-green)](.github/workflows/backend.yml)
[![CI Frontend](https://img.shields.io/badge/CI-frontend-green)](.github/workflows/frontend.yml)
[![Security](https://img.shields.io/badge/Security-bandit%20%7C%20trivy%20%7C%20semgrep%20%7C%20gitleaks-blue)](.github/workflows/security-extended.yml)
[![Tests](https://img.shields.io/badge/tests-63%20passing-brightgreen)](tests/)
[![Version](https://img.shields.io/badge/version-1.1.0-blue)](CHANGELOG.md)

VaxGenesis AI ingests pathogen genomes, runs a **31-module cognitive
pipeline**, and produces a versioned *digital vaccine twin* that
continuously updates itself as new sequences, structures, and wet-lab
measurements arrive.

## What's New in v1.1 (Audit Response)

This release closes every recommendation from the external audit.
See [`docs/AUDIT_RESPONSE.md`](docs/AUDIT_RESPONSE.md) for the full
classification.

**4 new bioinformatics modules:**
- Autoimmunity Screening (molecular mimicry vs. human proteome)
- Proteasome Cleavage (NetChop-style antigen processing)
- Glycosylation Site Analysis (N-linked + O-linked)
- Subcellular Localization (SignalP + TMHMM-style)
- Bioreactor Kinetics extension (Monod + DSP + supply chain)

**Agent orchestration hardening:**
- Typed `AgentResult` / `GraphResult` / `StepRecord` schemas
- Graph-based workflow engine with veto-loop support
- Reflexion-style reflect-and-revise pattern

**Security & compliance:**
- MFA (TOTP) for admin role
- Tamper-evident audit log hash chain + SIEM export
- JWT key rotation, 1h token TTL, API key rotation warnings
- mTLS (Istio), K8s NetworkPolicies, IAM Roles for Service Accounts
- HIPAA risk analysis document

**Testing & observability:**
- Playwright E2E tests (auth + full pipeline scenario)
- Schemathesis contract tests
- k6 load tests with SLO enforcement
- Chaos Mesh experiments (pod-kill, latency, partition)
- Gitleaks + Semgrep + license compliance in CI
- Prometheus alert rules + Alertmanager config (5 SLOs)

**LIMS integration:**
- Mock LIMS server (FastAPI stub)
- Async LIMS client
- Champion/challenger deployment validation tests
- GISAID/Nextstrain test fixtures

## Repository Layout

```
vaxgenesis/
├── apps/
│   ├── backend/                    FastAPI service (Python 3.11)
│   │   └── src/vaxgenesis/
│   │       ├── modules/            31 pipeline modules (27 v1.0 + 4 v1.1)
│   │       ├── agents/             5-agent orchestrator + graph engine + reflection
│   │       ├── learning/           Active learning + Bayesian updater + LIMS client
│   │       ├── surveillance/       Real-time variant ingest + escape detection
│   │       └── core/               Auth, MFA, audit, cache, token rotation, metrics
│   └── frontend/                   Next.js 14 + React + Tailwind
│       ├── src/                    App pages + components + lib
│       └── e2e/                    Playwright E2E tests
├── services/
│   └── mock_lims/                  Mock Laboratory Information Management System
├── infra/
│   ├── k8s/                        K8s manifests (mTLS, NetworkPolicies, GPU autoscaler)
│   ├── helm/                       Helm chart
│   ├── terraform/                  AWS IaC (EKS, RDS, IRSA)
│   ├── prometheus/                 Metrics + alert rules
│   ├── alertmanager/               Alert routing
│   ├── grafana/                    Dashboards
│   ├── otel/                       OpenTelemetry config
│   └── chaos/                      Chaos Mesh experiments + runbook
├── tests/
│   ├── test_audit_v11_bio_modules.py    16 tests for new bio modules
│   ├── test_audit_v11_agents.py          11 tests for graph engine + reflection
│   ├── test_audit_v11_security.py        17 tests for MFA, audit, cache, rotation
│   ├── integration/                      19 integration tests (LIMS, champion/challenger, surveillance)
│   ├── contract/                         Schemathesis OpenAPI contract tests
│   ├── perf/                             k6 load tests + HPA stress runbook
│   └── fixtures/                         GISAID + Nextstrain test data
├── .github/workflows/              CI/CD (backend, frontend, deploy, security, security-extended)
├── docs/                           ARCHITECTURE, API, DEVELOPMENT, DEPLOYMENT,
│                                   SECURITY, CONTRIBUTING, CHANGELOG,
│                                   AUDIT_RESPONSE, HIPAA_RISK_ANALYSIS
├── scripts/                        setup.sh, healthcheck.sh, promote.sh
├── conftest.py                     Pytest config (path setup, asyncio mode)
├── pytest.ini                      Pytest settings
├── docker-compose.yml              13-service stack
├── Makefile                        Common commands
└── README.md                       This file
```

## Quick Start

```bash
# 1. Clone
git clone https://github.com/vaxgenesis/vaxgenesis-ai.git
cd vaxgenesis-ai

# 2. Configure environment
cp .env.example .env

# 3. Start the full stack
make up

# 4. Run database migrations
make migrate

# 5. Seed reference data
make seed

# 6. Open the app
open http://localhost:3000
```

Default login: `admin@vaxgenesis.ai` / `admin123`

## Running Tests

```bash
# All audit-v1.1 tests (63 tests)
make test

# Just the bio modules
pytest tests/test_audit_v11_bio_modules.py -v

# Just the security tests
pytest tests/test_audit_v11_security.py -v

# Integration tests (LIMS, champion/challenger, surveillance)
pytest tests/integration/ -v

# E2E tests (requires running stack)
cd apps/frontend && npx playwright test

# Performance tests (requires running backend)
k6 run tests/perf/k6_load.js
```

## Audit Compliance Summary

| Audit Section | Items | Already Impl | Partial | Missing → Added |
|---------------|-------|--------------|---------|-----------------|
| 1. Bioinformatics | 7 | 2 | 3 | 2 → 4 new modules |
| 2. Multi-Agent | 5 | 1 | 3 | 1 → reflection module |
| 3. Security | 8 | 1 | 3 | 4 → MFA, mTLS, NetPol, IRSA, HIPAA |
| 4. CI/CD | 8 | 1 | 2 | 5 → e2e, contract, perf, gitleaks, Semgrep, SLOs |
| 5. Performance | 6 | 0 | 3 | 3 → chaos, GPU autoscaler, query cache |
| 6. Integration | 4 | 0 | 1 | 3 → mock LIMS, fixtures, champion/challenger tests |
| **Total** | **38** | **5** | **15** | **18 → all implemented** |

## License

Proprietary. See [`LICENSE`](LICENSE).
