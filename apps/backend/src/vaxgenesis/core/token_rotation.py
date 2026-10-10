"""Token rotation utility (audit 3.1).

Extends v1.0 auth with:
  - Shorter default token lifetime (1h instead of 24h, configurable)
  - Refresh-window detection (auto-rotate when within 15 min of expiry)
  - API key rotation tracking (warns when keys approach 90-day max age)
  - JWT key rotation (rolling set of N signing keys)
"""
from __future__ import annotations

import hashlib
import secrets
import time
from typing import Any

from vaxgenesis.config_audit_v11 import audit_v11_settings


class JWTKeyRing:
    """Rolling set of N JWT signing keys for zero-downtime rotation.

    - `current` is used to sign new tokens.
    - `previous` keys are still accepted for verification during the
      rotation window.
    - After the rotation window expires, old keys are purged.
    """

    def __init__(self, current_key: str | None = None, rotation_window_seconds: int = 3600) -> None:
        self._keys: list[tuple[str, float]] = []  # (key, added_at)
        self.rotation_window = rotation_window_seconds
        if current_key:
            self._keys.append((current_key, time.time()))
        else:
            self.rotate()

    def rotate(self) -> str:
        """Generate a new signing key and demote the current one."""
        new_key = secrets.token_urlsafe(64)
        self._keys.append((new_key, time.time()))
        # Purge keys older than rotation window
        cutoff = time.time() - self.rotation_window
        self._keys = [(k, t) for k, t in self._keys if t > cutoff]
        # Keep at most 3 keys
        self._keys = self._keys[-3:]
        return new_key

    @property
    def current(self) -> str:
        return self._keys[-1][0] if self._keys else self.rotate()

    @property
    def accepted_keys(self) -> list[str]:
        """All keys that are still valid for verification."""
        return [k for k, _ in self._keys]


# Singleton keyring (in production: load from KMS / Vault)
_keyring: JWTKeyRing | None = None


def get_keyring() -> JWTKeyRing:
    global _keyring
    if _keyring is None:
        _keyring = JWTKeyRing()
    return _keyring


def should_refresh_token(expires_at: float) -> bool:
    """Return True if the token is within the refresh window of expiry."""
    now = time.time()
    return (expires_at - now) < audit_v11_settings.jwt_refresh_window_minutes * 60


def api_key_needs_rotation(created_at: float) -> dict[str, Any]:
    """Check whether an API key is approaching its max age."""
    age_days = (time.time() - created_at) / 86400
    max_age = audit_v11_settings.api_key_max_age_days
    warning_days = audit_v11_settings.api_key_rotation_warning_days
    return {
        "age_days": round(age_days, 1),
        "max_age_days": max_age,
        "needs_rotation": age_days >= max_age - warning_days,
        "days_until_expiry": round(max_age - age_days, 1),
    }


def generate_api_key_with_metadata() -> dict[str, Any]:
    """Generate a new API key plus rotation metadata."""
    raw = secrets.token_urlsafe(32)
    plaintext = f"vgx_{raw}"
    key_hash = hashlib.sha256(plaintext.encode()).hexdigest()
    key_prefix = plaintext[:12] + "..."
    return {
        "plaintext": plaintext,
        "key_hash": key_hash,
        "key_prefix": key_prefix,
        "created_at": time.time(),
        "expires_at": time.time() + audit_v11_settings.api_key_max_age_days * 86400,
        "rotation_metadata": {
            "max_age_days": audit_v11_settings.api_key_max_age_days,
            "rotation_warning_days": audit_v11_settings.api_key_rotation_warning_days,
        },
    }
