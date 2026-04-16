"""Password hashing and JWT issuance/validation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from backend.app.core.config import get_settings


# bcrypt only hashes the first 72 bytes of the password; newer releases raise
# if the input exceeds that. Truncate defensively so verification of legacy
# hashes behaves the same as how they were originally hashed.
_BCRYPT_MAX_BYTES = 72


def _clip(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(_clip(plain), hashed.encode("utf-8"))
    except ValueError:
        return False


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of a plaintext password."""
    return bcrypt.hashpw(_clip(plain), bcrypt.gensalt()).decode("utf-8")


def _create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str) -> str:
    settings = get_settings()
    return _create_token(
        subject,
        timedelta(minutes=settings.access_token_ttl_minutes),
        token_type="access",
    )


def create_refresh_token(subject: str) -> str:
    settings = get_settings()
    return _create_token(
        subject,
        timedelta(days=settings.refresh_token_ttl_days),
        token_type="refresh",
    )


def decode_token(token: str, expected_type: str = "access") -> str:
    """Decode a JWT and return the subject (username). Raises JWTError on failure."""
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != expected_type:
        raise JWTError(f"Expected token type '{expected_type}', got '{payload.get('type')}'")
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise JWTError("Token missing subject")
    return subject
