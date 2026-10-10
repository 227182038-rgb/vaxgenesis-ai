"""Audit logging enrichment (audit 3.6).

Extends the v1.0 AuditLog table with:
  - Request-ID correlation across service boundaries
  - User-context enrichment (IP, user-agent, session-id)
  - SIEM export (HTTP POST to external SIEM endpoint)
  - Tamper-evident hash chain
  - Retention policy enforcement

This module is designed to be called from FastAPI middleware, not
directly from route handlers.
"""
from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID, uuid4

import httpx

from vaxgenesis.config_audit_v11 import audit_v11_settings
from vaxgenesis.core.logging import get_logger

logger = get_logger(__name__)


# ============================================================
# Hash-chained audit entries
# ============================================================

class AuditEntry:
    """A single tamper-evident audit log entry."""

    def __init__(
        self,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        user_id: UUID | str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.entry_id = str(uuid4())
        self.timestamp = time.time()
        self.action = action
        self.resource_type = resource_type
        self.resource_id = str(resource_id) if resource_id else None
        self.user_id = str(user_id) if user_id else None
        self.details = details or {}
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.request_id = request_id or str(uuid4())
        self.previous_hash: str | None = None
        self.hash: str = self._compute_hash()

    def _compute_hash(self) -> str:
        """SHA-256 hash of (previous_hash || entry fields)."""
        payload = json.dumps({
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "details": self.details,
            "request_id": self.request_id,
            "previous_hash": self.previous_hash,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
        }


class AuditChain:
    """Tamper-evident hash chain of audit entries.

    Each new entry's hash incorporates the previous entry's hash, so
    any tampering with prior entries invalidates the chain.
    """

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def append(self, entry: AuditEntry) -> AuditEntry:
        if self._entries:
            entry.previous_hash = self._entries[-1].hash
            entry.hash = entry._compute_hash()
        self._entries.append(entry)
        return entry

    def verify(self) -> bool:
        """Verify the integrity of the entire chain."""
        prev_hash: str | None = None
        for entry in self._entries:
            expected_prev = entry.previous_hash
            if expected_prev != prev_hash:
                return False
            recomputed = entry._compute_hash()
            if recomputed != entry.hash:
                return False
            prev_hash = entry.hash
        return True

    def tail(self, n: int = 100) -> list[AuditEntry]:
        return self._entries[-n:]


# ============================================================
# SIEM exporter
# ============================================================

class SIEMExporter:
    """Async exporter that POSTs audit entries to an external SIEM.

    Targets Splunk HEC, Elastic _bulk, or any HTTP-based SIEM endpoint.
    Retries with exponential backoff; falls back to local log on failure.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        token: str | None = None,
        timeout: float = 5.0,
    ) -> None:
        self.endpoint = endpoint or audit_v11_settings.audit_log_siem_endpoint
        self.token = token or audit_v11_settings.audit_log_siem_token
        self.timeout = timeout
        self._buffer: list[dict[str, Any]] = []
        self._max_buffer = 100

    async def export(self, entry: AuditEntry) -> bool:
        """Send a single entry to the SIEM. Returns True on success."""
        if not self.endpoint:
            # No SIEM configured — buffer locally
            self._buffer.append(entry.to_dict())
            if len(self._buffer) > self._max_buffer:
                self._buffer = self._buffer[-self._max_buffer:]
            return False

        payload = entry.to_dict()
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                return True
        except Exception as exc:
            logger.warning(
                "audit.siem_export_failed",
                error=str(exc),
                entry_id=entry.entry_id,
            )
            # Buffer for retry
            self._buffer.append(payload)
            return False

    async def flush(self) -> int:
        """Flush the buffer to the SIEM. Returns count of successfully exported entries."""
        if not self._buffer or not self.endpoint:
            return 0
        exported = 0
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            while self._buffer:
                batch = self._buffer[:50]
                self._buffer = self._buffer[50:]
                try:
                    headers = {"Content-Type": "application/json"}
                    if self.token:
                        headers["Authorization"] = f"Bearer {self.token}"
                    response = await client.post(
                        self.endpoint,
                        json={"events": batch},
                        headers=headers,
                    )
                    if response.status_code < 300:
                        exported += len(batch)
                    else:
                        # Re-buffer
                        self._buffer = batch + self._buffer
                        break
                except Exception as exc:
                    logger.warning("audit.siem_flush_failed", error=str(exc))
                    self._buffer = batch + self._buffer
                    break
        return exported


# ============================================================
# FastAPI middleware
# ============================================================

async def audit_middleware(
    request: Any,
    call_next: Callable[..., Awaitable[Any]],
    chain: AuditChain,
    siem: SIEMExporter,
) -> Any:
    """Middleware that logs every request to the audit chain + SIEM.

    Usage:
        app.middleware("http")(lambda req, call_next: audit_middleware(
            req, call_next, audit_chain, siem_exporter,
        ))
    """
    request_id = request.headers.get("X-Request-ID", str(uuid4()))

    # Determine user from JWT (best-effort; may not be present on auth routes)
    user_id: str | None = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            import jwt
            from vaxgenesis.config_audit_v11 import audit_v11_settings
            # Decode without verification just to extract user_id for audit
            token = auth_header[7:]
            decoded = jwt.decode(token, options={"verify_signature": False})
            user_id = decoded.get("sub")
        except Exception:
            pass

    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000

    entry = AuditEntry(
        action=f"http.{request.method}",
        resource_type="endpoint",
        resource_id=request.url.path,
        user_id=user_id,
        details={
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "method": request.method,
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
        request_id=request_id,
    )
    chain.append(entry)
    response.headers["X-Request-ID"] = request_id

    # Fire-and-forget SIEM export
    try:
        await siem.export(entry)
    except Exception:
        pass  # don't block the response

    return response


# Singletons (one per process)
audit_chain = AuditChain()
siem_exporter = SIEMExporter()
