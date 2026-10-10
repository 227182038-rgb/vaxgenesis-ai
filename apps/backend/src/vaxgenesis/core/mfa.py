"""MFA enforcement (audit 3.7).

TOTP-based multi-factor authentication for admin-role users.

Implements:
  - TOTP secret generation (Base32)
  - TOTP code verification (RFC 6238)
  - QR code URI generation for authenticator apps
  - Backup codes (single-use, hashed)

Usage:
  1. User calls `enable_mfa(user_id)` → returns QR URI + backup codes.
  2. User scans QR with Google Authenticator / 1Password / etc.
  3. User enters 6-digit code → `verify_mfa(user_id, code)` returns True/False.
  4. Backup codes can be used when the user loses their device.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from typing import Any

from vaxgenesis.config_audit_v11 import audit_v11_settings


# ============================================================
# TOTP (RFC 6238) — pure-Python implementation
# ============================================================

def generate_totp_secret() -> str:
    """Generate a random 20-byte Base32-encoded TOTP secret."""
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii")


def _hotp(secret_b32: str, counter: int, digits: int = 6) -> str:
    """HMAC-based one-time password (RFC 4226)."""
    key = base64.b32decode(secret_b32, casefold=True)
    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = (struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF) % (10 ** digits)
    return str(code).zfill(digits)


def generate_totp_code(
    secret_b32: str,
    timestamp: int | None = None,
    period: int | None = None,
    digits: int | None = None,
) -> str:
    """Generate the current TOTP code."""
    period = period or audit_v11_settings.mfa_totp_period_seconds
    digits = digits or audit_v11_settings.mfa_totp_digits
    ts = timestamp or int(time.time())
    counter = ts // period
    return _hotp(secret_b32, counter, digits)


def verify_totp_code(
    secret_b32: str,
    code: str,
    timestamp: int | None = None,
    window: int = 1,
) -> bool:
    """Verify a TOTP code with ±window period tolerance for clock skew."""
    ts = timestamp or int(time.time())
    period = audit_v11_settings.mfa_totp_period_seconds
    base_counter = ts // period
    for offset in range(-window, window + 1):
        expected = _hotp(secret_b32, base_counter + offset, audit_v11_settings.mfa_totp_digits)
        if hmac.compare_digest(expected, code):
            return True
    return False


# ============================================================
# QR code URI
# ============================================================

def get_totp_uri(
    secret_b32: str,
    account_name: str,
    issuer: str | None = None,
) -> str:
    """Generate the otpauth:// URI for QR code generation."""
    issuer = issuer or audit_v11_settings.mfa_issuer
    from urllib.parse import quote
    label = quote(f"{issuer}:{account_name}")
    return (
        f"otpauth://totp/{label}"
        f"?secret={secret_b32}"
        f"&issuer={quote(issuer)}"
        f"&algorithm=SHA1"
        f"&digits={audit_v11_settings.mfa_totp_digits}"
        f"&period={audit_v11_settings.mfa_totp_period_seconds}"
    )


# ============================================================
# Backup codes
# ============================================================

def generate_backup_codes(count: int = 10) -> list[str]:
    """Generate single-use backup codes (8 hex chars each)."""
    return [secrets.token_hex(4).upper() for _ in range(count)]


def hash_backup_code(code: str) -> str:
    """Hash a backup code for storage (never store plaintext)."""
    salt = secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac("sha256", code.encode(), salt, 100_000)
    return base64.b64encode(salt + hashed).decode("ascii")


def verify_backup_code(code: str, stored: str) -> bool:
    """Verify a backup code against its stored hash."""
    try:
        decoded = base64.b64decode(stored)
        salt, hashed = decoded[:16], decoded[16:]
        new_hash = hashlib.pbkdf2_hmac("sha256", code.encode(), salt, 100_000)
        return hmac.compare_digest(hashed, new_hash)
    except Exception:
        return False


# ============================================================
# MFA session enforcement
# ============================================================

class MFAEnforcer:
    """Middleware-style enforcer for MFA-required roles.

    Usage in FastAPI dependency:

        @router.post("/admin/...", dependencies=[Depends(require_mfa)])
        async def admin_action(...): ...
    """

    def __init__(self) -> None:
        # In-memory store for the demo. In production, persist to DB.
        self._user_secrets: dict[str, str] = {}
        self._user_backup_codes: dict[str, list[str]] = {}
        self._verified_sessions: dict[str, float] = {}  # user_id -> expiry timestamp

    def enable_mfa(self, user_id: str) -> dict[str, Any]:
        """Set up MFA for a user. Returns secret + backup codes + QR URI."""
        secret = generate_totp_secret()
        self._user_secrets[user_id] = secret
        backups = generate_backup_codes()
        self._user_backup_codes[user_id] = [hash_backup_code(c) for c in backups]
        return {
            "secret": secret,
            "backup_codes": backups,  # plaintext, shown once
            "qr_uri": get_totp_uri(secret, account_name=user_id),
        }

    def verify(self, user_id: str, code: str) -> bool:
        """Verify a TOTP code or backup code; if successful, mark session as MFA-verified."""
        secret = self._user_secrets.get(user_id)
        if not secret:
            return False

        # Try TOTP first
        if verify_totp_code(secret, code):
            self._verified_sessions[user_id] = time.time() + 3600  # 1h
            return True

        # Try backup codes
        for i, stored in enumerate(self._user_backup_codes.get(user_id, [])):
            if verify_backup_code(code, stored):
                # Burn the used backup code
                self._user_backup_codes[user_id].pop(i)
                self._verified_sessions[user_id] = time.time() + 3600
                return True

        return False

    def is_verified(self, user_id: str) -> bool:
        """Check if the user has a current MFA-verified session."""
        expiry = self._verified_sessions.get(user_id)
        if not expiry:
            return False
        if time.time() > expiry:
            self._verified_sessions.pop(user_id, None)
            return False
        return True

    def require_mfa(self, user_id: str, role: str) -> None:
        """Raise if the role requires MFA and the user hasn't completed it."""
        if role in audit_v11_settings.mfa_required_roles and not self.is_verified(user_id):
            from vaxgenesis.core.errors import AuthorizationError
            raise AuthorizationError(
                "MFA required for this role",
                detail={"role": role, "required_mfa": True},
            )


# Singleton
mfa_enforcer = MFAEnforcer()
