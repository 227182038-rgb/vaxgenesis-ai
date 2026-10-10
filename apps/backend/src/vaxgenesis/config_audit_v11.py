"""Configuration (audit v1.1 additions).

Extends the v1.0 Settings with new fields for:
- mTLS
- MFA
- token rotation
- audit/SIEM export
- query cache
- mock LIMS
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuditV11Settings(BaseSettings):
    """Settings added in v1.1 audit response. Loaded alongside the v1.0 Settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8",
        case_sensitive=False, extra="ignore",
    )

    # ---- Token rotation (3.1) ----
    jwt_expire_minutes: int = 60  # was 1440; reduced per audit
    jwt_refresh_window_minutes: int = 15
    api_key_max_age_days: int = 90
    api_key_rotation_warning_days: int = 7

    # ---- mTLS (3.2) ----
    mtls_enabled: bool = False
    mtls_cert_path: str = "/etc/vaxgenesis/tls/tls.crt"
    mtls_key_path: str = "/etc/vaxgenesis/tls/tls.key"
    mtls_ca_path: str = "/etc/vaxgenesis/tls/ca.crt"

    # ---- MFA (3.7) ----
    mfa_required_roles: list[str] = Field(
        default_factory=lambda: ["admin"],
        description="Roles that must complete MFA before any privileged action.",
    )
    mfa_issuer: str = "VaxGenesis AI"
    mfa_totp_digits: int = 6
    mfa_totp_period_seconds: int = 30

    # ---- Audit / SIEM (3.6) ----
    audit_log_siem_endpoint: str | None = None
    audit_log_siem_token: str | None = None
    audit_log_retention_days: int = 2555  # 7 years (HIPAA)
    audit_log_include_request_body: bool = False  # PHI risk

    # ---- Query cache (5.4) ----
    query_cache_enabled: bool = True
    query_cache_default_ttl_seconds: int = 300
    query_cache_max_size: int = 10000

    # ---- Mock LIMS (6.1) ----
    mock_lims_enabled: bool = False
    mock_lims_port: int = 9001

    # ---- E2E / test mode (4.1) ----
    e2e_test_mode: bool = False
    e2e_test_user_email: str = "e2e@test.vaxgenesis.ai"

    # ---- SLO thresholds (4.7) ----
    slo_api_success_rate: float = 0.99
    slo_api_p95_latency_ms: int = 200
    slo_pipeline_completion_hours: int = 72


audit_v11_settings = AuditV11Settings()
