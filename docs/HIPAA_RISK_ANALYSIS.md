# HIPAA Risk Analysis — VaxGenesis AI

**Document version:** 1.0
**Date:** 2026-01-15
**Prepared by:** VaxGenesis AI Engineering
**Audit item:** 3.8

## 1. Scope

This risk analysis covers the VaxGenesis AI platform as deployed in
production (AWS EKS, RDS PostgreSQL, ElastiCache Redis, S3 artifacts).
It identifies threats to the confidentiality, integrity, and availability
of Protected Health Information (PHI) that may flow through the system
via LIMS integration, clinical-trial metadata, or user-uploaded
patient-derived sequences.

## 2. PHI Inventory

| Data Element | Source | Stored? | Encrypted? |
|--------------|--------|---------|-----------|
| HLA genotype | LIMS assay result | Yes (PostgreSQL `wet_lab_assays.metadata`) | At rest (KMS) |
| Patient-derived sequences | GISAID upload | Yes (PostgreSQL `variants.sequence`) | At rest (KMS) |
| User email | Registration | Yes | At rest (KMS) |
| User IP address | Audit log | Yes (PostgreSQL `audit_logs`) | At rest (KMS) |
| LIMS credentials | Secrets Manager | Yes | KMS envelope |
| Pipeline predictions | Computed | Yes (PostgreSQL `predictions`) | At rest (KMS) |

## 3. Threat Model

| # | Threat | Likelihood | Impact | Risk | Mitigation |
|---|--------|-----------|--------|------|-----------|
| T1 | Unauthorized API access via stolen JWT | Medium | High | High | 1h token TTL + refresh window + JWT key rotation |
| T2 | Privilege escalation via RBAC bypass | Low | Critical | High | Per-endpoint role check + MFA for admin role |
| T3 | SQL injection via API | Low | Critical | High | SQLAlchemy parameterized queries + Pydantic input validation |
| T4 | Cross-tenant data access | Medium | Critical | High | Per-user `WHERE owner_id =` clause on all list endpoints |
| T5 | LIMS credential leakage | Low | Critical | High | Secrets Manager + IRSA (no static keys) |
| T6 | Audit log tampering | Low | High | Medium | SHA-256 hash chain + SIEM export (3.6) |
| T7 | Data exfiltration via LLM API | Medium | High | High | PHI redaction in audit logs; LLM inputs scrubbed of patient identifiers |
| T8 | Ransomware / data destruction | Low | Critical | High | RDS 30-day backups + cross-region replication; S3 versioning |
| T9 | Insider threat (privileged user) | Medium | High | High | MFA enforcement + quarterly access review + audit log review |
| T10 | Supply chain compromise (dependency) | Medium | High | High | Trivy + bandit + npm-audit + Semgrep + gitleaks in CI |
| T11 | mTLS bypass (pod impersonation) | Low | High | Medium | Istio STRICT mTLS + AuthorizationPolicy (3.2) |
| T12 | GPU memory leak exposing data | Low | Medium | Low | Pod isolation + GPU quota + per-task cleanup |

## 4. Safeguards Implemented

### Administrative
- Designated Security Officer: `security@vaxgenesis.ai`
- Quarterly access review documented in `docs/SECURITY.md`
- Annual workforce training required for all engineers with PHI access
- Incident response plan: `docs/INCIDENT_RESPONSE.md` (to be added in v1.2)

### Physical
- AWS data center controls (inherit from AWS)
- No on-premises infrastructure

### Technical
- **Access control:** JWT (1h TTL) + API keys (90-day rotation) + MFA (admin role)
- **Audit controls:** Hash-chained audit log + SIEM export (Splunk HEC compatible)
- **Integrity:** SHA-256 hash chain on audit log; provenance ledger on every prediction
- **Transmission security:** TLS 1.3 external + mTLS internal (Istio STRICT)
- **Encryption at rest:** RDS KMS, S3 SSE-KMS, ElastiCache at-rest encryption
- **Automatic logoff:** 1h token expiry + 15-min refresh window
- **Network segmentation:** K8s NetworkPolicies restrict inter-pod traffic (3.4)

## 5. Risk Treatment Plan

| Risk ID | Treatment | Owner | Due Date |
|---------|-----------|-------|----------|
| T7 | Add PHI redaction filter to all LLM inputs | Backend team | 2026-02-15 |
| T9 | Implement quarterly access review automation | SecOps | 2026-03-01 |
| T10 | Add dependency license + freshness check to CI | DevSecOps | 2026-02-01 |
| T11 | Deploy Istio + AuthorizationPolicies to staging | Platform team | 2026-02-15 |

## 6. Continuous Monitoring

- **Prometheus alerts** on: 5xx error rate > 1%, auth failures > 10/min,
  audit log export failures > 5/hour, HPA maxing out, GPU memory > 90%.
- **Daily SIEM review** of all `audit.action = 'auth.login'` failures.
- **Weekly review** of new dependencies added to `pyproject.toml` / `package.json`.
- **Monthly penetration test summary** reviewed by Security Officer.

## 7. Business Associate Agreements (BAAs)

Required with:
- AWS (signed)
- OpenAI (if processing PHI — currently no PHI sent to LLMs)
- Anthropic (same as above)
- GISAID (data sharing agreement — already in place)

## 8. Retention Policy

| Data Type | Retention | Disposal |
|-----------|-----------|----------|
| Audit logs | 7 years (HIPAA requirement) | Automated deletion after 2555 days |
| Predictions | 7 years | Automated deletion |
| User accounts | 7 years after deletion | Anonymize PII, retain aggregates |
| LIMS assay data | 7 years | Anonymize after retention period |

## 9. Sign-off

| Role | Name | Date |
|------|------|------|
| Security Officer | ___ | ___ |
| CTO | ___ | ___ |
| Privacy Officer | ___ | ___ |

This document is reviewed annually or upon material change to the system
architecture.
