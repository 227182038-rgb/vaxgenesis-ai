"""Tests for security hardening (audit 3.x)."""
from __future__ import annotations

import asyncio
import time

import pytest


# ============================================================
# MFA (3.7)
# ============================================================

class TestMFA:
    def test_totp_code_generation_and_verification(self):
        from vaxgenesis.core.mfa import generate_totp_secret, generate_totp_code, verify_totp_code
        secret = generate_totp_secret()
        code = generate_totp_code(secret)
        assert len(code) == 6
        assert verify_totp_code(secret, code)

    def test_totp_rejects_wrong_code(self):
        from vaxgenesis.core.mfa import generate_totp_secret, verify_totp_code
        secret = generate_totp_secret()
        assert not verify_totp_code(secret, "000000")

    def test_totp_uri_format(self):
        from vaxgenesis.core.mfa import generate_totp_secret, get_totp_uri
        secret = generate_totp_secret()
        uri = get_totp_uri(secret, account_name="user@test.com")
        assert uri.startswith("otpauth://totp/")
        assert "secret=" + secret in uri
        assert "VaxGenesis" in uri

    def test_backup_code_generation_and_verification(self):
        from vaxgenesis.core.mfa import generate_backup_codes, hash_backup_code, verify_backup_code
        codes = generate_backup_codes(10)
        assert len(codes) == 10
        for code in codes:
            assert len(code) == 8
            hashed = hash_backup_code(code)
            assert verify_backup_code(code, hashed)
            assert not verify_backup_code("WRONG123", hashed)

    def test_mfa_enforcer_full_flow(self):
        from vaxgenesis.core.mfa import mfa_enforcer
        # Enable MFA
        setup = mfa_enforcer.enable_mfa("user-123")
        assert "secret" in setup
        assert "backup_codes" in setup
        assert len(setup["backup_codes"]) == 10

        # Initially not verified
        assert not mfa_enforcer.is_verified("user-123")

        # Verify with TOTP code
        from vaxgenesis.core.mfa import generate_totp_code
        code = generate_totp_code(setup["secret"])
        assert mfa_enforcer.verify("user-123", code)
        assert mfa_enforcer.is_verified("user-123")

    def test_mfa_enforcer_requires_mfa_for_admin(self):
        from vaxgenesis.core.mfa import mfa_enforcer
        from vaxgenesis.core.errors import AuthorizationError
        # User without MFA setup
        with pytest.raises(AuthorizationError):
            mfa_enforcer.require_mfa("user-no-mfa", "admin")

        # User with MFA setup but not verified
        setup = mfa_enforcer.enable_mfa("user-admin")
        with pytest.raises(AuthorizationError):
            mfa_enforcer.require_mfa("user-admin", "admin")

        # Verify then require again — should not raise
        from vaxgenesis.core.mfa import generate_totp_code
        code = generate_totp_code(setup["secret"])
        mfa_enforcer.verify("user-admin", code)
        mfa_enforcer.require_mfa("user-admin", "admin")  # should not raise

    def test_mfa_not_required_for_viewer(self):
        from vaxgenesis.core.mfa import mfa_enforcer
        # Viewer role doesn't require MFA
        mfa_enforcer.require_mfa("user-viewer", "viewer")  # should not raise


# ============================================================
# Audit chain (3.6)
# ============================================================

class TestAuditChain:
    def test_chain_appends_and_verifies(self):
        from vaxgenesis.core.audit import AuditEntry, AuditChain
        chain = AuditChain()
        e1 = AuditEntry(action="login", resource_type="user", resource_id="u1")
        e2 = AuditEntry(action="logout", resource_type="user", resource_id="u1")
        chain.append(e1)
        chain.append(e2)
        assert chain.verify() is True
        assert len(chain.tail()) == 2

    def test_chain_tamper_detection(self):
        from vaxgenesis.core.audit import AuditEntry, AuditChain
        chain = AuditChain()
        e1 = AuditEntry(action="login", resource_type="user", resource_id="u1")
        chain.append(e1)
        # Tamper with the entry
        e1.action = "DELETE"
        assert chain.verify() is False

    def test_entry_has_request_id(self):
        from vaxgenesis.core.audit import AuditEntry
        e = AuditEntry(
            action="api_call",
            resource_type="endpoint",
            resource_id="/api/v1/candidates",
            request_id="req-123",
        )
        d = e.to_dict()
        assert d["request_id"] == "req-123"
        assert d["action"] == "api_call"
        assert "hash" in d
        assert "previous_hash" in d


# ============================================================
# Token rotation (3.1)
# ============================================================

class TestTokenRotation:
    def test_keyring_rotate(self):
        from vaxgenesis.core.token_rotation import JWTKeyRing
        ring = JWTKeyRing()
        first = ring.current
        ring.rotate()
        second = ring.current
        assert first != second
        # Old key should still be accepted during rotation window
        assert first in ring.accepted_keys

    def test_should_refresh_token(self):
        from vaxgenesis.core.token_rotation import should_refresh_token
        # Token expiring in 5 minutes — within 15-min refresh window
        soon = time.time() + 300
        assert should_refresh_token(soon) is True
        # Token expiring in 1 hour — outside refresh window
        later = time.time() + 3600
        assert should_refresh_token(later) is False

    def test_api_key_rotation_warning(self):
        from vaxgenesis.core.token_rotation import api_key_needs_rotation
        # Key created 85 days ago, max age 90, warning window 7 days
        # 85 >= 90 - 7 = 83 → needs_rotation = True
        old = time.time() - 85 * 86400
        result = api_key_needs_rotation(old)
        assert result["needs_rotation"] is True
        assert result["days_until_expiry"] < 7

        # Key created 10 days ago — fine
        fresh = time.time() - 10 * 86400
        result = api_key_needs_rotation(fresh)
        assert result["needs_rotation"] is False


# ============================================================
# Query cache (5.4)
# ============================================================

class TestQueryCache:
    def test_cache_set_and_get(self):
        from vaxgenesis.core.cache import query_cache
        asyncio.run(query_cache.set("test_key", {"value": 42}, ttl=60))
        result = asyncio.run(query_cache.get("test_key"))
        assert result == {"value": 42}

    def test_cache_miss_returns_none(self):
        from vaxgenesis.core.cache import query_cache
        result = asyncio.run(query_cache.get("nonexistent_key_12345"))
        assert result is None

    def test_cached_decorator(self):
        from vaxgenesis.core.cache import cached, query_cache

        call_count = {"n": 0}

        @cached(ttl=60, key_prefix="test_decorator")
        async def expensive_fn(x: int) -> int:
            call_count["n"] += 1
            return x * 2

        # First call — should execute
        r1 = asyncio.run(expensive_fn(5))
        assert r1 == 10
        assert call_count["n"] == 1

        # Second call with same args — should hit cache
        r2 = asyncio.run(expensive_fn(5))
        assert r2 == 10
        assert call_count["n"] == 1  # not incremented

    def test_cache_invalidation(self):
        from vaxgenesis.core.cache import query_cache
        asyncio.run(query_cache.set("prefix_key1", "v1", ttl=60))
        asyncio.run(query_cache.set("prefix_key2", "v2", ttl=60))
        count = asyncio.run(query_cache.invalidate("prefix_"))
        assert count >= 2
