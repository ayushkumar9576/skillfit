"""
app/core/security.py
--------------------
Low-level cryptographic utilities for SkillFit authentication.

Responsibilities:
    - Password hashing and verification (bcrypt, 12 rounds)
    - JWT access token creation and decoding (HS256, 15-minute expiry)

What this module does NOT do:
    - Database access
    - Business logic
    - HTTP request/response handling

Implementation note — passlib vs. bcrypt directly:
    passlib[bcrypt] 1.7.x is incompatible with bcrypt >= 4.0 (the __about__
    attribute was removed in bcrypt 4.0). Since the venv has bcrypt 5.0.0,
    we call the bcrypt library directly. This is equally secure and avoids the
    compatibility shim entirely.

JWT claim structure (Phase 2 architecture):
    {
        "sub":  "<user_uuid_as_string>",
        "role": "<student|faculty|admin>",
        "iat":  <issued-at timestamp>,
        "exp":  <expiry timestamp>
    }

Environment requirements:
    SECRET_KEY — cryptographically random string used to sign JWTs.
                 Must be set in .env. Generate with:
                 python -c "import secrets; print(secrets.token_hex(32))"
"""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt  # noqa: F401 — JWTError re-exported for callers

_SECRET_KEY: str | None = os.getenv("SECRET_KEY")
if not _SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not set. "
        "Add it to backend/.env before starting the application. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

_BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt (12 rounds).

    Args:
        password: Plain-text password from the registration request.

    Returns:
        A bcrypt hash string safe to store in the database (column: password_hash).

    Note:
        bcrypt automatically generates and embeds a unique salt per call,
        so two calls with the same password produce different hashes,
        both of which verify correctly.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored bcrypt hash.

    bcrypt.checkpw uses constant-time comparison internally,
    which prevents timing-based side-channel attacks.

    Args:
        plain_password:  The password supplied by the user at login.
        hashed_password: The bcrypt hash stored in the database.

    Returns:
        True if the password matches, False otherwise.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(subject: str, role: str) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject: The user's UUID as a string. Stored in the "sub" claim.
        role:    The user's role value (e.g. "student"). Stored in "role" claim.

    Returns:
        A signed JWT string.

    Token lifetime: ACCESS_TOKEN_EXPIRE_MINUTES (15 minutes).
    Signing algorithm: HS256.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(payload, _SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Validates:
        - Signature (using SECRET_KEY + HS256)
        - Expiry ("exp" claim) — raises JWTError if token is expired

    Args:
        token: The raw JWT string from the Authorization Bearer header.

    Returns:
        The decoded payload dict containing "sub", "role", "iat", "exp".

    Raises:
        jose.JWTError: If the token is invalid, expired, or tampered.
                       The auth dependency (app/api/deps.py) converts this
                       to an HTTP 401 response.
    """
    return jwt.decode(token, _SECRET_KEY, algorithms=[ALGORITHM])
