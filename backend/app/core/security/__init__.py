"""
app/core/security/__init__.py
------------------------------
Security infrastructure package for SkillFit.

This package replaces the former app/core/security.py module.
All existing imports (hash_password, verify_password, create_access_token,
decode_access_token) continue to work without modification.

Phase 4.2 addition: scanner sub-module for the malware scan hook.

Sub-modules:
    scanner.py — SecurityScanner abstract hook + NoOpScanner implementation
"""

# Re-export everything from the auth utilities so existing callers
# (app/api/deps.py, app/api/auth.py, tests, etc.) keep working unchanged.
from app.core.security._auth import (  # noqa: F401
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    MAX_LOGIN_ATTEMPTS,
    ACCOUNT_LOCK_MINUTES,
    LOGIN_IP_RATE_LIMIT,
)
