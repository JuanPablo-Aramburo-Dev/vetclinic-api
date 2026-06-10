"""Cryptographic utilities for authentication.

Pure functions for password hashing and JWT signing/verification.
This module has no dependencies on FastAPI or SQLAlchemy, making it
testable in isolation and reusable from CLI tools or scripts.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

# bcrypt has a maximum input of 72 bytes. Passwords longer than this
# are silently truncated by the underlying algorithm, which is a known
# behavior. We document it here and rely on Pydantic schemas at the
# router boundary to reject overly long passwords.
_BCRYPT_MAX_BYTES = 72


# --------------------------------------------------------------------------- #
# Password hashing
# --------------------------------------------------------------------------- #
def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of the given password.

    The hash includes a randomly generated salt, so calling this
    function twice with the same input returns different outputs.
    Both are valid hashes verifiable against the same password.

    The returned string is bcrypt's standard ASCII format, e.g.
    "$2b$12$...", safe to store in a UTF-8 VARCHAR column.
    """
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True iff the plain password matches the given hash.

    Uses constant-time comparison internally (bcrypt.checkpw) to
    prevent timing attacks.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        # Hash is malformed (e.g., not a valid bcrypt string).
        return False


# --------------------------------------------------------------------------- #
# JWT access tokens
# --------------------------------------------------------------------------- #
def create_access_token(
    subject: int,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token for the given subject.

    The subject is converted to a string per JWT spec (RFC 7519).
    If expires_delta is not provided, uses the default configured in
    settings (access_token_expire_minutes).
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )

    claims: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "type": "access",
    }

    return jwt.encode(claims, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Raises JWTError if the token is malformed, has an invalid signature,
    has expired, or is not an access token. The caller (typically a
    FastAPI dependency) is responsible for translating this into an
    HTTP 401 response.
    """
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )

    if payload.get("type") != "access":
        raise JWTError("Token is not an access token")

    return payload