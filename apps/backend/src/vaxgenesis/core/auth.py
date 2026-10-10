"""Authentication - delegates to v1.1 MFA + token rotation."""
from vaxgenesis.core.mfa import mfa_enforcer, generate_totp_code, verify_totp_code
from vaxgenesis.core.token_rotation import (
    JWTKeyRing, get_keyring, should_refresh_token,
    api_key_needs_rotation, generate_api_key_with_metadata,
)

# Re-export for backward compat
hash_password = lambda pwd: pwd  # stub - use argon2 in production
verify_password = lambda plain, hashed: plain == hashed  # stub
